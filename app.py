from datetime import date, time

import streamlit as st

from pawpal_system import (
    Category,
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Species,
    Task,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# st.session_state behaves like a dict that survives Streamlit's top-to-bottom reruns.
# Only create the Owner if the "vault" doesn't already hold one.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan", available_start=time(8, 0), available_end=time(18, 0)
    )
owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

col_a, col_b = st.columns(2)
with col_a:
    avail_start = st.time_input("Available from", value=owner.available_start)
with col_b:
    avail_end = st.time_input("Available until", value=owner.available_end)
try:
    owner.set_availability(avail_start, avail_end)
except ValueError as e:
    st.error(f"{e}. Keeping {owner.available_start:%H:%M}-{owner.available_end:%H:%M}.")

use_earliest = st.checkbox(
    "Don't start before a certain time", value=owner.preferences.earliest_start is not None
)
if use_earliest:
    owner.preferences.earliest_start = st.time_input(
        "Earliest start", value=owner.preferences.earliest_start or time(9, 0)
    )
else:
    owner.preferences.earliest_start = None

st.subheader("Add a Pet")
with st.form("add_pet", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", [s.value for s in Species])
    if st.form_submit_button("Add pet"):
        if pet_name.strip():
            owner.add_pet(Pet(name=pet_name.strip(), species=Species(species)))
        else:
            st.error("Pet name cannot be empty.")

if owner.pets:
    st.write("Your pets:")
    st.table([{"name": p.name, "species": p.species.value, "tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
if owner.pets:
    pet_by_id = {p.id: p for p in owner.pets}
    col0, col1, col2, col3 = st.columns(4)
    with col0:
        pet_id = st.selectbox("Pet", list(pet_by_id), format_func=lambda i: pet_by_id[i].name)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", [p.value for p in Priority], index=1)

    col4, col5, col6 = st.columns(3)
    with col4:
        category = st.selectbox("Category", [c.value for c in Category], index=len(Category) - 1)
    with col5:
        frequency = st.selectbox("Frequency", [f.value for f in Frequency])
    with col6:
        weekday = None
        if frequency == Frequency.WEEKLY.value:
            weekday = st.selectbox(
                "Weekday",
                range(7),
                format_func=lambda d: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d],
            )

    col7, col8 = st.columns(2)
    with col7:
        use_fixed = st.checkbox("Fixed time")
        fixed_time = st.time_input("At", value=time(9, 0)) if use_fixed else None
    with col8:
        notes = st.text_input("Notes", value="")

    if st.button("Add task"):
        try:
            pet_by_id[pet_id].add_task(
                Task(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=Priority(priority),
                    category=Category(category),
                    frequency=Frequency(frequency),
                    weekday=weekday,
                    fixed_time=fixed_time,
                    notes=notes,
                )
            )
        except ValueError as e:
            st.error(str(e))

    rows = [
        {
            "pet": pet.name,
            "title": task.title,
            "duration_minutes": task.duration_minutes,
            "priority": task.priority.value,
            "category": task.category.value,
            "frequency": task.frequency.value,
            "fixed_time": f"{task.fixed_time:%H:%M}" if task.fixed_time else "",
            "notes": task.notes,
        }
        for pet, task in owner.get_all_tasks()
    ]
    if rows:
        st.write("Current tasks:")
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("Add a pet before adding tasks.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    plan = Scheduler().build_plan(owner, date.today())
    if plan.scheduled:
        st.success(f"Scheduled {len(plan.scheduled)} task(s) for {plan.day:%A, %B %d}.")
        st.table(
            [
                {
                    "time": f"{e.start:%H:%M}-{e.end:%H:%M}",
                    "pet": e.pet.name,
                    "task": e.task.title,
                    "why": e.reason,
                }
                for e in plan.scheduled
            ]
        )
    else:
        st.info("Nothing to schedule today.")
    for c in plan.conflicts:
        st.warning(c.message)
    for u in plan.unscheduled:
        st.warning(f"Could not schedule {u.pet.name}'s {u.task.title}: {u.reason}")
