## 2026-01-18 - [Concurrent RSS Fetching]
**Learning:** Sequential network requests (like RSS fetching) are a major bottleneck in Python. Using `concurrent.futures.ThreadPoolExecutor` provides a simple, standard-library way to parallelize I/O-bound tasks without complex async/await refactoring.
**Action:** Always check for sequential loop-based network calls and consider parallelizing them with ThreadPoolExecutor.
