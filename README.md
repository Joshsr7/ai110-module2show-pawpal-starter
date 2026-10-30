# PawPal+ (Module 2 Project)

PawPal+ is a Streamlit app that helps a busy pet owner plan care tasks for their pets. It tracks walks, meals, medication, and grooming across more than one pet, sorts them by time, warns about overlaps, repeats daily and weekly tasks, and builds a daily plan that fits the time the owner actually has.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks such as walks, feeding, meds, enrichment, and grooming
- Consider constraints such as time available and priority
- Produce a daily plan and explain why it chose that plan

## Features

- Add more than one pet and give each pet its own tasks
- Each task has a time, a length in minutes, a priority, and a repeat setting of once, daily, or weekly
- Today's schedule is shown in time order across all pets
- Filter the schedule by pet or by done or not done
- Conflict warnings when two tasks overlap, even across different pets
- Marking a daily or weekly task done adds the next one automatically
- Generate schedule picks the most important tasks that fit the owner's minutes and explains each choice
- Free slot finder shows the earliest open gap of a given length
- Save and Load keep pets and tasks in a JSON file between runs

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run it

```bash
python main.py          # terminal demo
streamlit run app.py    # web app
pytest                  # tests
```

## Project files

| File | What it holds |
|------|---------------|
| pawpal_system.py | Owner, Pet, Task, and Scheduler classes |
| main.py | Terminal demo that exercises every feature |
| app.py | Streamlit UI connected to the classes |
| tests/test_pawpal.py | 20 automated tests |
| diagrams/uml_draft.mmd | First UML from Phase 1 |
| diagrams/uml_final.mmd | Final UML that matches the code, also copied to uml.mmd |
| diagrams/uml_final.png | Picture of the final UML |

## 🖥️ Sample Output

Output of `python main.py`:

```
PawPal+ for Jordan, 2 pets, 90 minutes available today

Today's Schedule, sorted by time
--------------------------------
  07:30-08:00  Mochi  Morning walk       high   daily  todo
  07:45-08:05  Luna   Brushing           low    once   todo
  08:00-08:10  Mochi  Breakfast          high   daily  todo
  08:00-08:10  Luna   Breakfast          high   daily  todo
  09:00-09:15  Luna   Litter box         medium daily  todo
  12:00-12:05  Mochi  Flea medication    high   weekly todo
  14:00-15:00  Mochi  Vet appointment    medium once   todo
  18:00-18:30  Mochi  Evening walk       high   daily  todo

Filter: Luna only
-----------------
  08:00-08:10  Luna   Breakfast          high   daily  todo
  09:00-09:15  Luna   Litter box         medium daily  todo
  07:45-08:05  Luna   Brushing           low    once   todo

Conflict check
--------------
  WARNING Conflict: Mochi Morning walk 07:30 to 08:00 overlaps Luna Brushing 07:45 to 08:05
  WARNING Conflict: Luna Brushing 07:45 to 08:05 overlaps Mochi Breakfast 08:00 to 08:10
  WARNING Conflict: Luna Brushing 07:45 to 08:05 overlaps Luna Breakfast 08:00 to 08:10
  WARNING Conflict: Mochi Breakfast 08:00 to 08:10 overlaps Luna Breakfast 08:00 to 08:10

Daily plan within 90 minutes
-------------------------------
  07:30  Mochi  Morning walk       high priority, fits with 60 of 90 min left
  08:00  Mochi  Breakfast          high priority, fits with 50 of 90 min left
  08:00  Luna   Breakfast          high priority, fits with 40 of 90 min left
  12:00  Mochi  Flea medication    high priority, fits with 35 of 90 min left
  18:00  Mochi  Evening walk       high priority, fits with 5 of 90 min left
  ----   Luna   Litter box         skipped, needs 15 min but only 5 min left
  ----   Mochi  Vet appointment    skipped, needs 60 min but only 5 min left
  ----   Luna   Brushing           skipped, needs 20 min but only 5 min left

Recurring task
--------------
  Completed Mochi Morning walk on 2026-10-30, next one added for 2026-10-31 at 07:30

Filter: completed tasks
-----------------------
  07:30-08:00  Mochi  Morning walk       high   daily  done

Next free 60 minute slot today: 09:15
Saved and reloaded 9 tasks for Mochi, Luna from JSON
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov=pawpal_system
```

The tests cover marking tasks done, adding tasks, sorting by time and by priority, filtering by pet and status, daily and weekly repeats, one time tasks that do not repeat, conflicts at the same time and with overlapping lengths, back to back tasks that should not be flagged, the daily plan staying inside the time budget, an owner with no tasks, the free slot finder, bad input, duplicate pet names, and saving to JSON.

Sample test output:

```
collected 20 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  5%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [ 10%]
tests/test_pawpal.py::test_sort_by_time_is_chronological_across_pets PASSED [ 15%]
tests/test_pawpal.py::test_sort_handles_times_that_sort_wrong_as_text PASSED [ 20%]
tests/test_pawpal.py::test_sort_by_priority_puts_high_first PASSED       [ 25%]
tests/test_pawpal.py::test_filter_by_pet_name PASSED                     [ 30%]
tests/test_pawpal.py::test_filter_by_completion_status PASSED            [ 35%]
tests/test_pawpal.py::test_completing_daily_task_creates_one_for_tomorrow PASSED [ 40%]
tests/test_pawpal.py::test_completing_weekly_task_creates_one_next_week PASSED [ 45%]
tests/test_pawpal.py::test_completing_one_time_task_creates_nothing PASSED [ 50%]
tests/test_pawpal.py::test_conflict_flagged_for_same_time_on_different_pets PASSED [ 55%]
tests/test_pawpal.py::test_conflict_flagged_for_overlapping_durations PASSED [ 60%]
tests/test_pawpal.py::test_back_to_back_tasks_are_not_a_conflict PASSED  [ 65%]
tests/test_pawpal.py::test_completed_tasks_do_not_cause_conflicts PASSED [ 70%]
tests/test_pawpal.py::test_plan_stays_within_available_minutes_and_keeps_high_priority PASSED [ 75%]
tests/test_pawpal.py::test_plan_for_owner_with_no_tasks_is_empty PASSED  [ 80%]
tests/test_pawpal.py::test_next_available_slot_finds_first_gap PASSED    [ 85%]
tests/test_pawpal.py::test_invalid_time_is_rejected PASSED               [ 90%]
tests/test_pawpal.py::test_duplicate_pet_name_is_rejected PASSED         [ 95%]
tests/test_pawpal.py::test_json_round_trip_keeps_pets_and_tasks PASSED   [100%]

============================== 20 passed in 0.03s ==============================

Name               Stmts   Miss  Cover
--------------------------------------
pawpal_system.py     151      7    95%
```

Confidence level: ★★★★☆

All 20 tests pass and coverage of the logic file is 95 percent. I am leaving one star off because the UI was checked by hand and with a scripted Streamlit run, not with a full test file, and tasks that run past midnight are not handled.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time`, `Scheduler.sort_by_priority` | Time sort uses the date and then minutes after midnight, so 9:05 comes before 10:00. Priority sort goes high, medium, low with earlier time first on ties. |
| Filtering | `Scheduler.filter_tasks`, `Scheduler.tasks_for_day`, `Scheduler.build_daily_plan` | Filter by pet name, by done or not done, or both. The daily plan skips tasks once the owner's minutes run out and says why. |
| Conflict handling | `Scheduler.detect_conflicts` | Uses start and end times, so a 07:30 walk for 30 minutes overlaps a 07:45 task. Works across pets. Returns warnings and never crashes. Back to back tasks are fine. |
| Recurring tasks | `Task.mark_complete`, `Scheduler.mark_task_complete` | Daily adds one day and weekly adds seven days using timedelta. One time tasks just get marked done. |
| Free time | `Scheduler.next_available_slot` | Walks through the day from 07:00 to 21:00 and returns the first gap long enough. |
| Saving data | `Owner.save_json`, `Owner.load_json` | Pets and tasks are turned into plain dictionaries so they survive a restart. |

## Stretch features attempted

- Data persistence with JSON save and load, in the sidebar of the app
- Advanced scheduling: priority based daily plan plus the next available slot finder
- Professional UI: emoji status, tables, success and warning messages
- Agent workflow notes in ai_interactions.md

## 📸 Demo Walkthrough

1. Run `streamlit run app.py`. Set the owner name and minutes available today in the sidebar.
2. In Add a pet, type Mochi, pick dog, and click Add pet. Do the same for Luna the cat.
3. In Schedule a task, add a Morning walk for Mochi at 07:30 for 30 minutes, high priority, daily. Add a Breakfast for Mochi and one for Luna, both at 08:00. Add Play for Luna at 09:00 for 60 minutes, low priority.
4. Today's schedule shows all four tasks in time order. A yellow warning says the two breakfasts overlap.
5. Use Show pet and Show status to narrow the table.
6. Click Generate schedule. With 90 minutes the plan keeps the walk and both breakfasts and explains each pick. Play is listed as skipped because it needs 60 minutes and only 40 are left.
7. Pick Morning walk in Mark a task complete and click the button. It leaves today's list and a new walk is added for tomorrow.
8. Enter a length in Find a free slot to see the earliest open time.
9. Click Save to write pawpal_data.json and Load to bring it back later.

**Final UML:** see diagrams/uml_final.png
