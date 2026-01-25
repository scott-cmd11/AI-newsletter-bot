## 2024-01-20 - Sequential RSS Fetching Bottleneck
**Learning:** The RSS fetcher was iterating sequentially through feeds, leading to a linear increase in fetch time with the number of feeds (approx 20 feeds * 1s/feed = 20s). This is a classic IO-bound bottleneck.
**Action:** Always check for sequential IO operations in loops. Parallelize using `ThreadPoolExecutor` for independent IO tasks to reduce total time to the slowest individual request.
