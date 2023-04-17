from __future__ import annotations

from typing import List, Dict, Union, Type

from pydantic import BaseModel

from bright_chatbot.configs import settings
from bright_chatbot.models.sessions import UserSession
from bright_chatbot.models.message import MessagePrompt, MessageResponse
from bright_chatbot.backends.base_backend import BaseDataBackend


class ChatHistory(BaseModel):
    """
    Represents the chat history between a user and the application
    in a given session.
    """

    session: UserSession
    messages: List[Union[MessagePrompt, MessageResponse]] = []

    def to_chat_representation(self) -> List[Dict[str, str]]:
        """
        Returns a list of dicts that can be used for chat completions
        """
        chat_history_repr = []
        # Add the initial system prompt containing instructions and the status of the session
        system_prompt = self._get_chat_system_role_prompt()
        sess_status_prompt = self._get_sess_status_prompt()
        chat_history_repr += [
            {"role": "system", "content": system_prompt},
            {
                "role": "system",
                "content": sess_status_prompt,
            },
        ]
        if self.session.session_config.extra_content_system_prompt:
            chat_history_repr.append(
                {
                    "role": "system",
                    "content": self.session.session_config.extra_content_system_prompt,
                }
            )
        # Only use the messages that don't exceed the chat completion length limit
        # Go backwards in the list of messages to get the most recent ones
        for msg_idx in range(len(self.messages) - 1, -1, -1):
            if (
                self.get_concat_chat_length(
                    [*chat_history_repr, self.messages[msg_idx].to_chat_repr()]
                )
                >= settings.CHAT_COMPLETION_LENGTH_LIMIT
            ):
                settings.logger.debug(
                    f"Chat completion length limit reached, using only the last {len(chat_history_repr)} messages"
                )
                break
            chat_history_repr.append(self.messages[msg_idx].to_chat_repr())
        return chat_history_repr

    def get_concat_chat_length(self, messages_repr: List[Dict[str, str]] = None) -> int:
        """
        Returns the total length of the chat history
        when concatenated as a single string
        """
        return sum(len(message["content"]) for message in messages_repr)

    def refresh_from_backend(
        self,
        backend: Type[BaseDataBackend],
        exclude: Union[MessagePrompt, MessageResponse] = None,
    ) -> None:
        """
        Retrieves the chat history from the backend and updates the chat history
        Optionally, a message can be excluded from the update
        """
        self.messages = backend.get_session_chat_history(self.session)
        if exclude:
            try:
                self.messages.remove(exclude)
            except ValueError:
                pass

    def _get_chat_system_role_prompt(self) -> str:
        """
        Returns the system prompt for the chat completion
        """
        chat_system_role_prompt = settings.CHAT_SYSTEM_ROLE_PROMPT
        return chat_system_role_prompt

    def _get_sess_status_prompt(self) -> str:
        """
        Returns the prompt with the status of the session
        at the beginning of the chat
        """
        session_status_prompt: str = settings.SESSION_STATUS_PROMPT
        return session_status_prompt.format(
            session_start_iso=self.session.session_start.isoformat(),
            session_end_iso=self.session.session_end.isoformat(),
            session_quota=self.session.session_quota,
        ).strip()

    def get_chat_responses(self) -> List[MessageResponse]:
        return list(filter(lambda x: isinstance(x, MessageResponse), self.messages))

    def get_chat_prompts(self) -> List[MessagePrompt]:
        return list(filter(lambda x: isinstance(x, MessagePrompt), self.messages))

    def get_image_generation_responses(self) -> List[MessageResponse]:
        responses = self.get_chat_responses()
        return list(filter(lambda x: x.media_url, responses))
