import pathlib
from typing import Literal, Union

from pydantic import BaseModel


class SubscriptionPlan(BaseModel):
    """
    Model that stores information about a subscription plan.
    """

    id: str
    """ Unique identifier of the subscription plan. """

    name: str
    """ Name of the subscription plan. """

    description: str
    """ Description of the subscription plan. """

    sessions_quota: Union[int, None]
    """Number of sessions allowed per period in the plan, None if unlimited"""

    messages_quota: Union[int, None]
    """Number of messages allowed per session in the plan, None if unlimited"""

    image_generation_quota: Union[int, None]
    """Number of image requests allowed per session in the plan, None if unlimited"""

    image_resolution_size: Literal["small", "medium", "large"]
    """Resolution of the images generated in the plan"""

    quota_reset_period: Union[
        Literal["hourly", "daily", "weekly", "monthly"], None
    ] = None
    """Period of time in which the quota is reset."""

    @property
    def quota_reset_period_text(self) -> str:
        quota_reset_period_text = self.quota_reset_period
        if not self.quota_reset_period:
            quota_reset_period_text = "in total."
        return quota_reset_period_text

    def get_welcome_message(self, referral_link: str) -> str:
        welcome_message_file = (
            pathlib.Path(__file__).parent / "user_welcome_msg_template.txt"
        )
        # Read from file:
        with welcome_message_file.open() as file:
            welcome_message_template = file.read()
        welcome_message = welcome_message_template.format(
            SUBSCRIPTION_PLAN_NAME=self.name,
            SUBSCRIPTION_PLAN_MESSAGE_QUOTA=self.messages_quota,
            SUBSCRIPTION_PLAN_RESET_PERIOD=self.quota_reset_period_text,
            REFERRAL_LINK=referral_link,
        )
        return welcome_message
