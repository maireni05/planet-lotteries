import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup


POWERBALL_URL = "https://www.powerball.com/DRAW-RESULT"


def _parse_us_money_to_int(text: str) -> Optional[int]:
    """
    Convierte textos como "$88 Million", "$1.2 Billion", "$39.8 Million" a dólares enteros.
    Devuelve None si no se puede parsear.
    """
    if not text:
        return None

    t = text.strip()
    # Ej: "$88 Million", "$1.2 Billion"
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
    # Si no hay unidad, asumimos que ya está en dólares
    return int(value)


def _extract_powerball(html: str) -> Tuple[Optional[str], list, Optional[int]]:
    """
    Retorna:
      - draw_date ISO "YYYY-MM-DD"
      - numbers: [w1,w2,w3,w4,w5,powerball]
      - jackpot_amount int (USD) o None
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    # 1) Fecha del sorteo: "Mon, Jan 5, 2026"
    dm = re.search(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Za-z]{3}\s+\d{1,2},\s+\d{4}\b", text)
    draw_iso = None
    if dm:
        dt = datetime.strptime(dm.group(0), "%a, %b %d, %Y")
        draw_iso = dt.strftime("%Y-%m-%d")

        # 2) Números: justo después de la fecha salen 6 números (5 + Powerball)
        after = text[dm.end():]
        nm = re.search(r"\b(\d{1,2})\b\s*\b(\d{1,2})\b\s*\b(\d{1,2})\b\s*\b(\d{1,2})\b\s*\b(\d{1,2})\b\s*\b(\d{1,2})\b", after)
        nums = [int(x) for x in nm.groups()] if nm else []
    else:
        nums = []

    # 3) Jackpot: "Estimated Jackpot:  $88 Million"
    jm = re.search(r"Estimated Jackpot:\s*\$?\s*([0-9][\d.,]*\s*(?:Million|Billion)?)", text, re.IGNORECASE)
    jackpot = _parse_us_money_to_int(jm.group(1)) if jm else None

    return draw_iso, nums, jackpot


def fetch() -> Dict[str, Any]:
    try:
        r = requests.get(
            POWERBALL_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        r.raise_for_status()

        draw_date, numbers, jackpot = _extract_powerball(r.text)

        return {
            "id": "powerball",
            "country": "US",
            "state": "NATIONAL",
            "name": "Powerball",
            "date": draw_date,
            "numbers": numbers,  # [w1,w2,w3,w4,w5,powerball]
            "extra": {},
            "jackpot": {"amount": jackpot, "currency": "USD"},
            "source": POWERBALL_URL,
        }

    except Exception:
        # Si falla, devolvemos estructura válida sin tumbar todo el agregador
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
