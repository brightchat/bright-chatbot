from typing import Any, Dict, List, Literal

from openai_mobile.backends.dynamodb.tables.base import BaseTableController


class ChatsTableController(BaseTableController):

    TABLE_NAME = "Chats"

    def get_user_chat_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the messages of the chat from the user
        given the session id.
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
        message: str,
        timestamp_created: float,
        agent: Literal["assistant", "user"],
        image_id: str = None,
    ) -> Dict[str, Any]:
        """
        Records a new chat message into the table
        """
        item = {
            "SessionId": {
                "S": session_id,
            },
            "UserId": {
                "S": user_id,
            },
            "Message": {"S": message},
            "TimestampCreated": {"N": str(timestamp_created)},
            "ChatAgent": {"S": agent.lower()},
            "ImageId": {"S": image_id or ""},
        }
        response = self._put_item(Item=item)
        response["Item"] = item
        return response

    def get_user_chat_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all the messages of the user given
        """
        response = self._query(
            ExpressionAttributeValues={
                ":user_id": {
                    "S": user_id,
                },
            },
            IndexName="UserIdGlobalIndex",
            KeyConditionExpression="UserId = :user_id",
        )
        return response["Items"]

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
            **extra_kwargs
        )
        return response["Items"]
