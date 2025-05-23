import json
import logging
import os
from typing import Any, Dict

import sentry_sdk

sentry_sdk.init(traces_sample_rate=1.0, enable_tracing=True)

from dynamo_auth_backend import DynamoSessionAuthBackend

from bright_chatbot.client import OpenAIChatClient
from bright_chatbot.models import MessagePrompt, User
from bright_chatbot.providers.ws_business.provider import WhatsAppBusinessProvider


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
    Handler that receives a callback from twillio
    containing a message sent by the user and responds
    to it with a response generated by an OpenAI model.
    """
    logger = init_logger()
    if logger.level < 30:
        print(f"Received event:\n{json.dumps(event)}")
    # Parse event:
    body = json.loads(event["body"])
    # Set the Running Platform:
    os.environ["BRIGHT_CHATBOT_RUNNING_PLATFORM"] = body.get("platform", "WhatsApp")
    # Initiate provider and backend:
    provider = WhatsAppBusinessProvider()
    backend = DynamoSessionAuthBackend()
    # Initiate client
    client = OpenAIChatClient(provider=provider, backend=backend)
    # Create User message prompt:
    user = User(user_id=body["sender"])
    message_prompt = MessagePrompt(
        body=body["message"],
        from_user=user,
    )
    # Record the User Id with X-ray using a new subsegment
    if xray_recorder:
        subsegment = xray_recorder.begin_subsegment("bright_chatbot")
        subsegment.put_annotation("user_id", user.hashed_user_id)
    # Record the User Id with Sentry:
    sentry_sdk.set_user({"id": user.hashed_user_id})
    client.reply(message_prompt)
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": {},
    }


def init_logger() -> logging.Logger:
    logging.basicConfig()
    logger = logging.getLogger("bright_chatbot")
    logger.setLevel(os.environ.get("LAMBDA_LOG_LEVEL", "WARNING"))
    return logger
