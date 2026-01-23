## 2026-01-23 - Sequential RSS Fetching Bottleneck
**Learning:** The RSS fetcher was processing feeds sequentially, which becomes a significant bottleneck as the number of feeds increases (N feeds * avg_fetch_time).
**Action:** Always check loop-based I/O operations for parallelization opportunities using `ThreadPoolExecutor`.
