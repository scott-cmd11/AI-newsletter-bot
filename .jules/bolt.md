## 2024-05-22 - [Repeated String Operations in Scoring Loops]
**Learning:** The article scoring logic was re-calculating lowercased text representation for every topic check, leading to O(N*M) string allocations and lowercasing operations where N is articles and M is topics.
**Action:** Lift invariant string operations out of inner loops. Pre-process static configuration (like keywords) once per batch rather than per item.
