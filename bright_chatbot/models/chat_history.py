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

        The system role is repeated every 3 messages to ensure that the chat
        completion is not biased towards the user's last messages.
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
        system_prompt_counter = 10
        system_prompt_seq_repetition = 10
        for message in self.messages:
            system_prompt_counter -= 1
            if system_prompt_counter <= 0:
                chat_history_repr.append({"role": "system", "content": system_prompt})
                system_prompt_counter = system_prompt_seq_repetition
            chat_history_repr.append(message.to_chat_repr())
        return chat_history_repr

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
        session_start = self.session.session_start
        return session_status_prompt.format(
            week_day=session_start.strftime("%A"),
            month=session_start.strftime("%B"),
            day=session_start.day,
            year=session_start.year,
            hour=session_start.hour,
            minute=session_start.minute,
            second=session_start.second,
            session_quota=self.session.session_quota,
        ).strip()

    def get_chat_responses(self) -> List[MessageResponse]:
        return list(filter(lambda x: isinstance(x, MessageResponse), self.messages))

    def get_chat_prompts(self) -> List[MessagePrompt]:
        return list(filter(lambda x: isinstance(x, MessagePrompt), self.messages))

    def get_image_generation_responses(self) -> List[MessageResponse]:
        responses = self.get_chat_responses()
        return list(filter(lambda x: x.media_url, responses))
