#Testing area
from datetime import datetime, date, time
#Import classes from pawpal_system.py
from pawpal_system import Pet, Owner, Task, TimeSlot, Priority, Frequency, Scheduler

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
    print(f"\n{title}")
    if not tasks:
        print("  (none)")
    for t in tasks:
        status = "done" if t.completed else "pending"
        print(f"  {t.time:%H:%M}-{t.end_time:%H:%M}  {t.name:<16} {t.pet.name:<6} {t.priority.name:<8} {status}")


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

print("\nConflict warnings for", f"{day:%B %d}:")
for warning in scheduler.conflict_warnings(owner, day) or ["  (none)"]:
    print(" ", warning)
