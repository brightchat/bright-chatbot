from datetime import datetime
import os
from typing import Any, Dict, List

from bright_chatbot.backends.dynamodb.tables.base import BaseTableController
from bright_chatbot.configs.settings import ProjectSettings
from bright_chatbot.utils import get_utc_timestamp_now


class SessionsTableController(BaseTableController):

    TABLE_NAME = "Sessions"
    DEFAULT_SESSIONS_EXPIRATION_HOURS = 3

    @staticmethod
    def generate_session_id(user_id: str, timestamp: float = None) -> str:
        if not timestamp:
            timestamp = get_utc_timestamp_now()
        return f"{user_id}:{str(timestamp)}"

    @property
    def session_expiration_hours(self) -> float:
        return ProjectSettings.MAX_SESSION_DURATION_MINUTES / 60

    def get_user_sessions(
        self,
        user_id: str,
        session_id_only: bool = False,
        created_at_start: datetime = None,
        created_at_end: datetime = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all the sessions of user_id.
        If `session_id_only` is true, the records in the response will only contain
        the `SessionId` attribute.

        If `created_at_start` and `created_at_end` are provided, the records will be
        filtered by the `TimestampCreated` attribute to retrieve only the sessions
        that were created between those two dates.
        """
        extra_kwargs = {}
        expr_attribute_values = {
            ":user_id": {
                "S": user_id,
            }
        }
        key_condition_expr = "UserId = :user_id"
        if session_id_only:
            extra_kwargs["ProjectionExpression"] = "SessionId"
        if created_at_start or created_at_end:
            if not created_at_start:
                created_at_start = datetime.utcfromtimestamp(0)
            if not created_at_end:
                created_at_end = datetime.utcnow()
            key_condition_expr += " AND TimestampCreated BETWEEN :start AND :end"
            expr_attribute_values.update(
                {
                    ":start": {"N": str(created_at_start.timestamp())},
                    ":end": {"N": str(created_at_end.timestamp())},
                }
            )
        response = self._query(
            ExpressionAttributeValues=expr_attribute_values,
            KeyConditionExpression=key_condition_expr,
            **extra_kwargs,
        )
        return response["Items"]

    def record_user_session(self, user_id: str, messages_quota: int) -> Dict[str, Any]:
        """
        Records a new user session into the Sessions table
        """
        timestamp = get_utc_timestamp_now()
        session_id = self.generate_session_id(user_id, timestamp)
        ttl = timestamp + (3600 * self.session_expiration_hours)
        item = {
            "UserId": {
                "S": user_id,
            },
            "SessionId": {
                "S": session_id,
            },
            "TimestampCreated": {"N": str(timestamp)},
            "TimestampFinished": {
                "NULL": True,
            },
            "MessagesQuota": {"N": str(messages_quota)},
            "SessionTTL": {"N": str(ttl)},
        }
        self._put_item(Item=item)
        return item

    def get_latest_user_session(
        self, user_id: str, filter_expired=False
    ) -> Dict[str, Any]:
        """
        Retrieves the latest session of user_id.

        If `filter_expired` is True, also filters out the records
        where TimestampFinished is not null or the SessionTTL has passed.
        """
        extra_kwargs = {}
        extra_attrs = {}
        if filter_expired:
            timestamp = get_utc_timestamp_now()
            filter_expr = f"TimestampFinished = :tf AND SessionTTL > :now"
            extra_kwargs = {"FilterExpression": filter_expr}
            extra_attrs = {":tf": {"NULL": True}, ":now": {"N": str(timestamp)}}
        response = self._query(
            ExpressionAttributeValues={
                ":user_id": {
                    "S": user_id,
                },
                **extra_attrs,
            },
            KeyConditionExpression="UserId = :user_id",
            ScanIndexForward=False,
            ConsistentRead=True,
            **extra_kwargs,
        )
        return response["Items"][0] if response["Items"] else None

    def expire_session(self, session_id: str) -> Dict[str, Any]:
        """
        Forcefully expires the user session given
        """
        timestamp = get_utc_timestamp_now()
        session_parts = session_id.split(":")
        user_id = ":".join(session_parts[:-1])
        timestamp_created = session_parts[-1]
        response = self._update_item(
            Key={
                "UserId": {"S": user_id},
                "TimestampCreated": {"N": str(timestamp_created)},
            },
            ConditionExpression="SessionId=:session_id",
            ExpressionAttributeNames={
                "#TF": "TimestampFinished",
            },
            ExpressionAttributeValues={
                ":tf": {"N": str(timestamp)},
                ":session_id": {"S": session_id},
            },
            UpdateExpression="SET #TF = :tf",
        )
        return response

    def count_active_sessions(self) -> int:
        """
        Returns the number of active sessions in the Sessions table.
        """
        timestamp = get_utc_timestamp_now()
        filter_expr = f"TimestampFinished = :tf AND SessionTTL > :now"
        response = self.scan(
            ExpressionAttributeValues={
                ":tf": {
                    "NULL": True,
                },
                ":now": {"N": str(timestamp)},
            },
            FilterExpression=filter_expr,
        )
        return response["Count"]
