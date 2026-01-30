## 2026-01-30 - CSRF Vulnerability in Article Selection
**Vulnerability:** The `/save` endpoint lacked CSRF protection, allowing attackers to submit article selections on behalf of authenticated users via malicious forms.
**Learning:** The application manually handles forms without a library like Flask-WTF, requiring manual CSRF token implementation. Relying on Basic Auth alone is insufficient for state-changing operations.
**Prevention:** Implemented a manual CSRF token pattern: generating a token in the session using `secrets`, injecting it into templates, and validating it in a `before_request` hook for all POST requests.
