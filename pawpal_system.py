from __future__ import annotations

from dataclasses import dataclass, field
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

    def validate(self) -> None:
        """Raise ValueError on empty title, duration <= 0, or WEEKLY without weekday."""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty")
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than 0 minutes")
        if self.frequency is Frequency.WEEKLY and self.weekday not in range(7):
            raise ValueError("Weekly tasks need a weekday from 0 (Mon) to 6 (Sun)")

    def is_due(self, day: date) -> bool:
        """ONCE: due until completed. DAILY: every day. WEEKLY: when day.weekday() == weekday."""
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

    def tasks_due(self, day: date) -> list[Task]:
        """Tasks that are due on day and not yet complete."""
        return [t for t in self.tasks if t.is_due(day) and not t.is_complete(day)]


@dataclass
class Preferences:
    earliest_start: time | None = None
    preferred_times: dict[Category, time] = field(default_factory=dict)  # not used by the Scheduler yet


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


@dataclass
class Plan:
    day: date
    scheduled: list[ScheduledEntry] = field(default_factory=list)
    unscheduled: list[UnscheduledEntry] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)

    def is_stale_for(self, owner: Owner) -> bool:
        """True if the owner's pets or tasks changed after this plan was built."""
        pass


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
        return plan

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
        """Place fixed-time tasks at their time, recording conflicts and out-of-window tasks."""
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
            for other in plan.scheduled:
                if entry.start < other.end and other.start < entry.end:
                    plan.conflicts.append(
                        Conflict(
                            other,
                            entry,
                            f"{other.pet.name}'s {other.task.title} "
                            f"({other.start:%H:%M}-{other.end:%H:%M}) overlaps "
                            f"{pet.name}'s {task.title} ({entry.start:%H:%M}-{entry.end:%H:%M})",
                        )
                    )
            plan.scheduled.append(entry)

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
