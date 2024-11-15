import datetime


class Duration(datetime.timedelta):
    def __str__(self) -> str:
        return super().__str__()


def parse_duration(s: str) -> Duration: ...
