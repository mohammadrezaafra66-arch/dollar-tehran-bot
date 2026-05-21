from __future__ import annotations

import json
from pathlib import Path

CONFIG_PATH = Path('configs/indicators.json')

UNSTABLE_SOURCES = {
    'rahavard_afghan_usd_current': 'Disabled: Rahavard timed out in live dashboard. Needs retry/API strategy before enabling.',
    'bonbast_eur_buy': 'Disabled: Bonbast EUR buy returned empty text. Selector or page output needs verification.',
    'bonbast_eur_sell': 'Disabled: Bonbast EUR sell returned empty text. Selector or page output needs verification.',
    'iranbroker_eur_current': 'Disabled: IranBroker EUR timed out in live dashboard. Needs longer timeout or alternate feed.',
    'bonbast_usd_tehran_buy': 'Disabled: Bonbast USD buy returned empty text. Selector or page output needs verification.',
    'bonbast_usd_tehran_current': 'Disabled: Bonbast USD current/sell returned empty text. Selector or page output needs verification.',
    'signal_usd_tehran_current': 'Disabled: Signal USD timed out in live dashboard. Needs retry/API strategy before enabling.'
}


def main() -> None:
    data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    changed = []
    for indicator in data.get('indicators', []):
        for source in indicator.get('sources', []):
            code = source.get('code')
            if code in UNSTABLE_SOURCES:
                source['enabled'] = False
                source['status'] = 'disabled_after_live_error'
                source['notes'] = UNSTABLE_SOURCES[code]
                changed.append(code)
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'disabled_count': len(changed), 'disabled_sources': changed}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
