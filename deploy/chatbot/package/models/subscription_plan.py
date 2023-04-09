import pathlib
from typing import Literal, Union

from pydantic import BaseModel


class SubscriptionPlan(BaseModel):
    """
    Model that stores information about a subscription plan.
    """

    """ Unique identifier of the subscription plan. """
    id: str

    """ Name of the subscription plan. """
    name: str

    """ Description of the subscription plan. """
    description: str

    """Number of sessions allowed per period in the plan, None if unlimited"""
    sessions_quota: Union[int, None]

    """Number of messages allowed per session in the plan, None if unlimited"""
    messages_quota: Union[int, None]

    """Number of image requests allowed per session in the plan, None if unlimited"""
    image_generation_quota: Union[int, None]

    """Resolution of the images generated in the plan"""
    image_resolution_size: Literal["small", "medium", "large"]

    """Period of time in which the quota is reset."""
    quota_reset_period: Union[Literal["day"], None] = None

    @property
    def quota_reset_period_text(self) -> str:
        quota_reset_period_text = f" per {self.quota_reset_period}."
        if not self.quota_reset_period:
            quota_reset_period_text = " in total."
        return quota_reset_period_text

    def get_welcome_message(self, refferal_link: str) -> str:
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
            REFFERAL_LINK=refferal_link,
        )
        return welcome_message
