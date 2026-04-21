from datetime import datetime, timezone

def parse_local_datetime_to_utc(date_string: str) -> datetime:
    local_dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M")
    local_tz = datetime.now().astimezone().tzinfo
    local_dt = local_dt.replace(tzinfo=local_tz)
    return local_dt.astimezone(timezone.utc)

def to_seconds(date_string: str) -> int:
    utc_dt = parse_local_datetime_to_utc(date_string)
    return int(utc_dt.timestamp())

def to_seconds(date_string: str) -> int:
    return int(parse_local_datetime_to_utc(date_string).timestamp())

def format_time_remaining(expires_at):
    if not expires_at:
        return "Ended"

    now = datetime.now().astimezone()

    # Handle string timestamps safely
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            return "Ended"

    # If DB time is naive, assume local timezone
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=now.tzinfo)

    diff = expires_at - now
    total_seconds = int(diff.total_seconds())

    if total_seconds <= 0:
        return "Ended"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"