import os
from playwright.sync_api import sync_playwright

WAKE_BTN_SELECTOR = "#root > div:nth-child(1) > div > div > div > div > button"

def urls_from_env():
    raw = os.getenv("STREAMLIT_URLS", "")
    return [line.strip() for line in raw.splitlines() if line.strip() and not line.strip().startswith("#")]

def wake_only(page, url: str) -> bool:
    print(f"\n[OPEN] {url}", flush=True)
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)

    # sleep UI가 늦게 뜰 수 있어서 약간 대기
    page.wait_for_timeout(4000)

    btn = page.locator(WAKE_BTN_SELECTOR).first
    cnt = btn.count()
    print(f"[WAKE] selector match count = {cnt}", flush=True)

    if cnt:
        # 보이면 클릭 시도
        try:
            if btn.is_visible(timeout=2000):
                btn.click(timeout=10_000)
                print("[WAKE] clicked", flush=True)
                # 클릭 반영 시간만 조금 주고 끝
                page.wait_for_timeout(3000)
                return True
        except Exception as e:
            print(f"[WAKE] click failed: {repr(e)}", flush=True)
            # 클릭 실패면 실패로 처리(원하면 True로 바꿔도 됨)
            return False

    # 버튼이 없으면: 이미 깨어있거나(또는 UI가 다름) → 워밍업 목적상 성공 처리
    print("[WAKE] no button found -> treat as OK", flush=True)
    return True

def main():
    urls = urls_from_env()
    if not urls:
        raise SystemExit("STREAMLIT_URLS is empty.")

    ok_all = True
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()

        for url in urls:
            ok_all = wake_only(page, url) and ok_all

        browser.close()

    if not ok_all:
        raise SystemExit("Some apps had wake click errors.")

if __name__ == "__main__":
    main()
