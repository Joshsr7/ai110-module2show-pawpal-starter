"""CLI demo for PawPal+. Run with: python main.py"""

import os
import tempfile

from pawpal_system import Owner, Pet, Task, Scheduler, to_hhmm


def show(title, pairs):
    print(f"\n{title}")
    print("-" * len(title))
    if not pairs:
        print("  (none)")
    for pet, task in pairs:
        status = "done" if task.completed else "todo"
        print(f"  {task.time}-{to_hhmm(task.end)}  {pet.name:<6} {task.description:<18}"
              f" {task.priority:<6} {task.frequency:<6} {status}")


def main():
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of order on purpose so sorting has work to do.
    mochi.add_task(Task("Evening walk", "18:00", 30, "high", "daily"))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    luna.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Litter box", "09:00", 15, "medium", "daily"))
    mochi.add_task(Task("Flea medication", "12:00", 5, "high", "weekly"))
    luna.add_task(Task("Brushing", "07:45", 20, "low", "once"))
    mochi.add_task(Task("Vet appointment", "14:00", 60, "medium", "once"))

    scheduler = Scheduler(owner)
    print(f"PawPal+ for {owner.name}, {len(owner.pets)} pets, "
          f"{owner.available_minutes} minutes available today")

    show("Today's Schedule, sorted by time", scheduler.sort_by_time(scheduler.tasks_for_day()))
    show("Filter: Luna only", scheduler.filter_tasks(pet_name="Luna"))

    print("\nConflict check")
    print("--------------")
    for warning in scheduler.detect_conflicts():
        print(f"  WARNING {warning}")

    plan, skipped = scheduler.build_daily_plan()
    print(f"\nDaily plan within {owner.available_minutes} minutes")
    print("-------------------------------")
    for pet, task, reason in plan:
        print(f"  {task.time}  {pet.name:<6} {task.description:<18} {reason}")
    for pet, task, reason in skipped:
        print(f"  ----   {pet.name:<6} {task.description:<18} {reason}")

    walk = next(t for t in mochi.tasks if t.description == "Morning walk")
    next_walk = scheduler.mark_task_complete(mochi, walk)
    print("\nRecurring task")
    print("--------------")
    print(f"  Completed Mochi Morning walk on {walk.due_date}, "
          f"next one added for {next_walk.due_date} at {next_walk.time}")
    show("Filter: completed tasks", scheduler.filter_tasks(completed=True))

    print("\nNext free 60 minute slot today:", scheduler.next_available_slot(60))

    path = os.path.join(tempfile.gettempdir(), "pawpal_data.json")
    owner.save_json(path)
    loaded = Owner.load_json(path)
    print(f"Saved and reloaded {len(loaded.get_all_tasks())} tasks for "
          f"{', '.join(p.name for p in loaded.pets)} from JSON")


if __name__ == "__main__":
    main()
