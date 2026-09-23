class timedelta:

    def __init__(self, days: int, hours: int, minutes: int, seconds: int) -> None:
        if not all(isinstance(value, int) for value in (days, hours, minutes, seconds)):
            raise TypeError("All timedelta arguments must be integers.")
        self.total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds

    def __add__(self, other: "timedelta") -> "timedelta":
        if not isinstance(other, timedelta):
            return NotImplemented
        return timedelta(0, 0, 0, self.total_seconds + other.total_seconds)

    def __sub__(self, other: "timedelta") -> "timedelta":
        if not isinstance(other, timedelta):
            return NotImplemented
        return timedelta(0, 0, 0, self.total_seconds - other.total_seconds)

    def __neg__(self) -> "timedelta":
        return timedelta(0, 0, 0, -self.total_seconds)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, timedelta):
            return NotImplemented
        return self.total_seconds == other.total_seconds

    def __lt__(self, other: "timedelta") -> bool:
        return self.total_seconds < other.total_seconds

    def __le__(self, other: "timedelta") -> bool:
        return self.total_seconds <= other.total_seconds

    def __gt__(self, other: "timedelta") -> bool:
        return self.total_seconds > other.total_seconds

    def __ge__(self, other: "timedelta") -> bool:
        return self.total_seconds >= other.total_seconds

def max_day_in_month(year: int, month: int) -> int:
    
    if not isinstance(year, int) or not isinstance(month, int):
        raise TypeError("year and month must be integers")

    if month < 1 or month > 12:
        return 0

    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    if leap:
        month_lengths[1] = 29

    return month_lengths[month - 1]

class datetime:

    def __init__(
        self, year: int, month: int, day: int, hour: int, minute: int, second: int
    ) -> None:
        if not all(
            isinstance(v, int) for v in (year, month, day, hour, minute, second)
        ):
            raise TypeError("All datetime components must be integers.")
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

    def normalize(self) -> None:
        while self.second < 0:
            self.second += 60
            self.minute -= 1
        while self.second > 59:
            self.second -= 60
            self.minute += 1

        while self.minute < 0:
            self.minute += 60
            self.hour -= 1
        while self.minute > 59:
            self.minute -= 60
            self.hour += 1

        while self.hour < 0:
            self.hour += 24
            self.day -= 1
        while self.hour > 23:
            self.hour -= 24
            self.day += 1

        while self.day < 1:
            self.month -= 1
            if self.month < 1:
                self.month = 12
                self.year -= 1
            self.day += max_day_in_month(self.year, self.month)

        while self.day > max_day_in_month(self.year, self.month):
            self.day -= max_day_in_month(self.year, self.month)
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1

        while self.month < 1:
            self.month += 12
            self.year -= 1
        while self.month > 12:
            self.month -= 12
            self.year += 1

    def adjust_gregorian(self, adding: bool) -> None:
        if adding:
            if self.year == 1582 and self.month == 10 and 5 <= self.day <= 14:
                self.day = 15
        else:
            if self.year == 1582 and self.month == 10 and 5 <= self.day <= 14:
                self.day = 4

    def add_second(self) -> None:
        self.second += 1
        self.normalize()
        self.adjust_gregorian(True)

    def add_minute(self) -> None:
        self.minute += 1
        self.normalize()
        self.adjust_gregorian(True)

    def add_hour(self) -> None:
        self.hour += 1
        self.normalize()
        self.adjust_gregorian(True)

    def add_day(self) -> None:
        self.day += 1
        self.normalize()
        self.adjust_gregorian(True)

    def sub_second(self) -> None:
        self.second -= 1
        self.normalize()
        self.adjust_gregorian(False)

    def sub_minute(self) -> None:
        self.minute -= 1
        self.normalize()
        self.adjust_gregorian(False)

    def sub_hour(self) -> None:
        self.hour -= 1
        self.normalize()
        self.adjust_gregorian(False)

    def sub_day(self) -> None:
        self.day -= 1
        self.normalize()
        self.adjust_gregorian(False)

    def add_seconds(self, seconds: int) -> None:
        for _ in range(seconds):
            self.add_second()

    def add_minutes(self, minutes: int) -> None:
        for _ in range(minutes):
            self.add_minute()

    def add_hours(self, hours: int) -> None:
        for _ in range(hours):
            self.add_hour()

    def add_days(self, days: int) -> None:
        for _ in range(days):
            self.add_day()

    def sub_seconds(self, seconds: int) -> None:
        for _ in range(seconds):
            self.sub_second()

    def sub_minutes(self, minutes: int) -> None:
        for _ in range(minutes):
            self.sub_minute()

    def sub_hours(self, hours: int) -> None:
        for _ in range(hours):
            self.sub_hour()

    def sub_days(self, days: int) -> None:
        for _ in range(days):
            self.sub_day()

    def __add__(self, td: timedelta) -> "datetime":
        if not isinstance(td, timedelta):
            return NotImplemented
        result = self.copy()
        if td.total_seconds >= 0:
            result.add_seconds(td.total_seconds)
        else:
            result.sub_seconds(-td.total_seconds)
        return result

    def __sub__(self, other: object):
        if isinstance(other, timedelta):
            return self + (-other)
        if isinstance(other, datetime):
            a = other.copy()
            b = self.copy()
            seconds = 0
            if b >= a:
                while a < b:
                    a.add_second()
                    seconds += 1
            else:
                while a > b:
                    a.sub_second()
                    seconds -= 1
            return timedelta(0, 0, 0, seconds)
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, datetime):
            return NotImplemented
        return (
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
        ) == (
            other.year,
            other.month,
            other.day,
            other.hour,
            other.minute,
            other.second,
        )

    def __lt__(self, other: "datetime") -> bool:
        return (
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
        ) < (
            other.year,
            other.month,
            other.day,
            other.hour,
            other.minute,
            other.second,
        )

    def __le__(self, other: "datetime") -> bool:
        return self == other or self < other

    def __gt__(self, other: "datetime") -> bool:
        return not self <= other

    def __ge__(self, other: "datetime") -> bool:
        return not self < other

    def __ne__(self, other: object) -> bool:
        return not self == other

    def copy(self) -> "datetime":
        return datetime(
            self.year, self.month, self.day, self.hour, self.minute, self.second
        )

    def isoformat(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}T{self.hour:02d}:{self.minute:02d}:{self.second:02d}"

