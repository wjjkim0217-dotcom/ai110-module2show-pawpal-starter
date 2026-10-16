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

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
