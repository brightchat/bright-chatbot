from typing import Literal

from bright_chatbot.services._base_handler import OpenAITaskBaseHandler
from bright_chatbot.configs.settings import ProjectSettings
from bright_chatbot import models


class ImageGenerationHandler(OpenAITaskBaseHandler):
    """
    Handler for the task of generating an image from a prompt.
    """

    def reply(
        self,
        prompt: models.MessagePrompt,
        user_session: models.UserSession,
        image_prompt: str,
    ) -> models.HandlerOutput:
        """
        Generates a response to a message prompt and sends it to the user via the
        communication provider.
        """
        self.logger.info(f"Generating an image from user prompt: '{prompt}'")
        image_url = self._generate_image(image_prompt, prompt)
        response = models.MessageResponse(
            body=image_prompt, media_url=image_url, to_user=prompt.from_user
        )
        self.client.send_response(response)
        self.client.save_response(response, user_session)
        output = models.HandlerOutput(
            message_prompt=prompt,
            message_response=response,
        )
        self.logger.info(f"Image generated with output: '{output}'")
        return output

    def _generate_image(self, img_prompt: str, prompt: models.MessagePrompt) -> str:
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
