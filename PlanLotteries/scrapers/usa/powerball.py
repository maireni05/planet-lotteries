import re
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.texaslottery.com/export/sites/lottery/Games/Powerball/index.html"


def _parse_us_money_to_int(text: str) -> Optional[int]:
    if not text:
        return None
    t = text.strip()
    m = re.search(r"\$?\s*([\d.,]+)\s*(Million|Billion)?", t, re.IGNORECASE)
    if not m:
        return None

    num = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()

    if unit == "billion":
        return int(num * 1_000_000_000)
    if unit == "million":
        return int(num * 1_000_000)
    return int(num)


def fetch() -> Dict[str, Any]:
    """
    Devuelve:
      numbers = [w1,w2,w3,w4,w5,powerball]
      extra.powerplay = "2" (o "10", etc.)
      jackpot.amount = USD entero
    """
    try:
        r = requests.get(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text("\n", strip=True)

        # Ejemplo de fila (según la página):
        # 01/05/2026 4 - 18 - 24 - 51 - 56 14 2 $86 Million Roll
        row = re.search(
            r"\b(\d{2}/\d{2}/\d{4})\b\s+"
            r"(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s+"
            r"(\d{1,2})\s+"
            r"(\d{1,2})\s+"
            r"(\$[0-9][\d.,]*\s*(?:Million|Billion)?)",
            text,
        )

        draw_date_iso = None
        numbers = []
        powerplay = None
        jackpot = None

        if row:
            dt = datetime.strptime(row.group(1), "%m/%d/%Y")
            draw_date_iso = dt.strftime("%Y-%m-%d")

            w1, w2, w3, w4, w5 = map(int, row.group(2, 3, 4, 5, 6))
            pb = int(row.group(7))
            powerplay = row.group(8)
            jackpot = _parse_us_money_to_int(row.group(9))

            numbers = [w1, w2, w3, w4, w5, pb]

        return {
            "id": "powerball",
            "country": "US",
            "state": "NATIONAL",
            "name": "Powerball",
            "date": draw_date_iso,
            "numbers": numbers,
            "extra": {"powerplay": powerplay} if powerplay else {},
            "jackpot": {"amount": jackpot, "currency": "USD"},
            "source": SOURCE_URL,
        }

    except Exception:
        return {
            "id": "powerball",
            "country": "US",
            "state": "NATIONAL",
            "name": "Powerball",
            "date": None,
            "numbers": [],
            "extra": {},
            "jackpot": {"amount": None, "currency": "USD"},
            "source": SOURCE_URL,
        }
