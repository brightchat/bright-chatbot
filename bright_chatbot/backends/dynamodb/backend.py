import json
from typing import List, Union

from bright_chatbot.models import (
    User,
    UserSession,
    MessagePrompt,
    MessageResponse,
    UserSessionConfig,
)
from bright_chatbot.backends.base_backend import BaseDataBackend
from bright_chatbot.backends.dynamodb._controller import DynamoTablesController
from bright_chatbot.configs import settings


class DynamodbBackend(BaseDataBackend):
    """
    Backend that uses DynamoDB to store and retrieve data.
    """

    def __init__(self, **client_kwargs):
        self._controller = DynamoTablesController(**client_kwargs)

    @property
    def controller(self) -> DynamoTablesController:
        return self._controller

    def get_latest_user_session(self, user: User) -> Union[UserSession, None]:
        session_obj = self.controller.sessions.get_latest_user_session(
            user.hashed_user_id, filter_expired=True
        )
        if not session_obj:
            return None
        session_id = session_obj["SessionId"]["S"]
        user_session = UserSession(
            user=user,
            session_id=session_id,
            session_start=session_obj["TimestampCreated"]["N"],
            session_end=session_obj["SessionTTL"]["N"],
            session_quota=session_obj["MessagesQuota"]["N"],
            session_config=UserSessionConfig(
                **json.loads(session_obj["SessionConfig"]["S"])
            ),
        )
        return user_session

    def create_user_session(self, user: User) -> UserSession:
        session_obj = self.controller.sessions.record_user_session(
            user.hashed_user_id,
            messages_quota=settings.MAX_REQUESTS_PER_SESSION,
            session_config={},  # Use default values
        )
        session_id = session_obj["SessionId"]["S"]
        user_session = UserSession(
            user=user,
            session_id=session_id,
            session_start=session_obj["TimestampCreated"]["N"],
            session_end=session_obj["SessionTTL"]["N"],
            session_config=UserSessionConfig(
                **json.loads(session_obj["SessionConfig"]["S"])
            ),
        )
        return user_session

    def end_user_session(self, user: User) -> None:
        latest_session = self.get_latest_user_session(user)
        if not latest_session:
            return
        self.controller.sessions.expire_session(latest_session.session_id)

    def does_user_exist(self, user: User) -> bool:
        return self.controller.chats.check_user_has_sent_messages(user.hashed_user_id)

    def get_count_of_active_sessions(self) -> int:
        return self.controller.sessions.count_active_sessions()

    def get_count_of_session_prompts(self, session: UserSession) -> int:
        user_chat_messages = self.controller.chat_messages.get_user_chat_session(
            session_id=session.session_id
        )
        return len(
            list(filter(lambda x: x["ChatAgent"]["S"] == "user", user_chat_messages))
        )

    def get_session_chat_history(
        self, session: UserSession
    ) -> List[Union[MessagePrompt, MessageResponse]]:
        user_chat_messages = self.controller.chat_messages.get_user_chat_session(
            session_id=session.session_id
        )
        chat_history = []
        user = session.user
        for message in user_chat_messages:
            message_agent = message["ChatAgent"]["S"]
            if message_agent == "user":
                chat_history.append(
                    MessagePrompt(
                        body=message["Message"]["S"],
                        created_at=message["TimestampCreated"]["N"],
                        from_user=user,
                    )
                )
            elif message_agent == "assistant":
                chat_history.append(
                    MessageResponse(
                        body=message["Message"]["S"],
                        created_at=message["TimestampCreated"]["N"],
                        to_user=user,
                        media_url=message["ImageId"]["S"],
                    )
                )
            else:
                raise ValueError("Invalid agent type. Got: '{}'".format(message_agent))
        return chat_history

    def save_message_prompt(
        self,
        message: MessagePrompt,
        session: UserSession,
    ) -> None:
        self.controller.chats.record_chat_message(
            session_id=session.session_id,
            user_id=session.user.hashed_user_id,
            message_length=len(message.body),
            timestamp_created=message.created_at.timestamp(),
            agent="user",
            user_chat_plan=session.session_config.user_plan,
        )
        self.controller.chat_messages.record_chat_message(
            session_id=session.session_id,
            session_ttl=session.session_end.timestamp(),
            message=message.body,
            timestamp_created=message.created_at.timestamp(),
            agent="user",
        )

    def save_message_response(
        self,
        message: MessageResponse,
        session: UserSession,
    ) -> None:
        image_id = None
        if message.media_url:
            image_obj = self.controller.image_responses.record_image(
                prompt=message.body,
                timestamp_created=message.created_at.timestamp(),
                image_uri=message.media_url,
                user_id=session.user.hashed_user_id,
            )
            image_id = image_obj["ImageId"]["S"]
        self.controller.chats.record_chat_message(
            session_id=session.session_id,
            user_id=session.user.hashed_user_id,
            message_length=len(message.body),
            timestamp_created=message.created_at.timestamp(),
            agent="assistant",
            user_chat_plan=session.session_config.user_plan,
            image_id=image_id,
        )
        self.controller.chat_messages.record_chat_message(
            session_id=session.session_id,
            session_ttl=session.session_end.timestamp(),
            message=message.body,
            timestamp_created=message.created_at.timestamp(),
            agent="assistant",
            image_id=image_id,
        )
