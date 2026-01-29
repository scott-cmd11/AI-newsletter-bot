## 2026-01-29 - [Expand Click Targets on Cards]
**Learning:** Users expect card-based list items (like article summaries) to be fully clickable for selection, not just the small checkbox. This is a common pattern in modern web UIs (e.g. Gmail).
**Action:** When implementing selection lists, wrap the item in a clickable container that toggles the checkbox, but ensure to explicitly exclude nested interactive elements like links (<a>) and the checkbox itself from the click handler to prevent conflicts.
