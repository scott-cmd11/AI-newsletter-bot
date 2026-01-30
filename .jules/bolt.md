## 2025-02-18 - [Scoring Loop String Overhead]
**Learning:** In the scoring loop, repeated string concatenation and lowercasing inside nested loops (Article -> Category -> Keywords) caused significant overhead. Even simple operations like `f"{title} {summary}".lower()` become expensive when multiplied by N articles * M categories.
**Action:** Always lift invariant calculations (like lowercasing the article text) out of the inner loops. Pass pre-processed data to helper functions instead of raw objects if they need to perform repeated transformations.
