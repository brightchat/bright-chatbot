from base64 import b64decode

from typing import Dict, Any
from urllib.parse import parse_qs


def build_api_callback_url(event) -> str:
    """
    From the lambda function event, reconstructs the URL
    of the API gateway endpoint where the event comes from
    """
    headers = event["headers"]
    request_context = event["requestContext"]
    callback_url = f'{headers["X-Forwarded-Proto"]}://{request_context["domainName"]}{request_context["path"]}'
    return callback_url


def parse_event_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event["body"]
    if event["isBase64Encoded"]:
        body = b64decode(body).decode("utf-8")
    response = {
        "headers": event["headers"],
        "params": url_params_to_dict(body),
        "callback_url": build_api_callback_url(event),
    }
    return response


def url_params_to_dict(body: str) -> Dict[str, str]:
    body_params = {key: v[0] for key, v in parse_qs(body.strip('"')).items()}
    return body_params
