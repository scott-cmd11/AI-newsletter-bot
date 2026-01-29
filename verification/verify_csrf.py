from flask import Flask, render_template_string, session
import secrets
import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mocking
app = Flask(__name__)
app.secret_key = 'test'

@app.route('/fetch')
def fetch_articles(): pass

@app.route('/save')
def save_selection(): pass

@app.route('/generate')
def generate(): pass

@app.route('/api/progress')
def get_progress(): pass

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = 'mock-token-123'
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def verify_and_screenshot():
    # Load template
    template_path = Path(__file__).parent.parent / "src" / "templates" / "web_interface.html"
    with open(template_path, 'r') as f:
        template = f.read()

    # Mock data
    data = {
        "total_articles": 1,
        "categories": {
            "test_cat": [
                {
                    "id": "1",
                    "title": "Test Article",
                    "url": "http://example.com",
                    "source": "Test",
                    "score": 5.0,
                    "summary": "Summary",
                    "selected": False
                }
            ]
        },
        "selected": []
    }

    with app.test_request_context():
        # Simulate session
        session['csrf_token'] = 'mock-token-123'
        rendered = render_template_string(template, data=data)

    # Save to file
    html_file = Path("verification/rendered.html")
    with open(html_file, "w") as f:
        f.write(rendered)

    print(f"✅ Rendered HTML saved to {html_file.absolute()}")

    # Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{html_file.absolute()}")

        # Verify
        csrf_input = page.locator('input[name="csrf_token"]')
        if csrf_input.count() > 0:
             print("✅ Playwright found CSRF token input.")
             val = csrf_input.get_attribute("value")
             if val == "mock-token-123":
                 print("✅ Token value matches.")
             else:
                 print(f"❌ Token value mismatch: {val}")
        else:
             print("❌ Playwright did NOT find CSRF token input.")

        # Screenshot
        page.screenshot(path="verification/verification.png")
        print("📸 Screenshot saved to verification/verification.png")

        browser.close()

if __name__ == "__main__":
    verify_and_screenshot()
