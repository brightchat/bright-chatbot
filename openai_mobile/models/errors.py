from pydantic import BaseModel


class ApplicationError(BaseModel):
    """
    Represents an error that occurred in the application.
    """

    message: str
    status_code: int
