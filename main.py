#Testing area
from datetime import datetime, date, time
#Import classes from pawpal_system.py
from pawpal_system import Pet, Owner, Task, TimeSlot, Priority, Frequency, Scheduler
from display import color, conflict_banner, conflicting_ids, tasks_table

owner = Owner(name="Alice", age=30)
buddy = Pet(name="Buddy", breed="Golden Retriever", age=5)
max = Pet(name="Max", breed="Labrador", age=3)
joe = Pet(name="Joe", breed="Beagle", age=4)

owner.add_pet(buddy)
owner.add_pet(max)
owner.add_pet(joe)

#Test output to verify the owner and pets have been added correctly
print(f"Owner: {owner.name}, Age: {owner.age}")
for pet in owner.pets:
    print(f"Pet: {pet.name}, Breed: {pet.breed}, Age: {pet.age}")

#Owner is available 8:00-17:00
owner.schedule.append(TimeSlot(start=time(8, 0), end=time(17, 0)))

#Tasks are added deliberately OUT OF ORDER (not sorted by time)
day = date(2026, 10, 1)
buddy.add_task(Task(name="Evening walk", time=datetime(2026, 10, 1, 16, 0), priority=Priority.MEDIUM, duration_minutes=30))
max.add_task(Task(name="Vet appointment", time=datetime(2026, 10, 1, 14, 0), priority=Priority.HIGHEST, duration_minutes=60))
joe.add_task(Task(name="Medication", time=datetime(2026, 10, 1, 9, 0), priority=Priority.HIGH, duration_minutes=15))
buddy.add_task(Task(name="Breakfast", time=datetime(2026, 10, 1, 8, 0), priority=Priority.HIGH, duration_minutes=30, frequency=Frequency.DAILY))
max.add_task(Task(name="Grooming", time=datetime(2026, 10, 1, 14, 30), priority=Priority.LOW, duration_minutes=45))  # overlaps vet
#Two tasks at exactly the same time (11:00): one for the same pet as Playtime, one for a different pet
joe.add_task(Task(name="Training session", time=datetime(2026, 10, 1, 11, 0), priority=Priority.MEDIUM, duration_minutes=30))
buddy.add_task(Task(name="Brushing", time=datetime(2026, 10, 1, 11, 0), priority=Priority.LOW, duration_minutes=30))
joe.add_task(Task(name="Playtime", time=datetime(2026, 10, 1, 11, 0), priority=Priority.LOW, duration_minutes=30))

scheduler = Scheduler()


def show(title, tasks):
    print(f"\n{color(title, 'cyan', bold=True)}")
    print(tasks_table(tasks, conflicting_ids(scheduler, tasks)))


all_tasks = owner.get_all_tasks()
show("Unsorted (grouped by pet, not by time):", all_tasks)
show("Sorted by time:", scheduler.sort_by_time(all_tasks))

#Mark a couple of tasks complete so the status filter has something to show
by_name = {t.name: t for t in all_tasks}
scheduler.complete_task(owner, by_name["Medication"].id)  # one-off
scheduler.complete_task(owner, by_name["Breakfast"].id)   # daily -> creates tomorrow's

show("Filter: pending only, sorted by time:", scheduler.sort_by_time(scheduler.get_tasks(owner, completed=False)))
show("Filter: completed only:", scheduler.filter_tasks(owner.get_all_tasks(), completed=True))
show("Filter: Max's tasks, sorted by time:", scheduler.sort_by_time(scheduler.get_tasks(owner, pet="max")))
show("Filter: Buddy's pending tasks, sorted by time:",
     scheduler.sort_by_time(scheduler.get_tasks(owner, pet=buddy, completed=False)))

print("\nRecurring: completing daily 'Breakfast' created a new task:")
for t in buddy.tasks:
    if t.name == "Breakfast":
        print(f"  {t.time:%b %d %H:%M} ({t.frequency.value}) completed={t.completed}")

print(f"\n{color(f'Conflict check for {day:%B %d}', 'cyan', bold=True)}")
print(conflict_banner(scheduler.conflict_warnings(owner, day)))

# --- Enhanced scheduling: priority ordering, daily plan, next free slot ---
all_tasks = owner.get_all_tasks()
show("Priority, then time (highest priority first):", scheduler.sort_by_priority_then_time(all_tasks))

plan = scheduler.build_daily_schedule(owner, day)
print(f"\n{color(f'Daily plan for {day:%B %d} (inside 08:00-17:00 availability):', 'cyan', bold=True)}")
for rank, t in enumerate(plan, 1):
    print(f"  {rank}. {t.time:%H:%M} {t.name} ({t.pet.name}) - {scheduler.explain_choice(t, plan)}")
dropped = [t for t in all_tasks if t.occurs_on(day) and not t.completed and t not in plan]
for t in dropped:
    print(f"  (left out: {t.name} at {t.time:%H:%M}-{t.end_time:%H:%M}, outside availability)")

print(f"\n{color('Next available slot:', 'cyan', bold=True)}")
asking_at = datetime(2026, 10, 1, 11, 0)
for minutes in (30, 120, 180):
    slot = scheduler.find_next_available_slot(owner, minutes, asking_at)
    print(f"  {minutes:>3} min, asking at {asking_at:%b %d %H:%M} -> {slot:%b %d %H:%M}" if slot else f"  {minutes} min -> none found")
