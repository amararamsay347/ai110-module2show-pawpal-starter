# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation Summary

I built the PawPal+ logic layer in `pawpal_system.py`. It models a pet owner, their pets and the care tasks for each pet, then turns those tasks into an ordered daily plan. An `Owner` manages several `Pet`s, and each `Pet` holds its own list of `Task`s. A task records what needs to be done, when, how often (once, daily, weekly, biweekly or monthly), its priority and whether it is done.

The `Scheduler` ties it together. It reads every task through `Owner.get_all_tasks()`, it plans across all of an owner's pets at once rather than one pet at a time. From there it builds the day's plan within the owner's available time, orders tasks by priority and then time, and flags tasks that overlap, even when they belong to different pets. It can also mark a task complete and explain why a task was placed where it was. `Reminder` is an optional add-on that the scheduler can create for a task, and nothing else depends on it.

`app.py` is the Streamlit front end. It holds one `Owner` and one `Scheduler` in `st.session_state`, and uses the Scheduler to sort and filter the task table, show red conflict warnings, let the user resolve a conflict by moving or deleting a task, and build the daily plan with explanations.

`main.py` is a CLI demo with one owner, three pets and eight tasks, and `tests/test_pawpal.py` holds the 38 automated tests described below. The class diagram is in `diagrams/uml_final.mmd`.

## Features

- **Multi-pet management:** An owner can have several pets, and each pet has its own tasks. `Owner.get_all_tasks()` collects every task, so the Scheduler works across all pets. `add_pet` and `add_task` keep both sides of each link in sync.
- **Sorting by time:** `sort_by_time` orders tasks by clock time using Python's `sorted` (O(n log n)), and returns a new list. It compares time of day only, not the date, so tasks from different days interleave.
- **Priority-based daily plan:** `build_daily_schedule` keeps the pending tasks that occur on the chosen day and orders them with `prioritize_tasks`. That means highest priority first, then earliest time of day. The result is in priority order, not chronological order.
- **Filtering:** `filter_tasks` filters by completion status and/or pet (a `Pet` object or a case-insensitive name). A filter left as `None` is ignored, so filters combine freely. The input list is not changed.
- **Conflict warnings:** `conflict_warnings` sorts the day's pending tasks by start time and scans forward from each task only while the next one starts before it ends. It returns one readable message per overlapping pair. Each message says whether the tasks start at the same time or just overlap, and whether they belong to the same pet or different pets. Tasks that only touch are not conflicts. The function returns strings and never raises, so the UI decides how to show them. In the app they appear in a red alert box.
- **Conflict resolution:** When a warning appears, a "Resolve conflicts" panel lists the clashing tasks (found with `find_daily_conflicts`). Each one can be moved to a new date and time with `Task.reschedule`, or deleted with `Pet.remove_task`. The warning clears once the overlap is gone.
- **Recurring tasks:** Frequencies are once, daily, weekly, biweekly and monthly. `occurs_on` projects a task forward from its start date, never before it. Weekly means the same weekday, and biweekly means every 14 days. Monthly means the same day of the month, using the last day when the month is shorter. Completing a recurring task creates the next occurrence on the same pet (+1, +7 or +14 days, or one calendar month). The finished task becomes a one-off, so each series has exactly one pending task.
- **Availability windows:** If the owner has `TimeSlot`s, a task is dropped from the plan unless it fits entirely inside one slot.
- **Plan explanations:** `explain_choice` says where a task ranks in the day's plan and why, by comparing it with the task just before it. It also lists any tasks it overlaps with.
- **Optional reminders:** `create_reminder` builds a `Reminder` that can be sent or snoozed. The UI doesn't use it.
- **Friendly terminal output:** `display.py` renders tasks as bordered tables with `tabulate`, adds an emoji for the kind of task, and color-codes status and priority. See [Display Features](#-display-features).
- **Streamlit UI:** Add pets and tasks through forms. Filter by pet and status. See a time-sorted table with summary metrics, complete tasks with a button, and generate a daily plan with explanations.

### Limitations

- Sorting and the overlap checks ignore the date, and tasks that run past midnight aren't handled.
- Three tasks at the same time produce three warnings, because each pair is reported.
- Monthly recurrence can drift: Jan 31 → Feb 28 → Mar 28.
- The UI's Complete button calls `Task.mark_complete()` directly, not `Scheduler.complete_task`.

## Data Persistence

Pets and tasks are saved to `data.json` so they are still there the next time you run the app.

### How it works

1. **Startup:** `app.py` calls `Owner.load_from_json("data.json")` once per session. If the file exists, the owner, availability slots, pets and tasks are rebuilt from it. If it is missing or corrupt, the method returns `None` and the app starts with a fresh owner instead of crashing.
2. **Saving:** After each change (renaming the owner, adding a pet, adding a task, completing a task, rescheduling or deleting a task) the app calls `owner.save_to_json("data.json")`. Streamlit reruns the whole script on every click, so saving right after each change means nothing is lost if you close the tab.
3. **Safe writes:** `save_to_json` writes to `data.json.tmp` and then swaps it in with `os.replace`, so a crash mid-save can't leave a half-written `data.json`.
4. **Round trip:** Each class has `to_dict()` and `from_dict()` (`TimeSlot`, `Task`, `Pet`, `Owner`). Tasks are stored inside their pet, and pets inside the owner, so the task-to-pet links are rebuilt on load with `Pet.add_task`. Task ids, completed flags, priorities (saved as numbers), repeat frequency and datetimes (saved as ISO strings) all come back unchanged.

The file is created in the folder you start `streamlit run app.py` from. Delete it to reset the app. It is listed in `.gitignore`, since it holds personal data.

### Files modified

| File | Change |
|------|--------|
| `pawpal_system.py` | Added `to_dict`/`from_dict` on `TimeSlot`, `Task`, `Pet` and `Owner`, plus `Owner.save_to_json` and `Owner.load_from_json`. Added `json` and `os` imports. |
| `app.py` | Loads `data.json` at startup and saves after each change. Added the `DATA_FILE` constant. |
| `tests/test_pawpal.py` | Added a save-and-reload round-trip test and a test that missing or corrupt files return `None`. |
| `.gitignore` | Added `data.json` and `data.json.tmp`. |
| `README.md` | This section. |

`main.py` (the CLI demo) is unchanged and does not save or load.

### Persistence limitations

- Only one owner is stored, in one file. The file is rewritten in full on every save.
- `preferences` dictionaries must contain JSON-friendly values (strings, numbers, lists, dicts).
- A pet shared by two owners would be saved under only the owner being saved.

## 🎨 Display Features

`display.py` holds the terminal output helpers. `main.py` uses them for its tables and conflict banner, and `app.py` borrows `task_emoji` for its task table.

| Feature | What it does |
|---------|--------------|
| **Tables** | `tasks_table(tasks, conflicting_ids)` prints a rounded-grid table with emoji, task, pet, time range, priority, repeats and status columns. An empty list prints `(no tasks)`. |
| **Status colors** | ✅ Done is green, ⏳ Pending is yellow, and ⚠️ Conflict is bold red. Conflict status comes from `Scheduler.detect_conflicts`, so clashing tasks are red in every table. |
| **Priority colors** | Lowest and low are green, medium is yellow, high is magenta, highest is red. |
| **Task emojis** | Tasks have no type field, so `task_emoji` guesses from the name: 🦮 walk, 🍖 feeding, 🏥 vet, 💊 medication, 🛁 grooming or brushing, 🎾 play, 🎓 training, 💧 water, 🐾 anything else. The first matching keyword wins. Edit `TASK_EMOJIS` to add more. |
| **Conflict banner** | `conflict_banner(warnings)` shows a red "🚨 N scheduling conflict(s)" list, or a green all-clear message. |

Colors are switched off automatically when output is piped to a file or when the `NO_COLOR` environment variable is set. On Windows, `colorama` enables them in older consoles.

**Dependencies:** `tabulate`, `wcwidth` (keeps emoji columns aligned) and, on Windows, `colorama`. All are in `requirements.txt`, so `pip install -r requirements.txt` covers them.

**Files changed:** `display.py` (new), `main.py` (tables and banner), `app.py` (emoji in the task table), `requirements.txt`, and `tests/test_pawpal.py` (2 display tests).

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Owner: Alice, Age: 30
Pet: Buddy, Breed: Golden Retriever, Age: 5
Pet: Max, Breed: Labrador, Age: 3
Pet: Joe, Breed: Beagle, Age: 4

Tasks for October 01, 2026:
- Feed Buddy from 08:00 to 09:00 for Buddy (priority: HIGH)
- Walk Max from 10:00 to 11:00 for Max (priority: MEDIUM)
- Vet Appointment for Joe from 14:00 to 15:00 for Joe (priority: HIGHEST)

Tasks for October 02, 2026:
- Grooming for Max from 12:00 to 13:00 for Max (priority: MEDIUM)
- Playtime with Buddy from 16:00 to 17:00 for Buddy (priority: LOW)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
pytest --cov
```
### What the tests cover:
- **Sorting:** tasks come back in chronological order, including edge cases like "10:00" after "09:00", empty and single-task lists, and identical times.
- **Recurrence:** completing a daily, weekly, biweekly or monthly task creates the next occurrence on the right date, including year-end and short-month rollover.
- **Conflict detection:** tasks that overlap or start together are flagged across pets, while back-to-back tasks and completed tasks are not.
- **Empty cases:** a pet with no tasks, or an owner with no pets, gives empty results and doesn't crash.

The rest cover filtering, adding and completing tasks, and the explanations of why a task was placed where it was.

Sample test output:

```
===================================================================== test session starts =====================================================================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\amara\OneDrive\CodePath AI110\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 38 items                                                                                                                                             

tests\test_pawpal.py ..............................                                                                                                      [100%]

===================================================================== 38 passed in 0.10s ======================================================================

Confidence Level: 5 Stars
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `scheduler.sort_by_time`, `scheduler.prioritize_tasks` | `sort_by_time` orders by clock time; `prioritize_tasks` orders by priority, then time of day |
| Filtering | `scheduler.filter_tasks`, `scheduler.get_tasks`, `owner.get_daily_tasks` | filters by pet name, completion status, and day |
| Conflict handling | `scheduler.conflict_warnings`, `scheduler.detect_conflicts`, `scheduler.find_daily_conflicts`, `scheduler._overlaps` | overlapping time slots; `conflict_warnings` gives the red alert text |
| Conflict resolution | `scheduler.find_daily_conflicts`, `task.reschedule`, `pet.remove_task` | UI panel to move or delete a clashing task |
| Recurring tasks | `Frequency`, `task.occurs_on`, `task.mark_complete` | once, daily, weekly, biweekly, monthly |

## 📸 Demo Walkthrough

### Main UI features

Run the app with `streamlit run app.py`. From the page you can:

- **Set the owner name.**
- **Add pets** (name, breed, age). A table lists each pet with its task count.
- **Add tasks** to a chosen pet: title, date, time, duration, priority and how often it repeats (once, daily, weekly, biweekly, monthly).
- **Filter the task list** by pet and by status (all, pending, completed).
- **Review the task table**, which is sorted by time and shows summary metrics for total, pending and completed tasks.
- **Resolve conflicts.** When tasks clash, move a task to a new date and time, or delete it.
- **Mark tasks complete.** A recurring task creates its next occurrence automatically.
- **Build a daily schedule** for any date and read why each task was placed where it was.

### Example workflow

1. **Add a pet.** Type a name such as "Buddy" in the Pets form and click **Add pet**. Buddy appears in the pets table with 0 tasks.
2. **Schedule a task.** In the Tasks form, pick Buddy, enter "Morning walk", choose a date, time and duration, set a priority and repeat frequency, then click **Add task**. The task shows up in the table, sorted by time, and the task count updates.
3. **Add a second task at an overlapping time**, for example a vet visit at the same start time. A red **⚠️ WARNING** box appears above the table naming both tasks. When there is no clash, a green "No scheduling conflicts" message shows instead.
4. **Resolve the conflict.** Open the **🛠️ Resolve conflicts** panel under the warning. For one of the clashing tasks, pick a new date and time and click **Reschedule**, or click **Delete** to remove it. The page refreshes with a confirmation, the red warning disappears, and the green "No scheduling conflicts" message returns.
5. **Filter the list.** Use "Filter by pet" and "Filter by status" to narrow the table, for example Buddy's pending tasks.
6. **Complete a task.** Click **Complete** next to a daily task. A message confirms it and gives the date of the next occurrence.
7. **View today's schedule.** Pick a date under **Build Schedule** and click **Generate schedule**. Tasks are listed in priority order with an explanation for each, followed by any conflict warnings for that day.

### Key Scheduler behaviors shown

- **Sorting by time:** the task table is ordered by clock time with `sort_by_time`.
- **Priority ordering:** the daily plan is ordered by `prioritize_tasks` (highest priority first, then earliest time), and `explain_choice` gives the reason for each task's position.
- **Filtering:** `filter_tasks` narrows tasks by pet and completion status.
- **Conflict warnings:** `conflict_warnings` reports overlapping or same-start tasks, within one pet or across pets, as red alerts.
- **Conflict resolution:** `find_daily_conflicts` finds the clashing tasks, and the UI fixes them with `Task.reschedule` or `Pet.remove_task`. The warning clears once the overlap is gone.
- **Recurring tasks:** completing a daily, weekly, biweekly or monthly task schedules the next occurrence.

### Sample CLI output

Running `python main.py` prints a demo with one owner, three pets and eight tasks. Output is shown as tables with emojis and color-coded status (colors appear in a real terminal, not in this copy):

```
Owner: Alice, Age: 30
Pet: Buddy, Breed: Golden Retriever, Age: 5
Pet: Max, Breed: Labrador, Age: 3
Pet: Joe, Breed: Beagle, Age: 4

Unsorted (grouped by pet, not by time):
╭────┬──────────────────┬───────┬────────────────────┬────────────┬───────────┬──────────────╮
│    │ Task             │ Pet   │ When               │ Priority   │ Repeats   │ Status       │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🦮 │ Evening walk     │ Buddy │ Oct 01 16:00-16:30 │ Medium     │ Once      │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🍖 │ Breakfast        │ Buddy │ Oct 01 08:00-08:30 │ High       │ Daily     │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Brushing         │ Buddy │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🏥 │ Vet appointment  │ Max   │ Oct 01 14:00-15:00 │ Highest    │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Grooming         │ Max   │ Oct 01 14:30-15:15 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 💊 │ Medication       │ Joe   │ Oct 01 09:00-09:15 │ High       │ Once      │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎓 │ Training session │ Joe   │ Oct 01 11:00-11:30 │ Medium     │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎾 │ Playtime         │ Joe   │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
╰────┴──────────────────┴───────┴────────────────────┴────────────┴───────────┴──────────────╯

Sorted by time:
╭────┬──────────────────┬───────┬────────────────────┬────────────┬───────────┬──────────────╮
│    │ Task             │ Pet   │ When               │ Priority   │ Repeats   │ Status       │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🍖 │ Breakfast        │ Buddy │ Oct 01 08:00-08:30 │ High       │ Daily     │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 💊 │ Medication       │ Joe   │ Oct 01 09:00-09:15 │ High       │ Once      │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Brushing         │ Buddy │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎓 │ Training session │ Joe   │ Oct 01 11:00-11:30 │ Medium     │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎾 │ Playtime         │ Joe   │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🏥 │ Vet appointment  │ Max   │ Oct 01 14:00-15:00 │ Highest    │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Grooming         │ Max   │ Oct 01 14:30-15:15 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🦮 │ Evening walk     │ Buddy │ Oct 01 16:00-16:30 │ Medium     │ Once      │ ⏳ Pending   │
╰────┴──────────────────┴───────┴────────────────────┴────────────┴───────────┴──────────────╯

Filter: pending only, sorted by time:
╭────┬──────────────────┬───────┬────────────────────┬────────────┬───────────┬──────────────╮
│    │ Task             │ Pet   │ When               │ Priority   │ Repeats   │ Status       │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🍖 │ Breakfast        │ Buddy │ Oct 02 08:00-08:30 │ High       │ Daily     │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Brushing         │ Buddy │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎓 │ Training session │ Joe   │ Oct 01 11:00-11:30 │ Medium     │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎾 │ Playtime         │ Joe   │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🏥 │ Vet appointment  │ Max   │ Oct 01 14:00-15:00 │ Highest    │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Grooming         │ Max   │ Oct 01 14:30-15:15 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🦮 │ Evening walk     │ Buddy │ Oct 01 16:00-16:30 │ Medium     │ Once      │ ⏳ Pending   │
╰────┴──────────────────┴───────┴────────────────────┴────────────┴───────────┴──────────────╯

Filter: completed only:
╭────┬────────────┬───────┬────────────────────┬────────────┬───────────┬──────────╮
│    │ Task       │ Pet   │ When               │ Priority   │ Repeats   │ Status   │
├────┼────────────┼───────┼────────────────────┼────────────┼───────────┼──────────┤
│ 🍖 │ Breakfast  │ Buddy │ Oct 01 08:00-08:30 │ High       │ Once      │ ✅ Done  │
├────┼────────────┼───────┼────────────────────┼────────────┼───────────┼──────────┤
│ 💊 │ Medication │ Joe   │ Oct 01 09:00-09:15 │ High       │ Once      │ ✅ Done  │
╰────┴────────────┴───────┴────────────────────┴────────────┴───────────┴──────────╯

Filter: Max's tasks, sorted by time:
╭────┬─────────────────┬───────┬────────────────────┬────────────┬───────────┬──────────────╮
│    │ Task            │ Pet   │ When               │ Priority   │ Repeats   │ Status       │
├────┼─────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🏥 │ Vet appointment │ Max   │ Oct 01 14:00-15:00 │ Highest    │ Once      │ ⚠️  Conflict │
├────┼─────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Grooming        │ Max   │ Oct 01 14:30-15:15 │ Low        │ Once      │ ⚠️  Conflict │
╰────┴─────────────────┴───────┴────────────────────┴────────────┴───────────┴──────────────╯

Filter: Buddy's pending tasks, sorted by time:
╭────┬──────────────┬───────┬────────────────────┬────────────┬───────────┬────────────╮
│    │ Task         │ Pet   │ When               │ Priority   │ Repeats   │ Status     │
├────┼──────────────┼───────┼────────────────────┼────────────┼───────────┼────────────┤
│ 🍖 │ Breakfast    │ Buddy │ Oct 02 08:00-08:30 │ High       │ Daily     │ ⏳ Pending │
├────┼──────────────┼───────┼────────────────────┼────────────┼───────────┼────────────┤
│ 🛁 │ Brushing     │ Buddy │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⏳ Pending │
├────┼──────────────┼───────┼────────────────────┼────────────┼───────────┼────────────┤
│ 🦮 │ Evening walk │ Buddy │ Oct 01 16:00-16:30 │ Medium     │ Once      │ ⏳ Pending │
╰────┴──────────────┴───────┴────────────────────┴────────────┴───────────┴────────────╯

Recurring: completing daily 'Breakfast' created a new task:
  Oct 01 08:00 (once) completed=True
  Oct 02 08:00 (daily) completed=False

Conflict check for October 01
🚨 4 scheduling conflict(s):
  • Conflict (same start time, different pets): 'Brushing' (Buddy, 11:00) and 'Training session' (Joe, 11:00)
  • Conflict (same start time, different pets): 'Brushing' (Buddy, 11:00) and 'Playtime' (Joe, 11:00)
  • Conflict (same start time, same pet): 'Training session' (Joe, 11:00) and 'Playtime' (Joe, 11:00)
  • Conflict (overlap, same pet): 'Vet appointment' (Max, 14:00) and 'Grooming' (Max, 14:30)

Priority, then time (highest priority first):
╭────┬──────────────────┬───────┬────────────────────┬────────────┬───────────┬──────────────╮
│    │ Task             │ Pet   │ When               │ Priority   │ Repeats   │ Status       │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🏥 │ Vet appointment  │ Max   │ Oct 01 14:00-15:00 │ Highest    │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🍖 │ Breakfast        │ Buddy │ Oct 01 08:00-08:30 │ High       │ Once      │ ✅ Done      │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 💊 │ Medication       │ Joe   │ Oct 01 09:00-09:15 │ High       │ Once      │ ✅ Done      │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🍖 │ Breakfast        │ Buddy │ Oct 02 08:00-08:30 │ High       │ Daily     │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎓 │ Training session │ Joe   │ Oct 01 11:00-11:30 │ Medium     │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🦮 │ Evening walk     │ Buddy │ Oct 01 16:00-16:30 │ Medium     │ Once      │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Brushing         │ Buddy │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎾 │ Playtime         │ Joe   │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Grooming         │ Max   │ Oct 01 14:30-15:15 │ Low        │ Once      │ ⚠️  Conflict │
╰────┴──────────────────┴───────┴────────────────────┴────────────┴───────────┴──────────────╯

Daily plan for October 01 (inside 08:00-17:00 availability):
  1. 14:00 Vet appointment (Max) - 'Vet appointment' has highest priority, is scheduled for 14:00 (once). It is #1 of 6 today: it has the highest priority of the day. It overlaps with 'Grooming'.
  2. 11:00 Training session (Joe) - 'Training session' has medium priority, is scheduled for 11:00 (once). It is #2 of 6 today: 'Vet appointment' comes first because it has higher priority (highest). It overlaps with 'Brushing', 'Playtime'.
  3. 16:00 Evening walk (Buddy) - 'Evening walk' has medium priority, is scheduled for 16:00 (once). It is #3 of 6 today: it ties with 'Training session' on priority, and 'Training session' starts earlier.
  4. 11:00 Brushing (Buddy) - 'Brushing' has low priority, is scheduled for 11:00 (once). It is #4 of 6 today: 'Evening walk' comes first because it has higher priority (medium). It overlaps with 'Training session', 'Playtime'.
  5. 11:00 Playtime (Joe) - 'Playtime' has low priority, is scheduled for 11:00 (once). It is #5 of 6 today: it ties with 'Brushing' on priority, and 'Brushing' starts earlier. It overlaps with 'Training session', 'Brushing'.
  6. 14:30 Grooming (Max) - 'Grooming' has low priority, is scheduled for 14:30 (once). It is #6 of 6 today: it ties with 'Playtime' on priority, and 'Playtime' starts earlier. It overlaps with 'Vet appointment'.

Next available slot:
   30 min, asking at Oct 01 11:00 -> Oct 01 11:30
  120 min, asking at Oct 01 11:00 -> Oct 01 11:30
  180 min, asking at Oct 01 11:00 -> Oct 02 08:30
```

### Enhanced scheduling output

The end of `python main.py` demonstrates the newer scheduling logic on the same eight tasks. The owner is available 08:00-17:00 and Oct 01 has overlapping tasks.

**1. Priority first, then time** (`sort_by_priority_then_time`). Highest priority comes first, and ties go to the earlier start. Both Breakfast tasks are High, so the Oct 01 one comes before the Oct 02 one even though the clock times match. The ⚠️ marks come from conflict detection.

```
Priority, then time (highest priority first):
╭────┬──────────────────┬───────┬────────────────────┬────────────┬───────────┬──────────────╮
│    │ Task             │ Pet   │ When               │ Priority   │ Repeats   │ Status       │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🏥 │ Vet appointment  │ Max   │ Oct 01 14:00-15:00 │ Highest    │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🍖 │ Breakfast        │ Buddy │ Oct 01 08:00-08:30 │ High       │ Once      │ ✅ Done      │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 💊 │ Medication       │ Joe   │ Oct 01 09:00-09:15 │ High       │ Once      │ ✅ Done      │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🍖 │ Breakfast        │ Buddy │ Oct 02 08:00-08:30 │ High       │ Daily     │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎓 │ Training session │ Joe   │ Oct 01 11:00-11:30 │ Medium     │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🦮 │ Evening walk     │ Buddy │ Oct 01 16:00-16:30 │ Medium     │ Once      │ ⏳ Pending   │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Brushing         │ Buddy │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🎾 │ Playtime         │ Joe   │ Oct 01 11:00-11:30 │ Low        │ Once      │ ⚠️  Conflict │
├────┼──────────────────┼───────┼────────────────────┼────────────┼───────────┼──────────────┤
│ 🛁 │ Grooming         │ Max   │ Oct 01 14:30-15:15 │ Low        │ Once      │ ⚠️  Conflict │
╰────┴──────────────────┴───────┴────────────────────┴────────────┴───────────┴──────────────╯
```

**2. Daily plan with explanations** (`build_daily_schedule` and `explain_choice`). Tasks are ranked by priority, then time, and each line says why it sits where it does and what it overlaps with. Breakfast and Medication are done, so they are not planned. The output below is shortened; the full run lists all 6 tasks.

```
Daily plan for October 01 (inside 08:00-17:00 availability):
  1. 14:00 Vet appointment (Max) - 'Vet appointment' has highest priority, is scheduled for 14:00 (once). It is #1 of 6 today: it has the highest priority of the day. It overlaps with 'Grooming'.
  2. 11:00 Training session (Joe) - 'Training session' has medium priority, is scheduled for 11:00 (once). It is #2 of 6 today: 'Vet appointment' comes first because it has higher priority (highest). It overlaps with 'Brushing', 'Playtime'.
  ...
  6. 14:30 Grooming (Max) - 'Grooming' has low priority, is scheduled for 14:30 (once). It is #6 of 6 today: it ties with 'Playtime' on priority, and 'Playtime' starts earlier. It overlaps with 'Vet appointment'.
```

**3. Next available slot** (`find_next_available_slot`). Asking at 11:00, a 30-minute task fits right after the 11:00 block ends. A 120-minute task fits in the gap before the 14:00 vet visit. A 180-minute task fits in no gap on Oct 01 (the 15:15-16:00 and 16:30-17:00 gaps are too short), so it rolls to Oct 02 at 08:30, just after the daily Breakfast.

```
Next available slot:
   30 min, asking at Oct 01 11:00 -> Oct 01 11:30
  120 min, asking at Oct 01 11:00 -> Oct 01 11:30
  180 min, asking at Oct 01 11:00 -> Oct 02 08:30
```


