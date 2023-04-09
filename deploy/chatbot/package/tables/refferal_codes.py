from typing import Any, Dict, Union
from bright_chatbot.backends.dynamodb.tables.base import BaseTableController


class UsersRefferalCodesTableController(BaseTableController):

    TABLE_NAME = "UsersRefferalCodes"

    def get_user_refferal_code(self, user_phone_number: str) -> Union[str, None]:
        """
        Retrieves the refferal code of the user
        given the user id.
        Returns None if the user has no refferal code.
        """
        response = self._query(
            recursive=True,
            ExpressionAttributeValues={
                ":user_phone_number": {
                    "S": user_phone_number,
                },
            },
            KeyConditionExpression="UserPhoneNumber = :user_phone_number",
            ConsistentRead=True,
        )
        if not response["Items"]:
            return None
        return response["Items"][0]["RefferalCode"]["S"]

    def record_user_refferal_code(
        self,
        user_phone_number: str,
        refferal_code: str,
    ) -> Dict[str, Any]:
        """
        Records a new user refferal code into the table
        carefully checking that the refferal code does
        not exist yet.

        Raises a ValueError if the refferal code already
        exists.
        """
        item = {
            "UserPhoneNumber": {
                "S": user_phone_number,
            },
            "RefferalCode": {
                "S": refferal_code,
            },
        }
        if not self.check_refferal_code_exists(refferal_code):
            response = self._put_item(Item=item)
        else:
            raise ValueError(f"Refferal code {refferal_code} already exists")
        response["Item"] = item
        return response

    def check_refferal_code_exists(self, refferal_code: str) -> bool:
        """
        Checks if the refferal code exists in the table by
        using the RefferalCodesIndex
        """
        response = self._query(
            recursive=True,
            ExpressionAttributeValues={
                ":refferal_code": {
                    "S": refferal_code,
                },
            },
            IndexName="RefferalCodesIndex",
            KeyConditionExpression="RefferalCode = :refferal_code",
        )
        return bool(response["Items"])
