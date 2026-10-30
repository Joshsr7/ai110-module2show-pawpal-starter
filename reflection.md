# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My first UML had four classes. Task holds one care activity with a description, time, length in minutes, priority, repeat setting, and a done flag. Pet holds a name, species, and its list of tasks. Owner holds the owner's name, the minutes they have each day, and their pets. Scheduler is the brain. It takes an Owner, reads every task across every pet, and sorts, filters, checks conflicts, and builds the daily plan.

The three core actions I designed around were adding a pet, scheduling a task, and seeing today's plan.

**b. Design changes**

Yes. The final design is in diagrams/uml_final.mmd and the first draft is in diagrams/uml_draft.mmd.

- I added a due_date to Task. Without a date, a daily task marked done had nowhere to go, so recurrence could not work.
- I added start and end properties to Task so conflict checks and the free slot finder could do math in minutes instead of comparing text.
- I added sort_by_priority, tasks_for_day, mark_task_complete, and next_available_slot to Scheduler.
- I added save and load methods to Owner for JSON so the app keeps data between runs.

The biggest reason for these changes was that the draft had no idea of days, and almost every smart feature needed one.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler looks at the owner's minutes for the day, each task's priority, each task's time and length, the due date, and whether the task is already done. Time available and priority mattered most because the scenario is a busy owner who cannot do everything. Medication and meals should never lose to a play session.

**b. Tradeoffs**

The daily plan is greedy. It takes tasks from highest priority down and keeps each one that still fits. This can leave a few minutes unused when a smarter mix of tasks would fill them, but it is easy to explain to the owner and it never drops a high priority task to squeeze in two low ones.

Conflict detection also only warns. It does not move tasks for the owner. I think that is right for pets because the owner knows if two feedings at 08:00 is really a problem or not.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI to turn my UML into class skeletons, to brainstorm which scheduling features made sense, to write and explain tests, and to help connect the classes to Streamlit with session_state. The most helpful prompts were specific ones that named the file and the method, like asking how detect_conflicts should handle two tasks that touch but do not overlap.

**b. Judgment and verification**

The first sorting idea was to sort on the HH:MM text directly with a lambda. I tested it and Python put 10:00 before 9:05 because it compares text one character at a time. I changed the sort key to minutes after midnight and wrote a test for that exact case. I also did not take the idea of having the scheduler move conflicting tasks automatically, because it hid decisions from the owner and made the code harder to test. I checked every change by running main.py and pytest before moving on.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 20 tests. They cover marking tasks done, adding tasks, sorting by time and priority, filtering, daily and weekly repeats, one time tasks, conflicts at the same time and with overlapping lengths, back to back tasks, done tasks not causing conflicts, the plan staying inside the time budget, an owner with no tasks, the free slot finder, bad times, duplicate pet names, and saving to JSON. These matter because the plan is only useful if the order is right, nothing important gets dropped, and repeating tasks do not disappear.

**b. Confidence**

Four out of five stars. All tests pass and the logic file has 95 percent coverage. Next I would test tasks that run past midnight, two pets with the same name in different cases in the UI, and loading a JSON file that was edited by hand.

---

## 5. Reflection

**a. What went well**

Keeping all the logic in pawpal_system.py worked well. The CLI demo, the tests, and the Streamlit app all use the same classes, so when something worked in main.py it worked in the app too.

**b. What you would improve**

I would let the owner edit or delete tasks from the app, let them set their own day start and end for the free slot finder, and make the plan smarter about filling leftover minutes.

**c. Key takeaway**

Designing first saved time, but the design still had to change once real features needed things like dates. AI was fast at writing code, but I had to be the one who decided what the system should do and who proved it worked with tests.
