import abc
from typing import List, Union

from bright_chatbot.models import User, UserSession, MessagePrompt, MessageResponse
from bright_chatbot.configs import settings


class BaseDataBackend(abc.ABC):
    @abc.abstractmethod
    def get_latest_user_session(self, user: User) -> Union[UserSession, None]:
        """
        Returns the latest active session of an user.
        Returns None if the user has no active sessions.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def create_user_session(
        self, user: User, sess_quota: int = settings.MAX_REQUESTS_PER_SESSION
    ) -> UserSession:
        """
        Creates a new session for an user.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def end_user_session(self, user: User) -> None:
        """
        Forcefully ends a user's latest session.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_count_of_active_sessions(self) -> int:
        """
        Returns the total number of active sessions
        across all users.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_count_of_session_prompts(self, session: UserSession) -> int:
        """
        Returns the number of prompts that the user has sent in the current session.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_session_chat_history(
        self, session: UserSession
    ) -> List[Union[MessagePrompt, MessageResponse]]:
        """
        Returns the chat history of a session.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_message_prompt(
        self, prompt: MessagePrompt, user_session: UserSession
    ) -> None:
        """
        Saves a message prompt to the database.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_message_response(
        self, response: MessageResponse, user_session: UserSession
    ) -> None:
        """
        Saves a message response to the database.
        """
        raise NotImplementedError()
