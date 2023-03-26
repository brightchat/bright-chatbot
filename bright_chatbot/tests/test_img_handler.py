from unittest.mock import patch
from aws.dynamo.tables.sessions import SessionsTableController

from backend.models import MessageResponse, User
from handler import MessagesHandler
from tests.base import ApplicationBaseTestCase
from tests.mock.request import ApplicationRequestParams
from tests.mock.images_handler import ResponseObjects


class TestImageHandler(ApplicationBaseTestCase):
    def test_request_img_prompt_msg(self):
        """
        Checks that the functionality to generate an image
        works well when the user sends a correct prompt from
        the application.
        """
        send_msg_mock = self._mocks["send_message"]
        event = {
            "From": ApplicationRequestParams.USER_WS_PHONE_NUMBER,
            "Body": "_This is a test prompt_",
        }
        handler = MessagesHandler(event, xray_recorder=None)
        response = handler.respond_message()
        send_msg_mock.assert_called_once_with(
            response_model=ResponseObjects.message_response
        )
        self.assertEqual(response["statusCode"], 200)

    def test_request_img_prompt2_msg(self):
        """
        Checks that the functionality to generate an image
        works well when the user sends a correct second prompt from
        the application.
        #TODO: This should test the parameters (prompt) given to the OpenAI API.
        """
        send_msg_mock = self._mocks["send_message"]
        event = {
            "From": ApplicationRequestParams.USER_WS_PHONE_NUMBER,
            "Body": "Image of some image description",
        }
        handler = MessagesHandler(event, xray_recorder=None)
        response = handler.respond_message()
        send_msg_mock.assert_called_once_with(
            response_model=ResponseObjects.message_response
        )
        self.assertEqual(response["statusCode"], 200)

    def test_request_invalid_prompt_msg(self):
        """
        Checks that the functionality to generate an image
        works well when the user sends an invalid prompt from
        the application.
        """
        send_msg_mock = self._mocks["send_message"]
        event = {
            "From": ApplicationRequestParams.USER_WS_PHONE_NUMBER,
            "Body": "This is a test prompt",
        }
        expected_response = MessageResponse(
            body="Message can not be understanded or has a wrong syntax",
            from_=User(ApplicationRequestParams.FROM_WS_PHONE_NUMBER),
            to=User(ApplicationRequestParams.USER_WS_PHONE_NUMBER),
            is_invalid=True,
        )
        handler = MessagesHandler(event, xray_recorder=None)
        response = handler.respond_message()
        call_kwargs = send_msg_mock.call_args_list[0][1]
        response_gotten = call_kwargs["response_model"]
        self.assertEqual(response["statusCode"], 200)
        self.assertDictEqual(response_gotten.to_dict(), expected_response.to_dict())

    @patch.object(
        SessionsTableController,
        "get_latest_user_session",
        return_value={},
    )
    @patch.object(
        SessionsTableController,
        "get_user_sessions",
        return_value=[{"SessionId": i} for i in range(5)],
    )
    def test_request_session_quota_surpassed(self, *mocks):
        """ "
        Checks that the functionality to generate an image
        returns an error when the user has surpassed their
        normal quota of sessions per user.
        """
        send_msg_mock = self._mocks["send_message"]
        env_mock = self._mocks["environ"]
        env_mock.pop("OPENAI_WS_APP_ADMIN_USERS", None)
        event = {
            "From": ApplicationRequestParams.USER_WS_PHONE_NUMBER,
            "Body": "_This is a test prompt_",
        }
        expected_response = MessageResponse(
            body=(
                "You have surpassed your quota of sessions for the time being"
                ", retry after some time has passed"
            ),
            is_quota_surpassed=True,
            from_=User(ApplicationRequestParams.FROM_WS_PHONE_NUMBER),
            to=User(ApplicationRequestParams.USER_WS_PHONE_NUMBER),
        )
        handler = MessagesHandler(event, xray_recorder=None)
        response = handler.respond_message()
        call_kwargs = send_msg_mock.call_args_list[0][1]
        response_gotten = call_kwargs["response_model"]
        self.assertEqual(response["statusCode"], 200)
        self.assertDictEqual(response_gotten.to_dict(), expected_response.to_dict())

    @patch.object(
        SessionsTableController,
        "get_latest_user_session",
        return_value={},
    )
    @patch.object(
        SessionsTableController,
        "get_user_sessions",
        return_value=[{"SessionId": i} for i in range(5)],
    )
    def test_request_session_admin_quota_surpassed(self, *mocks):
        """ "
        Checks that the functionality to generate an image from
        an admin user that has surpassed the normal quota of
        sessions per user works well -> ie. request is handled
        normally without any interruptions.
        """
        send_msg_mock = self._mocks["send_message"]
        env_mock = self._mocks["environ"]
        event = {
            "From": ApplicationRequestParams.USER_WS_PHONE_NUMBER,
            "Body": "_This is a test prompt_",
        }
        env_mock[
            "OPENAI_WS_APP_ADMIN_USERS"
        ] = ApplicationRequestParams.USER_WS_PHONE_NUMBER
        handler = MessagesHandler(event, xray_recorder=None)
        response = handler.respond_message()
        send_msg_mock.assert_called_once_with(
            response_model=ResponseObjects.message_response
        )
        self.assertEqual(response["statusCode"], 200)

    def test_request_end_session(self):
        """
        Tests the response gotten when the user requests to end
        their current session.
        """
        send_msg_mock = self._mocks["send_message"]
        event = {
            "From": ApplicationRequestParams.USER_WS_PHONE_NUMBER,
            "Body": "bye",
        }
        expected_response = MessageResponse(
            body="Bye!",
            from_=User(ApplicationRequestParams.FROM_WS_PHONE_NUMBER),
            to=User(ApplicationRequestParams.USER_WS_PHONE_NUMBER),
        )
        handler = MessagesHandler(event, xray_recorder=None)
        response = handler.respond_message()
        call_kwargs = send_msg_mock.call_args_list[0][1]
        response_gotten = call_kwargs["response_model"]
        self.assertEqual(response["statusCode"], 200)
        self.assertDictEqual(response_gotten.to_dict(), expected_response.to_dict())
