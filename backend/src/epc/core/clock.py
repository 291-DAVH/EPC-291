"""The current moment as text, in the two formats the platform writes: local time without zone (files, ledgers, job status) and with the zone offset (audit trails)."""
import datetime as dt


def now_local() -> str:
    """`2026-10-25T21:30:00`: local wall-clock time, seconds precision, no zone."""
    return dt.datetime.now().isoformat(timespec="seconds")


def now_aware() -> str:
    """`2026-10-25T21:30:00-03:00`: local time with its UTC offset, seconds precision."""
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")
