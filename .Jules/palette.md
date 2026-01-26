## 2024-05-22 - Clickable Cards with Nested Links
**Learning:** When making a card clickable to improve usability (Fitts's Law), standard `onclick` handlers on the container will capture clicks on nested links, causing double actions or unintended selection toggles.
**Action:** Always check `!event.target.closest('a')` and `!event.target.closest('input')` in the container's click handler to preserve native behavior of nested interactive elements.
