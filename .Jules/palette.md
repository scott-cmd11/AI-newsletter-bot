# Palette's UX Journal

This journal records critical UX and accessibility learnings for the AI Newsletter Bot.

## 2024-05-22 - Interaction Feedback Patterns
**Learning:** Users often double-click "Generate" buttons when there's no immediate visual feedback, causing parallel requests or confusion.
**Action:** Always implement immediate "disabled + loading text" state on action buttons, even before the network request starts.

## 2024-05-22 - Fitts's Law in Lists
**Learning:** Small checkboxes in list items are hard to target.
**Action:** Make the entire list item card clickable to toggle the selection, while preserving link behavior for nested anchors.
