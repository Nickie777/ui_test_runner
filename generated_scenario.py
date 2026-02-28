import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://playwright.dev/")
    page.get_by_role("link", name="Docs").click()
    page.get_by_role("link", name="Setting up CI").click()
    page.get_by_role("link", name="HTML Report", exact=True).click()
    page.get_by_role("link", name="Canary releases").click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
