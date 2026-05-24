from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


PERSIAN_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')


@dataclass
class NormalizedPrice:
    raw: str
    value: Optional[int]
    currency: str = 'IRR'

    def to_dict(self) -> dict:
        return {
            'raw': self.raw,
            'value': self.value,
            'currency': self.currency,
        }


class PriceNormalizer:
    @staticmethod
    def normalize(price_text: str) -> NormalizedPrice:
        if not price_text:
            return NormalizedPrice(raw='', value=None)

        raw = price_text.strip()
        text = raw.translate(PERSIAN_DIGITS).translate(ARABIC_DIGITS)
        text = text.replace(',', '').replace('٬', '').replace(' ', '')

        match = re.search(r'(\d+)', text)
        if not match:
            return NormalizedPrice(raw=raw, value=None)

        value = int(match.group(1))

        if 'تومان' in raw or 'toman' in raw.lower():
            value *= 10

        return NormalizedPrice(raw=raw, value=value)
