import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

import requests


# Endpoint que devuelve el último sorteo (números + fecha) en un payload tipo JSON
LATEST_URL = "https://www.megamillions.com/cmspages/utilservice.asmx/GetLatestDrawData"
FALLBACK_SITE = "https://www.megamillions.com/"


def _safe_json_from_response(text: str) -> Optional[dict]:
    """
    Algunos .asmx devuelven JSON directo, otros devuelven un wrapper.
    Este helper intenta extraer el primer objeto JSON {...}.
    """
    text = text.strip()

    # Caso 1: JSON puro
    try:
        return json.loads(text)
    except Exception:
        pass

    # Caso 2: extraer substring JSON
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return None

    return None


def _parse_money_to_int(maybe_money: Any) -> Optional[int]:
    """
    Mega Millions a veces trae jackpot como número o string. Maneja ambos.
    """
    if maybe_money is None:
        return None
    if isinstance(maybe_money, (int, float)):
        return int(maybe_money)

    s = str(maybe_money).strip()
    m = re.search(r"\$?\s*([\d.,]+)\s*(Million|Billion)?", s, re.IGNORECASE)
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
    try:
        r = requests.get(LATEST_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()

        payload = _safe_json_from_response(r.text) or {}
        # En muchos casos viene algo como {"Drawing": {...}, "Jackpot": {...}} o similar
        drawing = payload.get("Drawing") or payload.get("d") or payload

        # Campos típicos vistos en ese servicio:
        # PlayDate: "2026-01-02T00:00:00"
        play_date = drawing.get("PlayDate") if isinstance(drawing, dict) else None
        draw_iso = None
        if play_date:
            dt = datetime.fromisoformat(play_date.replace("Z", ""))
            draw_iso = dt.strftime("%Y-%m-%d")

        # N1..N5 y MBall
        nums = []
        if isinstance(drawing, dict):
            keys = ["N1", "N2", "N3", "N4", "N5"]
            if all(k in drawing for k in keys) and "MBall" in drawing:
                nums = [int(drawing[k]) for k in keys] + [int(drawing["MBall"])]

        # Jackpot (si viene)
        jackpot_amount = None
        # algunos payloads traen "Jackpot" arriba
        jp = payload.get("Jackpot") if isinstance(payload, dict) else None
        if isinstance(jp, dict):
            jackpot_amount = _parse_money_to_int(jp.get("NextJackpot") or jp.get("Jackpot") or jp.get("Amount"))
        else:
            # a veces viene como campo directo
            jackpot_amount = _parse_money_to_int(payload.get("NextJackpot") if isinstance(payload, dict) else None)

        return {
            "id": "megamillions",
            "country": "US",
            "state": "NATIONAL",
            "name": "Mega Millions",
            "date": draw_iso,
            "numbers": nums,  # [w1,w2,w3,w4,w5,megaball]
            "extra": {
                "megamultiplier": (drawing.get("Megaplier") if isinstance(drawing, dict) else None),
            },
            "jackpot": {"amount": jackpot_amount, "currency": "USD"},
            "source": LATEST_URL,
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
            "source": FALLBACK_SITE,
        }
