## 2026-01-18 - Manual CSRF Protection
**Vulnerability:** Lack of CSRF protection on form submissions exposed users to state-changing attacks.
**Learning:** `flask-wtf` dependency was missing, necessitating a manual implementation using standard library `secrets` and Flask `session`.
**Prevention:** Apply the `csrf_protect` before_request hook globally and ensure `csrf_token` is included in all forms and as a meta tag for AJAX.
