## 2025-02-18 - [CSRF Protection]
**Vulnerability:** The application lacked Cross-Site Request Forgery (CSRF) protection, allowing attackers to potentially submit forms on behalf of authenticated users.
**Learning:** Basic Authentication alone does not protect against CSRF attacks. Flask applications need explicit CSRF protection (like `Flask-WTF` or manual token validation) for state-changing operations.
**Prevention:** Implemented the Synchronizer Token Pattern manually using `secrets` and `session`. Added a `before_request` hook to validate tokens on all POST requests and injected the token into forms and meta tags.
