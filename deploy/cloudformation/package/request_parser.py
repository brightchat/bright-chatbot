from base64 import b64decode

import re
from typing import Dict, Any
from urllib.parse import parse_qs


def build_api_callback_url(parsed_body: Dict[str, Any]) -> str:
    """
    From the lambda function event, reconstructs the URL
    of the API gateway endpoint where the event comes from
    """
    headers = parsed_body["headers"]
    uri_path = parsed_body["uri_path"]
    return f"https://{headers['Host']}{uri_path}"


def parse_event_body(event_body: str) -> Dict[str, Any]:
    body_parts = event_body_to_parts(event_body)
    response = {
        "headers": raw_header_to_dict(body_parts["headers"]),
        "params": url_params_to_dict(body_parts["body"]),
        "uri_path": body_parts["uri_path"],
    }
    return response


def event_body_to_parts(event_body: str) -> Dict[str, str]:
    regex = re.compile(
        r"body:(?P<body>[\w=]+),headers:{(?P<headers>.*)},uri_path:(?P<uri_path>[\w/]+)"
    )
    matches = re.match(regex, event_body)
    grouped_m = matches.groupdict()
    return grouped_m


def url_params_to_dict(body: str) -> Dict[str, str]:
    body = b64decode(body).decode("utf-8")
    body_params = {key: v[0] for key, v in parse_qs(body.strip('"')).items()}
    return body_params


def raw_header_to_dict(raw_headers: str) -> Dict[str, str]:
    ls = list(map(str.strip, raw_headers.split(",")))
    d = {}
    for h in ls:
        splitted = h.split("=", maxsplit=1)
        if len(splitted) < 2:
            continue
        key, value = splitted
        d[key] = value
    return d
