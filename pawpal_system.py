"""PawPal+ logic layer.

Owner, Pet, and Task hold the data. Scheduler is the brain that reads tasks
across every pet and sorts, filters, plans, and checks them for conflicts.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


def to_minutes(hhmm: str) -> int:
    """Convert an HH:MM string to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def to_hhmm(total_minutes: int) -> str:
    """Convert minutes after midnight back to an HH:MM string."""
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


@dataclass
class Task:
    """One care activity for a pet, such as a walk, a meal, or medication."""

    description: str
    time: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "once"
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def __post_init__(self):
        """Reject bad input early so the scheduler never sees it."""
        try:
            hours, minutes = self.time.split(":")
            valid_time = 0 <= int(hours) < 24 and 0 <= int(minutes) < 60
        except (ValueError, AttributeError):
            valid_time = False
        if not valid_time:
            raise ValueError(f"time must be HH:MM, got {self.time!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")
        if self.frequency not in ("once", *FREQUENCY_DAYS):
            raise ValueError("frequency must be once, daily, or weekly")

    @property
    def start(self) -> int:
        """Start time in minutes after midnight."""
        return to_minutes(self.time)

    @property
    def end(self) -> int:
        """End time in minutes after midnight."""
        return self.start + self.duration_minutes

    def mark_complete(self):
        """Mark this task done and return the next occurrence if it repeats."""
        self.completed = True
        if self.frequency in FREQUENCY_DAYS:
            next_date = self.due_date + timedelta(days=FREQUENCY_DAYS[self.frequency])
            return Task(self.description, self.time, self.duration_minutes,
                        self.priority, self.frequency, next_date)
        return None


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task):
        """Attach a task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a task from this pet."""
        self.tasks.remove(task)

    def list_tasks(self) -> list:
        """Return a copy of this pet's tasks."""
        return list(self.tasks)


@dataclass
class Owner:
    """A pet owner with a daily time budget and one or more pets."""

    name: str
    available_minutes: int = 120
    pets: list = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet, refusing a second pet with the same name."""
        if self.get_pet(pet.name):
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def get_pet(self, name: str):
        """Return the pet with this name, or None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list:
        """Return (pet, task) pairs for every task across every pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def to_dict(self) -> dict:
        """Turn the owner, pets, and tasks into plain data for JSON."""
        data = asdict(self)
        for pet in data["pets"]:
            for task in pet["tasks"]:
                task["due_date"] = task["due_date"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """Rebuild an owner, pets, and tasks from plain data."""
        owner = cls(data["name"], data["available_minutes"])
        for pet_data in data["pets"]:
            pet = Pet(pet_data["name"], pet_data["species"])
            for t in pet_data["tasks"]:
                task = Task(t["description"], t["time"], t["duration_minutes"],
                            t["priority"], t["frequency"],
                            date.fromisoformat(t["due_date"]), t["completed"])
                pet.add_task(task)
            owner.add_pet(pet)
        return owner

    def save_json(self, path: str):
        """Save everything to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: str):
        """Load an owner, pets, and tasks from a JSON file."""
        with open(path) as f:
            return cls.from_dict(json.load(f))


class Scheduler:
    """Reads tasks across all of an owner's pets and organizes them."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def tasks_for_day(self, day: date = None, include_completed: bool = False) -> list:
        """Return (pet, task) pairs due on a day, pending only by default."""
        day = day or date.today()
        return [(pet, task) for pet, task in self.owner.get_all_tasks()
                if task.due_date == day and (include_completed or not task.completed)]

    def sort_by_time(self, pairs: list = None) -> list:
        """Return pairs in chronological order by date, then HH:MM time."""
        pairs = self.owner.get_all_tasks() if pairs is None else pairs
        return sorted(pairs, key=lambda pair: (pair[1].due_date, pair[1].start))

    def sort_by_priority(self, pairs: list = None) -> list:
        """Return pairs from high to low priority, earlier time first on ties."""
        pairs = self.owner.get_all_tasks() if pairs is None else pairs
        return sorted(pairs, key=lambda pair: (-PRIORITY_RANK[pair[1].priority], pair[1].start))

    def filter_tasks(self, pet_name: str = None, completed: bool = None) -> list:
        """Return pairs matching a pet name and or a completion status."""
        result = []
        for pet, task in self.owner.get_all_tasks():
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            if completed is not None and task.completed != completed:
                continue
            result.append((pet, task))
        return result

    def mark_task_complete(self, pet: Pet, task: Task):
        """Complete a task and add its next occurrence to the pet if it repeats."""
        next_task = task.mark_complete()
        if next_task:
            pet.add_task(next_task)
        return next_task

    def detect_conflicts(self, day: date = None) -> list:
        """Return warning strings for pending tasks on a day whose times overlap."""
        pairs = self.sort_by_time(self.tasks_for_day(day))
        warnings = []
        for i, (pet_a, task_a) in enumerate(pairs):
            for pet_b, task_b in pairs[i + 1:]:
                if task_b.start >= task_a.end:
                    break
                warnings.append(
                    f"Conflict: {pet_a.name} {task_a.description} "
                    f"{task_a.time} to {to_hhmm(task_a.end)} overlaps "
                    f"{pet_b.name} {task_b.description} "
                    f"{task_b.time} to {to_hhmm(task_b.end)}"
                )
        return warnings

    def build_daily_plan(self, day: date = None):
        """Pick tasks by priority until the owner's time runs out.

        Returns (plan, skipped). plan is a list of (pet, task, reason) in time
        order. skipped is a list of (pet, task, reason) that did not fit.
        """
        remaining = self.owner.available_minutes
        chosen, skipped = [], []
        for pet, task in self.sort_by_priority(self.tasks_for_day(day)):
            if task.duration_minutes <= remaining:
                remaining -= task.duration_minutes
                reason = (f"{task.priority} priority, fits with "
                          f"{remaining} of {self.owner.available_minutes} min left")
                chosen.append((pet, task, reason))
            else:
                reason = (f"skipped, needs {task.duration_minutes} min "
                          f"but only {remaining} min left")
                skipped.append((pet, task, reason))
        plan = sorted(chosen, key=lambda item: item[1].start)
        return plan, skipped

    def next_available_slot(self, duration_minutes: int, day: date = None,
                            day_start: str = "07:00", day_end: str = "21:00"):
        """Return the earliest HH:MM start with a free gap of this length, or None."""
        cursor = to_minutes(day_start)
        for _, task in self.sort_by_time(self.tasks_for_day(day)):
            if task.start - cursor >= duration_minutes:
                return to_hhmm(cursor)
            cursor = max(cursor, task.end)
        if to_minutes(day_end) - cursor >= duration_minutes:
            return to_hhmm(cursor)
        return None
