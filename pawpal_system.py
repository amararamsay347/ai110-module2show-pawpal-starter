# Logic layer where the backend classes are.
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time


@dataclass
class TimeSlot:
    """A block of time in an owner's day (e.g. when they are available)."""

    start: time
    end: time


@dataclass
class Task:
    name: str
    time: datetime
    priority: int
    reason: str = ""
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        raise NotImplementedError

    def reschedule(self, new_time: datetime) -> None:
        """Move this task to a new time."""
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    breed: str
    age: int
    preferences: dict = field(default_factory=dict)
    # repr=False avoids infinite recursion between Pet <-> Owner
    owners: list[Owner] = field(default_factory=list, repr=False)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    age: int
    schedule: list[TimeSlot] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet and register this owner on the pet."""
        raise NotImplementedError

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet and unregister this owner from the pet."""
        raise NotImplementedError

    def get_daily_tasks(self, day: date) -> list[Task]:
        """Return all tasks across this owner's pets for the given day."""
        raise NotImplementedError


@dataclass
class Reminder:
    time: datetime
    priority: int
    task: Task
    message: str = ""

    def send(self) -> None:
        """Deliver the reminder/notification."""
        raise NotImplementedError

    def snooze(self, minutes: int) -> None:
        """Push the reminder back by the given number of minutes."""
        raise NotImplementedError


class Scheduler:
    """Builds and explains a daily plan from an owner's pets' tasks."""

    def __init__(self, tasks: list[Task] | None = None) -> None:
        self.tasks: list[Task] = tasks if tasks is not None else []

    def build_daily_schedule(self, owner: Owner, day: date) -> list[Task]:
        """Create an ordered plan for the day using the owner's schedule and preferences."""
        raise NotImplementedError

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (and time as a tiebreaker)."""
        raise NotImplementedError

    def detect_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Return tasks that overlap or clash with each other."""
        raise NotImplementedError

    def explain_choice(self, task: Task) -> str:
        """Explain why a task was placed where it was."""
        raise NotImplementedError

    def create_reminder(self, task: Task) -> Reminder:
        """Create a reminder for a scheduled task."""
        raise NotImplementedError
