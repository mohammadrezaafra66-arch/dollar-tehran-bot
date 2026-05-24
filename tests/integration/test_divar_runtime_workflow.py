"""Integration tests for Divar runtime workflow."""

from __future__ import annotations

from divar_bot.divar.extractor import DivarPageExtractor
from divar_bot.infra.kafka_adapter import QueueEvent


class FakeLocator:
    """Very small Playwright-like locator fake."""

    def __init__(self, text: str) -> None:
        self._text = text
        self.first = self

    def count(self) -> int:
        return 1 if self._text else 0

    def inner_text(self, timeout: int = 0) -> str:
        return self._text


class FakePage:
    """Minimal browser page fake for extraction tests."""

    def __init__(self) -> None:
        self._body = """
        فروش یخچال سامسونگ
        قیمت 25 میلیون تومان
        تهران
        محله سعادت آباد
        تماس: 09121234567
        یخچال کم کارکرد و سالم
        """

    def locator(self, selector: str) -> FakeLocator:
        if selector == "h1":
            return FakeLocator("فروش یخچال سامسونگ")
        return FakeLocator(self._body)

    def title(self) -> str:
        return "دیوار | فروش یخچال سامسونگ"


def test_divar_extraction_workflow() -> None:
    """Validate a minimal end-to-end extraction workflow."""

    event = QueueEvent(
        event_id="evt-divar-1",
        event_type="divar.extract",
        payload={"url": "https://divar.ir/v/example"},
        trace_id="trace-divar-1",
        headers={"attempt": "1"},
    )

    extractor = DivarPageExtractor()
    lead = extractor.extract(FakePage(), url=event.payload["url"])

    assert lead.source_url == "https://divar.ir/v/example"
    assert "یخچال" in lead.title
    assert lead.phone == "09121234567"
    assert lead.city == "تهران"
    assert lead.extracted_status == "ok"
