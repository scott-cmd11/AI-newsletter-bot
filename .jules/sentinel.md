## 2024-05-22 - Missing CSRF Protection in Flask
**Vulnerability:** The Flask app lacked CSRF protection for state-changing POST requests (e.g., `/save`).
**Learning:** Even simple Flask apps need manual CSRF protection or `Flask-WTF`. Relying on `requests` library without validation on server side is a common oversight. Also, `before_request` hooks must be registered *after* the function definition in Python if using decorators isn't an option or if order matters.
**Prevention:** Use `Flask-WTF` or ensure manual token verification is in place for all unsafe methods. Ensure `app.secret_key` is set.
