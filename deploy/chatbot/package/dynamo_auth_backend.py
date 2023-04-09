from datetime import datetime
import logging
import os
import random
import string
from typing import Literal, Tuple, Union
from urllib.parse import quote

from bright_chatbot.backends import DynamodbBackend
from bright_chatbot.models import User, UserSession, UserSessionConfig
from bright_chatbot.configs import settings
import pandas as pd
import stripe

import subscription_plans as BrightBotPlans
from models.subscription_plan import SubscriptionPlan
from tables.refferal_codes import UsersRefferalCodesTableController


class DynamoSessionAuthBackend(DynamodbBackend):
    """
    Extends the DynamoDB backend to add authentication features
    for specific users and users subscriptions (via Stripe).
    It also implements a daily quota for each user depending on
    which subscription they have.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stripe.api_key = os.environ["STRIPE_API_KEY"]

    def create_user_session(self, user: User) -> UserSession:
        user_plan = self._get_user_subscription_plan(user)
        user_conversation = self._get_user_conversation(
            user, period=user_plan.quota_reset_period
        )
        used_quota = self._count_user_msgs_in_convo(user_conversation)
        img_generation_used_quota = self._count_images_in_convo(user_conversation)
        session_quota = user_plan.messages_quota - used_quota
        session_config = self._get_session_config(
            user, user_plan, img_generation_used_quota
        )
        session_obj = self.controller.sessions.record_user_session(
            user.hashed_user_id,
            messages_quota=session_quota,
            session_config=session_config.dict(),
        )
        session_id = session_obj["SessionId"]["S"]
        user_session = UserSession(
            user=user,
            session_id=session_id,
            session_start=session_obj["TimestampCreated"]["N"],
            session_end=session_obj["SessionTTL"]["N"],
            session_quota=session_quota if not user.is_admin else 10e6,
            session_config=session_config,
        )
        return user_session

    def _get_session_config(
        self, user: User, plan: SubscriptionPlan, img_used_quota: int
    ) -> UserSessionConfig:
        """
        Configures the number of messages per day for each subscription plan.
        """
        extra_content_system_prompt = (
            f"The user is on the '{plan.name}' Suscription Plan of the service."
            f"With a maximum quota of {plan.messages_quota} messages and {plan.image_generation_quota} image generations"
        )
        extra_content_system_prompt += plan.quota_reset_period_text
        # Get user's refferal link:
        refferal_link = self._get_user_refferal_link(user)
        # Set the user welcome message:
        settings.USER_WELCOME_MESSAGE = plan.get_welcome_message(refferal_link)
        # Create the user's session config:
        session_config = UserSessionConfig(
            max_image_requests=(
                plan.image_generation_quota - img_used_quota
                if plan.image_generation_quota
                else None
            ),
            image_generation_size=plan.image_resolution_size,
            extra_content_system_prompt=extra_content_system_prompt,
            user_refferal_link=refferal_link,
        )
        logging.getLogger("bright_chatbot").debug(
            f"Set user session config to '{session_config.dict()}'"
        )
        return session_config

    def _get_user_refferal_link(self, user: User) -> str:
        refferal_code, _ = self.__get_or_create_refferal_code(user)
        code_text_url = quote(f"/refferal {refferal_code}")
        phone_number = settings.WHATSAPP_BUSINESS_FROM_PHONE_NUMBER
        url = f"https://wa.me/{phone_number}?text={code_text_url}"
        return url

    def __get_or_create_refferal_code(self, user: User) -> Tuple[str, bool]:
        refferal_table = UsersRefferalCodesTableController(
            client=self.controller.client
        )
        created = False
        refferal_code = refferal_table.get_user_refferal_code(user.user_id)
        if not refferal_code:
            while not created:
                refferal_code = self.__generate_refferal_code()
                try:
                    refferal_table.record_user_refferal_code(
                        user.user_id, refferal_code
                    )
                except ValueError:
                    continue
                created = True
        return refferal_code, created

    def __generate_refferal_code(self) -> str:
        """
        Generates a random code of 5 characters
        """
        return "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(5)
        )

    def _count_images_in_convo(self, user_conversation: list) -> int:
        """
        Gets the number of images the user has generated in the conversation.
        """
        return len(list(filter(lambda x: x["ImageId"]["S"], user_conversation)))

    def _get_user_subscription_plan(self, user: User) -> SubscriptionPlan:
        user_subscription = self._get_user_subscription(user)
        if user_subscription is not None:
            logging.getLogger("bright_chatbot").debug(
                f"User has subscription '{user_subscription}'"
            )
            if user_subscription in (
                "BrightBot Standard",
                "Standard Plan",
                "Standard Test Plan",
                BrightBotPlans.StandardPlan.id,
            ):
                plan = BrightBotPlans.StandardPlan
            elif user_subscription in (
                "BrightBot Unlimited",
                "Premium Plan",
                BrightBotPlans.PremiumPlan.id,
            ):
                plan = BrightBotPlans.PremiumPlan
        else:
            logging.getLogger("bright_chatbot").debug(
                f"User does not have a subscription"
            )
            plan = BrightBotPlans.BasicPlan
        logging.getLogger("bright_chatbot").debug(f"Set user plan to: {plan}")
        return plan

    def _get_user_conversation(
        self, user: User, period: str = Union[Literal["day"], None]
    ) -> list:
        if period == "day":
            # Retrieve all messages from the user from the beginning of the day
            day_start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif not period:
            day_start_date = None
        user_conversation = self.controller.chats.get_user_chat_messages(
            user_id=user.hashed_user_id, from_date=day_start_date
        )
        return user_conversation

    def _count_user_msgs_in_convo(self, user_conversation: list) -> int:
        """
        Gets the number of messages the user has sent in the conversation.
        """
        user_msgs = list(
            filter(lambda x: x["ChatAgent"]["S"] == "user", user_conversation)
        )
        return len(user_msgs)

    def _get_user_subscription(self, user: User) -> str:
        """
        Checks if the user has an active subscription with Stripe
        """
        active_customers = self._get_active_stripe_customers()
        user_number = "+" + user.user_id.split("+")[-1]
        if (
            active_customers.empty
            or not user_number in active_customers["customer_phone"].values
        ):
            return None
        subscription_data = active_customers[
            active_customers["customer_phone"] == user_number
        ].iloc[0]
        return subscription_data["product_name"]

    def _get_active_stripe_customers(self) -> pd.DataFrame:
        active_subscriptions = stripe.Subscription.list(status="active")
        active_subscriptions_df = pd.DataFrame(active_subscriptions["data"])
        if active_subscriptions_df.empty:
            return active_subscriptions_df
        active_subscriptions_df["product_id"] = active_subscriptions_df["plan"].apply(
            lambda x: x["product"]
        )
        products = stripe.Product.list(active=True)
        products_df = pd.DataFrame(products["data"])
        subscriptions = active_subscriptions_df.merge(
            products_df[["id", "name"]].rename(
                columns={"name": "product_name", "id": "product_id"}
            ),
            on="product_id",
        ).rename(columns={"customer": "customer_id"})
        customers_df = pd.DataFrame(stripe.Customer.list()["data"]).rename(
            columns={
                "id": "customer_id",
                "email": "customer_email",
                "phone": "customer_phone",
            }
        )
        active_customers_df = subscriptions.merge(
            customers_df[["customer_id", "customer_email", "customer_phone"]],
            on="customer_id",
        )
        return active_customers_df
