import logging
import os

from openai_mobile.backends import DynamodbBackend
from openai_mobile.models import User, UserSession
from openai_mobile.configs import ProjectSettings
import pandas as pd
import stripe

from datetime import datetime


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
        session_quota = self._get_user_session_quota(user)
        session_obj = self.controller.sessions.record_user_session(
            user.hashed_user_id, messages_quota=session_quota
        )
        session_id = session_obj["SessionId"]["S"]
        user_session = UserSession(
            user=user,
            session_id=session_id,
            session_start=session_obj["TimestampCreated"]["N"],
            session_end=session_obj["SessionTTL"]["N"],
            session_quota=session_quota,
        )
        return user_session

    def _get_user_session_quota(self, user: User) -> int:
        if user.is_admin:
            return None
        max_daily_quota = ProjectSettings.MAX_REQUESTS_PER_SESSION
        user_subscription = self._get_user_subscription(user)
        # Get used quota
        used_quota = self._get_user_used_quota(user)
        if user_subscription is not None:
            logging.getLogger("openai_mobile").debug(
                f"User {user.user_id} has subscription {user_subscription}"
            )
            user_subscription = user_subscription.title()
            if user_subscription in ("Standard", "Standard Plan", "Standard Test Plan"):
                max_daily_quota = 100
            if user_subscription in ("Premium", "Premium Plan"):
                max_daily_quota = 10e6
        logging.getLogger("openai_mobile").debug(
            f"User {user.user_id} does not have a subscription"
        )
        return max_daily_quota - used_quota

    def _get_user_used_quota(self, user: User) -> int:
        """
        Gets the number of messages the user has sent today
        """
        day_start_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        user_conversation = self.controller.chats.get_user_chat_messages(
            user_id=user.hashed_user_id, from_date=day_start_date
        )
        user_msgs = list(filter(lambda x: x["Agent"]["S"] == "user", user_conversation))
        return len(user_msgs)

    def _get_user_subscription(self, user: User) -> str:
        """
        Checks if the user has an active subscription with Stripe
        """
        active_customers = self.__get_active_stripe_customers()
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

    def __get_active_stripe_customers(self) -> pd.DataFrame:
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
