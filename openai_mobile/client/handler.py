import abc
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Type

import openai

from openai_mobile.backends.base_backend import BaseDataBackend
from openai_mobile.models import MessagePrompt, MessageResponse, UserSession
from openai_mobile.providers.base_provider import BaseProvider


class OpenAITaskBaseHandler(abc.ABC):
    """
    Base class for all OpenAI task handlers.

    A task handler can run a specific task with the OpenAI API given a prompt from the user and
    generate a reply.

    Various tasks can include image generation, text generation, etc.
    """

    def __init__(
        self,
        openai_lib: openai,
        thread_pool: "ThreadPoolExecutor",
        backend: Type["BaseDataBackend"],
        provider: Type["BaseProvider"],
    ):
        self._thread_pool = thread_pool
        self._backend = backend
        self._provider = provider
        self._responses_generated = []
        self._openai_lib = openai_lib
        self._logger = logging.getLogger(f"{__package__}.{self.__class__.__name__}")

    @property
    def openai(self) -> openai:
        return self._openai_lib

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abc.abstractmethod
    def reply(self, prompt: MessagePrompt, *args, **kwargs) -> None:
        """
        Generates a response to a message prompt and sends it to the user via the
        communication provider.
        """
        raise NotImplementedError

    @property
    def backend(self) -> Type["BaseDataBackend"]:
        """
        Backend object used to store and retrieve data of the chat.
        """
        return self._backend

    @property
    def provider(self) -> Type["BaseProvider"]:
        """
        Communication provider used to send messages.
        """
        return self._provider

    def _send_response(
        self, message: MessageResponse, user_session: UserSession
    ) -> None:
        """
        Sends a message to the user via the communication provider
        and saves it to the backend.

        Both operations are performed asynchronously.
        """
        print("Sending message response: ", message)
        self._responses_generated.append(message)
        self._thread_pool.submit(self.provider.send_message, message)
        self._thread_pool.submit(
            self.backend.save_message_response, message, user_session
        )
