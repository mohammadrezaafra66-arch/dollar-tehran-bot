"""End-to-end Divar extraction pipeline.

This module connects listing discovery, detail extraction, deduplication, and
final export into one bot-level pipeline. It is intentionally independent from
web-app concerns and can be invoked by CLI, scheduler, or distributed runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from divar_bot.data.deduplication import LeadDeduplicator
from divar_bot.divar.detail_extractor import DivarAdDetail, DivarDetailExtractor
from divar_bot.divar.listing_crawler import DivarListingCrawler, DivarListingCrawlerSettings
from divar_bot.export.final_exporter import FinalLeadExporter
from divar_bot.infra.browser_pool import BrowserPool
from divar_bot.infra.structured_logging import StructuredLogger
from divar_bot.infra.tracing import RuntimeTracer, TraceAttributes


@dataclass(frozen=True)
class DivarPipelineSettings:
    """Settings for a full Divar pipeline run."""

    max_ads: int = 100
    max_scrolls: int = 10
    export_enabled: bool = True


@dataclass(frozen=True)
class DivarPipelineResult:
    """Summary of one Divar pipeline run."""

    listing_url: str
    discovered_ads: int
    extracted_ads: int
    failed_ads: int
    duplicate_count: int
    export_paths: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class DivarExtractionPipeline:
    """Runs listing crawl, detail extraction, deduplication, and export."""

    def __init__(
        self,
        browser_pool: Optional[BrowserPool] = None,
        settings: Optional[DivarPipelineSettings] = None,
    ) -> None:
        self.settings = settings or DivarPipelineSettings()
        self.browser_pool = browser_pool or BrowserPool()
        self.logger = StructuredLogger("afra.divar.pipeline")
        self.tracer = RuntimeTracer("afra.divar.pipeline")
        self.crawler = DivarListingCrawler(
            DivarListingCrawlerSettings(
                max_scrolls=self.settings.max_scrolls,
                max_ads=self.settings.max_ads,
            )
        )
        self.detail_extractor = DivarDetailExtractor()
        self.deduplicator = LeadDeduplicator()
        self.exporter = FinalLeadExporter()

    def run(self, listing_url: str) -> DivarPipelineResult:
        """Run the complete Divar bot pipeline for one listing URL."""

        errors: List[str] = []
        extracted: List[Dict[str, Any]] = []

        with self.tracer.span(
            "divar.pipeline.run",
            TraceAttributes(plugin_name="divar", stage_name="pipeline", extra={"listing_url": listing_url}),
        ):
            self.logger.info("divar_pipeline_started", listing_url=listing_url)

            with self.browser_pool.session(metadata={"stage": "listing", "listing_url": listing_url}) as listing_lease:
                listing_result = self.crawler.crawl(listing_lease.page, listing_url)

            if listing_result.status != "ok":
                errors.append(listing_result.error)
                self.logger.error("divar_listing_failed", listing_url=listing_url, error=listing_result.error)
                return DivarPipelineResult(
                    listing_url=listing_url,
                    discovered_ads=0,
                    extracted_ads=0,
                    failed_ads=0,
                    duplicate_count=0,
                    errors=errors,
                )

            self.logger.info("divar_listing_completed", listing_url=listing_url, discovered_ads=len(listing_result.ads))

            failed_ads = 0
            for ad in listing_result.ads:
                with self.tracer.span(
                    "divar.detail.extract",
                    TraceAttributes(plugin_name="divar", stage_name="detail", extra={"ad_url": ad.url, "slug": ad.slug}),
                ):
                    try:
                        with self.browser_pool.session(metadata={"stage": "detail", "ad_url": ad.url}) as detail_lease:
                            detail = self.detail_extractor.extract(detail_lease.page, ad.url)
                        extracted.append(self._detail_to_lead(detail))
                        if detail.extraction_status in {"navigation_failed", "partial"}:
                            failed_ads += 1
                    except Exception as exc:
                        failed_ads += 1
                        message = f"{ad.url}: {type(exc).__name__}: {str(exc)[:300]}"
                        errors.append(message)
                        self.logger.exception("divar_detail_failed", ad_url=ad.url, error_type=type(exc).__name__)

            deduped = self.deduplicator.deduplicate(extracted)
            export_paths: Dict[str, str] = {}
            if self.settings.export_enabled:
                export_paths = self.exporter.export(deduped.unique_leads)

            result = DivarPipelineResult(
                listing_url=listing_url,
                discovered_ads=len(listing_result.ads),
                extracted_ads=len(extracted),
                failed_ads=failed_ads,
                duplicate_count=deduped.duplicate_count,
                export_paths=export_paths,
                errors=errors,
            )

            self.logger.info(
                "divar_pipeline_completed",
                listing_url=listing_url,
                discovered_ads=result.discovered_ads,
                extracted_ads=result.extracted_ads,
                failed_ads=result.failed_ads,
                duplicate_count=result.duplicate_count,
                export_paths=export_paths,
            )
            return result

    def _detail_to_lead(self, detail: DivarAdDetail) -> Dict[str, Any]:
        """Convert DivarAdDetail to final export lead schema."""

        return {
            "source_platform": "divar",
            "source_url": detail.source_url,
            "title": detail.title,
            "price_text": detail.price_text,
            "seller_name": detail.seller_name,
            "phone": detail.phone,
            "city": detail.city,
            "district": detail.district,
            "description": detail.description,
            "extracted_status": detail.extraction_status,
        }
