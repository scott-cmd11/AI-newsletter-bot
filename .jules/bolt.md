## 2025-01-31 - Hot Loop Invariants & Legacy Configs
**Learning:** Significant performance gains (and bug fixes) come from hoisting invariant processing (like lowercasing keywords) out of hot loops. Also, legacy configuration formats (dict vs list) can silently break processing if not normalized early.
**Action:** When working on batch processing functions, always look for opportunities to pre-process configuration and invariant data *once* before the loop. Ensure robust normalization for inputs that might vary in format.
