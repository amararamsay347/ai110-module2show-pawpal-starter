from datetime import date, datetime

import streamlit as st

from display import task_emoji
from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan pet care tasks across all of your pets.")

# Session "vault": Streamlit re-runs this script on every interaction, so create
# the Owner and Scheduler only if they aren't already stored.
DATA_FILE = "data.json"
if "owner" not in st.session_state:
    # Restore pets and tasks from the last run if a saved file exists.
    st.session_state.owner = Owner.load_from_json(DATA_FILE) or Owner(name="Jordan", age=30)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# --- Owner ---
st.subheader("Owner")
new_owner_name = st.text_input("Owner name", value=owner.name)
if new_owner_name != owner.name:
    owner.name = new_owner_name
    owner.save_to_json(DATA_FILE)

# --- Pets ---
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        breed = st.text_input("Breed")
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if pet_name.strip():
            owner.add_pet(Pet(name=pet_name.strip(), breed=breed.strip(), age=int(age)))
            owner.save_to_json(DATA_FILE)
        else:
            st.warning("Give the pet a name.")

if owner.pets:
    st.table(
        [{"Name": p.name, "Breed": p.breed, "Age": p.age, "Tasks": len(p.tasks)} for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

# --- Tasks ---
st.subheader("Tasks")
if owner.pets:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", range(len(owner.pets)), format_func=lambda i: owner.pets[i].name)
        task_title = st.text_input("Task title", value="Morning walk")
        col1, col2, col3 = st.columns(3)
        with col1:
            task_date = st.date_input("Date", value=date.today())
        with col2:
            task_time = st.time_input("Time")
        with col3:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        col4, col5 = st.columns(2)
        with col4:
            priority = st.selectbox("Priority", list(Priority), index=2, format_func=lambda p: p.name.title())
        with col5:
            frequency = st.selectbox("Repeats", list(Frequency), format_func=lambda f: f.value.title())
        if st.form_submit_button("Add task"):
            owner.pets[pet_choice].add_task(
                Task(
                    name=task_title,
                    time=datetime.combine(task_date, task_time),
                    priority=priority,
                    frequency=frequency,
                    duration_minutes=int(duration),
                )
            )
            owner.save_to_json(DATA_FILE)
else:
    st.info("Add a pet before adding tasks.")

# Read through the owner so tasks from every pet show together.
sort_mode = st.radio("Sort tasks by", ["Time", "Priority, then time"], horizontal=True)
if sort_mode == "Time":
    all_tasks = scheduler.sort_by_time(owner.get_all_tasks())
else:
    all_tasks = scheduler.sort_by_priority_then_time(owner.get_all_tasks())

# Filters are applied by the Scheduler on top of the time-sorted list.
if all_tasks:
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        pet_filter = st.selectbox("Filter by pet", ["All pets"] + [p.name for p in owner.pets])
    with f_col2:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
    shown_tasks = scheduler.filter_tasks(
        all_tasks,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
        pet=None if pet_filter == "All pets" else pet_filter,
    )
else:
    shown_tasks = []

# Red alert for overlaps on every day that still has pending work.
conflict_alerts = [
    f"**{day:%b %d}** - {warning}"
    for day in sorted({t.time.date() for t in scheduler.filter_tasks(all_tasks, completed=False)})
    for warning in scheduler.conflict_warnings(owner, day)
]
if conflict_alerts:
    st.error(
        f"### ⚠️ WARNING: {len(conflict_alerts)} scheduling conflict(s) detected\n"
        "Adjust the times below so your pets aren't double-booked.\n\n"
        + "\n".join(f"- 🔴 {a}" for a in conflict_alerts),
        icon="🚨",
    )
elif all_tasks:
    st.success("No scheduling conflicts. Your pets' day looks good!", icon="✅")

# Let the user fix a conflict by moving or deleting one of the clashing tasks.
if conflict_alerts:
    clashing = {}
    for day in sorted({t.time.date() for t in scheduler.filter_tasks(all_tasks, completed=False)}):
        for t in scheduler.find_daily_conflicts(owner, day):
            clashing[t.id] = t
    with st.expander("🛠️ Resolve conflicts", expanded=True):
        st.caption("Move a clashing task to a new time, or delete it.")
        for t in clashing.values():
            st.write(f"**{t.name}** ({t.pet.name}) - {t.time:%Y-%m-%d %H:%M}, {t.duration_minutes} min")
            c_date, c_time, c_move, c_del = st.columns([2, 2, 1.5, 1.5])
            new_date = c_date.date_input("New date", value=t.time.date(), key=f"fix_date_{t.id}")
            new_time = c_time.time_input("New time", value=t.time.time(), key=f"fix_time_{t.id}")
            if c_move.button("Reschedule", key=f"fix_move_{t.id}"):
                t.reschedule(datetime.combine(new_date, new_time))
                owner.save_to_json(DATA_FILE)
                st.session_state.complete_msg = f"Moved '{t.name}' to {t.time:%Y-%m-%d %H:%M}."
                st.rerun()
            if c_del.button("Delete", key=f"fix_del_{t.id}"):
                t.pet.remove_task(t)
                owner.save_to_json(DATA_FILE)
                st.session_state.complete_msg = f"Deleted '{t.name}'."
                st.rerun()

if all_tasks:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total tasks", len(all_tasks))
    m2.metric("Pending", len(scheduler.filter_tasks(all_tasks, completed=False)))
    m3.metric("Completed", len(scheduler.filter_tasks(all_tasks, completed=True)))

PRIORITY_ICONS = {"LOWEST": "🟢", "LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "HIGHEST": "🔴"}

if shown_tasks:
    st.caption(f"Showing {len(shown_tasks)} of {len(all_tasks)} task(s), sorted by {'time of day' if sort_mode == 'Time' else 'priority, then time'}.")
    st.table(
        [
            {
                "Pet": t.pet.name,
                "Task": f"{task_emoji(t)} {t.name}",
                "Start": f"{t.time:%Y-%m-%d %H:%M}",
                "Minutes": t.duration_minutes,
                "Priority": f"{PRIORITY_ICONS.get(t.priority.name, '⚪')} {t.priority.name.title()}",
                "Repeats": t.frequency.value.title(),
                "Status": "✅ Done" if t.completed else "⏳ Pending",
            }
            for t in shown_tasks
        ]
    )
elif all_tasks:
    st.info("No tasks match those filters.")
elif owner.pets:
    st.info("No tasks yet. Add one above.")

# Message from the previous click; shown after the rerun that refreshes the table.
if "complete_msg" in st.session_state:
    st.success(st.session_state.pop("complete_msg"))

pending = scheduler.filter_tasks(all_tasks, completed=False)
if pending:
    st.markdown("**Mark complete**")
    for t in pending:
        col_label, col_btn = st.columns([4, 1])
        with col_label:
            st.write(f"{t.time:%Y-%m-%d %H:%M} - {t.name} ({t.pet.name})")
        with col_btn:
            if st.button("Complete", key=f"complete_{t.id}"):
                nxt = t.mark_complete()  # recurring tasks create their next occurrence
                owner.save_to_json(DATA_FILE)
                msg = f"Completed '{t.name}' for {t.pet.name}."
                if nxt is not None:
                    msg += f" Next one scheduled for {nxt.time:%Y-%m-%d %H:%M}."
                st.session_state.complete_msg = msg
                st.rerun()

st.divider()

# --- Schedule ---
st.subheader("Build Schedule")
plan_day = st.date_input("Plan for", value=date.today(), key="plan_day")

if st.button("Generate schedule"):
    plan = scheduler.build_daily_schedule(owner, plan_day)
    if not plan:
        st.info("Nothing to schedule for that day.")
    else:
        st.success(f"{len(plan)} task(s) planned for {plan_day:%B %d, %Y}.")
        for task in plan:
            st.markdown(
                f"**{task.time:%H:%M}** - {task.name} ({task.pet.name})  \n"
                f"{scheduler.explain_choice(task, plan)}"
            )
    day_warnings = scheduler.conflict_warnings(owner, plan_day)
    if day_warnings:
        st.error(
            f"### ⚠️ WARNING: {len(day_warnings)} conflict(s) on {plan_day:%B %d}\n\n"
            + "\n".join(f"- 🔴 {w}" for w in day_warnings),
            icon="🚨",
        )
