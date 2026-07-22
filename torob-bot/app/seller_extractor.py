"""استخراج فروشندگان از صفحه محصول ترب."""
from typing import Any
from app.config import cfg


class SellerExtractor:
    def parse(self, payload: dict[str, Any], product_url: str) -> list[dict[str, Any]]:
        page_props = payload.get("props", {}).get("pageProps", {})
        product_data = page_props.get("baseProduct") or page_props.get("product") or {}
        products_info = product_data.get("products_info", {}) or {}
        result = products_info.get("result", []) or []

        sellers: list[dict[str, Any]] = []
        for item in result[:cfg.TOROB_MAX_SELLERS]:
            sellers.append({
                "name": item.get("shop_name") or item.get("name1") or item.get("name2") or "unknown",
                "price": int(item.get("price") or 0),
                "seller_url": item.get("page_url") or product_url,
                "torob_url": product_url,
            })
        return sellers
