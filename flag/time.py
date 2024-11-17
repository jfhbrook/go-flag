import datetime

from flag.panic import panic, Panic


class Duration(datetime.timedelta):
    def __str__(self) -> str:
        secs = int(self.total_seconds())
        mins = secs // 60
        hours = secs // 3600
        secs = secs % 60
        fmt = f"{secs}s"
        if mins:
            fmt = f"{mins}m{fmt}"
        if hours:
            fmt = f"{hours}h{fmt}"
        return fmt


def parse_duration(s: str) -> Duration:
    error = f"invalid format for duration: {s}"
    hours = ""
    mins = ""
    secs = ""
    buf = ""
    for c in s:
        print("c:", c)
        if c == "s":
            secs = buf
            buf = ""
        elif c == "m":
            mins = buf
            buf = ""
        elif c == "h":
            hours = buf
            buf = ""
        else:
            buf += c

    if buf:
        panic(error)

    try:
        return Duration(
            hours=int(hours) if hours else 0,
            minutes=int(mins) if mins else 0,
            seconds=int(secs) if secs else 0,
        )
    except Exception as exc:
        raise Panic(error) from exc
