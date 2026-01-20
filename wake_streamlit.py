import os
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

def urls_from_env():
    raw = os.getenv("STREAMLIT_URLS", "")
    return [line.strip() for line in raw.splitlines() if line.strip()]

def wake_one(page, url: str) -> bool:
    print(f"[OPEN] {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)

    wake_btn = page.get_by_role("button", name="Yes, get this app back up!")
    if wake_btn.count() > 0:
        print("[WAKE] button found -> click")
        wake_btn.first.click()
    else:
        print("[WAKE] button not found (maybe already awake)")

    try:
        page.wait_for_selector("div[data-testid='stApp']", timeout=120_000)
        print("[OK] stApp loaded")
        return True
    except PWTimeout:
        print("[FAIL] stApp not loaded in time")
        return False

def main():
    urls = urls_from_env()
    if not urls:
        raise SystemExit("STREAMLIT_URLS is empty.")

    ok_all = True
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            ok = wake_one(page, url)
            ok_all = ok_all and ok

        browser.close()

    if not ok_all:
        raise SystemExit("Some apps did not wake successfully.")

if __name__ == "__main__":
    main()
