from __future__ import annotations
import abc
from typing import List

from bright_chatbot import models


class BaseProvider(abc.ABC):
    MSG_LENGTH_LIMIT = 1250

    @abc.abstractmethod
    def send_message(self, message: models.MessageResponse) -> None:
        """
        Sends a message to a user using the communication provider's API.
        """
        raise NotImplementedError()

    def send_response(self, message: models.MessageResponse) -> None:
        """
        Sends a response message to a user.
        The response is split into multiple messages if it's too long.
        """
        for msg in self._split_message(message):
            self.send_message(msg)

    def _split_message(
        self, message: models.MessageResponse
    ) -> List[models.MessageResponse]:
        """
        Splits a message into multiple messages if it's too long.
        Attempts to split the message at the last line break before the limit.
        """
        if len(message.body) <= self.MSG_LENGTH_LIMIT:
            return [message]
        messages = []
        while len(message.body) > self.MSG_LENGTH_LIMIT:
            split_index = message.body.rfind("\n", 0, self.MSG_LENGTH_LIMIT)
            if split_index == -1:
                split_index = self.MSG_LENGTH_LIMIT
            messages.append(
                models.MessageResponse(
                    body=message.body[:split_index],
                    **message.dict(exclude={"body"}),
                )
            )
            message.body = message.body[split_index:]
        messages.append(message)
        return messages
