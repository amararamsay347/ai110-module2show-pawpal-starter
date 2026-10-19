# Logic layer where the backend classes are.
from __future__ import annotations

from dataclasses import dataclass, field
import calendar
import json
import os
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum
from uuid import uuid4


@dataclass
class TimeSlot:
    """A block of time in an owner's day (e.g. when they are available)."""

    start: time
    end: time

    def to_dict(self) -> dict:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}

    @classmethod
    def from_dict(cls, data: dict) -> TimeSlot:
        return cls(time.fromisoformat(data["start"]), time.fromisoformat(data["end"]))


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
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


def _add_months(when: datetime, months: int = 1) -> datetime:
    """Shift a datetime by whole months, clamping the day to the target month's length.

    Month arithmetic is done on a zero-based month index so the year rolls over correctly
    (Dec + 1 -> Jan of next year). Jan 31 + 1 month -> Feb 28 (or 29 in a leap year).
    The result is based on `when`, not an original anchor day, so it can drift
    (Jan 31 -> Feb 28 -> Mar 28).
    """
    index = when.month - 1 + months
    year, month = when.year + index // 12, index % 12 + 1
    day = min(when.day, calendar.monthrange(year, month)[1])
    return when.replace(year=year, month=month, day=day)


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

    def mark_complete(self) -> Task | None:
        """Mark this task as done.

        A recurring task (daily/weekly/biweekly/monthly) attached to a pet also gets its next occurrence created
        (returned, and added to the same pet). Completing an already-done task does nothing new.

        Algorithm: the next start is `time` + 1/7/14 days, or one calendar month for monthly.
        The finished task is switched to ONCE so it stops projecting itself forward, and the
        new task carries the series; this keeps exactly one pending task per series.

        Returns:
            The newly created task, or None for one-off tasks, tasks with no pet, and
            tasks that were already completed.
        """
        if self.completed:
            return None
        self.completed = True
        if self.frequency == Frequency.ONCE or self.pet is None:
            return None
        if self.frequency == Frequency.MONTHLY:
            next_time = _add_months(self.time)
        else:
            days = {Frequency.DAILY: 1, Frequency.WEEKLY: 7, Frequency.BIWEEKLY: 14}[self.frequency]
            next_time = self.time + timedelta(days=days)
        nxt = Task(
            name=self.name, time=next_time, priority=self.priority,
            description=self.description, frequency=self.frequency,
            duration_minutes=self.duration_minutes, reason=self.reason,
        )
        # The finished task stops projecting itself forward; the new one carries the series.
        self.frequency = Frequency.ONCE
        self.pet.add_task(nxt)
        return nxt

    def to_dict(self) -> dict:
        """JSON-safe form of this task (the pet link is implied by where it is stored)."""
        return {
            "id": self.id, "name": self.name, "time": self.time.isoformat(),
            "priority": int(self.priority), "description": self.description,
            "frequency": self.frequency.value, "duration_minutes": self.duration_minutes,
            "reason": self.reason, "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Rebuild a task saved by to_dict(), keeping its original id."""
        return cls(
            name=data["name"], time=datetime.fromisoformat(data["time"]),
            priority=Priority(data["priority"]), description=data.get("description", ""),
            frequency=Frequency(data.get("frequency", "once")),
            duration_minutes=data.get("duration_minutes", 15), reason=data.get("reason", ""),
            completed=data.get("completed", False), id=data["id"],
        )

    def reschedule(self, new_time: datetime) -> None:
        """Move this task to a new time."""
        self.time = new_time

    def occurs_on(self, day: date) -> bool:
        """Whether this task falls on the given day, given its frequency.

        Recurrence is projected from the task's start date (never before it):
        daily is every day, weekly the same weekday, biweekly every 14 days from the start,
        monthly the same day of the month (the last day when the month is shorter).
        A ONCE task occurs only on its start date.
        """
        start = self.time.date()
        if day < start:
            return False
        if self.frequency == Frequency.DAILY:
            return True
        if self.frequency == Frequency.WEEKLY:
            return day.weekday() == start.weekday()
        if self.frequency == Frequency.BIWEEKLY:
            return (day - start).days % 14 == 0
        if self.frequency == Frequency.MONTHLY:
            return day.day == min(start.day, calendar.monthrange(day.year, day.month)[1])
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

    def to_dict(self) -> dict:
        return {
            "name": self.name, "breed": self.breed, "age": self.age,
            "preferences": self.preferences, "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        pet = cls(
            name=data["name"], breed=data.get("breed", ""), age=data.get("age", 0),
            preferences=data.get("preferences", {}),
        )
        for t in data.get("tasks", []):
            pet.add_task(Task.from_dict(t))
        return pet


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

    def to_dict(self) -> dict:
        return {
            "name": self.name, "age": self.age, "preferences": self.preferences,
            "schedule": [s.to_dict() for s in self.schedule],
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        owner = cls(
            name=data["name"], age=data.get("age", 0), preferences=data.get("preferences", {}),
            schedule=[TimeSlot.from_dict(s) for s in data.get("schedule", [])],
        )
        for p in data.get("pets", []):
            owner.add_pet(Pet.from_dict(p))
        return owner

    def save_to_json(self, path: str = "data.json") -> None:
        """Write the owner, pets and tasks to a JSON file.

        Writes to a temporary file and swaps it in, so a crash mid-write can't leave a
        half-written data file behind.
        """
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        os.replace(tmp, path)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> Owner | None:
        """Load an owner saved by save_to_json().

        Returns None when the file is missing, unreadable or malformed, so callers can
        fall back to a fresh owner instead of crashing.
        """
        try:
            with open(path, encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        except (OSError, ValueError, KeyError, TypeError):
            return None


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
        pet: Pet | str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """All of the owner's tasks across pets, optionally filtered by pet (object or name) or completion.

        A thin wrapper that gathers tasks via Owner.get_all_tasks() and delegates to filter_tasks().
        """
        return self.filter_tasks(owner.get_all_tasks(), completed=completed, pet=pet)

    def filter_tasks(
        self,
        tasks: list[Task],
        completed: bool | None = None,
        pet: Pet | str | None = None,
    ) -> list[Task]:
        """Keep tasks matching completion status and/or pet (object or name, case-insensitive).

        Any filter left as None is ignored, so filters can be combined or omitted.

        Args:
            tasks: The tasks to filter (any list, e.g. a day's tasks or a sorted list).
            completed: True for finished tasks, False for pending ones, None for both.
            pet: A Pet (matched by identity) or a pet name (matched case-insensitively).

        Returns:
            A new list in the original order; the input list is not modified.
            Tasks with no pet never match a pet-name filter.
        """
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if isinstance(pet, str):
            tasks = [t for t in tasks if t.pet is not None and t.pet.name.lower() == pet.lower()]
        elif pet is not None:
            tasks = [t for t in tasks if t.pet is pet]
        return tasks

    # --- organize ---
    def build_daily_schedule(self, owner: Owner, day: date) -> list[Task]:
        """Create an ordered plan for the day using the owner's schedule and preferences.

        Algorithm: keep pending tasks that occur on `day`; if the owner has availability
        slots, drop tasks that don't fit entirely inside one; then order the rest with
        prioritize_tasks() (highest priority first, earlier time of day on ties).

        Returns:
            The plan in priority order, not chronological order. Use sort_by_time() for that.
        """
        tasks = [
            t for t in owner.get_all_tasks()
            if t.occurs_on(day) and not t.completed
        ]
        if owner.schedule:
            tasks = [t for t in tasks if self._fits_schedule(t, owner.schedule)]
        return self.prioritize_tasks(tasks)

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (and time as a tiebreaker).

        Sorts on (-priority, time of day): highest priority first, and among equal priorities
        the earliest time of day first. The date is ignored, so this is meant for one day's tasks.
        Python's sort is stable, so tasks tied on both keep their input order. O(n log n).
        """
        return sorted(tasks, key=lambda t: (-t.priority, t.time.time()))

    def sort_by_priority_then_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (highest first), then by full start datetime.

        Unlike prioritize_tasks(), ties are broken by the real date and time, so it is safe
        for tasks spread over several days (an Oct 1 task beats an Oct 2 task of equal
        priority). Returns a new list; the input is not modified. Stable. O(n log n).
        """
        return sorted(tasks, key=lambda t: (-t.priority, t.time))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks chronologically by time of day.

        Compares only the clock time, not the date, so tasks from different days interleave
        (Oct 2 08:00 sorts before Oct 1 14:00). Use it on a single day's tasks. Returns a new
        list; the input is not modified. O(n log n).
        """
        return sorted(tasks, key=lambda t: t.time.time())

    def detect_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Return tasks that overlap or clash with each other (across any pets).

        Algorithm: sort by full start datetime, then for each task scan forward only while the
        next task starts before it ends; the scan stops at the first task that starts at or after
        the end, since later tasks start even later. Tasks that merely touch (one ends exactly when
        the next starts) are not conflicts. Roughly O(n log n) plus the number of overlapping pairs.

        Returns:
            Each conflicting task once, in start-time order. Empty if there are none.
        """
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
        """Conflicts among the owner's tasks on one day, comparing across all pets.

        Recurring tasks are placed on `day` (using temporary copies at that day's time) so a daily
        task from a past start date is compared at the right time, then detect_conflicts() runs on
        them. Completed tasks are skipped. The original task objects are returned, not the copies.
        """
        todays = [
            Task(
                name=t.name, time=t.time_on(day), priority=t.priority,
                duration_minutes=t.duration_minutes, id=t.id, pet=t.pet,
            )
            for t in owner.get_all_tasks() if t.occurs_on(day) and not t.completed
        ]
        clashing = {t.id for t in self.detect_conflicts(todays)}
        return [t for t in owner.get_all_tasks() if t.id in clashing]

    def find_next_available_slot(
        self,
        owner: Owner,
        duration_minutes: int,
        after: datetime,
        max_days: int = 14,
    ) -> datetime | None:
        """Earliest start at or after `after` where a task of this length fits without any clash.

        Algorithm: for each day from `after`'s date (up to `max_days` days), take the owner's
        availability windows (the whole day if none are set), and collect the pending tasks
        that occur that day as busy intervals sorted by start. Sweep each window with a cursor:
        if the gap before the next busy interval is big enough, the cursor is the answer;
        otherwise jump the cursor past that interval. Back-to-back placement is allowed
        (touching intervals don't clash). Roughly O(days * (n log n)) for n tasks.

        Returns:
            The start datetime, or None if nothing fits within `max_days` (or the duration is
            not positive).
        """
        if duration_minutes <= 0:
            return None
        need = timedelta(minutes=duration_minutes)
        tasks = [t for t in owner.get_all_tasks() if not t.completed]
        for offset in range(max_days):
            day = after.date() + timedelta(days=offset)
            if owner.schedule:
                windows = sorted(
                    (datetime.combine(day, s.start), datetime.combine(day, s.end))
                    for s in owner.schedule
                )
            else:
                midnight = datetime.combine(day, time.min)
                windows = [(midnight, midnight + timedelta(days=1))]
            busy = sorted(
                (t.time_on(day), t.time_on(day) + timedelta(minutes=t.duration_minutes))
                for t in tasks if t.occurs_on(day)
            )
            for w_start, w_end in windows:
                cursor = max(w_start, after)
                for b_start, b_end in busy:
                    if b_end <= cursor:
                        continue
                    if b_start - cursor >= need:
                        break
                    cursor = max(cursor, b_end)
                if cursor + need <= w_end:
                    return cursor
        return None

    # --- manage ---
    def complete_task(self, owner: Owner, task_id: str) -> Task | None:
        """Mark the task with this id complete, wherever it lives. None if not found.

        Completing a recurring task (daily/weekly/biweekly/monthly) also schedules its next
        occurrence; see Task.mark_complete().
        """
        for t in owner.get_all_tasks():
            if t.id == task_id:
                t.mark_complete()
                return t
        return None

    def conflict_warnings(self, owner: Owner, day: date) -> list[str]:
        """Human-readable warnings for tasks that overlap on one day (never raises).

        Covers the same pet or different pets, and says whether the tasks start at the
        exact same time or just overlap.

        Algorithm: the same sort-and-scan as detect_conflicts(), on pending tasks placed on `day`,
        but it reports one message per overlapping pair (three tasks at once give three warnings).
        Tasks that only touch (one ends when the next starts) are not reported. It returns
        messages instead of raising, so the caller decides whether to show, log or ignore them.

        Returns:
            Warning strings such as "Conflict (overlap, same pet): ...". Empty if none.
        """
        todays = sorted(
            (t for t in owner.get_all_tasks() if t.occurs_on(day) and not t.completed),
            key=lambda t: t.time_on(day),
        )
        warnings = []
        for i, a in enumerate(todays):
            a_start = a.time_on(day)
            a_end = a_start + timedelta(minutes=a.duration_minutes)
            for b in todays[i + 1:]:
                b_start = b.time_on(day)
                if b_start >= a_end:
                    break
                kind = "same start time" if b_start == a_start else "overlap"
                scope = "same pet" if a.pet is b.pet else "different pets"
                a_pet, b_pet = (t.pet.name if t.pet else "no pet" for t in (a, b))
                warnings.append(
                    f"Conflict ({kind}, {scope}): '{a.name}' ({a_pet}, {a.time:%H:%M}) "
                    f"and '{b.name}' ({b_pet}, {b.time:%H:%M})"
                )
        return warnings

    def explain_choice(self, task: Task, plan: list[Task] | None = None) -> str:
        """Explain why a task was placed where it was.

        Pass the plan from build_daily_schedule to explain its rank and any clashes;
        without it, only the task's own details are described.

        The explanation mirrors the real ordering rule in prioritize_tasks() (priority, then
        time), so what it says matches why the task landed where it did. Clashes are noted
        only when the task is in `plan`.
        """
        text = (f"'{task.name}' has {task.priority.name.lower()} priority, "
                f"is scheduled for {task.time:%H:%M} ({task.frequency.value})")
        if task.reason:
            text += f" because {task.reason}"
        text += "."
        if plan and any(t is task for t in plan):
            text += " " + self._explain_rank(task, plan)
            clashes = [t.name for t in plan if t is not task and self._overlaps(task, t)]
            if clashes:
                text += " It overlaps with " + ", ".join(f"'{n}'" for n in clashes) + "."
        return text

    @staticmethod
    def _explain_rank(task: Task, plan: list[Task]) -> str:
        """Why the task sits at its position in a plan ordered by priority, then time.

        The first task is explained by its priority (the highest of the day, or tied for top and
        earliest). Every other task is explained against the task just before it: either that
        task has higher priority, or the two tie on priority and that one starts earlier.
        Only the immediate neighbor is mentioned, to keep the sentence short.
        """
        i = next(k for k, t in enumerate(plan) if t is task)
        place = f"It is #{i + 1} of {len(plan)} today"
        if i == 0:
            if len(plan) == 1:
                return f"{place}: it's the only task."
            if plan[1].priority == task.priority:
                return f"{place}: it ties for top priority and starts earliest."
            return f"{place}: it has the highest priority of the day."
        prev = plan[i - 1]
        if prev.priority > task.priority:
            return f"{place}: '{prev.name}' comes first because it has higher priority ({prev.priority.name.lower()})."
        return f"{place}: it ties with '{prev.name}' on priority, and '{prev.name}' starts earlier."

    @staticmethod
    def _overlaps(a: Task, b: Task) -> bool:
        """Whether two tasks overlap by time of day (the date is ignored, as in a one-day plan).

        Standard interval test: a overlaps b when a starts before b ends and b starts before a
        ends. Touching intervals don't overlap. Tasks that run past midnight aren't handled.
        """
        day = date(2000, 1, 1)
        a_start, b_start = a.time_on(day), b.time_on(day)
        return a_start < b_start + timedelta(minutes=b.duration_minutes) and b_start < a_start + timedelta(minutes=a.duration_minutes)

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
        """Whether the task fits entirely inside one of the available time slots.

        True when some slot starts at or before the task's start and ends at or after its end
        (time of day only). A task that spans two adjacent slots does not fit either one.
        """
        start = task.time.time()
        end = task.end_time.time()
        return any(s.start <= start and end <= s.end for s in slots)
