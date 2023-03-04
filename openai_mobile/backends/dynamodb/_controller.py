import boto3

from openai_mobile.backends.dynamodb.tables import (
    SessionsTableController,
    ImageResponsesTableController,
    ChatsTableController,
)


class DynamoTablesController:
    def __init__(self, **client_kwargs):
        self.client = boto3.client("dynamodb", **client_kwargs)
        self.sessions = SessionsTableController(self.client)
        self.image_responses = ImageResponsesTableController(self.client)
        self.chats = ChatsTableController(self.client)
