## 2025-02-18 - Sequential Feed Fetching Discrepancy
**Learning:** The codebase (specifically `src/sources/rss_fetcher.py`) was implementing feed fetching sequentially using simple `for` loops, despite memory/documentation claiming it was parallelized with `ThreadPoolExecutor`.
**Action:** Always verify implementation details against the code itself, not just documentation or memory, especially for performance critical sections.
