from datetime import date, datetime

import streamlit as st

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan pet care tasks across all of your pets.")

# Session "vault": Streamlit re-runs this script on every interaction, so create
# the Owner and Scheduler only if they aren't already stored.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", age=30)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# --- Owner ---
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

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
else:
    st.info("Add a pet before adding tasks.")

# Read through the owner so tasks from every pet show together.
all_tasks = scheduler.sort_by_time(owner.get_all_tasks())
if all_tasks:
    st.table(
        [
            {
                "Pet": t.pet.name,
                "Task": t.name,
                "Start": f"{t.time:%Y-%m-%d %H:%M}",
                "Minutes": t.duration_minutes,
                "Priority": t.priority.name.title(),
                "Repeats": t.frequency.value.title(),
                "Done": t.completed,
            }
            for t in all_tasks
        ]
    )
elif owner.pets:
    st.info("No tasks yet. Add one above.")

# Message from the previous click; shown after the rerun that refreshes the table.
if "complete_msg" in st.session_state:
    st.success(st.session_state.pop("complete_msg"))

pending = [t for t in all_tasks if not t.completed]
if pending:
    st.markdown("**Mark complete**")
    for t in pending:
        col_label, col_btn = st.columns([4, 1])
        with col_label:
            st.write(f"{t.time:%Y-%m-%d %H:%M} - {t.name} ({t.pet.name})")
        with col_btn:
            if st.button("Complete", key=f"complete_{t.id}"):
                nxt = t.mark_complete()  # recurring tasks create their next occurrence
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
    for warning in scheduler.conflict_warnings(owner, plan_day):
        st.warning(warning)
