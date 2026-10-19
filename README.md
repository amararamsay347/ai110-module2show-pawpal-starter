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

I built the PawPal+ logic layer in `pawpal_system.py`. It models a pet owner, their pets and the care tasks for each pet, then turns those tasks into an ordered daily plan. An `Owner` manages several `Pet`s, and each `Pet` holds its own list of `Task`s. A task records what needs to be done, when, how often (once, daily or weekly), its priority and whether it is done.

The `Scheduler` ties it together. It reads every task through `Owner.get_all_tasks()`, it plans across all of an owner's pets at once rather than one pet at a time. From there it builds the day's plan within the owner's available time, orders tasks by priority and then time, and flags tasks that overlap, even when they belong to different pets. It can also mark a task complete and explain why a task was placed where it was. `Reminder` is an optional add-on that the scheduler can create for a task, and nothing else depends on it.

`main.py` is a CLI demo with one owner, three pets and five tasks, and `tests/test_pawpal.py` covers task completion and adding a task to a pet. The class diagram is in `diagrams/updated_uml.mmd`.

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
- Sorting: tasks come back in chronological order, including edge cases like "10:00" after "09:00", empty listsRecurrence: completing a daily, weekly, biweekly or monthly task creates the next
  occurrence on the right darrect year-end andshort-month rollover.
- Conflict detection: tasks ng are flagged across pets,while back-to-back tasks and completed tasks are not.
- Empty cases: a pet with nots gives empty results and
  doesn't crash.                                                                     
The rest cover filtering, adding and completing tasks, and the explanations of why a task was placed where it was. 

Sample test output:

```
===================================================================== test session starts =====================================================================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\amara\OneDrive\CodePath AI110\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 30 items                                                                                                                                             

tests\test_pawpal.py ..............................                                                                                                      [100%]

===================================================================== 30 passed in 0.08s ======================================================================

Confidence Level: 5 Stars
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting |scheduler.sort_by_time, scheduler.prioritize_tasks | sorts by priority, duration |
| Filtering |scheduler.filter_tasks, scheduler.get_tasks, owner.get_daily_tasks  | filters by pet name, competion status, and day |
| Conflict handling |scheduler.conflict_warnings, scheduler.detect_conflicts, scheduler.find_daily_conflicts, scheduler._overlaps | overlapping time slots |
| Recurring tasks |Frequency, task.occurs_on, task.mark_complete,  | daily, weekly, bi-weekly, monthly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
