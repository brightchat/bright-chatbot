from backend.models import MessageResponse, User
from tests.mock.request import ApplicationRequestParams


class ResponseObjects:
    message_response = MessageResponse(
        body="",
        media_url="http://example.com/image.jpg",
        to=User(ApplicationRequestParams.USER_WS_PHONE_NUMBER),
    )
