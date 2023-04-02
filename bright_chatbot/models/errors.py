from typing import Type

from pydantic import BaseModel

from bright_chatbot.utils import exceptions


class ApplicationError(BaseModel):
    """
    Represents an error that occurred in the application.
    """

    message: str
    status_code: int

    @property
    def exception(self) -> Type[exceptions.ApplicationError]:
        """
        Retrieves the exception that corresponds to the error.
        """
        if self.status_code == 422:
            return exceptions.ModerationError(
                self.message, status_code=self.status_code
            )
        if self.status_code == 429:
            return exceptions.SessionQuotaLimitReached(
                self.message, status_code=self.status_code
            )
        if self.status_code == 503:
            return exceptions.SessionLimitError(
                self.message, status_code=self.status_code
            )
        return exceptions.ApplicationError(self.message, status_code=self.status_code)

    def raise_error(self, source_exc=None) -> None:
        """
        Raises the error as an exception.
        """
        raise self.exception from source_exc
