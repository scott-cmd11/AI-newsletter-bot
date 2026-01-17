## 2024-05-23 - Sequential Feed Fetching Bottleneck
**Learning:** Fetching multiple RSS feeds sequentially significantly increases total execution time, especially when network latency is involved.
**Action:** Use `ThreadPoolExecutor` to fetch feeds in parallel. This is a classic I/O bound optimization.
