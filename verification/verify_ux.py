
from playwright.sync_api import sync_playwright

def verify_ux():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:5001")

        # 1. Verify aria-label
        checkbox = page.locator('input[type="checkbox"]').first
        aria_label = checkbox.get_attribute("aria-label")
        print(f"Aria Label: {aria_label}")
        if aria_label != "Select Article One":
            print("ERROR: Incorrect aria-label")
            exit(1)

        # 2. Verify click on card toggles checkbox
        article_card = page.locator('.article').first

        # Initial state: unchecked
        if checkbox.is_checked():
            print("ERROR: Should be unchecked initially")
            exit(1)

        # Click the card (outside the checkbox)
        article_card.click()

        # Verify checked
        if not checkbox.is_checked():
            print("ERROR: Click on card did not check the box")
            exit(1)

        # Click again to uncheck
        article_card.click()
        if checkbox.is_checked():
            print("ERROR: Second click did not uncheck")
            exit(1)

        # Re-check for screenshot
        article_card.click()

        page.screenshot(path="verification/ux_verification.png")
        print("Verification successful, screenshot saved.")
        browser.close()

if __name__ == "__main__":
    verify_ux()
