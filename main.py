from datetime import date, time

from pawpal_system import (
    Category,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Species,
    Task,
)


def main() -> None:
    owner = Owner(name="Jordan", available_start=time(7, 0), available_end=time(21, 0))

    mochi = Pet(name="Mochi", species=Species.DOG)
    luna = Pet(name="Luna", species=Species.CAT)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(
        Task("Morning walk", 30, priority=Priority.HIGH, category=Category.WALK, fixed_time=time(8, 0))
    )
    mochi.add_task(
        Task("Medication", 5, priority=Priority.HIGH, category=Category.MEDS, fixed_time=time(12, 30))
    )
    luna.add_task(
        Task("Dinner", 10, priority=Priority.MEDIUM, category=Category.FEEDING, fixed_time=time(18, 0))
    )
    luna.add_task(
        Task("Brushing", 15, priority=Priority.LOW, category=Category.GROOMING)
    )

    today = date.today()
    plan = Scheduler().build_plan(owner, today)

    print(f"Today's Schedule ({today:%A, %B %d}) for {owner.name}")
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
