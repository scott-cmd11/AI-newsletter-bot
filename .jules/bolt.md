## 2024-05-23 - RSS Fetching Optimization
**Learning:** Sequential network requests in loops are a major performance killer. `feedparser.parse` is blocking. Using `concurrent.futures.ThreadPoolExecutor` allows for significant speedup (10x in simulations with 10 feeds) by overlapping I/O wait times.
**Action:** Always check `for` loops that perform network I/O. If order doesn't matter (or can be reconstructed), parallelize them. Ensure exception handling is inside the parallelized function to avoid crashing the whole batch.
