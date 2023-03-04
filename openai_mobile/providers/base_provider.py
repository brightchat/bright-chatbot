import abc

from openai_mobile.models.message import MessageResponse
from openai_mobile.models.user import User


class BaseProvider(abc.ABC):
    @abc.abstractmethod
    def send_message(self, message: MessageResponse) -> None:
        """
        Sends a message to a user using the communication provider's API.
        """
        raise NotImplementedError()
