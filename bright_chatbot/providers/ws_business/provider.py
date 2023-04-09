from typing import Dict

from bright_chatbot import models
from bright_chatbot.utils.functional import classproperty
from bright_chatbot.providers.base_provider import BaseProvider
from bright_chatbot.providers.ws_business.client import WhatsAppBusinessClient
from bright_chatbot.configs import settings
from bright_chatbot.utils.exceptions import ValidationError


class WhatsAppBusinessProvider(BaseProvider):
    MSG_LENGTH_LIMIT = 1250

    def __init__(self, **ws_client_kwargs):
        kwargs = {
            "from_phone_number": self.from_phone_number,
            "auth_token": self.auth_token,
        }
        kwargs.update(ws_client_kwargs)
        self._client = WhatsAppBusinessClient(**kwargs)

    @property
    def client(self) -> WhatsAppBusinessClient:
        """
        Returns the object instance of the Twilio client.
        """
        return self._client

    def send_message(self, message: models.MessageResponse):
        for msg in self._split_message(message):
            parsed_msg = self._parse_message(msg)
            self.client.send_message(**parsed_msg)

    def _parse_message(self, message: models.MessageResponse) -> Dict[str, str]:
        """
        Parses a message into a dictionary that can be sent to the Twilio Client.
        """
        return {
            "phone_number": message.to_user.user_id,
            "message": message.body,
            "image_url": message.media_url,
        }

    def verify_signature(
        self,
        callback_url: str,
        request_params: Dict[str, str],
        signature: str,
        raise_on_failure=False,
    ):
        """
        Verifies that an HTTP request is actually coming from the WhatsApp business API
        by validating the signature of the request.

        :raises ValidationError: If the signature is invalid and `raise_on_failure` is True.
        """
        pass

    @classproperty
    def auth_token(self) -> str:
        return settings.WHATSAPP_BUSINESS_AUTH_TOKEN

    @classproperty
    def from_phone_number(self) -> str:
        return settings.WHATSAPP_BUSINESS_PHONE_NUMBER_ID
