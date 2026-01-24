## 2024-05-22 - [Parallel RSS Fetching]
**Learning:** Network I/O for RSS feeds was serialized, causing slow startup times (2.5s for 5 feeds). Parallelizing with `ThreadPoolExecutor` reduced this to 0.5s.
**Action:** When fetching multiple external resources (RSS, APIs), always verify if they are parallelized. `ThreadPoolExecutor` is effective for I/O bound tasks in Python.
