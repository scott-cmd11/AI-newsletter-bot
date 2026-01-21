## 2025-05-23 - Flask request.json and 415 Errors
**Vulnerability:** N/A (Implementation detail)
**Learning:** Accessing `request.json` in a Flask `before_request` hook on a request with non-JSON Content-Type (e.g. form submission) raises a 415 Unsupported Media Type error, blocking legitimate form requests.
**Prevention:** Always check `request.is_json` before accessing `request.json` in global hooks.
