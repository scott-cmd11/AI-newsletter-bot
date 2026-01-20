## 2025-02-18 - Clickable Cards with Links
**Learning:** When making cards clickable, simple `tagName === 'A'` checks fail for nested elements inside links.
**Action:** Use `event.target.closest('a')` to reliably detect link clicks and prevent double-triggering or navigation interruption.

## 2025-02-18 - Checkbox Accessibility in Lists
**Learning:** Checkboxes in article lists often lack visual labels, relying on the adjacent text.
**Action:** Always add `aria-label` using the item's title (e.g., `aria-label="Select {{ article.title|e }}"`) to ensure screen reader accessibility.
