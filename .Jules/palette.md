# Palette's Journal

## 2025-02-18 - Enhancing Card Selectability
**Learning:** Making entire cards clickable improves hit areas but requires careful event management to avoid double-toggling (checkboxes) or hijacking navigation (links). Also, always ensure inputs have `aria-label` if no visible label exists.
**Action:** Use `closest('a')` and `window.getSelection()` checks when implementing card-wide click handlers. Add `aria-label` to orphaned inputs.
