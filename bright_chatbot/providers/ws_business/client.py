from typing import Dict, Any, Union
import requests


class WhatsAppBusinessClient:
    def __init__(self, from_phone_number: str, auth_token: str):
        self._from_phone_number = from_phone_number
        self._auth_token = auth_token

    @property
    def from_phone_number(self):
        return self._from_phone_number

    @property
    def auth_token(self):
        return self._auth_token

    @property
    def url_endpoint(self):
        return f"https://graph.facebook.com/v16.0/{self.from_phone_number}/messages"

    def get_request_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def send_message(
        self,
        phone_number: str,
        message: str = None,
        image_url: str = None,
        template: Union[Dict[str, Any], None] = None,
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message to an user using the WhatsApp Business API.
        """
        if not (message or template or image_url):
            raise ValueError("Either a message or template must be provided.")
        data = {
            "messaging_product": "whatsapp",
            "to": phone_number,
        }
        if template:
            data["type"] = "template"
            data["template"] = template
        if message:
            data["text"] = {"body": message}
        if image_url:
            data["type"] = "image"
            data["image"] = {
                "link": image_url,
                "caption": message,
            }
        response = requests.post(
            self.url_endpoint, json=data, headers=self.get_request_headers()
        )
        response.raise_for_status()
        result = response.json()
        return result
