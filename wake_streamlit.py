import os
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

WAKE_BTN_SELECTOR = "#root > div:nth-child(1) > div > div > div > div > button"

def urls_from_env():
    raw = os.getenv("STREAMLIT_URLS", "")
    return [line.strip() for line in raw.splitlines() if line.strip() and not line.strip().startswith("#")]

def wake_one(page, url: str) -> bool:
    print(f"\n[OPEN] {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)

    # sleep 화면 버튼이 늦게 뜨는 경우가 있어 약간 대기
    page.wait_for_timeout(4000)

    btn = page.locator(WAKE_BTN_SELECTOR).first
    count = btn.count()
    print(f"[WAKE] selector match count = {count}")

    # 버튼이 있는지만 확인 
    try:
        visible = btn.is_visible(timeout=2000) if count else False
    except Exception:
        visible = False
    print(f"[WAKE] visible = {visible}")
    
    if visible:
        btn.click(timeout=10_000)

    # 최종적으로 앱 본문이 로드됐는지 확인(이걸 성공 기준으로 두는 게 안전)
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
            ok_all = wake_one(page, url) and ok_all
        browser.close()

    if not ok_all:
        raise SystemExit("Some apps did not load successfully.")

if __name__ == "__main__":
    main()
