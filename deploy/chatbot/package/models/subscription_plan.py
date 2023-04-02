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

    """Number of sessions allowed per day in the plan"""
    sessions_quota: Union[int, None]

    """Number of messages allowed per session in the plan"""
    messages_quota: Union[int, None]

    """Number of image requests allowed per session in the plan"""
    image_generation_quota: Union[int, None]

    """Resolution of the image generated in the plan"""
    image_resolution_size: Literal["small", "medium", "large"]
