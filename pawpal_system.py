from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def rank(self) -> int:
        """Sort rank: lower is scheduled first (HIGH=0, MEDIUM=1, LOW=2)."""
        return list(Priority).index(self)


class Category(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


class TaskStatus(Enum):
    PENDING = "pending"
    DONE = "done"


class Species(Enum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


# eq=False on Task, Pet and Owner: equality is identity, so list.remove() and
# `in` never match a different object that happens to have the same field values.
# Look things up by id instead.
@dataclass(eq=False)
class Task:
    title: str
    duration_minutes: int
    id: str = field(default_factory=lambda: str(uuid4()))
    priority: Priority = Priority.MEDIUM
    category: Category = Category.OTHER
    fixed_time: time | None = None
    frequency: Frequency = Frequency.ONCE
    weekday: int | None = None  # 0=Mon..6=Sun; required when frequency is WEEKLY
    notes: str = ""
    completed_on: date | None = None
    due_date: date | None = None  # not due before this day; set on renewed recurring tasks
    renewed: bool = False  # True once a successor was created; the task stops recurring

    def validate(self) -> None:
        """Raise ValueError on empty title, duration <= 0, or WEEKLY without weekday."""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty")
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than 0 minutes")
        if self.frequency is Frequency.WEEKLY and self.weekday not in range(7):
            raise ValueError("Weekly tasks need a weekday from 0 (Mon) to 6 (Sun)")

    def is_due(self, day: date) -> bool:
        """ONCE: due from due_date until completed. DAILY: every day from due_date. WEEKLY: on its weekday from due_date."""
        if self.due_date is not None and day < self.due_date:
            return False
        if self.renewed and self.completed_on is not None and day > self.completed_on:
            return False
        if self.frequency is Frequency.WEEKLY:
            return day.weekday() == self.weekday
        return True

    def mark_complete(self, day: date) -> None:
        """Record that the task was completed on day."""
        self.completed_on = day

    def is_complete(self, day: date) -> bool:
        """DAILY/WEEKLY: completed_on == day. A ONCE task stays complete for good."""
        if self.completed_on is None:
            return False
        if self.frequency is Frequency.ONCE:
            return True
        return self.completed_on == day

    def status(self, day: date) -> TaskStatus:
        """DONE if the task is complete on day, else PENDING."""
        return TaskStatus.DONE if self.is_complete(day) else TaskStatus.PENDING

    def complete_and_renew(self, day: date) -> Task | None:
        """Mark complete on day. DAILY/WEEKLY return a fresh copy due on the next occurrence
        (counted from day, so missed days never pile up); ONCE returns None. The completed task
        is flagged renewed so it stops being due next to its replacement (frequency is kept).
        """
        self.mark_complete(day)
        if self.frequency is Frequency.ONCE:
            return None
        if self.frequency is Frequency.DAILY:
            next_due = day + timedelta(days=1)
        else:
            next_due = day + timedelta(days=(self.weekday - day.weekday()) % 7 or 7)
        renewed = replace(self, id=str(uuid4()), completed_on=None, due_date=next_due)
        self.renewed = True
        return renewed

    def update(self, **fields: Any) -> None:
        """Apply the given fields, then re-run validate(). Restores the old values if invalid."""
        old = {name: getattr(self, name) for name in fields}
        for name, value in fields.items():
            if not hasattr(self, name):
                raise AttributeError(f"Task has no field '{name}'")
            setattr(self, name, value)
        try:
            self.validate()
        except ValueError:
            for name, value in old.items():
                setattr(self, name, value)
            raise

    def sort_key(self) -> tuple[Any, ...]:
        """Priority rank, then fixed time, then shorter duration. Python's stable sort keeps insertion order."""
        return (
            self.priority.rank,
            self.fixed_time is None,
            self.fixed_time or time.min,
            self.duration_minutes,
        )


@dataclass(eq=False)
class Pet:
    name: str
    species: Species
    id: str = field(default_factory=lambda: str(uuid4()))
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Validate, then append."""
        task.validate()
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with this id, if present."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_task(self, task_id: str) -> Task | None:
        """Return None if no task has this id."""
        return next((t for t in self.tasks if t.id == task_id), None)

    def complete_task(self, task_id: str, day: date) -> Task | None:
        """Complete a task and add its next occurrence. Returns the new task, or None if there is
        none (ONCE task, unknown id, or an identical occurrence already exists).
        """
        task = self.get_task(task_id)
        if task is None:
            return None
        renewed = task.complete_and_renew(day)
        if renewed is None or any(
            t.title == renewed.title and t.due_date == renewed.due_date for t in self.tasks
        ):
            return None
        self.add_task(renewed)
        return renewed


@dataclass
class Preferences:
    earliest_start: time | None = None


@dataclass(eq=False)
class Owner:
    name: str
    available_start: time
    available_end: time
    preferences: Preferences = field(default_factory=Preferences)
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the availability window given at construction."""
        self.set_availability(self.available_start, self.available_end)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Also removes the pet's tasks."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Every task from every pet, paired with its pet. The Scheduler's only source of tasks."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def all_tasks_due(self, day: date) -> list[tuple[Pet, Task]]:
        """get_all_tasks() filtered to tasks due and not complete on day (one pool: the owner is one person)."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.is_due(day) and not task.is_complete(day)
        ]

    def filter_tasks(
        self,
        pet_name: str | None = None,
        status: TaskStatus | None = None,
        day: date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Tasks filtered by pet name (case-insensitive) and/or status on day (default today)."""
        day = day or date.today()
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if (pet_name is None or pet.name.lower() == pet_name.lower())
            and (status is None or task.status(day) is status)
        ]

    def available_minutes(self) -> int:
        """Return the length of the availability window in minutes."""
        start = datetime.combine(date.min, self.available_start)
        end = datetime.combine(date.min, self.available_end)
        return int((end - start).total_seconds() // 60)

    def set_availability(self, start: time, end: time) -> None:
        """Raise ValueError unless start < end (no midnight crossing)."""
        if start >= end:
            raise ValueError("Availability must end after it starts")
        self.available_start = start
        self.available_end = end


@dataclass
class ScheduledEntry:
    task: Task
    pet: Pet
    start: time
    end: time
    reason: str

    def overlaps(self, other: ScheduledEntry) -> bool:
        """True if the two time ranges overlap (touching ends do not count)."""
        return self.start < other.end and other.start < self.end


@dataclass
class UnscheduledEntry:
    task: Task
    pet: Pet
    reason: str


@dataclass
class Conflict:
    first: ScheduledEntry
    second: ScheduledEntry
    message: str
    same_pet: bool = False
    suggestion: time | None = None  # next free start for the later task


@dataclass
class Plan:
    day: date
    scheduled: list[ScheduledEntry] = field(default_factory=list)
    unscheduled: list[UnscheduledEntry] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)

    def for_pet(self, pet_name: str) -> Plan:
        """A copy of this plan holding only one pet's entries (conflicts involving that pet)."""
        name = pet_name.lower()
        return Plan(
            day=self.day,
            scheduled=[e for e in self.scheduled if e.pet.name.lower() == name],
            unscheduled=[e for e in self.unscheduled if e.pet.name.lower() == name],
            conflicts=[
                c for c in self.conflicts
                if name in (c.first.pet.name.lower(), c.second.pet.name.lower())
            ],
        )


class Scheduler:
    """Fixed-time tasks are placed first at their time, whatever their priority:
    they are commitments. Flexible tasks are then placed greedily by sort_key
    into the first gap that fits. Time arithmetic uses datetime.combine(day, t).
    """

    def build_plan(self, owner: Owner, day: date) -> Plan:
        """Reads tasks only via owner.all_tasks_due(day), never from a single pet."""
        plan = Plan(day=day)
        entries = owner.all_tasks_due(day)
        fixed = [e for e in entries if e[1].fixed_time is not None]
        flexible = [e for e in entries if e[1].fixed_time is None]

        self._place_fixed(fixed, owner, plan, day)
        gaps = self._find_gaps(owner, plan, day)
        self._fill_gaps(flexible, gaps, plan)

        plan.scheduled.sort(key=lambda e: e.start)
        self._detect_conflicts(owner, plan, day)
        return plan

    def mark_complete(self, owner: Owner, task_id: str, day: date) -> Task | None:
        """Complete the task with this id on day, wherever it lives. A DAILY or WEEKLY task
        automatically gets a new instance for its next occurrence, which is returned
        (None for ONCE tasks, unknown ids, or an occurrence that already exists).
        """
        for pet in owner.pets:
            if pet.get_task(task_id) is not None:
                return pet.complete_task(task_id, day)
        return None

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Tasks ordered by fixed_time via its "HH:MM" string; tasks with no time go last.
        Zero-padded "HH:MM" strings sort the same as the times they represent, and "99:99"
        is a sentinel that sorts after every real time. sorted() is stable, so ties keep order.
        """
        return sorted(
            tasks,
            key=lambda t: t.fixed_time.strftime("%H:%M") if t.fixed_time else "99:99",
        )

    def _window(self, owner: Owner, day: date) -> tuple[datetime, datetime]:
        """Return the owner's available window on day, honouring the earliest_start preference."""
        start = owner.available_start
        earliest = owner.preferences.earliest_start
        if earliest is not None and earliest > start:
            start = earliest
        return datetime.combine(day, start), datetime.combine(day, owner.available_end)

    def _place_fixed(
        self,
        entries: list[tuple[Pet, Task]],
        owner: Owner,
        plan: Plan,
        day: date,
    ) -> None:
        """Place fixed-time tasks at their time; out-of-window tasks go to unscheduled."""
        window_start, window_end = self._window(owner, day)
        for pet, task in sorted(entries, key=lambda e: (e[1].fixed_time, e[1].sort_key())):
            start = datetime.combine(day, task.fixed_time)
            end = start + timedelta(minutes=task.duration_minutes)
            if start < window_start or end > window_end:
                plan.unscheduled.append(
                    UnscheduledEntry(task, pet, "fixed time is outside the available window")
                )
                continue
            entry = ScheduledEntry(
                task, pet, start.time(), end.time(), self._reason_for(task, placed_fixed=True)
            )
            plan.scheduled.append(entry)

    def _detect_conflicts(self, owner: Owner, plan: Plan, day: date) -> None:
        """Sweep the entries in start order, comparing each only with those still running.
        Only fixed-time tasks can overlap (flexible ones are placed into gaps).
        """
        active: list[ScheduledEntry] = []
        for entry in plan.scheduled:
            active = [a for a in active if a.end > entry.start]
            for other in active:
                if other.overlaps(entry):
                    plan.conflicts.append(self._make_conflict(owner, plan, day, other, entry))
            active.append(entry)

    def _make_conflict(
        self, owner: Owner, plan: Plan, day: date, first: ScheduledEntry, second: ScheduledEntry
    ) -> Conflict:
        """Build the Conflict for two overlapping entries (first starts no later than second).
        The message names both tasks and times, flags a same-pet overlap as a likely duplicate,
        and suggests the next free slot for the later task, or says none is left today.
        """
        same_pet = first.pet is second.pet
        slot = self.next_free_slot(
            owner, plan, day, second.task.duration_minutes, after=second.start
        )
        message = (
            f"{first.pet.name}'s {first.task.title} "
            f"({first.start:%H:%M}-{first.end:%H:%M}) overlaps "
            f"{second.pet.name}'s {second.task.title} "
            f"({second.start:%H:%M}-{second.end:%H:%M})"
        )
        if same_pet:
            message += " [same pet: check for a duplicate]"
        message += f"; next free slot: {slot:%H:%M}" if slot else "; no free slot left today"
        return Conflict(first, second, message, same_pet, slot)

    def next_free_slot(
        self, owner: Owner, plan: Plan, day: date, duration_minutes: int, after: time
    ) -> time | None:
        """Earliest start at or after `after` where duration_minutes fits around the scheduled
        entries, or None.
        """
        need = timedelta(minutes=duration_minutes)
        floor = datetime.combine(day, after)
        for gap_start, gap_end in self._find_gaps(owner, plan, day):
            start = max(gap_start, floor)
            if gap_end - start >= need:
                return start.time()
        return None

    def _find_gaps(
        self, owner: Owner, plan: Plan, day: date
    ) -> list[tuple[datetime, datetime]]:
        """Return the free (start, end) gaps in the window around the already scheduled entries."""
        window_start, window_end = self._window(owner, day)
        busy = sorted(
            (datetime.combine(day, e.start), datetime.combine(day, e.end)) for e in plan.scheduled
        )
        gaps = []
        cursor = window_start
        for start, end in busy:
            if start > cursor:
                gaps.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < window_end:
            gaps.append((cursor, window_end))
        return gaps

    def _fill_gaps(
        self,
        entries: list[tuple[Pet, Task]],
        gaps: list[tuple[datetime, datetime]],
        plan: Plan,
    ) -> None:
        """Place flexible tasks by sort_key into the first gap that fits; the rest go to unscheduled."""
        for pet, task in sorted(entries, key=lambda e: e[1].sort_key()):
            need = timedelta(minutes=task.duration_minutes)
            for i, (gap_start, gap_end) in enumerate(gaps):
                if gap_end - gap_start >= need:
                    plan.scheduled.append(
                        ScheduledEntry(
                            task,
                            pet,
                            gap_start.time(),
                            (gap_start + need).time(),
                            self._reason_for(task, placed_fixed=False),
                        )
                    )
                    gaps[i] = (gap_start + need, gap_end)
                    break
            else:
                plan.unscheduled.append(
                    UnscheduledEntry(task, pet, "no gap long enough in the available time")
                )

    def _reason_for(self, task: Task, placed_fixed: bool) -> str:
        """Return the short explanation shown for why a task was placed where it is."""
        if placed_fixed:
            return f"fixed time {task.fixed_time:%H:%M}"
        return f"{task.priority.value} priority, first gap that fits"
