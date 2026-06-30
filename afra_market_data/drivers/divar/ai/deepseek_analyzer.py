import os
import requests
import logging

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "http://localhost:11434")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-r1")
TIMEOUT = 30

PROMPT_TEMPLATE = """
تو یک تحلیلگر کوتاه تجاری هستی. اطلاعات زیر درباره یک فروشنده از سایت دیوار است:

عنوان آگهی: {title}
قیمت: {price}
توضیحات (200 کاراکتر اول): {description}
شهر: {city}

لطفا در 2 تا 3 جمله فارسی بگو:
- این فروشنده چه نوع کسب‌وکاری دارد؟
- عمده‌فروش است یا خرده‌فروش؟
- بهترین رویکرد برای تماس با او چیست؟
فقط تحلیل بنویس، بدون مقدمه.
"""


class DeepSeekAnalyzer:

    def analyze(self, lead: dict) -> str:
        prompt = PROMPT_TEMPLATE.format(
            title=lead.get("title", ""),
            price=lead.get("price_text", "نامشخص"),
            description=str(lead.get("description", ""))[:200],
            city=lead.get("city", "نامشخص"),
        )
        try:
            resp = requests.post(
                f"{DEEPSEEK_BASE_URL}/api/generate",
                json={
                    "model": DEEPSEEK_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 150},
                },
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
            logger.warning(f"DeepSeek returned {resp.status_code}")
        except requests.exceptions.ConnectionError:
            logger.info("DeepSeek not reachable - skipping AI analysis")
        except Exception as exc:
            logger.warning(f"DeepSeek error: {exc}")
        return ""

    def analyze_batch(self, leads: list) -> list:
        for lead in leads:
            if not lead.get("ai_analysis"):
                lead["ai_analysis"] = self.analyze(lead)
        return leads
