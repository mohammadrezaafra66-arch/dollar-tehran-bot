from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Any


@dataclass
class PriceAnalyticsSummary:
    count: int
    min_price: int | None
    max_price: int | None
    avg_price: float | None
    median_price: float | None
    price_spread: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            'count': self.count,
            'min_price': self.min_price,
            'max_price': self.max_price,
            'avg_price': self.avg_price,
            'median_price': self.median_price,
            'price_spread': self.price_spread,
        }


class PriceAnalytics:
    @staticmethod
    def summarize(sellers: list[dict[str, Any]]) -> PriceAnalyticsSummary:
        values = [seller.get('price_value') for seller in sellers if seller.get('price_value')]

        if not values:
            return PriceAnalyticsSummary(
                count=0,
                min_price=None,
                max_price=None,
                avg_price=None,
                median_price=None,
                price_spread=None,
            )

        min_price = min(values)
        max_price = max(values)

        return PriceAnalyticsSummary(
            count=len(values),
            min_price=min_price,
            max_price=max_price,
            avg_price=round(mean(values), 2),
            median_price=round(median(values), 2),
            price_spread=max_price - min_price,
        )
