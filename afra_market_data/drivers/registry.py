from __future__ import annotations

from typing import Type

from afra_market_data.drivers.base_driver import BaseDriver
from afra_market_data.drivers.torob_driver import TorobDriver


DRIVER_REGISTRY: dict[str, Type[BaseDriver]] = {
    'torob': TorobDriver,
}


def get_driver_class(platform: str) -> Type[BaseDriver]:
    try:
        return DRIVER_REGISTRY[platform]
    except KeyError as exc:
        raise ValueError(f'Unsupported platform: {platform}') from exc
