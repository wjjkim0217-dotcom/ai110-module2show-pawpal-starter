from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Any
from uuid import uuid4


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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


@dataclass
class Task:
    title: str
    duration_minutes: int
    id: str = field(default_factory=lambda: str(uuid4()))
    priority: Priority = Priority.MEDIUM
    category: Category = Category.OTHER
    fixed_time: time | None = None
    frequency: Frequency = Frequency.ONCE
    weekday: int | None = None
    notes: str = ""
    completed_on: date | None = None

    def validate(self) -> None:
        pass

    def is_due(self, day: date) -> bool:
        pass

    def mark_complete(self, day: date) -> None:
        pass

    def is_complete(self, day: date) -> bool:
        pass

    def update(self, **fields: Any) -> None:
        pass

    def sort_key(self) -> tuple[Any, ...]:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task_id: str) -> None:
        pass

    def get_task(self, task_id: str) -> Task:
        pass

    def tasks_due(self, day: date) -> list[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_start: time
    available_end: time
    preferences: dict[str, Any] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def all_tasks_due(self, day: date) -> list[tuple[Pet, Task]]:
        pass

    def available_minutes(self) -> int:
        pass

    def set_availability(self, start: time, end: time) -> None:
        pass


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
class Plan:
    scheduled: list[ScheduledEntry] = field(default_factory=list)
    unscheduled: list[UnscheduledEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Scheduler:
    def build_plan(self, owner: Owner, day: date) -> Plan:
        pass