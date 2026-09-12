"""Calendar arithmetic for the initial working-day scheduling kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import FrozenSet


@dataclass(frozen=True)
class WorkingCalendar:
    """A calendar with working weekdays and project-specific holiday exceptions.

    Durations are expressed in working days. A one-day task beginning on Monday
    finishes on Monday; a zero-day task is a milestone and finishes on its start.
    """

    working_weekdays: FrozenSet[int] = frozenset({0, 1, 2, 3, 4})
    holidays: FrozenSet[date] = field(default_factory=frozenset)

    def is_working_day(self, value: date) -> bool:
        return value.weekday() in self.working_weekdays and value not in self.holidays

    def next_working_day(self, value: date) -> date:
        while not self.is_working_day(value):
            value += timedelta(days=1)
        return value

    def previous_working_day(self, value: date) -> date:
        """Return `value`, or the nearest preceding working day."""
        while not self.is_working_day(value):
            value -= timedelta(days=1)
        return value

    def add_working_days(self, start: date, days: int) -> date:
        """Return the date reached after adding `days` working days.

        `days=0` returns the first eligible working date. This is used for
        dependency handoffs; task finish calculation uses duration minus one.
        """
        result = self.next_working_day(start) if days >= 0 else self.previous_working_day(start)
        remaining = abs(days)
        direction = 1 if days >= 0 else -1
        while remaining:
            result += timedelta(days=direction)
            if self.is_working_day(result):
                remaining -= 1
        return result

    def start_for_finish(self, finish: date, duration_days: int) -> date:
        """Return the working-day start needed to finish on `finish`."""
        if duration_days < 0:
            raise ValueError("Task duration cannot be negative.")
        scheduled_finish = self.previous_working_day(finish)
        if duration_days == 0:
            return scheduled_finish
        return self.add_working_days(scheduled_finish, -(duration_days - 1))

    def working_day_difference(self, start: date, end: date) -> int:
        """Return the signed number of working-day steps from start to end."""
        current = self.next_working_day(start) if end >= start else self.previous_working_day(start)
        target = self.next_working_day(end) if end >= start else self.previous_working_day(end)
        if current == target:
            return 0
        direction = 1 if target > current else -1
        steps = 0
        while current != target:
            current += timedelta(days=direction)
            if self.is_working_day(current):
                steps += direction
        return steps

    def finish_for_duration(self, start: date, duration_days: int) -> date:
        if duration_days < 0:
            raise ValueError("Task duration cannot be negative.")
        scheduled_start = self.next_working_day(start)
        if duration_days == 0:
            return scheduled_start
        return self.add_working_days(scheduled_start, duration_days - 1)
