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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
