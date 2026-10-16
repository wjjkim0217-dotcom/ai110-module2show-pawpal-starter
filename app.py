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
    TaskStatus,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}

st.title("🐾 PawPal+")
st.caption("Plan your pets' care around your day: priorities, fixed times, and conflicts handled for you.")

# st.session_state survives Streamlit's top-to-bottom reruns; create the Owner only once.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan", available_start=time(8, 0), available_end=time(18, 0)
    )
owner: Owner = st.session_state.owner
scheduler = Scheduler()

# ---------------------------------------------------------------- Owner
with st.expander("👤 Owner & availability", expanded=not owner.pets):
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

    if st.checkbox(
        "Don't start before a certain time", value=owner.preferences.earliest_start is not None
    ):
        owner.preferences.earliest_start = st.time_input(
            "Earliest start", value=owner.preferences.earliest_start or time(9, 0)
        )
    else:
        owner.preferences.earliest_start = None

# ---------------------------------------------------------------- Pets
st.subheader("🐶 Pets")
with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="bottom")
    pet_name = c1.text_input("Pet name", value="Mochi")
    species = c2.selectbox("Species", [s.value for s in Species])
    if c3.form_submit_button("Add pet", use_container_width=True):
        if pet_name.strip():
            owner.add_pet(Pet(name=pet_name.strip(), species=Species(species)))
        else:
            st.error("Pet name cannot be empty.")

if not owner.pets:
    st.info("No pets yet. Add one above.")
for pet in list(owner.pets):
    c1, c2 = st.columns([5, 1], vertical_alignment="center")
    c1.write(f"**{pet.name}** · {pet.species.value} · {len(pet.tasks)} task(s)")
    if c2.button("Remove", key=f"rm_pet_{pet.id}"):
        owner.remove_pet(pet.id)
        st.rerun()

# ---------------------------------------------------------------- Tasks
st.subheader("📋 Tasks")
if owner.pets:
    pet_by_id = {p.id: p for p in owner.pets}
    with st.form("add_task", clear_on_submit=False):
        c0, c1, c2, c3 = st.columns(4)
        pet_id = c0.selectbox("Pet", list(pet_by_id), format_func=lambda i: pet_by_id[i].name)
        task_title = c1.text_input("Task title", value="Morning walk")
        duration = c2.number_input("Minutes", min_value=1, max_value=240, value=20)
        priority = c3.selectbox("Priority", [p.value for p in Priority], index=1)

        c4, c5, c6 = st.columns(3)
        category = c4.selectbox("Category", [c.value for c in Category], index=len(Category) - 1)
        frequency = c5.selectbox("Frequency", [f.value for f in Frequency])
        weekday = c6.selectbox(
            "Weekday (weekly tasks)", range(7), format_func=lambda d: WEEKDAYS[d]
        )

        c7, c8, c9 = st.columns(3, vertical_alignment="bottom")
        use_fixed = c7.checkbox("Fixed time")
        fixed_at = c8.time_input("At", value=time(9, 0))
        notes = c9.text_input("Notes", value="")

        if st.form_submit_button("Add task"):
            try:
                pet_by_id[pet_id].add_task(
                    Task(
                        title=task_title.strip(),
                        duration_minutes=int(duration),
                        priority=Priority(priority),
                        category=Category(category),
                        frequency=Frequency(frequency),
                        weekday=weekday if frequency == Frequency.WEEKLY.value else None,
                        fixed_time=fixed_at if use_fixed else None,
                        notes=notes,
                    )
                )
                st.success(f"Added '{task_title}' for {pet_by_id[pet_id].name}.")
                # Immediate feedback: does the new task clash with anything on the chosen day?
                new_plan = scheduler.build_plan(owner, date.today())
                for c in new_plan.conflicts:
                    st.warning(c.message)
            except ValueError as e:
                st.error(str(e))

    # ------------------------------------------------------------ view controls
    plan_day = st.date_input("Day", value=date.today(), help="Status and the schedule are for this day.")
    f1, f2, f3 = st.columns(3)
    pet_filter = f1.selectbox("Filter by pet", ["All pets"] + [p.name for p in owner.pets])
    status_filter = f2.selectbox("Filter by status", ["All", "Pending", "Done"])
    sort_by_time = f3.checkbox("Sort by fixed time", help="Tasks without a fixed time go last.")

    status = {"All": None, "Pending": TaskStatus.PENDING, "Done": TaskStatus.DONE}[status_filter]
    pairs = owner.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter, status=status, day=plan_day
    )
    if sort_by_time:
        by_id = {t.id: pet for pet, t in pairs}
        pairs = [(by_id[t.id], t) for t in scheduler.sort_by_time([t for _, t in pairs])]

    if not pairs:
        st.info("No tasks match these filters.")
    else:
        def recurrence(t: Task) -> str:
            if t.frequency is Frequency.WEEKLY and t.weekday is not None:
                return f"weekly ({WEEKDAYS[t.weekday]})"
            return t.frequency.value

        st.caption(f"{len(pairs)} task(s) · {sum(t.duration_minutes for _, t in pairs)} min total")
        st.table(
            [
                {
                    "Status": "✅ Done" if t.is_complete(plan_day) else "⏳ Pending",
                    "Time": f"{t.fixed_time:%H:%M}" if t.fixed_time else "flexible",
                    "Pet": p.name,
                    "Task": t.title,
                    "Min": t.duration_minutes,
                    "Priority": PRIORITY_BADGE.get(t.priority.value, t.priority.value),
                    "Repeats": recurrence(t),
                }
                for p, t in pairs
            ]
        )

        # Actions: one picker instead of a button pair per row.
        a1, a2, a3 = st.columns([4, 1.5, 1.5], vertical_alignment="bottom")
        choice = a1.selectbox(
            "Update a task",
            [t.id for _, t in pairs],
            format_func=lambda i: next(f"{p.name} – {t.title}" for p, t in pairs if t.id == i),
        )
        pet, task = next((p, t) for p, t in pairs if t.id == choice)
        can_complete = task.is_due(plan_day) and not task.is_complete(plan_day)
        if a2.button("✅ Mark done", disabled=not can_complete, help=None if can_complete else "Not due, or already done, on this day"):
            renewed = scheduler.mark_complete(owner, task.id, plan_day)
            if renewed:
                st.toast(f"Done! Next '{renewed.title}' is due {renewed.due_date:%a %b %d}.")
            st.rerun()
        if a3.button("🗑️ Delete"):
            pet.remove_task(task.id)
            st.rerun()
else:
    st.info("Add a pet before adding tasks.")
    plan_day = date.today()

# ---------------------------------------------------------------- Schedule
st.divider()
st.subheader("🗓️ Today's schedule")

# The plan is rebuilt on every rerun once requested, so it never goes stale
# after completing/adding/deleting a task.
if st.button("Generate schedule", type="primary"):
    st.session_state.show_plan = True

if st.session_state.get("show_plan"):
    full_plan = scheduler.build_plan(owner, plan_day)  # free-slot search needs everyone's tasks
    view = st.radio(
        "Show", ["All pets"] + [p.name for p in owner.pets], horizontal=True, key="plan_view"
    )
    plan = full_plan if view == "All pets" else full_plan.for_pet(view)

    if plan.scheduled:
        mins = sum(e.task.duration_minutes for e in plan.scheduled)
        st.success(f"{len(plan.scheduled)} task(s) scheduled for {plan.day:%A, %B %d} · {mins} min total.")
        st.table(
            [
                {
                    "Time": f"{e.start:%H:%M}–{e.end:%H:%M}",
                    "Pet": e.pet.name,
                    "Task": e.task.title,
                    "Priority": e.task.priority.value,
                    "Why": e.reason,
                }
                for e in plan.scheduled
            ]
        )
    else:
        st.info("Nothing to schedule for this day.")

    if plan.conflicts:
        # Lead with the consequence, then per conflict: what clashes, why it matters, what to do.
        st.error(
            f"**{len(plan.conflicts)} scheduling conflict(s).** These tasks are fixed at "
            "overlapping times, so they can't all happen as planned.",
            icon="🚨",
        )
        for c in plan.conflicts:
            a, b = c.first, c.second
            with st.container(border=True):
                st.markdown(
                    f"**{a.pet.name}: {a.task.title}** ({a.start:%H:%M}–{a.end:%H:%M})  \n"
                    f"clashes with  \n"
                    f"**{b.pet.name}: {b.task.title}** ({b.start:%H:%M}–{b.end:%H:%M})"
                )
                if c.same_pet:
                    st.warning("Same pet, same time: this may be a duplicate. Consider deleting one.", icon="🐾")
                if c.suggestion:
                    st.success(
                        f"**Fix:** move **{b.task.title}** to **{c.suggestion:%H:%M}** "
                        "(next opening that fits it).",
                        icon="💡",
                    )
                else:
                    st.warning(
                        f"No opening left today for **{b.task.title}**. Shorten it, "
                        "widen your availability, or move it to another day.",
                        icon="💡",
                    )

    st.markdown("#### 🔎 Find a free slot")
    s1, s2, s3 = st.columns(3, vertical_alignment="bottom")
    need = s1.number_input("Minutes needed", min_value=1, max_value=240, value=30)
    after = s2.time_input("Not before", value=owner.available_start, key="slot_after")
    if s3.button("Find slot"):
        slot = scheduler.next_free_slot(owner, full_plan, plan_day, int(need), after)
        if slot:
            st.success(f"Next free {int(need)}-minute slot starts at {slot:%H:%M}.")
        else:
            st.warning("No free slot that long is left on this day.")

    if plan.unscheduled:
        st.markdown("#### ❌ Couldn't fit")
        for u in plan.unscheduled:
            st.error(f"{u.pet.name}'s **{u.task.title}** ({u.task.duration_minutes} min): {u.reason}")
