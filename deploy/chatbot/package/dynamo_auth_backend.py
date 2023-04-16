import datetime as dt
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
from tables.referral_codes import UsersReferralCodesTableController


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
        # Get user's referral link:
        referral_link = self._get_user_referral_link(user)
        extra_content_system_prompt = (
            "There are a total of 3 subscriptions plans available for the service. "
            "The 'BrightBot Basic' plan is free and allows up to 20 messages and 1 image generation in total "
            "The 'BrightBot Standard' plan costs $4.99 per month and allows up to 50 messages and 5 image generations per day "
            "The 'BrightBot Premium' plan costs $14.99 per month and allows up to 250 messages and 10 high-resolution image generations per day. "
            f"The user is on the '{plan.name}' Suscription Plan of the service. "
            f"With a maximum quota of {plan.messages_quota} {plan.quota_reset_period} messages and {plan.image_generation_quota} image generations. "
            "They can also refer their friends and colleagues to get free rewards on their subscription plan "
            f"by sending them their referral link '{referral_link}'."
            f"The platform where the user is running the application is {settings.RUNNING_PLATFORM}"
            "Here are some useful links for if the user asks for them:\n"
            "- Our website: https://brightbot.chat\n"
            "- Our FAQ: https://brightbot.chat/faq\n"
            "- Our Privacy Policy: https://brightbot.chat/privacy\n"
            "- Our Terms and Conditions: https://brightbot.chat/cookies#Terms%20and%20Conditions.\n"
        )
        # Set the user welcome message:
        settings.USER_WELCOME_MESSAGE = plan.get_welcome_message(referral_link)
        # Create the user's session config:
        session_config = UserSessionConfig(
            max_image_requests=(
                plan.image_generation_quota - img_used_quota
                if plan.image_generation_quota
                else None
            ),
            image_generation_size=plan.image_resolution_size,
            extra_content_system_prompt=extra_content_system_prompt,
            user_referral_link=referral_link,
            user_plan=plan.name,
        )
        logging.getLogger("bright_chatbot").debug(
            f"Set user session config to '{session_config.dict()}'"
        )
        return session_config

    def _get_user_referral_link(self, user: User) -> str:
        referral_code, _ = self.__get_or_create_referral_code(user)
        code_text_url = quote(f"BrightBot referral: {referral_code}")
        phone_number = settings.WHATSAPP_BUSINESS_FROM_PHONE_NUMBER
        url = f"https://wa.me/{phone_number}?text={code_text_url}"
        return url

    def __get_or_create_referral_code(self, user: User) -> Tuple[str, bool]:
        referral_table = UsersReferralCodesTableController(
            client=self.controller.client
        )
        created = False
        referral_code = referral_table.get_user_referral_code(user.user_id)
        if not referral_code:
            while not created:
                referral_code = self.__generate_referral_code()
                try:
                    referral_table.record_user_referral_code(
                        user.user_id, referral_code
                    )
                except ValueError:
                    continue
                created = True
        return referral_code, created

    def __generate_referral_code(self) -> str:
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
        return len(list(filter(lambda x: x["ImageId"].get("S"), user_conversation)))

    def _get_user_subscription_plan(self, user: User) -> SubscriptionPlan:
        user_subscription = self._get_user_subscription(user)
        if user_subscription is not None:
            logging.getLogger("bright_chatbot").debug(
                f"User has subscription '{user_subscription}'"
            )
            if user_subscription in (
                BrightBotPlans.StandardPlan.name,
                BrightBotPlans.StandardPlan.id
            ):
                plan = BrightBotPlans.StandardPlan
            elif user_subscription in (
                BrightBotPlans.PremiumPlan.name,
                BrightBotPlans.PremiumPlan.id
            ):
                plan = BrightBotPlans.PremiumPlan
            else:
                raise ValueError(
                    f"Subscription Plan '{user_subscription}' not detected"
                )
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
        if period == "daily":
            # Retrieve all messages from the user from the beginning of the day
            day_start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif period == "weekly":
            # Retrieve all messages from the user from the beginning of the week
            day_start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_start_date -= dt.timedelta(days=day_start_date.weekday())
        elif period == "monthly":
            # Retrieve all messages from the user from the beginning of the month
            day_start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0, day=1
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
        user_number = "+" + user.user_id.split("+")[-1]
        user_stripe_subscription = self._get_stripe_customer_subscription(user_number)
        return user_stripe_subscription

    def _get_stripe_customer_subscription(self, user_number: str) -> Union[str, None]:
        """
        Given a phone number, returns the name of the subscription plan
        that the user has in Stripe.
        """
        customers = stripe.Customer.search(
            query=f"phone:'{user_number}'", expand=["data.subscriptions"]
        )
        if customers.is_empty:
            return None
        customer_data = pd.json_normalize(customers.data).iloc[0]
        subscription_data = customer_data["subscriptions.data"]
        if not subscription_data:
            return None
        # Get the first active or trialing subscription:
        active_subscription = None
        for subscription in subscription_data:
            if subscription["status"] in ("active", "trialing"):
                active_subscription = subscription
                break
        if not active_subscription:
            return None
        product_id = active_subscription["plan"]["product"]
        products = stripe.Product.list(active=True, limit=100)
        products_df = pd.DataFrame(products["data"])
        customer_product = products_df[products_df["id"] == product_id].iloc[0]
        return customer_product["name"]
