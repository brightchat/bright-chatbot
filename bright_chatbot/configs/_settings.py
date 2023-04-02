from .project_settings import ProjectSettings


class Settings:
    """
    Class used to access and customize the project settings
    """

    def __init__(self):
        self.__custom_settings = {}

    def __getattr__(self, item):
        if not item.startswith("_"):
            return self.__custom_settings.get(item, getattr(ProjectSettings(), item))
        return super().__getattr__(item)

    def __setattr__(self, key, value):
        if not key.startswith("_"):
            self.__check_is_setting(key)
            self.__custom_settings[key] = value
        else:
            super().__setattr__(key, value)

    def __check_is_setting(self, key):
        if not (
            key in ProjectSettings.__dict__
            and isinstance(ProjectSettings.__dict__[key], property)
        ):
            raise AttributeError(f"Attribute '{key}' is not a valid setting")
