from typing import Any, Dict, List

from openai_mobile.client.handler import OpenAITaskBaseHandler
from openai_mobile.models.message import MessagePrompt, MessageResponse
from openai_mobile.models.user import UserSession


class ChatCommandsHandler(OpenAITaskBaseHandler):
    """
    Handler for the task of generating a reply to a user message.
    """

    def reply(
        self,
        prompt: MessagePrompt,
        user_session: UserSession,
    ) -> None:
        """
        Generates a response to a command prompt.
        """
        self.logger.info(f"Generating a response to the command: '{prompt}'")
        response = None
        if prompt.body in ["/exit", "/quit", "/reset", "/bye"]:
            response = self._handle_end_session_request(user_session)
        if response:
            self.client.send_response(response)
            self.client.save_response(response, user_session)
        output = {
            "message_response": response,
        }
        self.logger.info(f"Sent reply to commoand with output: '{output}'")
        return output

    def _handle_end_session_request(self, user_session: UserSession) -> MessageResponse:
        """
        Handles the end of a user session.
        """
        self.client.end_user_session(user_session.user)
        return MessageResponse(
            body="Thank you for chatting with me! Have a nice day!",
            to_user=user_session.user,
        )
