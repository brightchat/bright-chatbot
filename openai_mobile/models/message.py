from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, validator, Field

from openai_mobile.models.user import User


class MessagePrompt(BaseModel):
    """
    Represents a message from a user to the application.
    """

    body: str
    from_user: User
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    def to_text_repr(self) -> str:
        """
        Returns a string representation of the content of the message.
        """
        return self.body

    def to_chat_repr(self) -> Dict[str, str]:
        """
        Returns a string representation of the message that can be used for chat completions
        """
        return {
            "role": "user",
            "content": f"{self.created_at.isoformat()}: {self.to_text_repr()}",
        }


class MessageResponse(BaseModel):
    """
    Represents a response to a message sent to the application.
    """

    body: str
    to_user: User
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    media_url: str = None
    is_empty: bool = False  # 204 http status code
    is_invalid: bool = False  # 400 http status code
    is_flagged: bool = False  # 422 http status code
    is_quota_surpassed: bool = False  # 429 http status code
    is_error: bool = False  # 500 http status code
    is_in_maintenance: bool = False  # 503 http status code
    status_code: Optional[int] = 200

    @validator("is_empty", always=True)
    def set_is_empty(cls, v, values):
        if not values.get("body") and not values.get("media_url"):
            return True
        return v

    @validator("status_code", always=True)
    def set_status_code(cls, v, values):
        if values.get("is_empty"):
            return 204
        if values.get("is_invalid"):
            return 400
        if values.get("is_flagged"):
            return 422
        if values.get("is_quota_surpassed"):
            return 429
        if values.get("is_error"):
            return 500
        return v

    def to_text_repr(self) -> str:
        """
        Returns a string representation of the content of the message.
        """
        if self.media_url:
            return f"Dalia: '{self.body}'"
        return self.body

    def to_chat_repr(self) -> Dict[str, str]:
        """
        Returns a string representation of the message that can be used for chat completions
        """
        if self.media_url:
            return {"role": "user", "content": self.to_text_repr()}
        return {"role": "assistant", "content": self.to_text_repr()}
