from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from bright_chatbot.configs import settings
from bright_chatbot.utils import hash_user_id


class User(BaseModel):
    """
    Model that stores information about a user sending
    messages to the application.
    """

    """ Unique identifier of the user for the communication provider. e.g. A phone number. """
    user_id: str

    @property
    def is_admin(self) -> bool:
        return self.user_id in settings.ADMIN_USERS

    @property
    def hashed_user_id(self) -> str:
        return hash_user_id(self.user_id)


class UserSessionConfig(BaseModel):
    max_image_requests: Optional[int] = settings.MAX_IMAGE_REQUESTS_PER_SESSION
    image_generation_size: Optional[str] = settings.IMAGE_GENERATION_SIZE
    extra_content_system_prompt: Optional[str] = settings.EXTRA_CONTENT_SYSTEM_PROMPT
    user_refferal_link: Optional[str] = settings.USER_REFFERAL_LINK


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
