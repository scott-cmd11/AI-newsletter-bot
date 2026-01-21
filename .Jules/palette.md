# Palette's Journal

## 2023-10-27 - Clickable Cards and Context
**Learning:** Users often expect card-based UIs to be fully clickable, not just the small checkbox within. Adding an `onclick` handler to the container while preserving link behavior (via `closest('a')`) significantly improves usability and touch targets. Also, screen readers need context for checkboxes in lists - adding `aria-label="Select [Title]"` is essential.
**Action:** When building list interfaces with actions, always make the container interactive and ensure individual controls have descriptive accessible labels.
