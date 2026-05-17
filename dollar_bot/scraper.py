from __future__ import annotations

import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

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

    def enabled_sources(self) -> list[dict[str, Any]]:
        return [s for s in self.config.get('sources', []) if s.get('enabled', True)]

    def run_once(self, job_id: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        sources = self.enabled_sources()
        self.storage.log('info', f'شروع دریافت قیمت دلار تهران از {len(sources)} منبع', job_id=job_id)
        for source in sources:
            row = self.collect_source(source, job_id=job_id)
            self.storage.insert_price(row)
            results.append(row)
            if self.sleep_between > 0:
                time.sleep(self.sleep_between)
        self.storage.log('info', 'پایان اجرای ربات قیمت دلار تهران', job_id=job_id, details={'count': len(results)})
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

    def collect_source(self, source: dict[str, Any], job_id: str | None = None) -> dict[str, Any]:
        collected_at = now_iso(self.tz)
        source_code = source.get('source_code', 'unknown')
        source_name = source.get('source_name', source_code)
        source_url = source.get('source_url', '')
        method = source.get('method', 'html_regex')

        try:
            if method == 'manual':
                raw_text = str(source.get('manual_price_toman', ''))
                price = normalize_price_to_toman(raw_text)
                price = self._apply_unit(source, price)
                return self._success_row(source, raw_text, price, collected_at, raw_response={'method': 'manual'})

            headers = {'User-Agent': self.user_agent, 'Accept': 'text/html,application/json'}
            response = requests.get(source_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            if method == 'json_path':
                data = response.json()
                raw_value = get_by_json_path(data, source.get('json_path', ''))
                raw_text = str(raw_value) if raw_value is not None else ''
                price = normalize_price_to_toman(raw_text)
                price = self._apply_unit(source, price)
                return self._success_row(source, raw_text, price, collected_at, raw_response=data)

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

            return self._success_row(source, raw_text, price, collected_at, raw_response={'http_status': response.status_code})

        except Exception as exc:
            msg = str(exc)
            self.storage.log('error', f'خطا در منبع {source_name}: {msg}', job_id=job_id, source_code=source_code, details={'url': source_url})
            return {
                'source_code': source_code,
                'source_name': source_name,
                'buy_price_toman': None,
                'sell_price_toman': None,
                'average_price_toman': None,
                'raw_price_text': None,
                'source_url': source_url,
                'status': 'failed',
                'error_message': msg,
                'raw_response_json': {},
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
