# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The initial UML will have the options to add a pet, see daily tasks, schedule and set reminders for walks, etc.
- What classes did you include, and what responsibilities did you assign to each?

Owner has a name, age, schedule, preferences, and pet(s)
Pet has a name, breed, age, preferences, and owner(s)
Task has a name, time, priority, and reason 
Scheduler has a time, priority, and reason 
Reminder/Notification has a time and priority 


**b. Design changes**

- Did your design change during implementation?

Yes, the design was changed to implement more responsibilies for each class. 

- If yes, describe at least one change and why you made it.

Here are the changes:
- Owner: name, age, availability schedule, preferences, and pets. Adds/removes pets and gets the day's tasks.
- Pet: name, breed, age, preferences, owners, and its care tasks. Adds/removes tasks.
- Task: name, time, priority, reason, and completed status. Can be completed or rescheduled.
- Scheduler: builds the daily plan from the owner's pets' tasks. Prioritizes, detects conflicts, explains choices, and creates reminders.
- Reminder: time, priority, message, and the Task it refers to. Can be sent or snoozed.

- **Task → Pet link:** `Task.pet` points back to its pet. It is hidden from printing and comparison to avoid recursion.
- **Priority:** a new `Priority` enum runs from 1 (lowest) to 5 (highest). `Task` and `Reminder` both use it.
- **Unique id:** each new `Task` gets an auto-generated UUID in `Task.id`.
- **UML:** updated to show `Priority`, `Task.id`, `Task.pet` and the Task → Pet relationship.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used AI tools for improving on the brainstorming and debugging.
- What kinds of prompts or questions were most helpful?
The prompts and questions were most helpful when they were extremely direct and to the point. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
I did not accept AI suggestion as is for the classes, and the first uml script. For the classes, I made sure that each class made sense and had the requirements to flow properly. AI did an okay job with the classes but some did not make sense and did not flow properly. Also, the first uml was basic and did not allow for proper, logical flow. 
- How did you evaluate or verify what the AI suggested?
I verified what the AI suggested by cross referencing it with my original brainstorming ideas. For the UML, I ensured it made sense from the human perspective since AI cannot think like a human. ALso, for the classes, I ensured that each was linked, e.g owners, pets, tasks were linked.  

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
