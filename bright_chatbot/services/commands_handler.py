import re

from bright_chatbot.services._base_handler import OpenAITaskBaseHandler
from bright_chatbot.models import (
    MessagePrompt,
    MessageResponse,
    UserSession,
    HandlerOutput,
)
from bright_chatbot.configs import settings


class ChatCommandsHandler(OpenAITaskBaseHandler):
    """
    Handler for the task of generating a reply to a user's command.
    """

    _IMG_CMD_REGEX = re.compile(r"/(img|image)\s+(.+)")

    def reply(
        self,
        prompt: MessagePrompt,
        user_session: UserSession,
    ) -> HandlerOutput:
        """
        Generates a response to a command prompt.
        """
        self.logger.info(f"Generating a response to the command: '{prompt.body}'")
        if prompt.body in ["/exit", "/quit", "/reset", "/bye"]:
            output = self._handle_end_session_cmd(prompt, user_session)
        # Match /img or /image command followed by a space and then the image prompt
        elif re.match(self._IMG_CMD_REGEX, prompt.body):
            output = self._handle_img_cmd(prompt, user_session)
        elif prompt.body == "/help":
            output = self._handle_help_cmd(prompt, user_session)
        elif prompt.body == "/referral":
            output = self._handle_referral_cmd(prompt, user_session)
        else:
            output = self._handle_not_recognized(prompt, user_session)
        self.logger.info(f"Sent reply to command with output: '{output}'")
        return output

    def _handle_img_cmd(self, prompt: str, user_session: UserSession) -> HandlerOutput:
        image_prompt = re.match(self._IMG_CMD_REGEX, prompt.body).group(2)
        response = MessageResponse(
            body=f"Processing image '{image_prompt}'",
            to_user=user_session.user,
        )
        self.client.send_response(response)
        self.client.save_response(response, user_session)
        output = HandlerOutput(
            message_prompt=prompt,
            message_response=response,
            requested_features={"generate_image": image_prompt},
        )
        return output

    def _handle_referral_cmd(self, prompt, user_session: UserSession) -> HandlerOutput:
        """
        Handles the referral command.
        """
        response = MessageResponse(
            body=f"Here's a link you can share to refer your friends: {user_session.session_config.user_referral_link}",
            to_user=user_session.user,
        )
        self.client.send_response(response)
        self.client.save_response(response, user_session)
        output = HandlerOutput(
            message_prompt=prompt,
            message_response=response,
        )
        return output

    def _handle_end_session_cmd(
        self, prompt, user_session: UserSession
    ) -> HandlerOutput:
        """
        Handles the end of a user session.
        """
        self.client.end_user_session(user_session.user)
        response = MessageResponse(
            body="Thank you for chatting with me! Have a nice day!",
            to_user=user_session.user,
        )
        self.client.send_response(response)
        self.client.save_response(response, user_session)
        output = HandlerOutput(
            message_prompt=prompt,
            message_response=response,
        )
        return output

    def _handle_help_cmd(self, prompt, user_session: UserSession) -> HandlerOutput:
        """
        Handles the help command.
        """
        response = MessageResponse(
            body="Here's a list of commands you can use:\n\n"
            "/help - Show this message\n"
            "/reset or /quit - End the chat session\n"
            "/image <prompt> or /img <prompt> - Generate an image using the given prompt\n"
            "/referral - Get a link to refer your friends\n"
            "/referral <code> - Use a referral code to get a discount\n",
            to_user=user_session.user,
        )
        self.client.send_response(response)
        self.client.save_response(response, user_session)
        output = HandlerOutput(
            message_prompt=prompt,
            message_response=response,
        )
        return output

    def _handle_not_recognized(
        self, prompt, user_session: UserSession
    ) -> HandlerOutput:
        """
        Handles the case when a command is not recognized.
        """
        response = MessageResponse(
            body="Sorry, I didn't understand that command. Use /help to see the list of available commands.",
            to_user=user_session.user,
        )
        self.client.send_response(response)
        self.client.save_response(response, user_session)
        output = HandlerOutput(
            message_prompt=prompt,
            message_response=response,
        )
        return output
