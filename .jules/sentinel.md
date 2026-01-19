# Sentinel's Journal

## 2025-02-12 - Flask CSRF Protection
**Vulnerability:** Missing CSRF protection on POST endpoints (`/save`, `/api/predictions`).
**Learning:** Pure Flask applications (without Flask-WTF) are vulnerable to CSRF by default. Global protection via `before_request` is effective but requires careful handling of API vs Form endpoints.
**Prevention:** Implement "Synchronizer Token Pattern" manually using `secrets` and `session`, injecting the token into all templates and verifying it on every POST request.
