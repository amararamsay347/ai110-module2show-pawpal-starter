"""User-friendly terminal output: color-coded status, task-type emojis, and tables."""
from __future__ import annotations

import os
import sys

from tabulate import tabulate

from pawpal_system import Priority, Scheduler, Task

try:  # makes ANSI colors work in older Windows consoles
    import colorama
    colorama.just_fix_windows_console()
except ImportError:
    pass

_COLOR_ON = sys.stdout.isatty() and "NO_COLOR" not in os.environ
_CODES = {"red": "31", "green": "32", "yellow": "33", "blue": "34", "magenta": "35", "cyan": "36", "gray": "90"}

# Task "type" is inferred from the name, since tasks don't have a type field.
# The first matching keyword wins, so order matters.
TASK_EMOJIS = [
    (("walk", "run", "jog"), "🦮"),
    (("feed", "breakfast", "dinner", "lunch", "meal", "treat"), "🍖"),
    (("vet", "appointment", "checkup", "vaccin"), "🏥"),
    (("med", "pill", "insulin"), "💊"),
    (("groom", "brush", "bath", "nail"), "🛁"),
    (("play", "fetch", "toy"), "🎾"),
    (("train", "learn", "trick"), "🎓"),
    (("water",), "💧"),
]
PRIORITY_COLORS = {
    Priority.LOWEST: "green", Priority.LOW: "green", Priority.MEDIUM: "yellow",
    Priority.HIGH: "magenta", Priority.HIGHEST: "red",
}


def color(text: str, name: str, bold: bool = False) -> str:
    """Wrap text in an ANSI color (a no-op when output isn't a terminal or NO_COLOR is set)."""
    if not _COLOR_ON:
        return text
    return f"\033[{'1;' if bold else ''}{_CODES[name]}m{text}\033[0m"


def task_emoji(task: Task) -> str:
    """Emoji for the kind of care this task is, guessed from its name (🐾 if unknown)."""
    name = task.name.lower()
    return next((e for words, e in TASK_EMOJIS if any(w in name for w in words)), "🐾")


def status_label(task: Task, conflicting: bool = False) -> str:
    """Colored status: done (green), conflict (red), or pending (yellow)."""
    if task.completed:
        return color("✅ Done", "green")
    if conflicting:
        return color("⚠️  Conflict", "red", bold=True)
    return color("⏳ Pending", "yellow")


def priority_label(task: Task) -> str:
    return color(task.priority.name.title(), PRIORITY_COLORS[task.priority])


def tasks_table(tasks: list[Task], conflicting_ids: set[str] | None = None, fmt: str = "rounded_grid") -> str:
    """A bordered table of tasks (see tabulate's formats for `fmt`)."""
    conflicting_ids = conflicting_ids or set()
    rows = [
        [
            task_emoji(t), t.name, t.pet.name if t.pet else "-",
            f"{t.time:%b %d %H:%M}-{t.end_time:%H:%M}", priority_label(t),
            t.frequency.value.title(), status_label(t, t.id in conflicting_ids),
        ]
        for t in tasks
    ]
    headers = ["", "Task", "Pet", "When", "Priority", "Repeats", "Status"]
    return tabulate(rows, headers=headers, tablefmt=fmt) if rows else color("(no tasks)", "gray")


def conflict_banner(warnings: list[str]) -> str:
    """Red heading plus one line per warning, or a green all-clear."""
    if not warnings:
        return color("✅ No scheduling conflicts.", "green")
    lines = [color(f"🚨 {len(warnings)} scheduling conflict(s):", "red", bold=True)]
    lines += [f"  {color('•', 'red')} {w}" for w in warnings]
    return "\n".join(lines)


def conflicting_ids(scheduler: Scheduler, tasks: list[Task]) -> set[str]:
    return {t.id for t in scheduler.detect_conflicts([t for t in tasks if not t.completed])}
