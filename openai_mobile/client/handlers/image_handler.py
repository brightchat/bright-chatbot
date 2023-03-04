from typing import Any, Dict, List, Literal

from openai_mobile.client.handler import OpenAITaskBaseHandler
from openai_mobile.configs.settings import ProjectSettings
from openai_mobile.models import MessagePrompt, MessageResponse, UserSession


class ImageGenerationHandler(OpenAITaskBaseHandler):
    """
    Handler for the task of generating an image from a prompt.
    """

    def reply(
        self,
        prompt: MessagePrompt,
        parsed_img_prompt: str,
        user_session: UserSession,
    ) -> None:
        """
        Generates a response to a message prompt and sends it to the user via the
        communication provider.
        """
        self.logger.info(f"Generating an image from user prompt: '{prompt}'")
        image_url = self._generate_image(parsed_img_prompt, prompt)
        response = MessageResponse(
            body=parsed_img_prompt, media_url=image_url, to_user=prompt.from_user
        )
        self._send_response(response, user_session)
        output = {
            "message_response": response,
            "raw": image_url,
            "parsed": {},
        }
        self.logger.info(f"Image generated with output: '{output}'")
        return output

    def _generate_image(self, img_prompt: str, prompt: MessagePrompt) -> str:
        """
        Generates an image using the OpenAI Image Generation Model (Dall-E)
        """
        image_resp = self.openai.Image.create(
            prompt=img_prompt,
            size=self.get_image_dimmensions(ProjectSettings.IMAGE_GENERATION_SIZE),
            n=1,
            response_format="url",
            user=prompt.from_user.hashed_user_id,
        )
        img = image_resp["data"][0]
        img_url = img["url"]
        return img_url

    @property
    def image_generation_dims(self):
        return {"small": "256x256", "medium": "512x512", "large": "1024x1024"}

    def get_image_dimmensions(self, size: Literal["small", "medium", "large"]):
        return self.image_generation_dims[size]
