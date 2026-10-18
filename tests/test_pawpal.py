from datetime import datetime

from pawpal_system import Pet, Priority, Task


def make_task() -> Task:
    return Task(name="Morning walk", time=datetime(2026, 10, 1, 8, 0), priority=Priority.HIGH)


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", breed="Golden Retriever", age=5)
    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1
