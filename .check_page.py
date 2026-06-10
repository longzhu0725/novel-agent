from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Capture console logs
    console_messages = []
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: console_messages.append(f"[pageerror] {exc}"))

    page.goto('http://127.0.0.1:5173/')
    page.wait_for_load_state('networkidle')

    # Take screenshot
    page.screenshot(path='/workspace/.page-state.png', full_page=True)

    # Get rendered content
    root_content = page.locator('#root').inner_html()
    print("=== ROOT CONTENT (first 2000 chars) ===")
    print(root_content[:2000])
    print()

    print("=== CONSOLE MESSAGES ===")
    for msg in console_messages:
        print(msg)

    browser.close()
