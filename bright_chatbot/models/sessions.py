from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from bright_chatbot.configs import settings
from bright_chatbot.models.user import User


class UserSessionConfig(BaseModel):
    """
    Configuration for a user session.
    """

    max_image_requests: Optional[int] = settings.MAX_IMAGE_REQUESTS_PER_SESSION
    image_generation_size: Optional[str] = settings.IMAGE_GENERATION_SIZE
    extra_content_system_prompt: Optional[str] = settings.EXTRA_CONTENT_SYSTEM_PROMPT
    user_referral_link: Optional[str] = settings.USER_REFERRAL_LINK
    user_plan: Optional[str] = None


class UserSession(BaseModel):
    """
    Model that stores information about a user session.
    """

    user: User
    session_id: str
    session_start: datetime
    session_end: datetime
    session_quota: int = settings.MAX_REQUESTS_PER_SESSION
    session_config: UserSessionConfig = UserSessionConfig()
