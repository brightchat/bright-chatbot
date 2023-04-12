from datetime import datetime
from typing import Any, Dict, List, Literal

from bright_chatbot.backends.dynamodb.tables.base import BaseTableController


class ChatsTableController(BaseTableController):
    TABLE_NAME = "Chats"

    def get_user_chat_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the entries of the chat given a session id.
        """
        response = self._query(
            recursive=True,
            ExpressionAttributeValues={
                ":session_id": {
                    "S": session_id,
                },
            },
            KeyConditionExpression="SessionId = :session_id",
            ConsistentRead=True,
        )
        return response["Items"]

    def record_chat_message(
        self,
        session_id: str,
        user_id: str,
        message_length: int,
        timestamp_created: float,
        agent: Literal["assistant", "user"],
        user_chat_plan: str = None,
        image_id: str = None,
    ) -> Dict[str, Any]:
        """
        Records a new chat entry into the table
        """
        item = {
            "SessionId": {
                "S": session_id,
            },
            "UserId": {
                "S": user_id,
            },
            "MessageLength": {"N": str(message_length)},
            "TimestampCreated": {"N": str(timestamp_created)},
            "ChatAgent": {"S": agent.lower()},
            "ImageId": {"S": image_id or ""},
            "UserChatPlan": {"S": user_chat_plan} if user_chat_plan else {"NULL": True},
        }
        response = self._put_item(Item=item)
        response["Item"] = item
        return response

    def get_user_chat_messages(
        self, user_id: str, from_date: datetime = None, to_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all the chat entries of the user given,
        optionally filtered by two dates.
        """
        kwargs = dict(
            KeyConditionExpression="UserId = :user_id",
            ExpressionAttributeValues={
                ":user_id": {
                    "S": user_id,
                },
            },
        )
        if from_date or to_date:
            if not from_date:
                from_date = datetime.fromtimestamp(0)
            if not to_date:
                to_date = datetime.now()
            kwargs[
                "KeyConditionExpression"
            ] += " AND TimestampCreated BETWEEN :from_date AND :to_date"
            kwargs["ExpressionAttributeValues"].update(
                {
                    ":from_date": {"N": str(from_date.timestamp())},
                    ":to_date": {"N": str(to_date.timestamp())},
                }
            )
        response = self._query(
            **kwargs,
            recursive=True,
            IndexName="UserConverationGlobalIndex",
        )
        return response["Items"]

    def check_user_has_sent_messages(self, user_id: str) -> bool:
        """
        Checks if a user has sent any message to the chat
        by checking the existance of its id in the table
        using the UsersLastMessageGlobalIndex
        """
        response = self._query(
            IndexName="UsersLastMessageGlobalIndex",
            KeyConditionExpression="UserId = :user_id",
            ExpressionAttributeValues={
                ":user_id": {
                    "S": user_id,
                },
            },
            Limit=1,
        )
        return bool(response["Items"])

    def get_messages_by_image_id(
        self, session_id: str, image_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the messages in the chat that match the given image id.
        """
        response = self._query(
            ExpressionAttributeValues={
                ":session_id": {
                    "S": session_id,
                },
                ":image_id": {"S": image_id},
            },
            KeyConditionExpression="SessionId = :session_id",
            FilterExpression="ImageId = :image_id",
        )
        return response["Items"]

    def get_session_images(
        self, session_id: str, project_all: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the image ids that have been generated in this session
        """
        extra_kwargs = {}
        if not project_all:
            extra_kwargs["ProjectionExpression"] = "ImageId"
        response = self._query(
            ExpressionAttributeValues={
                ":session_id": {
                    "S": session_id,
                },
                ":empty": {"S": ""},
            },
            KeyConditionExpression="SessionId = :session_id",
            FilterExpression="ImageId <> :empty",
            **extra_kwargs,
        )
        return response["Items"]
