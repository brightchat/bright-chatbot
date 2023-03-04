from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any, Dict, List, Tuple, Type, Union

import openai

from openai_mobile.backends.base_backend import BaseDataBackend
from openai_mobile.client.handlers.chat_handler import ChatReplyHandler
from openai_mobile.client.handlers.image_handler import ImageGenerationHandler
from openai_mobile.configs.settings import ProjectSettings
from openai_mobile.models import MessagePrompt, MessageResponse, User, UserSession
from openai_mobile.models.errors import ApplicationError
from openai_mobile.providers.base_provider import BaseProvider
from openai_mobile.utils import exceptions as errors
import openai_mobile.client.templates.errors as error_msgs


class OpenAIChatClient:
    def __init__(
        self,
        backend: Type[BaseDataBackend],
        provider: Type[BaseProvider],
        n_threads: int = 5,
    ):
        self._logger = logging.getLogger(f"{__package__}.{self.__class__.__name__}")
        self._backend = backend
        self._provider = provider
        self._responses_generated = []
        self._thread_pool = ThreadPoolExecutor(
            max_workers=n_threads if ProjectSettings.USE_MULTI_THREADING else 1
        )
        openai.api_key = ProjectSettings.OPENAI_API_KEY

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

    def reply(self, prompt: MessagePrompt) -> None:
        """
        Generates a response to a message prompt and sends it to the user via the
        communication provider.
        """
        try:
            self._make_reply(prompt)
        except errors.SessionLimitError:
            self._handle_error(prompt, error_msgs.MAX_ACTIVE_SESSIONS_SURPASSED)
        except errors.ModerationError:
            self._handle_error(prompt, error_msgs.MODERATION_ERROR)
        except Exception:
            self.logger.exception("Error while generating response")
            self._handle_error(prompt, error_msgs.UNEXPECTED_ERROR)

    def _make_reply(self, prompt: MessagePrompt) -> None:
        """
        Uses the OpenAI API to generate a response to a message prompt and sends
        it to the user via the communication provider.

        The message prompt is saved to the backend and the response is also saved,
        preserving the conversation history for the current session.
        """
        moderation_prm = self._thread_pool.submit(
            self._check_message_moderation, prompt.body
        )
        user_session, sess_created = self._get_or_create_user_session(prompt.from_user)
        valid_session_prm = self._thread_pool.submit(
            self._validate_session, user_session
        )
        chat_history = []
        if not sess_created:
            user_session_history_prm = self._thread_pool.submit(
                self._get_session_chat_history, prompt.from_user, user_session
            )
        # Check if the message is moderate:
        is_flagged = moderation_prm.result()
        if is_flagged:
            raise errors.ModerationError(
                "The message given might violate OpenAI's content policy"
            )
        # Check if the session is valid:
        session_validation_error = valid_session_prm.result()
        if session_validation_error:
            raise session_validation_error
        # Get the chat history of the current session:
        if not sess_created:
            chat_history = user_session_history_prm.result()
        # Save the message prompt to the backend:
        self._thread_pool.submit(self.backend.save_message_prompt, prompt, user_session)
        # Generate response from the prompt:
        chat_handler = ChatReplyHandler(
            openai_lib=openai,
            thread_pool=self._thread_pool,
            backend=self.backend,
            provider=self.provider,
        )
        handler_response = chat_handler.reply(
            prompt=prompt, chat_history=chat_history, user_session=user_session
        )
        parsed_answer = handler_response["parsed"]
        extra_tasks = []
        # Check if message requests for image generation
        if parsed_answer["image"]:
            image_handler = ImageGenerationHandler(
                openai_lib=openai,
                thread_pool=self._thread_pool,
                backend=self.backend,
                provider=self.provider,
            )
            # Reply with the image asynchronously
            img_prm = self._thread_pool.submit(
                image_handler.reply, prompt, parsed_answer["image"], user_session
            )
            extra_tasks.append(img_prm)
        for task in extra_tasks:
            task.result()
        self._thread_pool.shutdown(wait=True, cancel_futures=False)

    def _get_or_create_user_session(self, user: User) -> Tuple[UserSession, bool]:
        """
        Returns a tuple of the session object and a boolean indicating whether
        the session was created or not.
        """
        session = self.backend.get_latest_user_session(user)
        created = False
        if not session:
            session = self.backend.create_user_session(user)
            created = True
        return session, created

    def _get_session_chat_history(
        self, prompt: MessagePrompt, session: UserSession
    ) -> List[Dict[str, str]]:
        """
        Returns the chat history of the current session and the
        session object itself.
        """
        chat_history = self.backend.get_session_chat_history(session)
        return [
            msg.to_chat_repr()
            for msg in chat_history
            if not (type(msg) == MessagePrompt and msg.sent_at == prompt.sent_at)
        ]

    def _validate_session(
        self, session: UserSession
    ) -> Union[Type[ApplicationError], None]:
        """
        Validates a session to ensure that it is not over the
        allowed quota of messages or of total active sessions.

        If the session is valid, returns None, otherwise returns
        an ApplicationError object.
        """
        sess_cnt_prm = self._thread_pool.submit(
            self.backend.get_count_of_active_sessions
        )
        sess_msgs_cnt_prm = self._thread_pool.submit(
            self.backend.get_count_of_session_prompts, session
        )
        if sess_cnt_prm.result() > ProjectSettings.MAX_ACTIVE_SESSIONS:
            return errors.SessionLimitError(
                f"Maximum total number of active sessions ({ProjectSettings.MAX_ACTIVE_SESSIONS}) reached"
            )
        if sess_msgs_cnt_prm.result() > ProjectSettings.MAX_REQUESTS_PER_SESSION:
            return errors.SessionLimitError(
                f"Maximum number of prompts per session ({ProjectSettings.MAX_REQUESTS_PER_SESSION}) reached"
            )
        return None

    def _check_message_moderation(self, message: str) -> None:
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

    def _send_response(self, message: MessageResponse) -> None:
        """
        Sends a message to the user via the communication provider
        and saves it to the backend.

        Both operations are performed asynchronously.
        """
        self._responses_generated.append(message)
        self._thread_pool.submit(self.provider.send_message, message)
        self._thread_pool.submit(self.backend.save_message_response, message)

    def _handle_error(self, prompt: MessagePrompt, error: ApplicationError) -> None:
        """
        Handles a ModerationError by sending a message to the user
        to inform them that their message was flagged.
        """
        if error.status_code >= 500:
            self.logger.error(
                f"An error '{ApplicationError}' occurred while generating a response for the message: '{MessagePrompt}'"
            )
        self._send_response(
            MessageResponse(
                body=error.message,
                to_user=prompt.from_user,
                status_code=error.status_code,
            )
        )
        if error.status_code < 500:
            self.backend.end_user_session(prompt.from_user)
