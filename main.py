#Testing area
from datetime import datetime, date, time
#Import classes from pawpal_system.py
from pawpal_system import Pet, Owner, Task, TimeSlot, Reminder, Priority, Scheduler

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


#Adds tasks with different times to each pet
task1 = Task(name="Feed Buddy", time=datetime(2026, 10, 1, 8, 0), priority=Priority.HIGH, duration_minutes=60)
task2 = Task(name="Walk Max", time=datetime(2026, 10, 1, 10, 0), priority=Priority.MEDIUM, duration_minutes=60)
task3 = Task(name="Vet Appointment for Joe", time=datetime(2026, 10, 1, 14, 0), priority=Priority.HIGHEST, duration_minutes=60)
task4 = Task(name="Playtime with Buddy", time=datetime(2026, 10, 2, 16, 0), priority=Priority.LOW, duration_minutes=60)
task5 = Task(name="Grooming for Max", time=datetime(2026, 10, 2, 12, 0), priority=Priority.MEDIUM, duration_minutes=60)

#Attach each task to its pet
buddy.add_task(task1)
max.add_task(task2)
joe.add_task(task3)
buddy.add_task(task4)
max.add_task(task5)

#Owner is available 8:00-17:00
owner.schedule.append(TimeSlot(start=time(8, 0), end=time(17, 0)))

#Display the tasks for each day, in time order
scheduler = Scheduler()
for day in (date(2026, 10, 1), date(2026, 10, 2)):
    print(f"\nTasks for {day:%B %d, %Y}:")
    for task in scheduler.sort_by_time(owner.get_daily_tasks(day)):
        print(f"- {task.name} from {task.time:%H:%M} to {task.end_time:%H:%M} for {task.pet.name} (priority: {task.priority.name})")
