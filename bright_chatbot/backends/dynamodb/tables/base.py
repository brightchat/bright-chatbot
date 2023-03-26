import abc
from typing import Any, Dict

import boto3

from bright_chatbot.configs import ProjectSettings


class BaseTableController(abc.ABC):
    """
    Base Abstract class for a Dynamo Table controller
    """

    @abc.abstractmethod
    def TABLE_NAME(self) -> str:
        pass

    def __init__(self, client=None, **client_kwargs):
        if not client:
            self.client = boto3.client("dynamodb", **client_kwargs)
        else:
            self.client = client

    @property
    def table_name(self) -> str:
        return f"{ProjectSettings.DYNAMODB_TABLES_PREFIX}{self.TABLE_NAME}"

    def scan(self, index_name: str = None, **kwargs) -> Dict[str, Any]:
        if index_name:
            kwargs["IndexName"] = index_name
        return self.client.scan(TableName=self.table_name, **kwargs)

    def _query(self, recursive=False, **kwargs):
        response = self.client.query(TableName=self.table_name, **kwargs)
        if recursive and "LastEvaluatedKey" in response:
            next_response = response.copy()
            while "LastEvaluatedKey" in next_response:
                kwargs["ExclusiveStartKey"] = next_response["LastEvaluatedKey"]
                next_response = self.client.query(TableName=self.table_name, **kwargs)
                if "Items" in response:
                    response["Items"].extend(next_response["Items"])
                response["Count"] += next_response["Count"]
        return response

    def _put_item(self, **kwargs):
        return self.client.put_item(TableName=self.table_name, **kwargs)

    def _update_item(self, **kwargs):
        return self.client.update_item(TableName=self.table_name, **kwargs)
