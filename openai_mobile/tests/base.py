import abc
from os import environ
from typing import Dict
import unittest
from unittest import mock

from backend.handlers.images_handler import ImageRequestedHandler
from backend.app_loggers import XRaySegmentsAppLogger
from clients.twilio import TwilioClient
from tests.mock.twilio_objs import MessageInstanceResponse
from tests.mock.system import EnvironmentVariables
from tests.mock.images_handler import ResponseObjects


class ApplicationBaseTestCase(unittest.TestCase, metaclass=abc.ABCMeta):
    _CLASS_PATCHES = {
        "boto_client": (mock.patch, ("boto3.client",), {}),
        "make_reply": (
            mock.patch.object,
            (
                ImageRequestedHandler,
                "make_reply",
            ),
            {"return_value": ResponseObjects.message_response},
        ),
        "start_segment": (
            mock.patch.object,
            (XRaySegmentsAppLogger, "start_segment"),
            {"return_value": None},
        ),
        "end_segment": (
            mock.patch.object,
            (XRaySegmentsAppLogger, "end_segment"),
            {"return_value": None},
        ),
        "send_message": (
            mock.patch.object,
            (TwilioClient, "send_message"),
            {"return_value": MessageInstanceResponse},
        ),
        "verify_signature": (
            mock.patch.object,
            (TwilioClient, "verify_signature"),
            {"return_value": None},
        ),
        "tw_cl_init": (
            mock.patch.object,
            (TwilioClient, "__init__"),
            {"return_value": None},
        ),
        "environ": (
            mock.patch.dict,
            (
                environ,
                EnvironmentVariables.PROJECT_SETTINGS_DEFAULT,
            ),
            {"clear": True},
        ),
    }

    def setUp(self):
        """
        Patch the objects in self._CLASS_PATCHES
        """
        super().setUp()
        self._patchers = {}
        self._mocks: Dict[str, mock.Mock] = {}
        for patch_name, patch_attrs in self._CLASS_PATCHES.items():
            patch_f, patch_args, patch_kwargs = patch_attrs
            patcher = patch_f(*patch_args)
            mocked = patcher.start()
            self._patchers[patch_name] = patcher
            self._mocks[patch_name] = mocked
            for key, value in patch_kwargs.items():
                setattr(mocked, key, value)
            if not patch_kwargs.get("clear"):
                self.addCleanup(patcher.stop)
