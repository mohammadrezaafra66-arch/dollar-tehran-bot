from __future__ import annotations

import json
from pathlib import Path

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover
    Workbook = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
INPUT_JSON = DATA_DIR / 'panel_google_maps_inputs.json'
MANAGE_JSON = DATA_DIR / 'panel_google_maps_manage.json'
INPUT_XLSX = BASE_DIR / 'google_maps_input.xlsx'
MANAGE_XLSX = BASE_DIR / 'google_maps_management.xlsx'


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def write_input_excel() -> dict:
    if Workbook is None:
        return {'ok': False, 'error': 'openpyxl is not installed'}
    data = read_json(INPUT_JSON, {'items': []})
    wb = Workbook()
    ws = wb.active
    ws.title = 'Input'
    headers = ['استان', 'شهر', 'کلمه اصلی', 'برند', 'کلمات مرتبط', 'دسته بندی', 'active']
    ws.append(headers)
    for item in data.get('items', []):
        ws.append([
            item.get('province', ''),
            item.get('city', ''),
            item.get('keyword', ''),
            item.get('brand', ''),
            item.get('related_keywords', ''),
            item.get('category', ''),
            item.get('active', True),
        ])
    wb.save(INPUT_XLSX)
    return {'ok': True, 'path': str(INPUT_XLSX), 'rows': len(data.get('items', []))}


def write_manage_excel() -> dict:
    if Workbook is None:
        return {'ok': False, 'error': 'openpyxl is not installed'}
    data = read_json(MANAGE_JSON, {})
    wb = Workbook()
    ws = wb.active
    ws.title = 'Config'
    ws.append(['key', 'value'])
    def flatten(prefix: str, value):
        if isinstance(value, dict):
            for k, v in value.items():
                yield from flatten(f'{prefix}.{k}' if prefix else k, v)
        else:
            yield prefix, value
    for key, value in flatten('', data):
        ws.append([key, value])
    wb.save(MANAGE_XLSX)
    return {'ok': True, 'path': str(MANAGE_XLSX)}


def sync_all() -> dict:
    return {'input': write_input_excel(), 'manage': write_manage_excel()}


if __name__ == '__main__':
    print(sync_all())
