from datetime import datetime

from pydantic import BaseModel

from openai_mobile.configs import ProjectSettings
from openai_mobile.utils import hash_user_id


class User(BaseModel):
    """
    Model that stores information about a user sending
    messages to the application.
    """

    """ Unique identifier of the user for the communication provider. e.g. A phone number. """
    user_id: str

    @property
    def is_admin(self) -> bool:
        return self.user_id in ProjectSettings.ADMIN_USERS

    @property
    def hashed_user_id(self) -> str:
        return hash_user_id(self.user_id)


class UserSession(BaseModel):
    """
    Model that stores information about a user session.
    """

    user: User
    session_id: str
    session_start: datetime
    session_end: datetime
