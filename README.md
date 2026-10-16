# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

The scheduling logic is in `pawpal_system.py` and has no Streamlit code, so it can be run and tested on its own (`python main.py`). The Streamlit UI in `app.py` is not connected to it yet.

How the classes work together:

- **`Owner`** holds the owner's available time window and a list of **`Pet`**s. `get_all_tasks()` and `all_tasks_due(day)` return every pet's tasks as one pool of `(pet, task)` pairs, because the owner is a single person.
- **`Pet`** holds its own list of **`Task`**s. Tasks and pets have unique ids, so two with the same name never get mixed up.
- **`Task`** is one care activity: title, duration, priority, and optional category, fixed time, and frequency (once, daily, weekly). It validates itself, knows whether it is due on a given day, and tracks completion.
- **`Scheduler.build_plan(owner, day)`** reads tasks only through `owner.all_tasks_due(day)`, so tasks from all pets are scheduled together and never overlap. It:
  1. Places fixed-time tasks first, at their time, whatever their priority. Overlaps are reported as conflicts and nothing is dropped.
  2. Finds the free gaps in the owner's window.
  3. Fills the gaps with the remaining tasks by priority, then shorter duration, into the first gap that fits.
  4. Lists tasks that don't fit as unscheduled, with a reason.
- **`Plan`** is the result: scheduled entries (task, pet, start, end, reason), unscheduled entries, and conflicts. The UI or `main.py` only reads the plan.

Known gaps: `Plan.is_stale_for` is a stub, and `Preferences.preferred_times` is stored but not used by the scheduler yet.

## 🖥️ Sample Output

Output from running `python main.py`:

```
Today's Schedule (Thursday, October 15) for Jordan
----------------------------------------------------
07:00-07:15  Luna   Brushing       [low priority, first gap that fits]
08:00-08:30  Mochi  Morning walk   [fixed time 08:00]
12:30-12:35  Mochi  Medication     [fixed time 12:30]
18:00-18:10  Luna   Dinner         [fixed time 18:00]
```

## 🧪 Testing PawPal+

Run the full suite from the project root (with the virtual environment active):

```bash
python -m pytest          # add -v to list every test
```

The tests are in `tests/test_pawpal.py` and exercise `pawpal_system.py` directly, with no Streamlit involved. They cover:

- **Sorting:** `sort_by_time` returns tasks in clock order with untimed tasks last. Built plans list entries chronologically, and flexible tasks are placed by priority.
- **Recurring tasks:** Completing a daily task creates one due the next day, and a weekly task renews on its next weekday. Once tasks don't renew, completing twice doesn't create a duplicate, and `Scheduler.mark_complete` adds the new task to the right pet.
- **Conflict detection:** Overlapping fixed-time tasks are flagged with a suggested free slot, and tasks at the exact same time are flagged for the same pet and across pets. Same-pet overlaps are marked as likely duplicates, and back-to-back tasks are not conflicts.
- **Edge cases:**
  - An owner with no pets, or a pet with no tasks, gives an empty plan.
  - A fixed task outside the availability window is unscheduled.
  - A task exactly as long as the window fits, and one a minute longer does not.
- **Validation:**
  - Empty titles, non-positive durations and weekly tasks without a weekday are rejected.
  - A failed `Task.update` restores the old values.
  - An availability window that ends before it starts is rejected.
- **Filtering:** Tasks can be filtered by pet name (case-insensitive) and by done or pending status.

Not covered yet: `Plan.is_stale_for` (still a stub) and `Preferences.preferred_times` (stored but not used by the scheduler).

Output of a successful run of `python -m pytest`:

```
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\wjkim\Documents\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 27 items

tests\test_pawpal.py ...........................                         [100%]

============================= 27 passed in 0.06s ==============================
```

**Confidence level: ★★★★☆ (4 / 5)**

All 27 tests pass, including the three core behaviors (chronological sorting, daily and weekly recurrence, and duplicate-time conflict detection) and the main edge cases (empty pets, window boundaries, invalid input). I'm holding back one star because the tests only run `pawpal_system.py`, not the Streamlit UI. `Plan.is_stale_for` is an untested stub. `Preferences.preferred_times` is unused, and I haven't tested a task update that mixes a valid field with an unknown one.

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
