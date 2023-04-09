from typing import Dict, List

from twilio.rest import Client
from twilio.request_validator import RequestValidator

from bright_chatbot.providers.base_provider import BaseProvider
from bright_chatbot.configs import settings
from bright_chatbot import models
from bright_chatbot.utils.exceptions import ValidationError


class TwilioProvider(BaseProvider):
    def __init__(self, **twilio_client_kwargs):
        self._client = Client(**twilio_client_kwargs)

    @property
    def client(self) -> Client:
        """
        Returns the object instance of the Twilio client.
        """
        return self._client

    def send_message(self, message: models.MessageResponse):
        parsed_msg = self._parse_message(message)
        self.client.messages.create(**parsed_msg)

    def _parse_message(self, message: models.MessageResponse) -> Dict[str, str]:
        """
        Parses a message into a dictionary that can be sent to the Twilio Client.
        """
        return {
            "body": message.body,
            "media_url": message.media_url,
            "from_": settings.TWILIO_PHONE_NUMBER,
            "to": message.to_user.user_id,
        }

    def verify_signature(
        self,
        callback_url: str,
        request_params: Dict[str, str],
        signature: str,
        raise_on_failure=False,
    ):
        """
        Verifies that an HTTP request is actually coming from Twillio by validating
        the signature of the request.
        """
        validator = RequestValidator(self._auth_token)
        validated = validator.validate(callback_url, request_params, signature)
        if not validated and raise_on_failure:
            raise ValidationError("Twillio request signature couldn't be verified")

    @property
    def _account_sid(self) -> str:
        return self.client.auth[0]

    @property
    def _auth_token(self) -> str:
        return self.client.auth[1]
