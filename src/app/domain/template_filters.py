import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def reduce_slashes(value: str) -> str:
    """Reduce any sequence of multiple backslashes to a single forward slash"""
    return re.sub(r"\\+", "/", value)


def format_and_localize_timestamp(value: datetime):  # TODO: get timezone from environment variable
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    tz = ZoneInfo("America/Detroit")
    localized_value = value.astimezone(tz)
    return localized_value.strftime("%B %d, %Y @ %I:%M %p")


def truncate_string(value: str, length: int) -> str:
    return value[:length] + "..." if len(value) > length else value


def get_basefile_name(value: str) -> str:
    return Path(value).name
