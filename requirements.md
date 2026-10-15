# PawPal+ Requirements and Edge Cases (Draft)

## Functional requirements

- FR1. Enter owner name and daily availability as a clock window (e.g. 07:00-21:00).
- FR2. Add pets (name, species) to the owner; one owner per pet.
- FR3. Record owner preferences (e.g. preferred walk time, no tasks before 08:00). Soft constraints; priority wins on conflict.
- FR4. Add tasks to a pet with title, duration (minutes), and priority (low/medium/high).
- FR5. Optional task fields: category (walk, feeding, meds, enrichment, grooming), fixed time, frequency (once/daily/weekly), notes.
- FR6. Edit, delete, and complete tasks.
- FR7. Generate a daily plan: ordered tasks with start/end times within the availability window.
- FR8. Schedule by priority; ties break by fixed time, then shorter duration, then insertion order.
- FR9. Place fixed-time tasks at their time first; fill remaining gaps with the rest.
- FR10. List tasks that don't fit as unscheduled, each with a reason.
- FR11. No overlaps (across all pets); warn on fixed-time conflicts, never silently drop a task.
- FR12. Include recurring tasks only on due days (daily: every day; weekly: chosen weekday).
- FR13. Explain why each task was placed (priority, fixed time, or filled a gap).
- FR14. Show the plan as a table or timeline in the UI, with warnings and unscheduled tasks separate.
- FR15. Keep state across Streamlit reruns (`st.session_state`).
- FR16. Test sorting, fit, conflicts, recurrence, and edge cases.

## Non-functional requirements
- NFR1. Scheduling logic lives in `pawpal_system.py` with no Streamlit imports, so it is testable alone.
- NFR2. The same input always produces the same plan.
- NFR3. Invalid input produces a clear message, not a crash.

## Edge cases

### Input validation
| # | Case | Expected behavior |
|---|------|-------------------|
| E1 | Duration is 0, negative or non-numeric | Reject with a message |
| E2 | Duration exceeds the whole available window | Accept the task, list it as unscheduled with the reason "longer than available time" |
| E3 | Empty or whitespace-only title | Reject |
| E4 | Duplicate title on the same pet | Allow, or warn. Pick one and document it |
| E5 | Very long title or special characters | Display without breaking the layout |
| E6 | Available time is 0 or end is before start | Block generation with a message |

### Scheduling
| # | Case | Expected behavior |
|---|------|-------------------|
| E7 | No tasks | Show "nothing to schedule", not an empty or broken table |
| E8 | Total task time is greater than available time | Schedule by priority, list the rest as unscheduled |
| E9 | Total task time exactly equals available time | All tasks fit with no gap |
| E10 | All tasks have the same priority | Deterministic tie-break (FR8) |
| E11 | Two fixed-time tasks overlap | Conflict warning, keep both visible |
| E12 | Fixed-time task falls outside the available window | Warn and mark it unscheduled |
| E13 | Fixed-time task is placed mid-window | Fill the gaps around it. A task too long for any gap goes to unscheduled |
| E14 | A low-priority task fits a gap that a high-priority task cannot use | Use the gap for the low-priority task |
| E15 | A high-priority task cannot fit but several small low-priority ones can | Define the rule (priority strictly first, or maximize the number of tasks) and document it as a tradeoff |
| E16 | Task crosses midnight | Out of scope. Keep the schedule within one day |
| E17 | Preferences conflict with priority (e.g. "no walks before 9" vs. a high-priority 8am med) | Priority wins, and the explanation says so |

### Multiple pets
| # | Case | Expected behavior |
|---|------|-------------------|
| E18 | Two pets have tasks at the same time | The owner is one person, so tasks cannot overlap across pets |
| E19 | Same task name on different pets | Treated as separate tasks |
| E20 | A pet with no tasks | Skip it in the plan without error |
| E21 | Deleting a pet | Its tasks are deleted too |

### Recurrence and state
| # | Case | Expected behavior |
|---|------|-------------------|
| E22 | A daily task is completed today | Not shown as pending today, reappears tomorrow |
| E23 | A weekly task on a non-due day | Excluded from the plan |
| E24 | Page refresh or Streamlit rerun | Data survives within the session. Lost on a new session unless persistence is added |
| E25 | Editing a task after the plan is generated | Plan is marked stale or regenerated |

## Open questions
1. Is available time a total minute budget or a clock window? A clock window is needed for fixed times and conflicts. A budget is simpler.
2. Does one owner mean one schedule across all pets? This draft assumes yes.
3. Is persistence (JSON file) in scope, or only the session?
4. Should the priority rule be strict (E15) or should it maximize the number of tasks?

## Suggested first test list
1. Higher priority is scheduled before lower priority.
2. Tasks that exceed the budget are unscheduled with a reason.
3. No two scheduled tasks overlap.
4. Overlapping fixed-time tasks produce a warning.
5. An empty task list returns an empty plan without error.
6. Invalid duration is rejected.
7. A completed daily task is excluded today.
