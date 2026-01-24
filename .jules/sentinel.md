## 2025-02-12 - [Missing CSRF Protection]
**Vulnerability:** The web interface endpoint `/save` (and other POST endpoints) lacked Cross-Site Request Forgery (CSRF) protection. The application used `request.form.getlist('selected')` without validating that the request originated from the authenticated user's session in the web interface.
**Learning:** Even when using "manual" authentication/authorization decorators like `requires_auth`, standard security mechanisms like CSRF protection are not automatically included in Flask. Explicit CSRF protection must be implemented either via a library (Flask-WTF) or manually using session tokens.
**Prevention:**
1. Always implement CSRF protection for any state-changing (POST, PUT, DELETE) endpoints.
2. Use a distinct CSRF token per session.
3. Verify the token in a `before_request` hook or decorator for all unsafe methods.
4. Ensure the token is injected into forms (hidden input) and AJAX requests (headers).
