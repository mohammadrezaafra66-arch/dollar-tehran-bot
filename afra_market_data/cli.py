from __future__ import annotations
import argparse, json, time
from .core import run_once, load_config, post_to_afra


def main():
    p=argparse.ArgumentParser('afra-market-data')
    p.add_argument('command', nargs='?', default='run-once', choices=['run-once','run-loop','post'])
    p.add_argument('--config', default='configs/indicators.json')
    args=p.parse_args()
    if args.command=='run-once':
        payload=run_once(args.config)
        print(json.dumps(payload['meta'], ensure_ascii=False, indent=2))
    elif args.command=='post':
        cfg=load_config(args.config); payload=run_once(args.config)
        ok,msg=post_to_afra(payload,cfg)
        print(('OK: ' if ok else 'ERROR: ')+msg)
    else:
        cfg=load_config(args.config); mins=cfg.get('schedule',{}).get('interval_minutes',3)
        while True:
            run_once(args.config)
            print(f'next run in {mins} minutes')
            time.sleep(mins*60)

if __name__ == '__main__': main()
