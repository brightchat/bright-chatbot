from typing import Dict

from twilio.rest import Client
from twilio.request_validator import RequestValidator

from openai_mobile.providers.base_provider import BaseProvider
from openai_mobile.configs.settings import ProjectSettings
from openai_mobile.models import MessageResponse
from openai_mobile.utils.exceptions import ValidationError
from openai_mobile.utils.functional import classproperty


class TwilioProvider(BaseProvider):
    def __init__(self):
        self._client = Client(self.account_sid, self.auth_token)

    @property
    def client(self):
        """
        Returns the object instance of the Twilio client.
        """
        return self._client

    def send_message(self, message: MessageResponse):
        parsed_msg = self._parse_message(message)
        self.client.messages.create(**parsed_msg)

    def _parse_message(self, message: MessageResponse) -> Dict[str, str]:
        """
        Parses a message into a dictionary that can be sent to the Twilio Client.
        """
        return {
            "body": message.body,
            "media_url": message.media_url,
            "from_": ProjectSettings.TWILIO_PHONE_NUMBER,
            "to": message.to_user.user_id,
        }

    @classmethod
    def verify_signature(
        cls,
        callback_url: str,
        request_params: Dict[str, str],
        signature: str,
        raise_on_failure=False,
    ):
        """
        Verifies that an HTTP request is actually coming from Twillio by validating
        the signature of the request.
        """
        validator = RequestValidator(cls.auth_token)
        validated = validator.validate(callback_url, request_params, signature)
        if not validated and raise_on_failure:
            raise ValidationError("Twillio request signature couldn't be verified")

    @classproperty
    def account_sid(cls) -> str:
        return ProjectSettings.TWILIO_ACCOUNT_SID

    @classproperty
    def auth_token(cls) -> str:
        return ProjectSettings.TWILIO_AUTH_TOKEN
