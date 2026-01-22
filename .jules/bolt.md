## 2024-03-21 - Parallel RSS Fetching
**Learning:** Sequential fetching of RSS feeds is a major bottleneck. Each feed adds its latency to the total time.
**Action:** Used `concurrent.futures.ThreadPoolExecutor` to parallelize `fetch_google_alerts` and `fetch_rss_feeds`. Reduced fetching time from linear O(N) to roughly O(1) (bounded by max latency).
