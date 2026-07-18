from typing import Any


class Deduplicator:
    @staticmethod
    def deduplicate(sellers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        unique: list[dict[str, Any]] = []
        seen = set()

        for seller in sellers:
            phone = seller.get("phone") or ""
            domain = seller.get("store_url") or seller.get("seller_url") or ""
            domain_key = Deduplicator._domain(domain)
            key = phone or domain_key
            if not key:
                key = f"fallback_{len(unique)}"
            if key in seen:
                existing = next(
                    item
                    for item in unique
                    if item.get("phone") == phone or Deduplicator._domain(item.get("store_url") or item.get("seller_url") or "") == domain_key
                )
                for field in ["phone", "email", "instagram", "telegram", "whatsapp", "crawl_status", "store_name"]:
                    if not existing.get(field) and seller.get(field):
                        existing[field] = seller[field]
                continue
            seen.add(key)
            unique.append(seller)

        return unique, max(0, len(sellers) - len(unique))

    @staticmethod
    def _domain(url: str) -> str:
        if not url:
            return ""
        url = url.replace("https://", "").replace("http://", "")
        return url.split("/")[0].split("?")[0]
