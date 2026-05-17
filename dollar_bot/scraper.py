from __future__ import annotations

import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests import exceptions as req_exc

from .storage import Storage
from .utils import calc_average, get_by_json_path, normalize_price_to_toman, now_iso


class DollarScraper:
    def __init__(self, config: dict[str, Any], storage: Storage):
        self.config = config
        self.storage = storage
        self.tz = config.get('app', {}).get('timezone', 'Asia/Tehran')
        self.timeout = int(config.get('app', {}).get('request_timeout_seconds', 20))
        self.user_agent = config.get('app', {}).get('user_agent', 'Mozilla/5.0')
        self.sleep_between = float(config.get('app', {}).get('sleep_between_sources_seconds', 3))
        self.cache_seconds = int(config.get('app', {}).get('min_cache_seconds', 60))
        self.max_failures = int(config.get('app', {}).get('max_consecutive_failures', 3))
        self.cooldown_seconds = int(config.get('app', {}).get('cooldown_seconds', 300))

    def enabled_sources(self) -> list[dict[str, Any]]:
        return [s for s in self.config.get('sources', []) if s.get('enabled', True)]

    def run_once(self, job_id: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        sources = self.enabled_sources()
        self.storage.log('info', f'شروع دریافت شاخص‌ها از {len(sources)} منبع', job_id=job_id)
        for source in sources:
            row = self.collect_source(source, job_id=job_id)
            self.storage.insert_price(row)
            results.append(row)
            if self.sleep_between > 0:
                time.sleep(self.sleep_between)
        self.storage.log('info', 'پایان اجرای ربات شاخص‌ها', job_id=job_id, details={'count': len(results)})
        return results

    def _apply_unit(self, source: dict[str, Any], price: int | None) -> int | None:
        if price is None:
            return None
        unit = str(source.get('unit', 'toman')).lower().strip()
        if unit in ('rial', 'ریال'):
            return round(price / 10)
        multiplier = source.get('multiplier')
        if multiplier is not None:
            try:
                return round(price * float(multiplier))
            except Exception:
                return price
        return price

    def _visible_text(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        return soup.get_text(' ', strip=True)

    def _regex_extract(self, regex: str, raw_html: str) -> str:
        match = re.search(regex, raw_html, flags=re.I | re.S)
        if match:
            return match.group(1) if match.groups() else match.group(0)
        visible = self._visible_text(raw_html)
        match = re.search(regex, visible, flags=re.I | re.S)
        if match:
            return match.group(1) if match.groups() else match.group(0)
        return ''

    def _is_in_cooldown(self, source_code: str) -> tuple[bool, int]:
        health = self.storage.get_source_health(source_code)
        if not health:
            return False, 0
        until = int(health.get('cooldown_until_epoch') or 0)
        now = int(time.time())
        return until > now, max(0, until - now)

    def _cached_success_row(self, source: dict[str, Any]) -> dict[str, Any] | None:
        source_code = source.get('source_code', 'unknown')
        latest = self.storage.latest_success_for_source(source_code)
        if not latest:
            return None
        # created_at is SQLite local timestamp; for simplicity, use id-based latest plus cache only if configured positive.
        # A cached row is returned only when min_cache_seconds is set and the process just ran recently enough is not strictly knowable from Jalali collected_at.
        return None

    def _error_type_from_exception(self, exc: Exception, http_status: int | None = None) -> str:
        if http_status in (403,):
            return 'blocked_403'
        if http_status in (429,):
            return 'rate_limited_429'
        if http_status and http_status >= 500:
            return 'server_error'
        if isinstance(exc, req_exc.Timeout):
            return 'timeout'
        if isinstance(exc, req_exc.ConnectionError):
            return 'connection_error'
        if isinstance(exc, req_exc.SSLError):
            return 'ssl_error'
        if isinstance(exc, ValueError) and 'price_not_found' in str(exc):
            return 'parse_error'
        return 'unknown_error'

    def collect_source(self, source: dict[str, Any], job_id: str | None = None) -> dict[str, Any]:
        collected_at = now_iso(self.tz)
        source_code = source.get('source_code', 'unknown')
        source_name = source.get('source_name', source_code)
        source_url = source.get('source_url', '')
        method = source.get('method', 'html_regex')
        http_status: int | None = None
        response_ms: int | None = None

        in_cooldown, remaining = self._is_in_cooldown(source_code)
        if in_cooldown:
            msg = f'منبع موقتاً در حالت انتظار است؛ {remaining} ثانیه تا تلاش بعدی'
            self.storage.log('warning', msg, job_id=job_id, source_code=source_code)
            return self._failed_row(source, collected_at, 'cooldown', msg, {'cooldown_remaining_seconds': remaining})

        start = time.perf_counter()
        try:
            if method == 'manual':
                raw_text = str(source.get('manual_price_toman', ''))
                price = normalize_price_to_toman(raw_text)
                price = self._apply_unit(source, price)
                row = self._success_row(source, raw_text, price, collected_at, raw_response={'method': 'manual'})
                self.storage.record_health(source_code, source_name, True, collected_at)
                return row

            headers = {'User-Agent': self.user_agent, 'Accept': 'text/html,application/json'}
            response = requests.get(source_url, headers=headers, timeout=self.timeout)
            response_ms = round((time.perf_counter() - start) * 1000)
            http_status = response.status_code
            response.raise_for_status()

            if method == 'json_path':
                data = response.json()
                raw_value = get_by_json_path(data, source.get('json_path', ''))
                raw_text = str(raw_value) if raw_value is not None else ''
                price = normalize_price_to_toman(raw_text)
                price = self._apply_unit(source, price)
                row = self._success_row(source, raw_text, price, collected_at, raw_response={'http_status': http_status, 'response_ms': response_ms})
                self.storage.record_health(source_code, source_name, True, collected_at, http_status=http_status, response_ms=response_ms)
                return row

            text = response.text
            raw_text = ''
            if method == 'html_selector':
                soup = BeautifulSoup(text, 'html.parser')
                selector = source.get('selector')
                if not selector:
                    raise ValueError('selector is required for html_selector method')
                element = soup.select_one(selector)
                raw_text = element.get_text(' ', strip=True) if element else ''
            elif method == 'html_regex':
                regex = source.get('regex')
                if not regex:
                    raise ValueError('regex is required for html_regex method')
                raw_text = self._regex_extract(regex, text)
            else:
                raise ValueError(f'Unsupported method: {method}')

            price = normalize_price_to_toman(raw_text)
            price = self._apply_unit(source, price)
            if price is None:
                raise ValueError('price_not_found_or_not_parseable')

            row = self._success_row(source, raw_text, price, collected_at, raw_response={'http_status': http_status, 'response_ms': response_ms})
            self.storage.record_health(source_code, source_name, True, collected_at, http_status=http_status, response_ms=response_ms)
            return row

        except Exception as exc:
            response_ms = response_ms or round((time.perf_counter() - start) * 1000)
            error_type = self._error_type_from_exception(exc, http_status=http_status)
            msg = str(exc)
            current = self.storage.get_source_health(source_code) or {}
            next_failures = int(current.get('consecutive_failures', 0)) + 1
            cooldown_until = 0
            if error_type in ('blocked_403', 'rate_limited_429') or next_failures >= self.max_failures:
                cooldown_until = int(time.time()) + self.cooldown_seconds
            details = {
                'url': source_url,
                'error_type': error_type,
                'http_status': http_status,
                'response_ms': response_ms,
                'consecutive_failures_after_this': next_failures,
                'cooldown_until_epoch': cooldown_until,
            }
            self.storage.log('error', f'خطا در منبع {source_name}: {msg}', job_id=job_id, source_code=source_code, details=details)
            self.storage.record_health(source_code, source_name, False, collected_at, error_type=error_type, error_message=msg, http_status=http_status, response_ms=response_ms, cooldown_until_epoch=cooldown_until)
            return self._failed_row(source, collected_at, error_type, msg, details)

    def _failed_row(self, source: dict[str, Any], collected_at: str, error_type: str, msg: str, details: dict[str, Any]) -> dict[str, Any]:
        return {
            'source_code': source.get('source_code', 'unknown'),
            'source_name': source.get('source_name', source.get('source_code', 'unknown')),
            'buy_price_toman': None,
            'sell_price_toman': None,
            'average_price_toman': None,
            'raw_price_text': None,
            'source_url': source.get('source_url', ''),
            'status': 'failed',
            'error_message': f'{error_type}: {msg}',
            'raw_response_json': details,
            'collected_at': collected_at,
        }

    def _success_row(self, source: dict[str, Any], raw_text: str, price: int | None, collected_at: str, raw_response: Any) -> dict[str, Any]:
        price_kind = source.get('price_kind', 'average')
        buy = price if price_kind == 'buy' else None
        sell = price if price_kind == 'sell' else None
        avg = price if price_kind == 'average' else calc_average(buy, sell, None)
        return {
            'source_code': source.get('source_code'),
            'source_name': source.get('source_name', source.get('source_code')),
            'buy_price_toman': buy,
            'sell_price_toman': sell,
            'average_price_toman': avg,
            'raw_price_text': raw_text,
            'source_url': source.get('source_url'),
            'status': 'success' if price is not None else 'failed',
            'error_message': None if price is not None else 'price_not_found',
            'raw_response_json': raw_response,
            'collected_at': collected_at,
        }
