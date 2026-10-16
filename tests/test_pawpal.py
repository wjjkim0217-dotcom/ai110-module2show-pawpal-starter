import pytest
from datetime import date, time

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Species, Task, TaskStatus


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


MONDAY = date(2025, 1, 6)
TUESDAY = date(2025, 1, 7)


def make_owner():
    owner = Owner("Jordan", time(7, 0), time(21, 0))
    mochi = Pet("Mochi", Species.DOG)
    luna = Pet("Luna", Species.CAT)
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


def test_sort_by_time_orders_hhmm_and_puts_untimed_last():
    tasks = [
        Task("evening", 5, fixed_time=time(18, 0)),
        Task("untimed", 5),
        Task("morning", 5, fixed_time=time(8, 5)),
        Task("noon", 5, fixed_time=time(12, 30)),
    ]

    result = Scheduler().sort_by_time(tasks)

    assert [t.title for t in result] == ["morning", "noon", "evening", "untimed"]


def test_filter_tasks_by_pet_name_ignores_case():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", 20))
    luna.add_task(Task("Brush", 5))

    result = owner.filter_tasks(pet_name="mOcHi", day=MONDAY)

    assert [(p.name, t.title) for p, t in result] == [("Mochi", "Walk")]


def test_filter_tasks_by_status_splits_done_and_pending():
    owner, mochi, _ = make_owner()
    walk, feed = Task("Walk", 20), Task("Feed", 5)
    mochi.add_task(walk)
    mochi.add_task(feed)
    walk.mark_complete(MONDAY)

    done = owner.filter_tasks(status=TaskStatus.DONE, day=MONDAY)
    pending = owner.filter_tasks(status=TaskStatus.PENDING, day=MONDAY)

    assert [t.title for _, t in done] == ["Walk"]
    assert [t.title for _, t in pending] == ["Feed"]


def test_daily_task_renews_for_tomorrow_only():
    owner, mochi, _ = make_owner()
    feed = Task("Feed", 5, frequency=Frequency.DAILY)
    mochi.add_task(feed)

    renewed = mochi.complete_task(feed.id, MONDAY)

    assert renewed.due_date == TUESDAY
    assert len(owner.all_tasks_due(MONDAY)) == 0
    assert owner.all_tasks_due(TUESDAY) == [(mochi, renewed)]


def test_weekly_task_renews_on_next_weekday_and_once_task_does_not_renew():
    _, mochi, _ = make_owner()
    bath = Task("Bath", 20, frequency=Frequency.WEEKLY, weekday=0)  # Monday
    vet = Task("Vet", 30)
    mochi.add_task(bath)
    mochi.add_task(vet)

    renewed = mochi.complete_task(bath.id, MONDAY)

    assert renewed.due_date == date(2025, 1, 13)
    assert mochi.complete_task(vet.id, MONDAY) is None
    assert vet.is_complete(MONDAY)


def test_completing_twice_does_not_create_duplicate_renewal():
    _, mochi, _ = make_owner()
    feed = Task("Feed", 5, frequency=Frequency.DAILY)
    mochi.add_task(feed)

    mochi.complete_task(feed.id, MONDAY)
    second = mochi.complete_task(feed.id, MONDAY)

    assert second is None
    assert len(mochi.tasks) == 2


def test_overlapping_fixed_tasks_produce_conflict_with_next_free_slot():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", 30, fixed_time=time(8, 0)))
    luna.add_task(Task("Vet call", 30, fixed_time=time(8, 15)))

    plan = Scheduler().build_plan(owner, MONDAY)

    assert len(plan.conflicts) == 1
    assert plan.conflicts[0].same_pet is False
    assert plan.conflicts[0].suggestion == time(8, 45)


def test_back_to_back_fixed_tasks_are_not_a_conflict():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", 30, fixed_time=time(8, 0)))
    mochi.add_task(Task("Feed", 10, fixed_time=time(8, 30)))

    assert Scheduler().build_plan(owner, MONDAY).conflicts == []


def test_same_pet_overlap_is_flagged_as_same_pet():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", 30, fixed_time=time(8, 0)))
    mochi.add_task(Task("Walk again", 30, fixed_time=time(8, 10)))

    conflicts = Scheduler().build_plan(owner, MONDAY).conflicts

    assert len(conflicts) == 1 and conflicts[0].same_pet is True


def test_scheduler_mark_complete_creates_next_daily_instance_on_the_right_pet():
    owner, mochi, luna = make_owner()
    feed = Task("Feed", 5, frequency=Frequency.DAILY)
    luna.add_task(feed)

    renewed = Scheduler().mark_complete(owner, feed.id, MONDAY)

    assert renewed is not feed and renewed.id != feed.id
    assert renewed.due_date == TUESDAY
    assert luna.get_task(renewed.id) is renewed
    assert mochi.tasks == []
    assert feed.is_complete(MONDAY)


def test_scheduler_mark_complete_creates_next_weekly_instance_and_ignores_unknown_id():
    owner, mochi, _ = make_owner()
    bath = Task("Bath", 20, frequency=Frequency.WEEKLY, weekday=2)  # Wednesday
    mochi.add_task(bath)
    wednesday = date(2025, 1, 8)

    renewed = Scheduler().mark_complete(owner, bath.id, wednesday)

    assert renewed.due_date == date(2025, 1, 15)
    assert Scheduler().mark_complete(owner, "no-such-id", wednesday) is None


def test_tasks_at_exact_same_time_conflict_for_same_and_different_pets():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", 30, fixed_time=time(9, 0)))
    mochi.add_task(Task("Bath", 30, fixed_time=time(9, 0)))
    luna.add_task(Task("Feed", 30, fixed_time=time(9, 0)))

    conflicts = Scheduler().build_plan(owner, MONDAY).conflicts

    assert len(conflicts) == 3  # three tasks at 09:00 -> three pairs
    assert sum(c.same_pet for c in conflicts) == 1


# --- sorting: the built plan is chronological and priority-aware ---


def test_build_plan_entries_are_in_chronological_order():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Evening walk", 30, fixed_time=time(18, 0)))
    luna.add_task(Task("Breakfast", 10, fixed_time=time(8, 0)))
    mochi.add_task(Task("Brush", 15))  # flexible, fills the first gap

    starts = [e.start for e in Scheduler().build_plan(owner, MONDAY).scheduled]

    assert starts == sorted(starts)
    assert starts[0] == time(7, 0)  # flexible task takes the first gap before 08:00


def test_flexible_tasks_are_placed_by_priority():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("low", 10, priority=Priority.LOW))
    mochi.add_task(Task("high", 10, priority=Priority.HIGH))
    mochi.add_task(Task("medium", 10, priority=Priority.MEDIUM))

    plan = Scheduler().build_plan(owner, MONDAY)

    assert [e.task.title for e in plan.scheduled] == ["high", "medium", "low"]


# --- edge cases ---


def test_pet_with_no_tasks_and_owner_with_no_pets_give_empty_plan():
    owner, _, _ = make_owner()
    empty_owner = Owner("Sam", time(7, 0), time(21, 0))

    for o in (owner, empty_owner):
        plan = Scheduler().build_plan(o, MONDAY)
        assert plan.scheduled == [] and plan.unscheduled == [] and plan.conflicts == []


def test_fixed_task_outside_window_is_unscheduled():
    owner, mochi, _ = make_owner()  # window 07:00-21:00
    mochi.add_task(Task("Early", 30, fixed_time=time(6, 30)))
    mochi.add_task(Task("Late", 60, fixed_time=time(20, 30)))  # ends 21:30

    plan = Scheduler().build_plan(owner, MONDAY)

    assert plan.scheduled == []
    assert len(plan.unscheduled) == 2


def test_task_exactly_filling_window_fits_but_one_minute_more_does_not():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Fits", owner.available_minutes()))
    mochi.add_task(Task("Too long", owner.available_minutes() + 1))

    plan = Scheduler().build_plan(owner, MONDAY)

    assert [e.task.title for e in plan.scheduled] == ["Fits"]
    assert [e.task.title for e in plan.unscheduled] == ["Too long"]


def test_daily_task_is_pending_tomorrow_and_not_due_twice_on_renewal_day():
    owner, mochi, _ = make_owner()
    feed = Task("Feed", 5, frequency=Frequency.DAILY)
    mochi.add_task(feed)

    mochi.complete_task(feed.id, MONDAY)

    assert feed.status(MONDAY) is TaskStatus.DONE
    assert feed.status(TUESDAY) is TaskStatus.PENDING
    assert [t.title for _, t in owner.all_tasks_due(TUESDAY)] == ["Feed"]  # only the successor


@pytest.mark.parametrize(
    "kwargs",
    [
        {"title": "  ", "duration_minutes": 10},
        {"title": "Walk", "duration_minutes": 0},
        {"title": "Walk", "duration_minutes": -5},
        {"title": "Bath", "duration_minutes": 10, "frequency": Frequency.WEEKLY},
        {"title": "Bath", "duration_minutes": 10, "frequency": Frequency.WEEKLY, "weekday": 7},
    ],
)
def test_add_task_rejects_invalid_tasks(kwargs):
    pet = Pet("Mochi", Species.DOG)

    with pytest.raises(ValueError):
        pet.add_task(Task(**kwargs))

    assert pet.tasks == []


def test_invalid_update_raises_and_restores_old_values():
    task = Task("Walk", 30)

    with pytest.raises(ValueError):
        task.update(title="Run", duration_minutes=0)

    assert (task.title, task.duration_minutes) == ("Walk", 30)


def test_availability_must_end_after_it_starts():
    with pytest.raises(ValueError):
        Owner("Jordan", time(21, 0), time(7, 0))
