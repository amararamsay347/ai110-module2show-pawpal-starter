from datetime import datetime

from pawpal_system import Pet, Priority, Task


def make_task() -> Task:
    return Task(name="Morning walk", time=datetime(2026, 10, 1, 8, 0), priority=Priority.HIGH)


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", breed="Golden Retriever", age=5)
    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1


from datetime import date, timedelta

from pawpal_system import Frequency, Owner, Scheduler


def make_owner():
    owner = Owner(name="Alice", age=30)
    buddy = Pet(name="Buddy", breed="Lab", age=3)
    max_ = Pet(name="Max", breed="Beagle", age=4)
    owner.add_pet(buddy)
    owner.add_pet(max_)
    return owner, buddy, max_


def test_sort_by_time_orders_chronologically():
    owner, buddy, max_ = make_owner()
    late = Task("Late", datetime(2026, 10, 1, 17, 0), Priority.LOW)
    early = Task("Early", datetime(2026, 10, 1, 7, 0), Priority.LOW)
    buddy.add_task(late)
    max_.add_task(early)

    assert Scheduler().sort_by_time(owner.get_all_tasks()) == [early, late]


def test_filter_by_pet_name_and_status():
    owner, buddy, max_ = make_owner()
    a = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH)
    b = Task("Feed", datetime(2026, 10, 1, 9, 0), Priority.HIGH)
    buddy.add_task(a)
    max_.add_task(b)
    a.mark_complete()
    s = Scheduler()

    assert s.get_tasks(owner, pet="buddy") == [a]
    assert s.get_tasks(owner, completed=False) == [b]
    assert s.get_tasks(owner, pet=max_, completed=True) == []


def test_completing_daily_task_creates_next_day_task():
    owner, buddy, _ = make_owner()
    t = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, frequency=Frequency.DAILY)
    buddy.add_task(t)

    Scheduler().complete_task(owner, t.id)

    assert len(buddy.tasks) == 2
    nxt = [x for x in buddy.tasks if x is not t][0]
    assert nxt.time == t.time + timedelta(days=1)
    assert nxt.completed is False and nxt.frequency == Frequency.DAILY


def test_completing_one_off_task_creates_nothing():
    owner, buddy, _ = make_owner()
    t = Task("Vet", datetime(2026, 10, 1, 8, 0), Priority.HIGH)
    buddy.add_task(t)

    Scheduler().complete_task(owner, t.id)

    assert len(buddy.tasks) == 1


def test_conflict_warning_across_pets_and_none_when_clear():
    owner, buddy, max_ = make_owner()
    buddy.add_task(Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, duration_minutes=60))
    max_.add_task(Task("Groom", datetime(2026, 10, 1, 8, 30), Priority.LOW, duration_minutes=30))
    s = Scheduler()
    day = date(2026, 10, 1)

    warnings = s.conflict_warnings(owner, day)
    assert len(warnings) == 1 and "Buddy" in warnings[0] and "Max" in warnings[0]
    assert "overlap, different pets" in warnings[0]
    assert s.conflict_warnings(owner, date(2026, 10, 2)) == []


def test_filter_tasks_on_any_list_combines_filters():
    owner, buddy, max_ = make_owner()
    a = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH)
    b = Task("Feed", datetime(2026, 10, 1, 9, 0), Priority.HIGH)
    c = Task("Groom", datetime(2026, 10, 1, 10, 0), Priority.LOW)
    buddy.add_task(a)
    buddy.add_task(b)
    max_.add_task(c)
    a.mark_complete()
    s = Scheduler()
    day_tasks = owner.get_daily_tasks(date(2026, 10, 1))

    assert s.filter_tasks(day_tasks, completed=False, pet="BUDDY") == [b]
    assert s.filter_tasks(day_tasks, completed=True) == [a]
    assert s.filter_tasks(day_tasks) == day_tasks
    assert s.filter_tasks(day_tasks, pet="Nobody") == []


def test_task_mark_complete_directly_creates_next_weekly_task():
    _, buddy, _ = make_owner()
    t = Task("Bath", datetime(2026, 10, 1, 18, 0), Priority.LOW, frequency=Frequency.WEEKLY)
    buddy.add_task(t)

    nxt = t.mark_complete()

    assert nxt is not None and nxt.pet is buddy
    assert nxt.time == t.time + timedelta(weeks=1)
    assert nxt.frequency == Frequency.WEEKLY and not nxt.completed


def test_completing_twice_does_not_duplicate_recurring_task():
    _, buddy, _ = make_owner()
    t = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, frequency=Frequency.DAILY)
    buddy.add_task(t)

    t.mark_complete()
    assert t.mark_complete() is None

    assert len(buddy.tasks) == 2


def test_recurring_task_without_pet_does_not_crash():
    t = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, frequency=Frequency.DAILY)

    assert t.mark_complete() is None and t.completed


def test_biweekly_completion_creates_task_two_weeks_later():
    _, buddy, _ = make_owner()
    t = Task("Nail trim", datetime(2026, 10, 1, 9, 0), Priority.LOW, frequency=Frequency.BIWEEKLY)
    buddy.add_task(t)

    nxt = t.mark_complete()

    assert nxt.time == datetime(2026, 10, 15, 9, 0)
    assert t.occurs_on(date(2026, 10, 1)) is True
    probe = Task("x", datetime(2026, 10, 1, 9, 0), Priority.LOW, frequency=Frequency.BIWEEKLY)
    assert probe.occurs_on(date(2026, 10, 15)) and not probe.occurs_on(date(2026, 10, 8))


def test_monthly_completion_clamps_to_short_months_and_rolls_year():
    _, buddy, _ = make_owner()
    jan31 = Task("Flea meds", datetime(2026, 1, 31, 9, 0), Priority.HIGH, frequency=Frequency.MONTHLY)
    dec15 = Task("Vet check", datetime(2026, 12, 15, 9, 0), Priority.HIGH, frequency=Frequency.MONTHLY)
    buddy.add_task(jan31)
    buddy.add_task(dec15)

    assert jan31.mark_complete().time == datetime(2026, 2, 28, 9, 0)
    assert dec15.mark_complete().time == datetime(2027, 1, 15, 9, 0)


def test_monthly_occurs_on_same_day_each_month():
    t = Task("Flea meds", datetime(2026, 1, 31, 9, 0), Priority.HIGH, frequency=Frequency.MONTHLY)

    assert t.occurs_on(date(2026, 2, 28)) and t.occurs_on(date(2026, 3, 31))
    assert not t.occurs_on(date(2026, 3, 30)) and not t.occurs_on(date(2025, 12, 31))


def test_same_start_time_warnings_for_same_pet_and_different_pets():
    owner, buddy, max_ = make_owner()
    at = datetime(2026, 10, 1, 8, 0)
    buddy.add_task(Task("Walk", at, Priority.HIGH))
    buddy.add_task(Task("Feed", at, Priority.HIGH))
    max_.add_task(Task("Groom", at, Priority.LOW))

    warnings = Scheduler().conflict_warnings(owner, date(2026, 10, 1))

    assert len(warnings) == 3  # every pair among the three tasks
    assert all("same start time" in w for w in warnings)
    assert sum("same pet" in w for w in warnings) == 1
    assert sum("different pets" in w for w in warnings) == 2


def test_back_to_back_tasks_are_not_conflicts():
    owner, buddy, max_ = make_owner()
    buddy.add_task(Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, duration_minutes=30))
    max_.add_task(Task("Feed", datetime(2026, 10, 1, 8, 30), Priority.HIGH))

    assert Scheduler().conflict_warnings(owner, date(2026, 10, 1)) == []


def build_plan():
    owner, buddy, max_ = make_owner()
    vet = Task("Vet", datetime(2026, 10, 1, 14, 0), Priority.HIGHEST, duration_minutes=60)
    walk = Task("Walk", datetime(2026, 10, 1, 9, 0), Priority.HIGH, reason="Buddy needs exercise")
    feed = Task("Feed", datetime(2026, 10, 1, 8, 0), Priority.HIGH, duration_minutes=30)
    groom = Task("Groom", datetime(2026, 10, 1, 14, 30), Priority.LOW, duration_minutes=45)
    for t in (vet, walk, groom):
        buddy.add_task(t)
    max_.add_task(feed)
    s = Scheduler()
    return s, s.build_daily_schedule(owner, date(2026, 10, 1)), (vet, walk, feed, groom)


def test_explain_without_plan_keeps_simple_sentence():
    walk = Task("Walk", datetime(2026, 10, 1, 9, 0), Priority.HIGH, reason="Buddy needs exercise")

    assert Scheduler().explain_choice(walk) == (
        "'Walk' has high priority, is scheduled for 09:00 (once) because Buddy needs exercise."
    )


def test_explain_with_plan_gives_rank_and_reason():
    s, plan, (vet, walk, feed, groom) = build_plan()
    assert [t.name for t in plan] == ["Vet", "Feed", "Walk", "Groom"]

    assert "#1 of 4" in s.explain_choice(vet, plan) and "highest priority of the day" in s.explain_choice(vet, plan)
    tie = s.explain_choice(walk, plan)
    assert "#3 of 4" in tie and "ties with 'Feed' on priority" in tie and "starts earlier" in tie
    assert "'Walk' comes first because it has higher priority (high)" in s.explain_choice(groom, plan)


def test_explain_mentions_overlaps():
    s, plan, (vet, walk, feed, groom) = build_plan()

    assert "overlaps with 'Groom'" in s.explain_choice(vet, plan)
    assert "overlaps" not in s.explain_choice(walk, plan)


# --- Sorting: happy path and edge cases ---

def test_sort_by_time_handles_out_of_order_input_and_leaves_original_untouched():
    owner, buddy, _ = make_owner()
    ten = Task("Ten", datetime(2026, 10, 1, 10, 0), Priority.LOW)
    nine = Task("Nine", datetime(2026, 10, 1, 9, 0), Priority.LOW)
    midnight = Task("Midnight", datetime(2026, 10, 1, 0, 0), Priority.LOW)
    late = Task("Late", datetime(2026, 10, 1, 23, 59), Priority.LOW)
    original = [ten, late, midnight, nine]
    for t in original:
        buddy.add_task(t)

    result = Scheduler().sort_by_time(original)

    assert result == [midnight, nine, ten, late]  # "10:00" after "09:00", not alphabetical
    assert original == [ten, late, midnight, nine]


def test_sort_by_time_empty_and_single_task():
    s = Scheduler()
    only = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH)

    assert s.sort_by_time([]) == []
    assert s.sort_by_time([only]) == [only]


def test_sort_by_time_keeps_input_order_for_identical_times():
    at = datetime(2026, 10, 1, 8, 0)
    first = Task("First", at, Priority.LOW)
    second = Task("Second", at, Priority.HIGH)

    assert Scheduler().sort_by_time([first, second]) == [first, second]
    assert Scheduler().sort_by_time([second, first]) == [second, first]


# --- Empty owners and pets ---

def test_pet_with_no_tasks_and_owner_with_no_pets_produce_empty_results():
    s = Scheduler()
    day = date(2026, 10, 1)
    owner, buddy, _ = make_owner()  # pets exist, but neither has tasks
    nobody = Owner(name="Solo", age=40)

    for o in (owner, nobody):
        assert o.get_all_tasks() == []
        assert s.get_tasks(o) == []
        assert s.build_daily_schedule(o, day) == []
        assert s.find_daily_conflicts(o, day) == []
        assert s.conflict_warnings(o, day) == []
    assert s.sort_by_time(buddy.tasks) == []
    assert s.detect_conflicts([]) == []


# --- Recurrence: daily ---

def test_daily_completion_rolls_over_year_end_and_keeps_pet_and_details():
    _, buddy, _ = make_owner()
    t = Task(
        "Walk", datetime(2026, 12, 31, 8, 0), Priority.HIGH, frequency=Frequency.DAILY,
        duration_minutes=45, description="Around the block", reason="exercise",
    )
    buddy.add_task(t)

    nxt = t.mark_complete()

    assert nxt.time == datetime(2027, 1, 1, 8, 0)
    assert nxt.pet is buddy and nxt in buddy.tasks
    assert (nxt.name, nxt.priority, nxt.duration_minutes) == ("Walk", Priority.HIGH, 45)
    assert (nxt.description, nxt.reason) == ("Around the block", "exercise")
    assert nxt.completed is False and nxt.id != t.id


def test_daily_series_keeps_exactly_one_pending_task():
    owner, buddy, _ = make_owner()
    t = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, frequency=Frequency.DAILY)
    buddy.add_task(t)
    s = Scheduler()

    s.complete_task(owner, t.id)
    pending = s.get_tasks(owner, completed=False)
    s.complete_task(owner, pending[0].id)

    assert len(buddy.tasks) == 3
    assert len(s.get_tasks(owner, completed=False)) == 1
    assert s.get_tasks(owner, completed=False)[0].time == datetime(2026, 10, 3, 8, 0)


def test_complete_task_with_unknown_id_returns_none():
    owner, buddy, _ = make_owner()
    buddy.add_task(Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, frequency=Frequency.DAILY))

    assert Scheduler().complete_task(owner, "no-such-id") is None
    assert len(buddy.tasks) == 1


# --- Conflict detection: duplicate times ---

def test_detect_conflicts_flags_two_tasks_at_the_same_time_across_pets():
    owner, buddy, max_ = make_owner()
    at = datetime(2026, 10, 1, 8, 0)
    walk = Task("Walk", at, Priority.HIGH)
    feed = Task("Feed", at, Priority.LOW)
    later = Task("Groom", datetime(2026, 10, 1, 12, 0), Priority.LOW)
    buddy.add_task(walk)
    max_.add_task(feed)
    buddy.add_task(later)

    conflicts = Scheduler().detect_conflicts(owner.get_all_tasks())

    assert conflicts == [walk, feed]  # each once, the unrelated task excluded


def test_detect_conflicts_empty_single_and_back_to_back_are_clear():
    s = Scheduler()
    a = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, duration_minutes=30)
    b = Task("Feed", datetime(2026, 10, 1, 8, 30), Priority.HIGH)

    assert s.detect_conflicts([]) == []
    assert s.detect_conflicts([a]) == []
    assert s.detect_conflicts([a, b]) == []


def test_find_daily_conflicts_flags_duplicate_times_and_skips_completed():
    owner, buddy, max_ = make_owner()
    at = datetime(2026, 10, 1, 8, 0)
    walk = Task("Walk", at, Priority.HIGH)
    feed = Task("Feed", at, Priority.LOW)
    buddy.add_task(walk)
    max_.add_task(feed)
    s = Scheduler()
    day = date(2026, 10, 1)

    assert s.find_daily_conflicts(owner, day) == [walk, feed]

    walk.mark_complete()

    assert s.find_daily_conflicts(owner, day) == []


def test_new_daily_occurrence_can_clash_with_existing_task():
    owner, buddy, max_ = make_owner()
    walk = Task("Walk", datetime(2026, 10, 1, 8, 0), Priority.HIGH, frequency=Frequency.DAILY)
    groom = Task("Groom", datetime(2026, 10, 2, 8, 0), Priority.LOW)
    buddy.add_task(walk)
    max_.add_task(groom)
    s = Scheduler()

    s.complete_task(owner, walk.id)

    warnings = s.conflict_warnings(owner, date(2026, 10, 2))
    assert len(warnings) == 1 and "same start time" in warnings[0]
