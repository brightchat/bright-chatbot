import abc
from os import environ
from typing import Type

from bright_chatbot.utils.exceptions import ImproperlyConfigured
from bright_chatbot.utils.functional import classproperty


class BaseSettings(abc.ABC):
    SETTINGS_PREFIX = "BRIGHT_CHATBOT"

    def get(
        self,
        name: str,
        default: str = None,
        required: bool = False,
        cast: Type = None,
        accept_plain_name: bool = False,
    ) -> str:
        """
        Retrieves a setting from the environment variables.

        :param name: Name of the setting
        :param default: Default value if the setting is not found
        :param required: Whether the setting is required or not
        :param cast: Type to cast the setting to
        :param accept_plain_name: Whether to accept the plain name of the setting as an environment variable

        :return: str
        """
        var_name = f"{self.SETTINGS_PREFIX}_{name}"
        value = environ.get(
            var_name, environ.get(name, default) if accept_plain_name else default
        )
        if required and not value:
            raise ImproperlyConfigured(f"Project setting '{var_name}' not found")
        if cast:
            try:
                value = cast(value)
            except (ValueError, TypeError) as e:
                raise ImproperlyConfigured(
                    f"Invalid value for setting '{name}', expected type '{cast.__name__}' but it was impossible to cast from value '{value}'"
                ) from e
        return value
