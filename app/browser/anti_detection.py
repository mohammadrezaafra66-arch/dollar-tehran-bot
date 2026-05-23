from __future__ import annotations

import asyncio
import random
from playwright.async_api import Page


class AntiDetection:
    @staticmethod
    async def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    @staticmethod
    async def human_scroll(page: Page):
        scroll_amounts = [200, 300, 450, 600]

        for amount in scroll_amounts:
            await page.mouse.wheel(0, amount)
            await asyncio.sleep(random.uniform(0.3, 1.2))

    @staticmethod
    async def human_mouse_move(page: Page):
        width = random.randint(200, 1200)
        height = random.randint(200, 700)
        await page.mouse.move(width, height)

    @staticmethod
    def random_user_agent() -> str:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0 Safari/537.36',
        ]
        return random.choice(user_agents)
