## 2024-05-23 - RSS Feed Fetching Optimization
**Learning:** Sequential fetching of RSS feeds is a major bottleneck due to network latency. Python's `ThreadPoolExecutor` is effective for parallelizing these I/O-bound tasks.
**Action:** Always check for sequential network operations in loops and consider parallelization.
