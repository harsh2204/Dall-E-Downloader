from playwright.sync_api import Playwright, sync_playwright, expect
import os

creds = open('.creds').read().split('\n') if os.path.isfile('.creds') else ('', '')
USER = os.getenv('USER', creds[0])
PASS = os.getenv('PASS', creds[1])

def login_session(page):
    print("Logging in...")
    page.goto("https://labs.openai.com/auth/login")

    page.wait_for_url("https://auth0.openai.com/u/login/identifier*")

    # Click input[name="username"]
    page.locator("input[name=\"username\"]").click()

    # Fill input[name="username"]
    page.locator("input[name=\"username\"]").fill(USER)

    # Press Enter
    page.locator("input[name=\"username\"]").press("Enter")
    page.wait_for_url("https://auth0.openai.com/u/login/password*")
    page.locator("input[name=\"password\"]").fill(PASS)

    # Click text=Continue
    page.locator("text=Continue").click()
    print("Login complete")

def ensure_login(page):
    with page.expect_navigation(url="https://labs.openai.com/", wait_until='load', timeout=2000) as ctx:
        page.goto("https://labs.openai.com/", wait_until='networkidle')
        if page.url.startswith("https://labs.openai.com"):
            print('Already logged in')
            return
    with page.expect_navigation(url="https://openai.com/dall-e-2/?labs", wait_until='load', timeout=2000) as ctx:
        page.goto("https://labs.openai.com/", wait_until='networkidle')
        if page.url.startswith('https://openai.com/dall-e-2/?labs'):
            login_session(page)

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state='state.json') if os.path.isfile('state.json') else browser.new_context()

    # Open new page
    page = context.new_page()
    ensure_login(page)
    page.wait_for_url("https://labs.openai.com/", wait_until='networkidle')

    # Click [aria-label="Show history"]
    page.locator(".create-page-header > button").click()

    history = page.query_selector_all(".hist-task-grid")

    # Scroll all the way to the bottom of the history
    new_l, l = 0, -1
    while new_l != l:
        last_h = history[-1]
        last_h.scroll_into_view_if_needed()
        last_h.wait_for_element_state(state='stable')
        l = len(history)
        history = page.query_selector_all(".hist-task-grid")
        new_l = len(history)
    # --- This is important for the active tab selector
    
    try:
        for j in range(len(history)):
            history[j].wait_for_element_state(state='stable')
            history[j].scroll_into_view_if_needed()
            history[j].click()
            page.wait_for_url("https://labs.openai.com/e/*", wait_until='networkidle')
            page.locator('.hist-task-grid').last.scroll_into_view_if_needed()
            page.wait_for_selector(".hist-task-active", state='visible')

            page.locator(".task-page-generations-img").first.click()
            page.wait_for_url("https://labs.openai.com/e/*", wait_until='networkidle')
            page.wait_for_selector('.task-page-generations-img > div > img', state='attached')
            images = page.query_selector_all('.task-page-generations-grid > div')
            for i in range(len(images)):
                edit_page_btns = page.query_selector_all('.edit-page-image-buttons > button:nth-child(2)')
                if not len(edit_page_btns):
                    page.keyboard.press('ArrowRight')
                    continue
                expect(page.locator(".edit-page-image-buttons > button:nth-child(2)").first).to_be_enabled()
                print('Clicking download button')
                with page.expect_download() as download_info:
                    page.query_selector_all(".edit-page-image-buttons > button:nth-child(2)")[-1].click()
                download = download_info.value
                download.save_as(path='downloads\\'+ download.suggested_filename)
                if i != len(images):
                    print("Right arrow")
                    page.keyboard.press('ArrowRight')

    except Exception as e:
        print(e)
    finally:
        context.storage_state(path='state.json')
        # ---------------------
        context.close()
        browser.close()


with sync_playwright() as playwright:
    run(playwright)
