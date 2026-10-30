import os
from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler, to_hhmm

DATA_FILE = "pawpal_data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan your pets' care around the time you actually have.")

# Session state keeps the Owner alive across reruns, so pets and tasks are not lost
# every time a button is clicked.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=90)
owner = st.session_state.owner
scheduler = Scheduler(owner)

# Owner settings
with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)
    owner.available_minutes = st.number_input(
        "Minutes available today", min_value=10, max_value=600,
        value=owner.available_minutes, step=5)
    st.divider()
    col_save, col_load = st.columns(2)
    if col_save.button("💾 Save"):
        owner.save_json(DATA_FILE)
        st.success("Saved")
    if col_load.button("📂 Load"):
        if os.path.exists(DATA_FILE):
            st.session_state.owner = Owner.load_json(DATA_FILE)
            st.rerun()
        else:
            st.info("No saved data yet")

# Add a pet
st.subheader("1. Add a pet")
with st.form("add_pet", clear_on_submit=True):
    c1, c2 = st.columns(2)
    pet_name = c1.text_input("Pet name")
    species = c2.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        try:
            if not pet_name.strip():
                raise ValueError("Enter a pet name")
            owner.add_pet(Pet(pet_name.strip(), species))
            st.success(f"Added {pet_name.strip()}")
        except ValueError as err:
            st.error(str(err))

if owner.pets:
    st.write("Pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

# Add a task
st.subheader("2. Schedule a task")
if owner.pets:
    with st.form("add_task", clear_on_submit=True):
        c1, c2 = st.columns(2)
        task_pet = c1.selectbox("For pet", [p.name for p in owner.pets])
        description = c2.text_input("Task", value="Morning walk")
        c3, c4, c5, c6 = st.columns(4)
        start = c3.time_input("Time", value=time(8, 0), step=300)
        duration = c4.number_input("Minutes", min_value=1, max_value=240, value=20)
        priority = c5.selectbox("Priority", ["high", "medium", "low"])
        frequency = c6.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            try:
                task = Task(description.strip() or "Task", start.strftime("%H:%M"),
                            int(duration), priority, frequency)
                owner.get_pet(task_pet).add_task(task)
                st.success(f"Added {task.description} for {task_pet} at {task.time}")
            except ValueError as err:
                st.error(str(err))

# Today's schedule
st.subheader("3. Today's schedule")
f1, f2 = st.columns(2)
pet_filter = f1.selectbox("Show pet", ["All"] + [p.name for p in owner.pets])
status_filter = f2.selectbox("Show status", ["Pending", "Done", "All"])
completed = {"Pending": False, "Done": True, "All": None}[status_filter]
pairs = scheduler.filter_tasks(None if pet_filter == "All" else pet_filter, completed)
today = scheduler.tasks_for_day(include_completed=True)
pairs = scheduler.sort_by_time([pair for pair in pairs if pair in today])

if pairs:
    st.table([{
        "Time": f"{t.time} to {to_hhmm(t.end)}", "Pet": p.name, "Task": t.description,
        "Priority": t.priority, "Repeats": t.frequency, "Status": "✅ done" if t.completed else "⏳ todo",
    } for p, t in pairs])
else:
    st.info("No tasks match these filters for today.")

for warning in scheduler.detect_conflicts():
    st.warning(f"⚠️ {warning}. Consider moving one of these tasks.")

pending = scheduler.sort_by_time(scheduler.tasks_for_day())
if pending:
    labels = [f"{t.time} {p.name}: {t.description}" for p, t in pending]
    choice = st.selectbox("Mark a task complete", labels)
    if st.button("Mark complete"):
        pet, task = pending[labels.index(choice)]
        next_task = scheduler.mark_task_complete(pet, task)
        if next_task:
            st.success(f"Done. Next {task.description} added for {next_task.due_date}.")
        else:
            st.success(f"Done: {task.description}")
        st.rerun()

# Daily plan
st.subheader("4. Build today's plan")
if st.button("Generate schedule"):
    plan, skipped = scheduler.build_daily_plan()
    if plan:
        used = sum(t.duration_minutes for _, t, _ in plan)
        st.success(f"Planned {len(plan)} tasks using {used} of {owner.available_minutes} minutes.")
        st.table([{"Time": t.time, "Pet": p.name, "Task": t.description, "Why": reason}
                  for p, t, reason in plan])
    else:
        st.info("Nothing to plan for today.")
    for p, t, reason in skipped:
        st.warning(f"{p.name}: {t.description} was {reason}.")

# Free time finder
st.subheader("5. Find a free slot")
need = st.number_input("How many minutes do you need?", min_value=5, max_value=240, value=30, step=5)
slot = scheduler.next_available_slot(int(need))
st.write(f"Next free {need} minute slot today: **{slot}**" if slot else "No free slot that long today.")
