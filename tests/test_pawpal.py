from datetime import date

from pawpal_system import Pet, Species, Task


def test_mark_complete_changes_task_status():
    task = Task("Walk", 30)
    today = date(2025, 1, 6)
    assert not task.is_complete(today)

    task.mark_complete(today)

    assert task.is_complete(today)


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species=Species.DOG)
    assert len(pet.tasks) == 0

    pet.add_task(Task("Walk", 30))

    assert len(pet.tasks) == 1
