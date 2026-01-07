import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

POWERBALL_URL = "https://www.powerball.com/draw-result"


def _parse_us_money_to_int(text: str) -> Optional[int]:
    if not text:
        return None

    t = text.strip()
    m = re.search(r"\$?\s*([\d.,]+)\s*(Million|Billion)?", t, re.IGNORECASE)
    if not m:
        return None

    num_str = m.group(1).replace(",", "")
    unit = (m.group(2) or "").lower()

    try:
        value = float(num_str)
    except ValueError:
        return None

    if unit == "billion":
        return int(value * 1_000_000_000)
    if unit == "million":
        return int(value * 1_000_000)
    return int(value)


def _extract_powerball_from_text(text: str) -> Tuple[Optional[str], list, Dict[str, Any], Optional[int]]:
    """
    Intenta extraer:
      - fecha (YYYY-MM-DD)
      - números (6: 5 blancos + powerball)
      - extra: powerplay (ej: "2x")
      - jackpot estimado (int USD)
    """
    # Fecha: "Mon, Jan 5, 2026"
    dm = re.search(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Za-z]{3}\s+\d{1,2},\s+\d{4}\b", text)
    draw_iso = None
    nums = []
    extra: Dict[str, Any] = {}

    if dm:
        dt = datetime.strptime(dm.group(0), "%a, %b %d, %Y")
        draw_iso = dt.strftime("%Y-%m-%d")

        after = text[dm.end():]
        nm = re.search(
            r"\b(\d{1,2})\b\s+\b(\d{1,2})\b\s+\b(\d{1,2})\b\s+\b(\d{1,2})\b\s+\b(\d{1,2})\b\s+\b(\d{1,2})\b",
            after,
        )
        if nm:
            nums = [int(x) for x in nm.groups()]

    pm = re.search(r"Power\s*Play\s*([0-9]+x)\b", text, re.IGNORECASE)
    if pm:
        extra["powerplay"] = pm.group(1)

    jm = re.search(r"Estimated Jackpot:\s*\$?\s*([0-9][\d.,]*\s*(?:Million|Billion)?)", text, re.IGNORECASE)
    jackpot = _parse_us_money_to_int(jm.group(1)) if jm else None

    return draw_iso, nums, extra, jackpot


def fetch() -> Dict[str, Any]:
    try:
        r = requests.get(
            POWERBALL_URL,
            headers={
                "User-Agent": "Mozilla/5.0",
            },
            timeout=30,
        )
        r.raise_for_status()

        # Asegura texto legible (por si viniera algún byte raro)
        html = r.content.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)

        draw_date, numbers, extra, jackpot = _extract_powerball_from_text(text)

        return {
            "id": "powerball",
            "country": "US",
            "state": "NATIONAL",
            "name": "Powerball",
            "date": draw_date,
            "numbers": numbers,
            "extra": extra,
            "jackpot": {"amount": jackpot, "currency": "USD"},
            "source": POWERBALL_URL,
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
            "source": POWERBALL_URL,
        }
