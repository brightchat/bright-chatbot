from typing import Any, Dict, List

from openai_mobile.backends.dynamodb.tables.base import BaseTableController
from openai_mobile.utils import hash_text


class ImageResponsesTableController(BaseTableController):

    TABLE_NAME = "ImageResponses"

    @staticmethod
    def generate_image_id(image_b64: str = None, image_uri: str = None) -> str:
        """
        Generates the ImageId of the image given
        by hashing the base64 encoding of the image or its url
        """
        if not (image_b64 or image_uri):
            raise ValueError("You must provide either image_b64 or image_uri")
        return hash_text(image_b64 or image_uri)

    def get_images_from_prompt(
        self, prompt: str, gte_timestamp: float = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the images in the table that contain
        the given text prompt.

        If `gte_timestamp` is provided, it will filter for the records
        where TimestampReceived is greater or equal to the value given.
        """
        projection = [
            "ImageId",
            "UserId",
            "Prompt",
            "Message",
            "TimestampReceived",
            "TimestampCreated",
        ]
        condition_expression = "Prompt = :prompt"
        attrs_values = {
            ":prompt": {
                "S": prompt,
            },
        }
        if gte_timestamp:
            condition_expression += " AND TimestampReceived >= :timestamp"
            attrs_values[":timestamp"] = {"N": str(gte_timestamp)}
        response = self._query(
            ExpressionAttributeValues=attrs_values,
            IndexName="PromptGlobalIndex",
            KeyConditionExpression=condition_expression,
            recursive=True,
            ProjectionExpression=", ".join(projection),
        )
        return response["Items"]

    def get_image_from_id(self, image_id: str) -> Dict[str, Any]:
        """
        Retrieves the image with the given image_id
        """
        response = self._query(
            ExpressionAttributeValues={
                ":image_id": {
                    "S": image_id,
                },
            },
            KeyConditionExpression="ImageId = :image_id",
        )
        return response["Items"][0] if response["Items"] else None

    def record_image(
        self,
        prompt: str,
        timestamp_received: float,
        timestamp_created: float,
        image_uri: str,
        image_b64: str = None,
        user_id: str = "",
        message: str = "",
    ) -> Dict[str, Any]:
        """
        Records a new image response into the table.
        Fails if the image already exists in the table.
        """
        image_id = self.generate_image_id(image_b64 or image_uri)
        item = {
            "ImageId": {
                "S": image_id,
            },
            "UserId": {
                "S": user_id,
            },
            "Prompt": {
                "S": prompt,
            },
            "Message": {"S": message},
            "ImageURI": {"S": image_uri},
            "TimestampReceived": {"N": str(timestamp_received)},
            "TimestampCreated": {"N": str(timestamp_created)},
        }
        response = self._put_item(
            Item=item,
            ExpressionAttributeValues={":image_id": {"S": image_id}},
            ConditionExpression="ImageId <> :image_id",
        )
        response["Item"] = item
        return response
