# Bolt's Journal

## 2025-02-23 - RSS Feed Parallelization
**Learning:** The RSS fetcher was processing feeds sequentially, which becomes a bottleneck as the number of feeds increases. Network I/O is a prime candidate for parallelization using threads.
**Action:** Implemented `ThreadPoolExecutor` to fetch feeds concurrently. This allows the total fetch time to be determined by the slowest feed rather than the sum of all feed response times.
