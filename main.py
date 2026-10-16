from datetime import date, time

from pawpal_system import (
    Category,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Species,
    Task,
    TaskStatus,
)


def show(heading: str, pairs: list[tuple[Pet, Task]]) -> None:
    print(f"\n{heading}")
    for pet, task in pairs:
        when = f"{task.fixed_time:%H:%M}" if task.fixed_time else "--:--"
        print(f"  {when}  {pet.name:<6} {task.title:<14} ({task.status(date.today()).value})")


def main() -> None:
    owner = Owner(name="Jordan", available_start=time(7, 0), available_end=time(21, 0))

    mochi = Pet(name="Mochi", species=Species.DOG)
    luna = Pet(name="Luna", species=Species.CAT)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of time order.
    luna.add_task(
        Task("Dinner", 10, priority=Priority.MEDIUM, category=Category.FEEDING, fixed_time=time(18, 0))
    )
    mochi.add_task(
        Task("Medication", 5, priority=Priority.HIGH, category=Category.MEDS, fixed_time=time(12, 30))
    )
    luna.add_task(Task("Brushing", 15, priority=Priority.LOW, category=Category.GROOMING))
    mochi.add_task(
        Task("Morning walk", 30, priority=Priority.HIGH, category=Category.WALK, fixed_time=time(8, 0))
    )
    mochi.add_task(Task("Play fetch", 20, priority=Priority.LOW, category=Category.ENRICHMENT))
    # Deliberate clash: both start at 18:00, one per pet, to show the conflict warning.
    mochi.add_task(
        Task("Vet call", 20, priority=Priority.HIGH, category=Category.OTHER, fixed_time=time(18, 0))
    )

    today = date.today()
    # Mark one task done so the status filter has something to separate.
    mochi.tasks[0].mark_complete(today)  # Medication

    all_pairs = owner.get_all_tasks()
    show("As added (out of order):", all_pairs)

    scheduler = Scheduler()
    ordered = scheduler.sort_by_time([task for _, task in all_pairs])
    pet_of = {task.id: pet for pet, task in all_pairs}
    show("Sorted by time (untimed last):", [(pet_of[t.id], t) for t in ordered])

    show("Filter: pet = Mochi", owner.filter_tasks(pet_name="Mochi", day=today))
    show("Filter: status = pending", owner.filter_tasks(status=TaskStatus.PENDING, day=today))
    show("Filter: status = done", owner.filter_tasks(status=TaskStatus.DONE, day=today))
    show(
        "Filter: Luna + pending",
        owner.filter_tasks(pet_name="luna", status=TaskStatus.PENDING, day=today),
    )

    plan = scheduler.build_plan(owner, today)

    print(f"\nToday's Schedule ({today:%A, %B %d}) for {owner.name}")
    print("-" * 52)
    for entry in plan.scheduled:
        print(
            f"{entry.start:%H:%M}-{entry.end:%H:%M}  {entry.pet.name:<6} "
            f"{entry.task.title:<14} [{entry.reason}]"
        )
    if plan.unscheduled:
        print("\nCould not schedule:")
        for entry in plan.unscheduled:
            print(f"  {entry.pet.name}: {entry.task.title} ({entry.reason})")
    if plan.conflicts:
        print("\nWarnings:")
        for conflict in plan.conflicts:
            print(f"  {conflict.message}")


if __name__ == "__main__":
    main()
