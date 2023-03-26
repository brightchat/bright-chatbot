from __future__ import annotations

import abc
import logging
from typing import Type, Any

import openai

from bright_chatbot import client
from bright_chatbot import models


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
        client: client.OpenAIChatClient,
    ):
        self._client = client
        self._openai_lib = openai_lib
        self._logger = logging.getLogger(f"{__package__}.{self.__class__.__name__}")

    @property
    def openai(self) -> openai:
        return self._openai_lib

    @property
    def client(self):
        return self._client

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abc.abstractmethod
    def reply(
        self,
        prompt: models.MessagePrompt,
        user_session: models.UserSession,
        **kwargs: Any,
    ) -> models.HandlerOutput:
        """
        Generates a response to a message prompt and sends it to the user via the
        communication provider.
        """
        raise NotImplementedError

    @property
    def backend(self):
        """
        Backend object used to store and retrieve data of the chat.
        """
        return self._client.backend

    @property
    def provider(self):
        """
        Communication provider used to send messages.
        """
        return self._client.provider
