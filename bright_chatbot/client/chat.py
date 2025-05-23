from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Dict, List, Tuple, Type, Union

import openai

from bright_chatbot import services
from bright_chatbot.backends.base_backend import BaseDataBackend
from bright_chatbot.providers.base_provider import BaseProvider
from bright_chatbot.configs import settings
from bright_chatbot import models
from bright_chatbot.utils import exceptions
import bright_chatbot.client.errors as error_msgs


class OpenAIChatClient:
    def __init__(
        self,
        backend: Type[BaseDataBackend],
        provider: Type[BaseProvider],
        n_threads: int = 5,
    ):
        openai.api_key = settings.OPENAI_API_KEY
        self._logger = logging.getLogger(f"{__package__}.{self.__class__.__name__}")
        self._backend = backend
        self._provider = provider
        self.__prompts_received = []
        self._responses_generated = []
        self.__futures_queue = []
        self.__thread_pool = ThreadPoolExecutor(
            max_workers=n_threads if settings.USE_MULTI_THREADING else 1
        )

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def backend(self) -> Type[BaseDataBackend]:
        """
        Backend object used to store and retrieve data of the chat.
        """
        return self._backend

    @property
    def provider(self) -> Type[BaseProvider]:
        """
        Communication provider used to send messages.
        """
        return self._provider

    def reply(self, prompt: models.MessagePrompt) -> None:
        """
        Generates a response to a message prompt and sends it to the user via the
        communication provider.
        """
        system_error = None
        try:
            self._make_reply(prompt)
            self._wait_for_promises()
        except exceptions.ApplicationError as e:
            self.logger.exception(
                f"Got an expected application error when generating the response"
            )
            self._handle_error(prompt, e)
        except Exception as e:
            self.logger.exception(
                "We got an unexpected error when generating the response"
            )
            self._handle_error(prompt, e)
            system_error = e
        if system_error:
            raise system_error

    def _make_reply(self, prompt: models.MessagePrompt) -> models.HandlerOutput:
        """
        Uses the OpenAI API to generate a response to a message prompt and sends
        it to the user via the communication provider.

        The message prompt is saved to the backend and the response is also saved,
        preserving the conversation history for the current session.
        """
        # Retrieve the user session:
        user_session, sess_created = self.get_or_create_user_session(prompt.from_user)
        if sess_created:
            self.logger.info(
                f"Created new session for user {prompt.from_user.hashed_user_id}"
            )
            # Only send a Greeting to the user if this is their first message to the bot:
            if not self.backend.does_user_exist(prompt.from_user):
                self.logger.info(
                    f"User {prompt.from_user.hashed_user_id} is new to the bot"
                )
                return self._send_greeting_message(prompt, user_session)
        self.chat_history = models.ChatHistory(session=user_session)
        # Save the message prompt to the backend:
        self.save_prompt(prompt, user_session)
        # Validations:
        valid_session = self._exec_async(self.validate_session, session=user_session)
        # Raise an error if the message is flagged by the moderation API:
        if self.check_message_moderation(prompt.body):
            error_msgs.MODERATION_ERROR.raise_error()
        # If the message is a command, let the commands handler handle it:
        if prompt.body.startswith("/"):
            cmds_handler = services.ChatCommandsHandler(openai, self)
            prompt_output = cmds_handler.reply(prompt, user_session)
        else:
            # Check if the session is valid:
            valid_session.result()
            # Get the chat history of the current session:
            if not sess_created:
                self.chat_history.refresh_from_backend(self.backend, exclude=prompt)
            # Generate response from the prompt:
            main_handler = services.ChatReplyHandler(openai_lib=openai, client=self)
            prompt_output = main_handler.reply(prompt=prompt, user_session=user_session)
        # Check if message requests for image generation
        if prompt_output.requested_features.get("generate_image"):
            # Check if the session is valid:
            valid_session.result()
            img_prompt = prompt_output.requested_features.get("generate_image")
            image_handler = services.ImageGenerationHandler(
                openai_lib=openai, client=self
            )
            # Reply with the image asynchronously
            self._exec_async(
                image_handler.reply, prompt, user_session, image_prompt=img_prompt
            )
        return prompt_output

    def _send_greeting_message(
        self, prompt: models.MessagePrompt, user_session: models.UserSession
    ) -> models.HandlerOutput:
        """
        Sends a greeting message to the user.
        """
        greeting_response = models.MessageResponse(
            body=settings.USER_WELCOME_MESSAGE,
            to_user=user_session.user,
        )
        self.send_response(greeting_response)
        return models.HandlerOutput(
            message_prompt=prompt,
            message_response=greeting_response,
            requested_features={},
        )

    def save_prompt(
        self, prompt: models.MessagePrompt, user_session: models.UserSession
    ) -> None:
        """
        Saves a message prompt to the backend asynchronously.
        """
        self.__prompts_received.append(prompt)
        self._exec_async(self.backend.save_message_prompt, prompt, user_session)

    def send_response(self, message: models.MessageResponse) -> None:
        """
        Sends a message to the user via the communication provider assynchronously.
        """
        self._responses_generated.append(message)
        self._exec_async(self.provider.send_response, message)

    def save_response(
        self, message: models.MessageResponse, user_session: models.UserSession
    ) -> None:
        """
        Saves a message response to the backend asynchronously.
        """
        self._exec_async(self.backend.save_message_response, message, user_session)

    def get_or_create_user_session(
        self, user: models.User
    ) -> Tuple[models.UserSession, bool]:
        """
        Returns a tuple of the session object and a boolean indicating whether
        the session was created or not.
        """
        session = self.backend.get_latest_user_session(user)
        created = False
        if not session:
            self.logger.info("Creating a new session")
            session = self.backend.create_user_session(user)
            created = True
        return session, created

    def end_user_session(self, user: models.User) -> None:
        """
        Asynchronously ends the User's latest session.
        """
        self._exec_async(self.backend.end_user_session, user)

    def validate_session(
        self, session: models.UserSession
    ) -> Union[Type[models.ApplicationError], None]:
        """
        Validates a session to ensure that it is not over the
        allowed quota of messages or of total active sessions.

        If the session is valid, returns None, otherwise returns
        an models.ApplicationError object.
        """
        sess_cnt_prm = self.__thread_pool.submit(
            self.backend.get_count_of_active_sessions
        )
        sess_msgs_cnt_prm = self.__thread_pool.submit(
            self.backend.get_count_of_session_prompts, session
        )
        if sess_cnt_prm.result() > settings.MAX_ACTIVE_SESSIONS:
            self.logger.error(
                f"Maximum total number of active sessions ({settings.MAX_ACTIVE_SESSIONS}) reached"
            )
            error_msgs.MAX_ACTIVE_SESSIONS_SURPASSED.raise_error()
        prompts_cnt = sess_msgs_cnt_prm.result()
        self.logger.debug(f"User number of prompts: {prompts_cnt}")
        self.logger.debug(f"User session quota: {session.session_quota}")
        if prompts_cnt > session.session_quota:
            self.logger.error(
                f"Maximum number of prompts allowed in this session ({session.session_quota}) has been reached"
            )
            error_msgs.QUOTA_SURPASSED.raise_error()
        return None

    def check_message_moderation(self, message: str) -> None:
        """
        Moderates the message to be sent to the OpenAI API to
        prevent it from generating inappropriate responses.
        """
        response = openai.Moderation.create(
            input=message,
        )
        flagged = any(r["flagged"] for r in response["results"])
        if flagged:
            self.logger.info(
                f"OpenAI's moderation model detected flagged content with response:\n{response}"
            )
        return flagged

    def _wait_for_promises(self) -> None:
        """
        Waits for all the asynchronous tasks to complete and
        removes them from the queue of promises.
        """
        errors = []
        while self.__futures_queue:
            promise = self.__futures_queue.pop(0)
            try:
                promise.result()
            except Exception as e:
                errors.append(e)
        if errors:
            raise errors[0]

    def _handle_error(self, prompt: models.MessagePrompt, error: Exception) -> None:
        """
        Handles a ModerationError by sending a message to the user
        to inform them that their message was flagged.
        """
        if not isinstance(error, exceptions.ApplicationError):
            error = error_msgs.UNEXPECTED_ERROR.exception
        self.provider.send_response(
            models.MessageResponse(
                body=error.message,
                to_user=prompt.from_user,
                status_code=error.status_code,
            )
        )
        self.backend.end_user_session(prompt.from_user)

    def _exec_async(self, f, *args, **kwargs):
        """
        Asynchronously executes a function by adding it to the thread pool.
        """
        future = self.__thread_pool.submit(f, *args, **kwargs)
        self.__futures_queue.append(future)
        return future
