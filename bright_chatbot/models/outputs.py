from typing import List, Dict, Any, Literal


from pydantic import BaseModel

from bright_chatbot.models.message import MessageResponse, MessagePrompt


class HandlerOutput(BaseModel):
    """
    Represents the output of a handler
    """

    message_prompt: MessagePrompt
    message_response: MessageResponse
    requested_features: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
