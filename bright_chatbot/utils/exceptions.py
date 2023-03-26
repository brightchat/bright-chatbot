class ValidationError(Exception):
    """
    Errors related to requests validation
    """

    pass


class ClientError(Exception):
    """
    Errors raised by a client connection
    """

    pass


class ModerationError(Exception):
    """
    Error raised when content received violates
    a content policy.
    """

    pass


class ImproperlyConfigured(Exception):
    """
    Error raised when the application is not properly configured
    """

    pass


class SessionLimitError(Exception):
    """
    Error raised when the maximum total number of active sessions
    is reached.
    """

    pass


class SessionQuotaLimitReached(Exception):
    """
    Error raised when the maximum number of requests allowed per session
    is reached.
    """

    pass


class AuthError(Exception):
    """
    Error raised when a user is not authorized
    """

    pass
