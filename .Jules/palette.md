# Palette's Journal

## 2024-05-24 - Article Selection Accessibility
**Learning:** Icon-only inputs (like checkboxes in cards) create significant accessibility barriers if not labeled, and small hit targets frustrate mouse users.
**Action:** Always wrap card selection inputs with the card itself as a click target, and ensure every input has a unique `aria-label` derived from its context (e.g., article title).
