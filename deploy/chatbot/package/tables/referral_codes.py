from typing import Any, Dict, Union
from bright_chatbot.backends.dynamodb.tables.base import BaseTableController


class UsersReferralCodesTableController(BaseTableController):

    TABLE_NAME = "UsersReferralCodes"

    def get_user_referral_code(self, user_phone_number: str) -> Union[str, None]:
        """
        Retrieves the referral code of the user
        given the user id.
        Returns None if the user has no referral code.
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
        return response["Items"][0]["ReferralCode"]["S"]

    def record_user_referral_code(
        self,
        user_phone_number: str,
        referral_code: str,
    ) -> Dict[str, Any]:
        """
        Records a new user referral code into the table
        carefully checking that the referral code does
        not exist yet.

        Raises a ValueError if the referral code already
        exists.
        """
        item = {
            "UserPhoneNumber": {
                "S": user_phone_number,
            },
            "ReferralCode": {
                "S": referral_code,
            },
        }
        if not self.check_referral_code_exists(referral_code):
            response = self._put_item(Item=item)
        else:
            raise ValueError(f"Referral code {referral_code} already exists")
        response["Item"] = item
        return response

    def check_referral_code_exists(self, referral_code: str) -> bool:
        """
        Checks if the referral code exists in the table by
        using the ReferralCodesIndex
        """
        response = self._query(
            recursive=True,
            ExpressionAttributeValues={
                ":referral_code": {
                    "S": referral_code,
                },
            },
            IndexName="ReferralCodesIndex",
            KeyConditionExpression="ReferralCode = :referral_code",
        )
        return bool(response["Items"])
