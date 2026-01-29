## 2025-02-18 - [Added CSRF Protection to Web Interface]
**Vulnerability:** The Flask web interface exposed POST endpoints (`/save`, `/api/predictions`) without Cross-Site Request Forgery (CSRF) protection. This could allow attackers to trick authenticated users into submitting unwanted actions, such as saving invalid article selections.
**Learning:** Even simple internal tools or "bot" interfaces need basic security protections if they are exposed via a web server. Adding `secrets` and `session` based token validation is a lightweight alternative to full frameworks like `Flask-WTF` when dependencies should be minimized.
**Prevention:** Always verify CSRF tokens on state-changing requests (POST, PUT, DELETE). Use the `secrets` module to generate cryptographically strong tokens.
