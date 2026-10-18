# Logic layer where the backend classes are.
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum
from uuid import uuid4


@dataclass
class TimeSlot:
    """A block of time in an owner's day (e.g. when they are available)."""

    start: time
    end: time


class Priority(IntEnum):
    """Task urgency from 1 (lowest) to 5 (highest)."""

    LOWEST = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    HIGHEST = 5


class Frequency(str, Enum):
    """How often a task repeats."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Task:
    """A single pet-care activity: what, when, how often, and whether it's done."""

    name: str
    time: datetime
    priority: Priority
    description: str = ""
    frequency: Frequency = Frequency.ONCE
    duration_minutes: int = 15
    reason: str = ""
    completed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)
    # Set by Pet.add_task; repr/compare off to avoid Pet <-> Task recursion
    pet: Pet | None = field(default=None, repr=False, compare=False)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def reschedule(self, new_time: datetime) -> None:
        """Move this task to a new time."""
        self.time = new_time

    def occurs_on(self, day: date) -> bool:
        """Whether this task falls on the given day, given its frequency."""
        start = self.time.date()
        if day < start:
            return False
        if self.frequency == Frequency.DAILY:
            return True
        if self.frequency == Frequency.WEEKLY:
            return day.weekday() == start.weekday()
        return day == start

    def time_on(self, day: date) -> datetime:
        """This task's start time placed on the given day."""
        return datetime.combine(day, self.time.time())

    @property
    def end_time(self) -> datetime:
        """When this task finishes (start time plus its duration)."""
        return self.time + timedelta(minutes=self.duration_minutes)


@dataclass
class Pet:
    """A pet's details plus the list of care tasks assigned to it."""

    name: str
    breed: str
    age: int
    preferences: dict = field(default_factory=dict)
    # repr=False/compare=False avoid infinite recursion between Pet <-> Owner
    owners: list[Owner] = field(default_factory=list, repr=False, compare=False)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet and set task.pet to this pet."""
        if task.pet is not None and task.pet is not self:
            task.pet.remove_task(task)
        if task not in self.tasks:
            self.tasks.append(task)
        task.pet = self

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet and clear task.pet."""
        if task in self.tasks:
            self.tasks.remove(task)
        if task.pet is self:
            task.pet = None


@dataclass
class Owner:
    """A pet owner who manages multiple pets and can see all of their tasks."""

    name: str
    age: int
    schedule: list[TimeSlot] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet and register this owner on the pet."""
        if not any(p is pet for p in self.pets):
            self.pets.append(pet)
        if not any(o is self for o in pet.owners):
            pet.owners.append(self)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet and unregister this owner from the pet."""
        self.pets = [p for p in self.pets if p is not pet]
        pet.owners = [o for o in pet.owners if o is not self]

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [t for pet in self.pets for t in pet.tasks]

    def get_daily_tasks(self, day: date) -> list[Task]:
        """Return all tasks across this owner's pets for the given day."""
        return [t for t in self.get_all_tasks() if t.occurs_on(day)]


@dataclass
class Reminder:
    """An optional notification that prompts the owner about a task."""

    time: datetime
    priority: Priority
    task: Task
    message: str = ""

    def send(self) -> None:
        """Deliver the reminder/notification."""
        pet_name = self.task.pet.name if self.task.pet else "your pet"
        text = self.message or f"{self.task.name} for {pet_name}"
        print(f"[{self.priority.name}] {self.time:%Y-%m-%d %H:%M} - {text}")

    def snooze(self, minutes: int) -> None:
        """Push the reminder back by the given number of minutes."""
        self.time += timedelta(minutes=minutes)


class Scheduler:
    """The brain: retrieves, organizes and manages tasks across all of an owner's pets.

    Stateless: every method reads tasks through Owner.get_all_tasks(), so tasks from
    every pet are considered together and there is a single source of truth.
    """

    # --- retrieve ---
    def get_tasks(
        self,
        owner: Owner,
        pet: Pet | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """All of the owner's tasks across pets, optionally filtered by pet or completion."""
        tasks = owner.get_all_tasks()
        if pet is not None:
            tasks = [t for t in tasks if t.pet is pet]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    # --- organize ---
    def build_daily_schedule(self, owner: Owner, day: date) -> list[Task]:
        """Create an ordered plan for the day using the owner's schedule and preferences."""
        tasks = [
            t for t in owner.get_all_tasks()
            if t.occurs_on(day) and not t.completed
        ]
        if owner.schedule:
            tasks = [t for t in tasks if self._fits_schedule(t, owner.schedule)]
        return self.prioritize_tasks(tasks)

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (and time as a tiebreaker)."""
        return sorted(tasks, key=lambda t: (-t.priority, t.time.time()))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks chronologically by time of day."""
        return sorted(tasks, key=lambda t: t.time.time())

    def detect_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Return tasks that overlap or clash with each other (across any pets)."""
        ordered = sorted(tasks, key=lambda t: t.time)
        conflicting: list[Task] = []
        for i, a in enumerate(ordered):
            for b in ordered[i + 1:]:
                if b.time >= a.end_time:
                    break
                for t in (a, b):
                    if t not in conflicting:
                        conflicting.append(t)
        return conflicting

    def find_daily_conflicts(self, owner: Owner, day: date) -> list[Task]:
        """Conflicts among the owner's tasks on one day, comparing across all pets."""
        todays = [
            Task(
                name=t.name, time=t.time_on(day), priority=t.priority,
                duration_minutes=t.duration_minutes, id=t.id, pet=t.pet,
            )
            for t in owner.get_all_tasks() if t.occurs_on(day) and not t.completed
        ]
        clashing = {t.id for t in self.detect_conflicts(todays)}
        return [t for t in owner.get_all_tasks() if t.id in clashing]

    # --- manage ---
    def complete_task(self, owner: Owner, task_id: str) -> Task | None:
        """Mark the task with this id complete, wherever it lives. None if not found."""
        for t in owner.get_all_tasks():
            if t.id == task_id:
                t.mark_complete()
                return t
        return None

    def explain_choice(self, task: Task) -> str:
        """Explain why a task was placed where it was."""
        parts = [
            f"'{task.name}' has {task.priority.name.lower()} priority",
            f"is scheduled for {task.time:%H:%M} ({task.frequency.value})",
        ]
        if task.reason:
            parts.append(f"because {task.reason}")
        return ", ".join(parts) + "."

    def create_reminder(self, task: Task) -> Reminder:
        """Optional add-on: create a reminder for a scheduled task."""
        return Reminder(
            time=task.time,
            priority=task.priority,
            task=task,
            message=f"Time for: {task.name}",
        )

    @staticmethod
    def _fits_schedule(task: Task, slots: list[TimeSlot]) -> bool:
        """Whether the task fits entirely inside one of the available time slots."""
        start = task.time.time()
        end = task.end_time.time()
        return any(s.start <= start and end <= s.end for s in slots)
