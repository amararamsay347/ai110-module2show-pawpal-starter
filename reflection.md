# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

  The initial UML had options to add a pet, see daily tasks, and schedule and set reminders for walks, etc.

- What classes did you include, and what responsibilities did you assign to each?

  - **Owner:** name, age, schedule, preferences, and pet(s).
  - **Pet:** name, breed, age, preferences, and owner(s).
  - **Task:** name, time, priority, and reason.
  - **Scheduler:** time, priority, and reason.
  - **Reminder/Notification:** time and priority.

**b. Design changes**

- Did your design change during implementation?

  Yes. The design changed so that each class had more responsibilities.

- If yes, describe at least one change and why you made it.

  The class responsibilities changed as follows:

  - **Owner:** name, age, availability schedule, preferences, and pets. Adds and removes pets and gets the day's tasks.
  - **Pet:** name, breed, age, preferences, owners, and its care tasks. Adds and removes tasks.
  - **Task:** name, time, priority, reason, and completed status. Can be completed or rescheduled.
  - **Scheduler:** builds the daily plan from the owner's pets' tasks. Prioritizes, detects conflicts, explains choices, and creates reminders.
  - **Reminder:** time, priority, message, and the Task it refers to. Can be sent or snoozed.

  Other changes:

  - **Task → Pet link:** `Task.pet` points back to its pet. It is hidden from printing and comparison to avoid recursion.
  - **Priority:** a new `Priority` enum runs from 1 (lowest) to 5 (highest). `Task` and `Reminder` both use it.
  - **Unique id:** each new `Task` gets an auto-generated UUID in `Task.id`.
  - **UML:** updated to show `Priority`, `Task.id`, `Task.pet` and the Task → Pet relationship.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

  The scheduler considers four constraints: priority, time of day, the owner's availability, and overlap. It keeps only pending tasks that occur on the chosen day, which takes recurrence into account. If the owner has availability slots (`TimeSlot`), it drops any task that doesn't fit entirely inside one. It then orders the rest by priority, highest first, with the earliest time of day breaking ties. Overlap is checked separately: `conflict_warnings` reports tasks that clash, for the same pet or different pets. The `preferences` fields on `Owner` and `Pet` exist, but nothing reads them yet.

- How did you decide which constraints mattered most?

  I put availability first because it is a hard limit. A task outside the owner's free time can't happen no matter how important it is, so it is removed before anything is ranked. Priority comes next because the scenario is about doing the most important care first, such as a vet visit before playtime. Time of day only breaks ties, so the plan stays predictable. Overlap is a warning and not a hard constraint, for the reasons in the tradeoff below.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

  My scheduler detects conflicts and returns a warning message instead of blocking the task or rearranging the schedule. `conflict_warnings` finds tasks that overlap, for the same pet or different pets, and reports them. It doesn't refuse to add the task, and it doesn't pick a new time automatically. Instead, the app shows a "Resolve conflicts" panel where the owner can move a clashing task or delete it. The check also compares time of day only and looks at one day at a time. It's a simple sort-and-scan, not a full optimizer.

- Why is that tradeoff reasonable for this scenario?

  The owner knows what is best for their pets, and two tasks at the same time might be fine if the owner can walk two dogs together, or if one task is quick. A hard block would stop real plans, and auto-rescheduling could move something like a vet appointment without asking. A warning gives the owner the information and leaves the decision to them. It's also cheap and can't crash the app: a sorted scan that returns a list of strings, which Streamlit shows in a red `st.error` box. For a pet owner with a handful of tasks a day, that's enough, and it's easy to test and explain.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

  I used AI tools (Claude) to improve my brainstorming and for debugging.

- What kinds of prompts or questions were most helpful?

  The prompts and questions were most helpful when they were extremely direct and to the point.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

  I did not accept the AI's suggestions as-is for the classes and the first UML script. For the classes, I made sure each one made sense and had what it needed to flow properly. The AI did an okay job, but some classes did not make sense and did not flow properly. The first UML was also basic and did not allow for a proper, logical flow. For instance, the first UML gave the `Scheduler` its own `List~Task~ tasks` attribute. I rejected that because it would create a second copy of the tasks that could fall out of sync with each pet's list. I removed it, so the `Scheduler` holds no data and reads every task through `Owner.get_all_tasks()`. That keeps one source of truth and lets it plan across all pets.

  I made similar fixes to the other classes: I added `Task.pet` (so warnings can name the pet), `duration_minutes` (so overlaps can be detected), `Task.id`, a `Priority` enum in place of a bare `int`, and the missing `TimeSlot` class.

- How did you evaluate or verify what the AI suggested?

  I verified the AI's suggestions by cross-referencing them with my original brainstorming ideas. For the UML, I made sure it made sense from a human perspective, since AI cannot think like a human. For the classes, I made sure each one was linked, e.g. owners, pets and tasks.

**c. AI strategy**

- Which AI coding assistant features were most effective for building your scheduler?

  I used Claude's manual feature and I used to improve on the brainstorming to give me addititonal ideas. Claude also helped with inline edits, tagging files with @, producing and running tests, generating docstrings and polishing my explainations in the README and reflection. 

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.

  The first UML gave the `Scheduler` its own `List~Task~ tasks` attribute. I rejected that because it would create a second copy of the tasks that could fall out of sync with each pet's list. I removed it, so the `Scheduler` holds no data and reads every task through `Owner.get_all_tasks()`. That keeps one source of truth and lets it plan across all pets.

- How did using separate chat sessions for different phases help you stay organized?

  Separate sessions for the UML, logic, Streamlit, and tests helped to keep all aspects separate entites and keep them focused instead of using the logic in the UML, the AI would have probably halucinated and produced strange outputs.  

- What did you learn about being the "lead architect" when collaborating with powerful AI tools?

  The AI writes code quickly, but it doesn't own the design, so I had to. I decided what each class was responsible for, checked every suggestion against the UML, and rejected changes that broke the structure, like a second copy of the task list. I also told the AI exactly what I wanted, because direct, specific prompts gave the best results. The tests were my check on whether the AI's code did what the design said it should.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

  Claude wrote 30 automated tests in `tests/test_pawpal.py`. They cover:

  - **Sorting:** by time, including out-of-order input, identical times, empty and single-task lists, and leaving the original list unchanged.
  - **Filtering:** by pet name and completion status, and combining filters.
  - **Recurrence:** completing a daily, weekly, biweekly or monthly task creates the next occurrence. Monthly tasks clamp to short months, and daily tasks roll over the year end. Completing a task twice doesn't duplicate it, and a recurring task with no pet doesn't crash.
  - **Conflicts:** same-start and overlapping tasks are flagged across pets and within one pet. Back-to-back tasks and completed tasks are not.
  - **Plan explanations:** with and without a plan, including overlap mentions.
  - **Empty cases:** a pet with no tasks, an owner with no pets, and an unknown task id.

- Why were these tests important?

  The scheduler is mostly date and time logic, where bugs hide at the edges: month ends, year ends, tasks that touch but don't overlap, and recurring tasks that could multiply. A wrong plan for someone's pet is a real cost, so I tested those cases and not only the normal path. Tests also let me change the scheduler (e.g when I added filtering and the conflict warnings) and see right away whether something broke.

**b. Confidence**

- How confident are you that your scheduler works correctly?

  I am mostly confident, about 4 out of 5, in the logic layer: all 30 tests pass and they cover the main behaviors and several edge cases. 

- What edge cases would you test next if you had more time?

  - Tasks that run past midnight, which the overlap checks don't handle.
  - Sorting and overlap across different dates, since they currently compare time of day only.
  - Availability slots: a task that spans two adjacent slots, and an owner with several slots.
  - The resolve-conflicts panel: rescheduling a recurring task, deleting a task that is part of a series, and moving a task onto another clash.
  - Daylight saving time changes and time zones.
  - Monthly drift, such as Jan 31 → Feb 28 → Mar 28.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

  I'm most satisfied with how the logic layer and the UI fit together. The `Scheduler` is stateless and reads everything through `Owner.get_all_tasks()`, so the Streamlit app, the CLI demo and the tests all use the same code. Adding filtering, conflict warnings, recurrence and the resolve-conflicts panel didn't require restructuring any classes. I'm also happy that the conflict warnings are clear: they name both tasks, say whether the clash is a same-start or an overlap, and show in red.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

  - Make sorting and conflict checks date-aware and handle tasks that run past midnight.
  - Suggest the next free time slot when there is a conflict, instead of leaving the owner to pick one.
  - Add a proper edit form for existing tasks. At the moment tasks can only be rescheduled or deleted from the conflict panel.
  - Save pets and tasks to a file or database. Everything is stored in `st.session_state`, so it disappears when the session ends.
  - Use the `preferences` fields or remove them, and add automated tests for the Streamlit UI.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

  Design the structure first, then use AI to build on it. Having a UML and clear class responsibilities let me check each AI suggestion against a plan, and the first UML and some of the class designs didn't hold up when I checked them. AI was fast at writing code, but it needed direct instructions and my review, and it didn't think about how a pet owner would actually use the app. The tests were what showed me the code worked.
