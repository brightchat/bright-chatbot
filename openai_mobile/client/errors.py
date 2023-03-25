from openai_mobile.models.errors import ApplicationError

MODERATION_ERROR = ApplicationError(
    message=(
        "The message you sent was flagged by OpenAI's moderation model. "
        "Please try again with a different message."
    ),
    status_code=422,
)

UNEXPECTED_ERROR = ApplicationError(
    message="Something went wrong. Please try again later.",
    status_code=500,
)

QUOTA_SURPASSED = ApplicationError(
    message=(
        "You have reached the maximum number of messages you can send for this session.\n"
        "Increase your message quota at https://brightbot.chat/."
    ),
    status_code=429,
)

MAX_ACTIVE_SESSIONS_SURPASSED = ApplicationError(
    message=(
        "The application is currently experiencing high traffic. "
        "Please try again later."
    ),
    status_code=503,
)
