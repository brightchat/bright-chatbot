import hashlib

import datetime as dt
from datetime import datetime
import pytz


def hash_user_id(user_id: str) -> str:
    from bright_chatbot.configs import ProjectSettings

    crypto_salt = ProjectSettings.SECRET_KEY
    hashed = hashlib.sha256((user_id + crypto_salt).encode()).hexdigest()
    return hashed


def hash_text(text: str) -> str:
    hashed = hashlib.sha256(text.encode()).hexdigest()
    return hashed


def get_utc_timestamp_now(offset_hours: int = 0):
    """
    Returns the current UTC epoch timestamp in seconds (POSIX)
    """
    dtnow = pytz.utc.localize(datetime.utcnow())
    target_dt = dtnow + dt.timedelta(hours=offset_hours)
    return target_dt.timestamp()
