from __future__ import annotations
import abc

from bright_chatbot import models


class BaseProvider(abc.ABC):
    @abc.abstractmethod
    def send_message(self, message: models.MessageResponse) -> None:
        """
        Sends a message to a user using the communication provider's API.
        """
        raise NotImplementedError()
