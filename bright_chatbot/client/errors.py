from bright_chatbot.models.errors import ApplicationError

MODERATION_ERROR = ApplicationError(
    message=(
        "The message you sent was flagged by the message moderation system. "
        "Please try again with a different message."
    ),
    status_code=422,
)

INVALID_REQUEST_ERROR = ApplicationError(
    message=(
        "Sorry, your request could not be fulfilled. It may have content "
        "that is not allowed by our safety system."
    ),
    status_code=400,
)

UNEXPECTED_ERROR = ApplicationError(
    message="Something went wrong. Please try again later.",
    status_code=500,
)

QUOTA_SURPASSED = ApplicationError(
    message=(
        "You have reached the maximum number of messages you can send for this period.\n"
        "Increase your messages quota at https://brightbot.chat/."
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

IMAGE_GENERATION_QUOTA_SURPASSED = ApplicationError(
    message=(
        "You have reached the maximum number of images you can generate for this period.\n"
        "Increase your image quota at https://brightbot.chat/."
    ),
    status_code=429,
)
