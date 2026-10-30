from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Scheduler

TODAY = date.today()


def make_owner(minutes=90):
    owner = Owner("Jordan", available_minutes=minutes)
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))
    return owner


# Phase 2 quick tests
def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30", 30)
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Breakfast", "08:00", 10))
    pet.add_task(Task("Walk", "09:00", 30))
    assert len(pet.list_tasks()) == 2


# Sorting
def test_sort_by_time_is_chronological_across_pets():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Evening walk", "18:00", 30))
    owner.get_pet("Luna").add_task(Task("Breakfast", "08:00", 10))
    owner.get_pet("Mochi").add_task(Task("Lunch", "12:30", 10))
    times = [task.time for _, task in Scheduler(owner).sort_by_time()]
    assert times == ["08:00", "12:30", "18:00"]


def test_sort_handles_times_that_sort_wrong_as_text():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Late", "10:00", 10))
    owner.get_pet("Mochi").add_task(Task("Early", "9:05", 10))
    times = [task.time for _, task in Scheduler(owner).sort_by_time()]
    assert times == ["9:05", "10:00"]


def test_sort_by_priority_puts_high_first():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Play", "08:00", 10, "low"))
    owner.get_pet("Luna").add_task(Task("Meds", "09:00", 5, "high"))
    first_pet, first_task = Scheduler(owner).sort_by_priority()[0]
    assert first_task.description == "Meds"


# Filtering
def test_filter_by_pet_name():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", "07:30", 30))
    owner.get_pet("Luna").add_task(Task("Brush", "08:00", 10))
    result = Scheduler(owner).filter_tasks(pet_name="luna")
    assert [pet.name for pet, _ in result] == ["Luna"]


def test_filter_by_completion_status():
    owner = make_owner()
    done = Task("Walk", "07:30", 30)
    done.mark_complete()
    owner.get_pet("Mochi").add_task(done)
    owner.get_pet("Mochi").add_task(Task("Dinner", "18:00", 10))
    pending = Scheduler(owner).filter_tasks(completed=False)
    assert [task.description for _, task in pending] == ["Dinner"]


# Recurrence
def test_completing_daily_task_creates_one_for_tomorrow():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    walk = Task("Morning walk", "07:30", 30, frequency="daily", due_date=TODAY)
    mochi.add_task(walk)
    next_walk = Scheduler(owner).mark_task_complete(mochi, walk)
    assert walk.completed is True
    assert next_walk.due_date == TODAY + timedelta(days=1)
    assert next_walk.completed is False
    assert next_walk in mochi.tasks


def test_completing_weekly_task_creates_one_next_week():
    task = Task("Flea medication", "12:00", 5, frequency="weekly", due_date=TODAY)
    assert task.mark_complete().due_date == TODAY + timedelta(days=7)


def test_completing_one_time_task_creates_nothing():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    vet = Task("Vet", "14:00", 60, frequency="once")
    mochi.add_task(vet)
    assert Scheduler(owner).mark_task_complete(mochi, vet) is None
    assert len(mochi.tasks) == 1


# Conflict detection
def test_conflict_flagged_for_same_time_on_different_pets():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Breakfast", "08:00", 10))
    owner.get_pet("Luna").add_task(Task("Breakfast", "08:00", 10))
    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1
    assert "Mochi" in warnings[0] and "Luna" in warnings[0]


def test_conflict_flagged_for_overlapping_durations():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", "07:30", 30))
    owner.get_pet("Mochi").add_task(Task("Brush", "07:45", 10))
    assert len(Scheduler(owner).detect_conflicts()) == 1


def test_back_to_back_tasks_are_not_a_conflict():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", "07:30", 30))
    owner.get_pet("Mochi").add_task(Task("Breakfast", "08:00", 10))
    assert Scheduler(owner).detect_conflicts() == []


def test_completed_tasks_do_not_cause_conflicts():
    owner = make_owner()
    walk = Task("Walk", "08:00", 30)
    walk.mark_complete()
    owner.get_pet("Mochi").add_task(walk)
    owner.get_pet("Luna").add_task(Task("Breakfast", "08:00", 10))
    assert Scheduler(owner).detect_conflicts() == []


# Daily plan
def test_plan_stays_within_available_minutes_and_keeps_high_priority():
    owner = make_owner(minutes=40)
    owner.get_pet("Mochi").add_task(Task("Walk", "07:30", 30, "high"))
    owner.get_pet("Luna").add_task(Task("Play", "09:00", 30, "low"))
    owner.get_pet("Luna").add_task(Task("Meds", "10:00", 5, "high"))
    plan, skipped = Scheduler(owner).build_daily_plan()
    assert sum(task.duration_minutes for _, task, _ in plan) <= 40
    assert [task.description for _, task, _ in plan] == ["Walk", "Meds"]
    assert [task.description for _, task, _ in skipped] == ["Play"]


def test_plan_for_owner_with_no_tasks_is_empty():
    plan, skipped = Scheduler(make_owner()).build_daily_plan()
    assert plan == [] and skipped == []


# Next available slot
def test_next_available_slot_finds_first_gap():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", "07:00", 60))
    owner.get_pet("Luna").add_task(Task("Brush", "08:30", 30))
    assert Scheduler(owner).next_available_slot(30) == "08:00"
    assert Scheduler(owner).next_available_slot(45) == "09:00"


# Input validation and persistence
def test_invalid_time_is_rejected():
    with pytest.raises(ValueError):
        Task("Walk", "25:99", 30)


def test_duplicate_pet_name_is_rejected():
    owner = make_owner()
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "dog"))


def test_json_round_trip_keeps_pets_and_tasks(tmp_path):
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", "07:30", 30, "high", "daily"))
    path = tmp_path / "data.json"
    owner.save_json(path)
    loaded = Owner.load_json(path)
    pet, task = loaded.get_all_tasks()[0]
    assert (pet.name, task.description, task.frequency, task.due_date) == ("Mochi", "Walk", "daily", TODAY)
