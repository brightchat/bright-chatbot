class ApplicationError(Exception):
    """
    Base class for all application errors
    """

    def __init__(self, message: str, status_code: int = None):
        self._message = message
        self._status_code = status_code
        super().__init__(message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def status_code(self) -> int:
        return self._status_code


class ValidationError(ApplicationError):
    """
    Errors related to requests validation
    """

    pass


class ClientError(ApplicationError):
    """
    Errors raised by a client connection
    """

    pass


class ModerationError(ApplicationError):
    """
    Error raised when content received violates
    a content policy.
    """

    pass


class ImproperlyConfigured(ApplicationError):
    """
    Error raised when the application is not properly configured
    """

    pass


class SessionLimitError(ApplicationError):
    """
    Error raised when the maximum total number of active sessions
    is reached.
    """

    pass


class SessionQuotaLimitReached(ApplicationError):
    """
    Error raised when the maximum number of requests allowed per session
    is reached.
    """

    pass


class AuthError(ApplicationError):
    """
    Error raised when a user is not authorized
    """

    pass
