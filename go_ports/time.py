import datetime


class Duration(datetime.timedelta):
    def string(self) -> str: ...


def parse_duration(s: str) -> Duration: ...
