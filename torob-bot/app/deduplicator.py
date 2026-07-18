from typing import Any
from urllib.parse import urlparse


class Deduplicator:
    @staticmethod
    def deduplicate(sellers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        unique: list[dict[str, Any]] = []

        for seller in sellers:
            phone = (seller.get("phone") or "").strip()
            domain = Deduplicator._domain(seller.get("store_url") or seller.get("seller_url") or "")

            if not phone and not domain:
                unique.append(seller)
                continue

            matched_index = None
            for idx, existing in enumerate(unique):
                existing_phone = (existing.get("phone") or "").strip()
                existing_domain = Deduplicator._domain(existing.get("store_url") or existing.get("seller_url") or "")
                if phone and existing_phone and phone == existing_phone:
                    matched_index = idx
                    break
                if domain and existing_domain and domain == existing_domain:
                    matched_index = idx
                    break

            if matched_index is not None:
                existing = unique[matched_index]
                for field in ["phone", "email", "instagram", "telegram", "whatsapp", "crawl_status", "store_name"]:
                    if not existing.get(field) and seller.get(field):
                        existing[field] = seller[field]
                if not existing.get("price_on_torob") and seller.get("price_on_torob"):
                    existing["price_on_torob"] = seller["price_on_torob"]
                continue

            unique.append(seller)

        return unique, max(0, len(sellers) - len(unique))

    @staticmethod
    def _domain(url: str) -> str:
        if not url:
            return ""
        parsed = urlparse(url)
        if not parsed.netloc:
            return ""
        host = parsed.netloc.lower()
        if "torob.com" in host or host.startswith("api."):
            return ""
        return host
