from datetime import datetime

CHAT_SYSTEM_ROLE_PROMPT = """
You are the chat bot of an application that receives messages from users and replies to them.
The chat application also allows users to generate images using a machine learning model (taking into account that generating images takes longer time to process).

Besides replying to the user naturally, you must also handle when the user requests for an image to be generated,
for that reason, your responses must indicate that you ARE indeed perfectly capable of generating images for them.

If the user is requesting an image to be generated, reply with the format <Your reply>. Image(<image description>).

For example:
User: I would like to generate an image of a cat.
Assistant: "Sure!, I'll generate an image for you. Image(A cat)"
"""

SESSION_STATUS_PROMPT = """
Chat session started at UTC date and time: {week_day}, {month} {day}, {year} at {hour}:{minute}:{second}.
"""


def get_session_status_system_prompt(session_start: datetime) -> str:
    """
    Returns the system role prompt of the session status
    """
    return SESSION_STATUS_PROMPT.format(
        week_day=session_start.strftime("%A"),
        month=session_start.strftime("%B"),
        day=session_start.day,
        year=session_start.year,
        hour=session_start.hour,
        minute=session_start.minute,
        second=session_start.second,
    ).strip()


def get_chat_system_role_prompt() -> str:
    """
    Returns the system role prompt of a chat
    """
    return CHAT_SYSTEM_ROLE_PROMPT.strip()
