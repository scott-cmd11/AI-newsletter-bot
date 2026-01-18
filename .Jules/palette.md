## 2026-01-18 - Clickable Cards for Selection
**Learning:** Users expect card-based boolean selections to be toggleable by clicking the entire card, not just the small checkbox. This significantly improves usability on touch devices and for mouse users.
**Action:** When using cards with checkboxes, always bind the click event of the card to toggle the checkbox, and ensure the checkbox has an aria-label since it often lacks a visible sibling label tag.
