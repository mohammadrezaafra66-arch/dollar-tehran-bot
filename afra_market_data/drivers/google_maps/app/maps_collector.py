# app/maps_collector.py - نسخه به‌روز شده با Config
from playwright.sync_api import sync_playwright
import time
import json
import re
import random
import os
from urllib.parse import quote
from app.config import Config
from app.browser_factory import launch_chromium


def human_type(page, selector, text):
    """تایپ به سبک انسان"""
    page.click(selector)
    time.sleep(random.uniform(0.3, 0.8))

    for i, char in enumerate(text):
        delay = random.uniform(0.05, 0.25)

        if random.random() < Config.MISTAKE_RATE and i > 2:
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            page.keyboard.type(wrong_char, delay=delay)
            time.sleep(random.uniform(0.1, 0.3))
            page.keyboard.press('Backspace')
            time.sleep(random.uniform(0.1, 0.2))

        page.keyboard.type(char, delay=delay)

    time.sleep(random.uniform(0.3, 0.8))


def human_like_mouse_move(page, target_x, target_y):
    """حرکت موس به سبک انسان"""
    current_x, current_y = random.randint(100, 500), random.randint(100, 300)
    steps = random.randint(5, 15)

    for i in range(steps):
        t = i / steps
        x = current_x + (target_x - current_x) * t + random.randint(-5, 5) * t
        y = current_y + (target_y - current_y) * t + random.randint(-3, 3) * t
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.01, 0.05))


def collect_businesses(search_query, max_scrolls=None, max_businesses=None):
    if max_scrolls is None:
        max_scrolls = Config.MAX_SCROLLS
    if max_businesses is None:
        max_businesses = Config.MAX_BUSINESSES_PER_QUERY

    print(f"📋 Settings: max_scrolls={max_scrolls}, max_businesses={max_businesses}")

    with sync_playwright() as p:
        browser = launch_chromium(p)
        page = browser.new_page()

        print(f"🧑 Human-like searching: {search_query}")

        print("🌍 Opening Google Maps...")
        page.goto("https://www.google.com/maps", wait_until="domcontentloaded")
        time.sleep(random.uniform(2, 4))

        print("🔍 Clicking on search box...")
        human_like_mouse_move(page, 300, 100)
        time.sleep(random.uniform(0.3, 0.6))

        search_box = page.locator('[role="combobox"]').first
        search_box.click()
        time.sleep(random.uniform(0.4, 0.8))

        print("⌨️ Typing search query...")
        human_type(page, '[role="combobox"]', search_query)

        time.sleep(random.uniform(0.5, 1.2))
        print("⏎ Pressing Enter...")
        page.keyboard.press("Enter")

        print("⏳ Waiting for results...")
        time.sleep(random.uniform(3, 6))

        feed = None
        try:
            feed = page.locator('[role="feed"]').first
            feed.wait_for(state="visible", timeout=Config.PAGE_TIMEOUT)
            print("✅ Results loaded")
        except Exception as e:
            print(f"⚠️ Feed not found: {e}")

        if feed:
            try:
                print(f"📜 Scrolling {max_scrolls} times...")
                for _ in range(max_scrolls):
                    scroll_amount = random.randint(400, 900)
                    feed.evaluate(f"el => el.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")
                    min_delay, max_delay = Config.DELAY_BETWEEN_SCROLLS
                    time.sleep(random.uniform(min_delay, max_delay))
            except Exception as e:
                print(f"  ⚠️ Scroll error: {e}")
        else:
            print("⚠️ No feed container found, skipping scroll")

        print("📋 Collecting businesses...")
        links = page.query_selector_all('a[href*="/place/"]')

        if not links:
            print("⚠️ No business links found on page")
            try:
                os.makedirs('screenshots', exist_ok=True)
                page.screenshot(path='screenshots/no_results.png')
                print("📸 Screenshot saved: screenshots/no_results.png")
            except:
                pass
            browser.close()
            return []

        businesses = []
        seen_slugs = set()

        for link in links:
            try:
                href = link.get_attribute('href')
                if not href:
                    continue

                clean_href = href.split('?')[0]
                match = re.search(r'/place/([^/?]+)', clean_href)
                if not match:
                    continue

                slug = match.group(1)
                if slug in seen_slugs:
                    continue

                seen_slugs.add(slug)
                name = link.get_attribute('aria-label') or "Unknown"

                businesses.append({
                    'slug': slug,
                    'name': name.strip(),
                    'clean_href': clean_href,
                    'raw_href': href
                })

                if max_businesses and len(businesses) >= max_businesses:
                    print(f"⚠️ Reached limit of {max_businesses} businesses, stopping collection")
                    break

            except Exception as e:
                print(f"  ⚠️ Error processing link: {e}")
                continue

        if max_businesses and len(businesses) > max_businesses:
            businesses = businesses[:max_businesses]
            print(f"⚠️ Limited to first {max_businesses} businesses")

        if not businesses:
            print("⚠️ No businesses collected!")
            browser.close()
            return []

        output = {
            'query': search_query,
            'total': len(businesses),
            'businesses': businesses,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        os.makedirs('output', exist_ok=True)
        with open('output/phase3_output.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Collected {len(businesses)} businesses")

        time.sleep(random.uniform(2, 4))
        browser.close()

        return businesses


if __name__ == "__main__":
    businesses = collect_businesses("کافی شاپ در تهران")
    print(f"\n📊 Ready for extraction ✅")
