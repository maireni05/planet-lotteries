import re
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.texaslottery.com/export/sites/lottery/Games/Mega_Millions/index.html"


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
      numbers = [w1,w2,w3,w4,w5,megaball]
      extra.multipliers_available = "2X, 3X, 4X, 5X or 10X" (si aparece)
      jackpot.amount = próximo jackpot estimado (USD int), si aparece
      extra.next_draw_date = YYYY-MM-DD (si aparece)
    """
    try:
        r = requests.get(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text("\n", strip=True)

        # --- Último sorteo + números ---
        # Texto típico: "Mega Millions Winning Numbers for 01/02/2026 are: 6 13 34 43 52 4"
        m_draw = re.search(
            r"Mega Millions Winning Numbers for\s+(\d{2}/\d{2}/\d{4})\s+are:\s*"
            r"(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})",
            text,
            re.IGNORECASE,
        )

        draw_date_iso = None
        numbers = []

        if m_draw:
            dt = datetime.strptime(m_draw.group(1), "%m/%d/%Y")
            draw_date_iso = dt.strftime("%Y-%m-%d")
            numbers = [int(m_draw.group(i)) for i in range(2, 8)]

        # --- Próximo jackpot y fecha ---
        # Texto típico:
        # "Current Est. Annuitized Jackpot for 01/06/2026: $180 Million"
        m_next = re.search(
            r"Current Est\. Annuitized Jackpot for\s+(\d{2}/\d{2}/\d{4})\s*:\s*\$?([0-9][\d.,]*\s*(?:Million|Billion)?)",
            text,
            re.IGNORECASE,
        )

        next_draw_iso = None
        jackpot_amount = None
        if m_next:
            ndt = datetime.strptime(m_next.group(1), "%m/%d/%Y")
            next_draw_iso = ndt.strftime("%Y-%m-%d")
            jackpot_amount = _parse_us_money_to_int(m_next.group(2))

        # --- Multiplicadores disponibles (suele aparecer en "Past Winning Numbers" / tabla) ---
        # En la página /Winning_Numbers también aparece "2X, 3X, 4X, 5X or 10X" :contentReference[oaicite:2]{index=2}
        m_mult = re.search(r"\b(2X,\s*3X,\s*4X,\s*5X\s*or\s*10X)\b", text, re.IGNORECASE)

        extra: Dict[str, Any] = {}
        if next_draw_iso:
            extra["next_draw_date"] = next_draw_iso
        if m_mult:
            extra["multipliers_available"] = m_mult.group(1)

        return {
            "id": "megamillions",
            "country": "US",
            "state": "NATIONAL",
            "name": "Mega Millions",
            "date": draw_date_iso,
            "numbers": numbers,
            "extra": extra,
            "jackpot": {"amount": jackpot_amount, "currency": "USD"},
            "source": SOURCE_URL,
        }

    except Exception:
        return {
            "id": "megamillions",
            "country": "US",
            "state": "NATIONAL",
            "name": "Mega Millions",
            "date": None,
            "numbers": [],
            "extra": {},
            "jackpot": {"amount": None, "currency": "USD"},
            "source": SOURCE_URL,
        }
