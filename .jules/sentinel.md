## 2026-01-22 - CSRF Protection in Legacy Forms
**Vulnerability:** Missing CSRF protection on the `/save` endpoint allowed attackers to modify article selections.
**Learning:** When adding CSRF protection to an existing Flask app using `before_request` hooks, it's critical to inspect both `request.form` (for traditional forms) and `request.headers` (for JSON APIs). In this case, the `generateNewsletter` function used `FormData` constructed from the form, which conveniently allowed the hidden input to be automatically included in the AJAX request without modifying the JavaScript.
**Prevention:** Always use `before_request` hooks for global CSRF protection instead of per-route decorators if possible, to ensure no endpoints are missed. Ensure all forms include the `csrf_token` hidden field.
