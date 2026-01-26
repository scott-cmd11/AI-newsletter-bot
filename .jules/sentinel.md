
## 2026-01-26 - Manual CSRF Protection Implementation
**Vulnerability:** The application lacked CSRF protection on POST endpoints, allowing attackers to perform actions on behalf of authenticated users via malicious forms.
**Learning:** Frameworks like Flask do not include CSRF protection by default; it requires  or manual implementation. In this case, we opted for manual implementation to avoid adding dependencies, using a  hook and session storage.
**Prevention:** Always verify if the web framework includes CSRF protection out-of-the-box. For Flask, enable  CSRF protection or implement a token verification middleware early in development.

## 2024-05-23 - Manual CSRF Protection Implementation
**Vulnerability:** The application lacked CSRF protection on POST endpoints, allowing attackers to perform actions on behalf of authenticated users via malicious forms.
**Learning:** Frameworks like Flask do not include CSRF protection by default; it requires `Flask-WTF` or manual implementation. In this case, we opted for manual implementation to avoid adding dependencies, using a `before_request` hook and session storage.
**Prevention:** Always verify if the web framework includes CSRF protection out-of-the-box. For Flask, enable `Flask-WTF` CSRF protection or implement a token verification middleware early in development.
