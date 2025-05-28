import re
from typing import Any, Union
from datetime import datetime, date, timedelta

from my_codegen.utils.report_utils import Reporter
from my_codegen.utils.logger import logger


class Expect:

    def __init__(self, actual: Any, name: str):
        self.actual = actual
        self._name = name
        self._negated = False

    def _not(self) -> 'Expect':
        new_expect = Expect(self.actual, self._name)
        new_expect._negated = not self._negated
        return new_expect

    def _fail(self, message: str, expected: Any = None):
        negation = "NOT " if self._negated else ""

        full_message = f"{self._name} expected {negation}{message}"

        if expected is not None:
            full_message += f"\nExpected: {repr(expected)}"

        full_message += f"\nActual: {repr(self.actual)}"

        raise AssertionError(full_message)

    def _success(self, message: str):
        """Логирует успешную проверку"""
        success_message = f'"{self._name}" {message}'

    def _check(self, condition: bool, message: str, expected: Any = None):
        message_step = f"Check {self._name} {message}"

        logger.info(f"{message_step}")
        with Reporter.step(f"{message_step}"):

            if self._negated:
                condition = not condition

            if not condition:
                self._fail(message, expected)
            else:
                self._success(f"{message}")

        return self

    # ===============================
    # БАЗОВЫЕ ПРОВЕРКИ (для всех типов)
    # ===============================

    def isEqual(self, expected: Any) -> 'Expect':
        return self._check(
            self.actual == expected,
            f"to equal {repr(expected)}",
            expected
        )

    def isNotEqual(self, expected: Any) -> 'Expect':
        return self._check(
            self.actual != expected,
            f"to not equal {repr(expected)}",
            expected
        )

    def isNone(self) -> 'Expect':
        return self._check(self.actual is None, "to be None")

    def isNotNone(self) -> 'Expect':
        return self._check(self.actual is not None, "to not be None")

    def isGreaterThan(self, expected: Union[int, float]) -> 'Expect':
        return self._check(
            self.actual > expected,
            f"to be greater than {expected}",
            f"> {expected}"
        )

    def isLessThan(self, expected: Union[int, float]) -> 'Expect':
        return self._check(
            self.actual < expected,
            f"to be less than {expected}",
            f"< {expected}"
        )

    def contains(self, substring: str) -> 'Expect':
        if not isinstance(self.actual, str):
            self._fail(f"to be a string for contains check, but got {type(self.actual).__name__}")
        return self._check(substring in self.actual, f"to contain '{substring}'")

    def startsWith(self, prefix: str) -> 'Expect':
        if not isinstance(self.actual, str):
            self._fail(f"to be a string for startsWith check, but got {type(self.actual).__name__}")
        return self._check(self.actual.startswith(prefix), f"to start with '{prefix}'")

    def endsWith(self, suffix: str) -> 'Expect':
        if not isinstance(self.actual, str):
            self._fail(f"to be a string for endsWith check, but got {type(self.actual).__name__}")
        return self._check(self.actual.endswith(suffix), f"to end with '{suffix}'")

    def matches(self, pattern: str) -> 'Expect':
        if not isinstance(self.actual, str):
            self._fail(f"to be a string for regex match, but got {type(self.actual).__name__}")
        return self._check(
            re.search(pattern, self.actual) is not None,
            f"to match pattern '{pattern}'"
        )

    # ===============================
    #       ПРОВЕРКИ КОЛЛЕКЦИЙ
    # ===============================

    def hasLength(self, expected_length: int) -> 'Expect':
        try:
            actual_length = len(self.actual)
        except TypeError:
            self._fail("to have length (no len() method)")

        return self._check(
            actual_length == expected_length,
            f"to have length {expected_length}",
            f"length {expected_length}"
        )

    def isEmpty(self) -> 'Expect':
        try:
            return self._check(len(self.actual) == 0, "to be empty")
        except TypeError:
            self._fail("to be empty (no len() method)")

    def containsItem(self, item: Any) -> 'Expect':
        try:
            return self._check(item in self.actual, f"to contain item {repr(item)}")
        except TypeError:
            self._fail("to be iterable for item check")

    def containsItems(self, *items: Any) -> 'Expect':
        for item in items:
            self.containsItem(item)
        return self

    # ===============================
    #          ПРОВЕРКА ДАТЫ
    # ===============================

    def _parse_date(self, value: Any) -> datetime:
        """Парсер дат - только основные форматы"""
        if isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        elif isinstance(value, str):
            # Только самые популярные форматы
            formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            self._fail(f"to be a valid date string, but got '{value}'")
        else:
            self._fail(f"to be a date, but got {type(value).__name__}")

    def isAfter(self, date_threshold: Union[datetime, date, str]) -> 'Expect':
        actual_dt = self._parse_date(self.actual)
        threshold_dt = self._parse_date(date_threshold)
        return self._check(
            actual_dt > threshold_dt,
            f"to be after {threshold_dt.date()}",
            f"after {threshold_dt.date()}"
        )

    def isBefore(self, date_threshold: Union[datetime, date, str]) -> 'Expect':
        actual_dt = self._parse_date(self.actual)
        threshold_dt = self._parse_date(date_threshold)
        return self._check(
            actual_dt < threshold_dt,
            f"to be before {threshold_dt.date()}",
            f"before {threshold_dt.date()}"
        )

    def isToday(self) -> 'Expect':
        actual_dt = self._parse_date(self.actual)
        today = date.today()
        return self._check(
            actual_dt.date() == today,
            f"to be today ({today})",
            today
        )

    def isAroundNow(self, minutes: int = 1) -> 'Expect':
        """Проверка, что дата в пределах ±N минут от текущего времени"""
        actual_dt = self._parse_date(self.actual)
        now = datetime.now()
        delta = timedelta(minutes=minutes)

        min_time = now - delta
        max_time = now + delta

        return self._check(
            min_time <= actual_dt <= max_time,
            f"to be around now (±{minutes} minutes)",
            f"[{min_time.strftime('%H:%M:%S')}, {max_time.strftime('%H:%M:%S')}]"
        )

    def isCloseToNow(self, seconds: int = 60) -> 'Expect':
        """Проверка, что дата в пределах ±N секунд от текущего времени"""
        actual_dt = self._parse_date(self.actual)
        now = datetime.now()
        delta = timedelta(seconds=seconds)

        min_time = now - delta
        max_time = now + delta

        return self._check(
            min_time <= actual_dt <= max_time,
            f"to be close to now (±{seconds} seconds)",
            f"[{min_time.strftime('%H:%M:%S')}, {max_time.strftime('%H:%M:%S')}]"
        )

    def isJustCreated(self, tolerance_minutes: int = 2) -> 'Expect':
        """Проверка, что объект только что создан (в пределах N минут назад)"""
        actual_dt = self._parse_date(self.actual)
        now = datetime.now()
        min_time = now - timedelta(minutes=tolerance_minutes)

        return self._check(
            min_time <= actual_dt <= now,
            f"to be just created (within last {tolerance_minutes} minutes)",
            f"between {min_time.strftime('%H:%M:%S')} and {now.strftime('%H:%M:%S')}"
        )

    def isRecentlyUpdated(self, minutes_ago: int = 5) -> 'Expect':
        """Проверка, что объект недавно обновлен"""
        actual_dt = self._parse_date(self.actual)
        now = datetime.now()
        threshold = now - timedelta(minutes=minutes_ago)

        return self._check(
            actual_dt >= threshold,
            f"to be recently updated (within last {minutes_ago} minutes)",
            f"after {threshold.strftime('%H:%M:%S')}"
        )


# ===============================
# ПРОСТОЙ API - ОДНА ФУНКЦИЯ
# ===============================

def expect(actual: Any, name: str) -> Expect:
    return Expect(actual, name)
