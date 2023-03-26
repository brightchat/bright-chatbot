import json
import logging
import os
from typing import Any, Dict

from bright_chatbot.models import MessagePrompt, User, MessageResponse
from bright_chatbot.providers.twilio import TwilioProvider
from bright_chatbot.utils.exceptions import ValidationError

import stripe

stripe.api_key = os.environ["STRIPE_API_KEY"]

xray_recorder = None
try:
    from aws_xray_sdk.core import patch_all
    from aws_xray_sdk.core import xray_recorder

    patch_all()
except ImportError:
    logging.warn("Optional library aws_xray_sdk not found. Skipping patching.")
    pass


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler that receives a callback from Stripe and
    sends a message to the user to confirm that their subscription
    is now active.
    """
    logger = init_logger()
    if logger.level < 30:
        print(f"Received event:\n{json.dumps(event)}")
    try:
        event = get_stripe_event(event["body"], event["headers"]["Stripe-Signature"])
    except ValueError as e:
        logger.exception("Invalid request")
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({"error": "Bad Request", "message": str(e)}),
        }
    except ValidationError as e:
        logger.exception("Invalid signature")
        return {
            "isBase64Encoded": False,
            "statusCode": 401,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({"error": "Unauthorized"}),
        }
    print(f"Received event {event}, {type(event)}")
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps({"success": True}),
    }


def init_logger() -> logging.Logger:
    logging.basicConfig()
    logger = logging.getLogger("brightbot_web_backend")
    logger.setLevel(os.environ.get("LAMBDA_LOG_LEVEL", "WARNING"))
    return logger


def get_stripe_event(payload, signature: str) -> stripe.Event:
    """
    Verifies the signature of the request to ensure that it
    was sent by Stripe.
    Raises a ValidationError if the signature is invalid.
    """
    endpoint_secret = os.environ["STRIPE_WEBHOOK_SECRET"]
    try:
        event = stripe.Webhook.construct_event(
            payload.encode("utf-8"), signature, endpoint_secret
        )
    except stripe.error.SignatureVerificationError as e:
        raise ValidationError("Invalid signature") from e
    return event
