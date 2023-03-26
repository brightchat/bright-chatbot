from tests.mock.request import ApplicationRequestParams


class EnvironmentVariables:

    PROJECT_SETTINGS_DEFAULT = {
        "OPENAI_WS_APP_TWILIO_PHONE_NUMBER": ApplicationRequestParams.FROM_WS_PHONE_NUMBER,
        "TWILIO_ACCOUNT_SID": "ACXXXXXXXX",
        "TWILIO_AUTH_TOKEN": "XXXXXXXX",
    }
