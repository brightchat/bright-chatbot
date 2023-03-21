from typing import Dict, List

from twilio.rest import Client
from twilio.request_validator import RequestValidator

from openai_mobile.providers.base_provider import BaseProvider
from openai_mobile.configs.settings import ProjectSettings
from openai_mobile import models
from openai_mobile.utils.exceptions import ValidationError


class TwilioProvider(BaseProvider):
    MSG_LENGTH_LIMIT = 1600

    def __init__(self, **twilio_client_kwargs):
        self._client = Client(**twilio_client_kwargs)

    @property
    def client(self) -> Client:
        """
        Returns the object instance of the Twilio client.
        """
        return self._client

    def send_message(self, message: models.MessageResponse):
        for msg in self._split_message(message):
            parsed_msg = self._parse_message(msg)
            self.client.messages.create(**parsed_msg)

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

    def _parse_message(self, message: models.MessageResponse) -> Dict[str, str]:
        """
        Parses a message into a dictionary that can be sent to the Twilio Client.
        """
        return {
            "body": message.body,
            "media_url": message.media_url,
            "from_": ProjectSettings.TWILIO_PHONE_NUMBER,
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
