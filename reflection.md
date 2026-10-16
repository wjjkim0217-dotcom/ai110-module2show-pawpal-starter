# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML separates data (who and what needs care) from planning logic (when it happens). Classes and responsibilities:

- **Task**: one care activity. Holds title, duration, priority, and optional category, fixed time, and frequency. Validates itself, decides whether it is due on a given day (once/daily/weekly), and tracks completion.
- **Pet**: owns a list of Tasks. Adds, removes, and looks up tasks, and returns the tasks due on a given day.
- **Owner**: owns the Pets and the constraints (available time window, preferences). Gathers all due tasks across pets and validates the availability window.
- **Scheduler**: holds the planning logic. Takes an Owner and a day, sorts tasks by priority, places fixed-time tasks first, fills the remaining gaps, and returns a Plan.
- **Plan** (with ScheduledEntry and UnscheduledEntry): the result. Lists scheduled tasks with start/end times and a reason, unscheduled tasks with a reason, and any conflict warnings.

Owner, Pet, and Task are mostly data plus validation, so the scheduling rules live in one place (Scheduler) and can be tested without the Streamlit UI.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Each pet now has its own unique ID, the same as each task already did. Two pets can share a name and species, so the ID is how the app tells them apart. The diagram has a note saying this.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers five constraints:

- **Fixed times:** a task can be pinned to a clock time, such as an 08:00 walk or a 12:30 medication.
- **The owner's available window:** nothing is placed before the owner starts or after they finish. An optional "don't start before" preference can move the start later. A fixed task outside the window is not scheduled and is listed with a reason.
- **Task length:** a task is only placed in a gap long enough to hold it. One that doesn't fit is listed as unscheduled instead of being squeezed in.
- **Priority:** among flexible tasks, high comes before medium before low. Ties go to the shorter task, then to the order they were added.
- **Whether a task is due that day:** daily and weekly tasks only appear on the days they apply to, and a task already done that day is skipped.

I ranked them by how costly it is to get each one wrong. The hard limits come first: the owner's hours and the task's length, because a plan that breaks them can't be carried out. Fixed times come next. They are commitments, like a medication or a vet call, so they are placed first whatever their priority, and the scheduler never moves them. Priority only decides the order of the flexible tasks, which fill the time around the fixed ones.

I dropped "preferred time of day" per category. It was in the first design, but I never made it affect the schedule, so I removed it rather than leave a setting that does nothing. The only preference that works is the earliest start.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

My scheduler warns about conflicts between fixed-time tasks but does not fix them. It checks for real overlaps, not just identical start times, so a 08:00-08:30 walk and an 08:15 vet call are flagged. Both tasks stay in the plan, and the warning suggests the next free slot. It never moves or drops a fixed task on its own, even when a high-priority task clashes with a low-priority one. Flexible tasks are placed first-come into the first gap that fits, ordered by priority only, so a long low-priority task can take a gap that several shorter tasks would have fit in better.

This is reasonable because a fixed time is something the owner committed to, such as a medication or a vet appointment, and the app should not quietly change it. A warning plus a suggested slot lets the owner decide. The greedy placement is also simple to read and test, and with only a handful of tasks per day a perfect packing would add complexity for very little gain.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used AI tools for every stel of this project. Utilizing the direct text from the instructions were most helpful as the instructions gave clear guidance you would give a student to implement (which is also what AI requires).

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
When I asked AI to make the tests directory and the testing file, it also automatically created 30 tests which I rejected. I then prompted it to add two tests which I verified manually.
- How did you evaluate or verify what the AI suggested?
I use my knowledge of coding and use my judgement to evaluate whether I should accept what the AI suggested.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I wrote 27 tests in `tests/test_pawpal.py`, covering these behaviors:

- **Sorting:** tasks come out in clock order with untimed ones last, and built plans are in chronological order. Flexible tasks are placed by priority.
- **Recurring tasks:** a daily task renews for the next day, a weekly task renews on its next weekday, and a one-off task does not renew. Completing a task twice does not create a duplicate, and the new task lands on the right pet.
- **Conflicts:** overlapping fixed tasks are flagged with a suggested free slot. Tasks at the exact same time are flagged for the same pet and across pets, a same-pet overlap is marked as a likely duplicate, and back-to-back tasks are not a conflict.
- **Filtering:** by pet name, ignoring case, and by done or pending status.
- **Edge cases and validation:** an owner with no pets or a pet with no tasks gives an empty plan. A fixed task outside the window is unscheduled, and a task exactly as long as the window fits while one a minute longer does not. Bad input is rejected, and a failed update restores the old values.

I chose these because they are the places where a wrong answer would hurt the owner without any error message. A missed conflict or a wrongly renewed task just produces a plan that looks fine and isn't, so I wanted tests that fail loudly. The tests call `pawpal_system.py` directly, which is why the scheduling rules live in one place and don't depend on Streamlit.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident, about 4 out of 5, in the scheduler itself. All 27 tests pass and they cover the three behaviors that matter most: sorting, recurrence and conflict detection. I hold back one star because the tests never touch the Streamlit UI. I checked the UI only by running it, so a wrong label or a button wired to the wrong task would not be caught.

If I had more time I would test:

- **Earliest start:** the "don't start before" preference, including a fixed task that falls before it.
- **Three or more overlapping tasks:** every pair should be reported once, with a sensible suggested slot for each.
- **Weekly renewal across month and year ends**, and a task completed on a day it was not due.
- **Flexible tasks around several fixed ones:** gaps on both sides of a fixed task, and a high-priority task that can't fit while smaller low-priority ones can.
- **Updating a task** with one valid field and one unknown field, to see whether the valid one is rolled back.
- **A suggested slot that doesn't exist**, such as a conflict late in the day with nothing left after it.
- **The UI itself**, with Streamlit's `AppTest`, to check the add, complete and delete flows.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
It was satisfying to build something concrete with clear instructions (as is what we would experience when working in the real world) which made working with the AI a joy.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
None.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
I learned that the AI system will sometimes overreach and try to do more than what was requested, but it is up to you to reel that behavior in. 