from __future__ import annotations

from typing import Any

import requests


class AfraKalaSync:
    def __init__(self, config: dict[str, Any]):
        sync = config.get('sync', {})
        self.enabled = bool(sync.get('enabled', False))
        self.base_url = str(sync.get('afrakala_api_base_url', '')).rstrip('/')
        self.api_key = str(sync.get('afrakala_bot_api_key', ''))
        self.table_slug = str(sync.get('dynamic_table_slug', ''))
        self.table_id = str(sync.get('dynamic_table_id', ''))

    def _headers(self) -> dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-Bot-Api-Key'] = self.api_key
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def resolve_table_id(self) -> str:
        if self.table_id:
            return self.table_id
        if not self.base_url or not self.table_slug:
            raise ValueError('AfraKala base_url or dynamic_table_slug is missing')
        url = f'{self.base_url}/api/public/bot/dynamic-tables/by-slug/{self.table_slug}'
        r = requests.get(url, headers=self._headers(), timeout=20)
        r.raise_for_status()
        data = r.json()
        table_id = data.get('id') or data.get('table_id') or data.get('uuid')
        if not table_id:
            raise ValueError(f'Could not find table id in response: {data}')
        self.table_id = str(table_id)
        return self.table_id

    def push_rows(self, rows: list[dict[str, Any]]) -> None:
        if not self.enabled:
            return
        table_id = self.resolve_table_id()
        url = f'{self.base_url}/api/public/bot/dynamic-tables/{table_id}/rows/upsert'
        for row in rows:
            values = dict(row)
            values['unique_key'] = f"{row.get('source_code')}-{row.get('collected_at')}"
            payload = {
                'unique_by': ['unique_key'],
                'values': values,
            }
            r = requests.post(url, headers=self._headers(), json=payload, timeout=30)
            r.raise_for_status()
