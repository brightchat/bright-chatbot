from datetime import datetime
import logging
import os

from bright_chatbot.backends import DynamodbBackend
from bright_chatbot.models import User, UserSession
from bright_chatbot.configs import settings
import pandas as pd
import stripe

import subscription_plans as BrightBotPlans
from models.subscription_plan import SubscriptionPlan


class DynamoSessionAuthBackend(DynamodbBackend):
    """
    Extends the DynamoDB backend to add authentication features
    for specific users and users subscriptions (via Stripe).
    It also implements a daily quota for each user depending on
    which subscription they have.

    #TODO: This could be a Mixin
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stripe.api_key = os.environ["STRIPE_API_KEY"]

    def create_user_session(self, user: User) -> UserSession:
        day_conversation = self._get_user_day_conversation(user)
        user_subscription_plan = self._get_user_subscription_plan(user)
        used_quota = self._get_user_used_quota(day_conversation)
        img_generation_used_quota = self._img_generation_used_quota(day_conversation)
        session_quota = user_subscription_plan.messages_quota - used_quota
        self._config_package_by_plan(user_subscription_plan, img_generation_used_quota)
        session_obj = self.controller.sessions.record_user_session(
            user.hashed_user_id, messages_quota=session_quota
        )
        session_id = session_obj["SessionId"]["S"]
        user_session = UserSession(
            user=user,
            session_id=session_id,
            session_start=session_obj["TimestampCreated"]["N"],
            session_end=session_obj["SessionTTL"]["N"],
            session_quota=session_quota if not user.is_admin else 10e6,
        )
        return user_session

    def _config_package_by_plan(
        self, plan: SubscriptionPlan, img_used_quota: int
    ) -> None:
        """
        Configures the number of messages per day for each subscription plan.
        """
        settings.MAX_IMAGE_REQUESTS_PER_SESSION = (
            plan.image_generation_quota - img_used_quota
            if plan.image_generation_quota
            else None
        )
        settings.IMAGE_GENERATION_SIZE = plan.image_resolution_size
        logging.getLogger("bright_chatbot").debug(
            f"Set image generation quota to {settings.MAX_IMAGE_REQUESTS_PER_SESSION} "
            f"and image size to {settings.IMAGE_GENERATION_SIZE}"
        )
        settings.EXTRA_CONTENT_SYSTEM_PROMPT = (
            f"The user is on the '{plan.name}' Suscription Plan of the service."
            f"With a quota of {plan.messages_quota} messages and {plan.image_generation_quota} image generations per day."
        )

    def _img_generation_used_quota(self, user_conversation: list) -> int:
        """
        Gets the number of images the user has generated today
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

    def _get_user_day_conversation(self, user: User) -> list:
        day_start_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        user_conversation = self.controller.chats.get_user_chat_messages(
            user_id=user.hashed_user_id, from_date=day_start_date
        )
        return user_conversation

    def _get_user_used_quota(self, user_conversation: list) -> int:
        """
        Gets the number of messages the user has sent today
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
