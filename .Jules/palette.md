## 2024-10-27 - [Accessibility] Custom Interactive Components
**Learning:** Custom interactive components like article cards with checkboxes and custom progress bars often miss basic ARIA roles and labels, making them invisible to screen readers.
**Action:** Always check `input[type="checkbox"]` inside custom cards for `aria-label` and ensure custom progress indicators have `role="progressbar"` and updating `aria-valuenow`.
