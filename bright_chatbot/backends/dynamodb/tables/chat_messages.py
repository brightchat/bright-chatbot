from datetime import datetime
from typing import Any, Dict, List, Literal

from bright_chatbot.backends.dynamodb.tables.base import BaseTableController


class ChatMessagesTableController(BaseTableController):
    TABLE_NAME = "ChatMessages"

    def get_user_chat_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the messages of the chat given a the session id.
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
        session_ttl: float,
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
            "Message": {"S": message},
            "TimestampCreated": {"N": str(timestamp_created)},
            "ChatAgent": {"S": agent.lower()},
            "ImageId": {"S": image_id or ""},
            "SessionTTL": {
                "N": str(session_ttl),
            },
        }
        response = self._put_item(Item=item)
        response["Item"] = item
        return response
