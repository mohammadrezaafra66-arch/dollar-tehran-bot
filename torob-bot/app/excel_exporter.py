from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import cfg


class ExcelExporter:
    def export(self, leads: list[dict[str, Any]]) -> str:
        output_dir = Path(cfg.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        path = output_dir / f"torob_leads_{timestamp}.xlsx"

        df = pd.DataFrame(
            leads,
            columns=[
                "store_name",
                "phone",
                "email",
                "store_url",
                "instagram",
                "telegram",
                "whatsapp",
                "price_on_torob",
                "torob_url",
            ],
        )
        df.rename(
            columns={
                "store_name": "نام فروشگاه",
                "phone": "شماره موبایل",
                "email": "ایمیل",
                "store_url": "سایت فروشنده",
                "instagram": "اینستاگرام",
                "telegram": "تلگرام",
                "whatsapp": "واتساپ",
                "price_on_torob": "قیمت در ترب",
                "torob_url": "لینک ترب",
            },
            inplace=True,
        )
        df.to_excel(path, index=False, engine="openpyxl")
        return str(path)
