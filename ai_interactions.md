# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**Files modified**

- `pawpal_system.py`: added `Scheduler.find_next_available_slot()`.
- `tests/test_pawpal.py`: added 4 tests for the new method.
- `ai_interactions.md`: this section.

**What task did you give the agent?**

"Add a third algorithmic capability (like 'next available slot', weighted prioritization, etc.) that goes beyond the basic requirements." The first two capabilities were sorting/filtering and conflict detection. The agent chose which feature to build.

**What did the agent do?**

1. Read `pawpal_system.py` and searched the project for existing classes and tests, so the change would fit the current design.
2. Chose "next available slot" because it reuses existing pieces: `Owner.schedule` availability windows, `Task.occurs_on`/`time_on`, and the touching-is-not-a-conflict rule.
3. Added `Scheduler.find_next_available_slot(owner, duration_minutes, after, max_days=14)`. For each day it builds the availability windows (the whole day if none are set) and the sorted busy intervals from pending tasks, including recurring ones. A cursor sweeps each window and returns the first gap that fits, otherwise it moves to the next day. It returns `None` if nothing fits within `max_days` or the duration is not positive.
4. Appended 4 tests: back-to-back placement, gap too small versus big enough, availability windows rolling to the next day, and completed tasks plus the `None` cases.
5. Ran `python -m pytest`: 34 passed.

**What did you have to verify or fix manually?**

- **Agent's own test bug:** the first test run had 1 failure. My "nothing fits" case used 600 minutes, which fits in a 24-hour day, so the method was right and the test was wrong. I changed it to 1500 minutes and all tests passed.
- **Manual review still to do:** I (the user) have not yet reviewed the algorithm or run the app by hand. Items to check: the method is not wired into `app.py`, so it is not visible in the UI. Tasks that run past midnight are not handled, as with `_overlaps`. `after` is treated as a naive datetime like every other time in the project.
- **Other uncommitted changes:** `README.md`, `app.py`, `reflection.md` and the diagrams were already modified before this session and were not touched by this task.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
