import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# 환경변수에 URL들을 줄바꿈으로 넣는 방식 추천
# 예: STREAMLIT_URLS="https://a.streamlit.app/\nhttps://b.streamlit.app/"
URLS_ENV = "STREAMLIT_URLS"

WAKE_BUTTON_TEXT_CANDIDATES = [
    "Yes, get this app back up!",
]

async def wake_one(page, url: str) -> dict:
    result = {"url": url, "status": "unknown", "woke": False}

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=90_000)

        # 1) (우선) test id / id 기반 탐색
        selectors = [
            "#wakeup-button-viewer",
            '[data-testid="wakeup-button-viewer"]',
            '[data-test-id="wakeup-button-viewer"]',
        ]

        wake_locator = None
        for sel in selectors:
            loc = page.locator(sel)
            try:
                if await loc.first.is_visible(timeout=2_000):
                    wake_locator = loc.first
                    break
            except PlaywrightTimeoutError:
                pass

        # 2) (백업) 버튼 텍스트로 탐색
        if wake_locator is None:
            for txt in WAKE_BUTTON_TEXT_CANDIDATES:
                loc = page.get_by_role("button", name=txt)
                try:
                    if await loc.is_visible(timeout=2_000):
                        wake_locator = loc
                        break
                except PlaywrightTimeoutError:
                    pass

        if wake_locator is not None:
            await wake_locator.click(timeout=10_000)
            result["woke"] = True
            result["status"] = "clicked_wake"

            # 클릭 후 앱이 로드될 시간을 조금 줌 (cold start 고려)
            await page.wait_for_timeout(15_000)
        else:
            result["status"] = "already_awake_or_unrecognized"

        return result

    except Exception as e:
        result["status"] = "error"
        result["error"] = repr(e)
        return result

async def main():
    raw = os.getenv(URLS_ENV, "").strip()
    if not raw:
        raise SystemExit(f"{URLS_ENV} env is empty. Put your app URLs separated by newlines.")

    urls = [u.strip() for u in raw.splitlines() if u.strip() and not u.strip().startswith("#")]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        results = []
        for url in urls:
            r = await wake_one(page, url)
            results.append(r)
            print(r)

        await context.close()
        await browser.close()

        # 실패가 있으면 Actions에서 눈에 띄게 실패 처리하고 싶다면 아래를 활성화
        # if any(r.get("status") == "error" for r in results):
        #     raise SystemExit("Some URLs failed")

if __name__ == "__main__":
    asyncio.run(main())
