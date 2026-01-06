import json
import os
import sys
from datetime import datetime, timezone

# Asegura que PlanLotteries/ esté en el path para poder importar scrapers/*
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scrapers.usa import powerball, megamillions  # noqa: E402


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def run_scrapers():
    scrapers = [powerball, megamillions]
    results = []

    for mod in scrapers:
        try:
            item = mod.fetch()
            if not isinstance(item, dict):
                raise TypeError("fetch() debe devolver un dict")

            # Campos mínimos esperados
            item.setdefault("id", mod.__name__)
            item.setdefault("updated_at", utc_now_iso())

            results.append(item)

        except Exception as e:
            results.append({
                "id": getattr(mod, "__name__", "unknown"),
                "error": str(e),
                "updated_at": utc_now_iso()
            })

    return results


def main():
    today = utc_today()
    updated_at = utc_now_iso()

    results_dir = os.path.join(BASE_DIR, "data", "results")
    ensure_dir(results_dir)

    payload = {
        "date": today,
        "updated_at": updated_at,
        "lotteries": run_scrapers()
    }

    # Archivo por fecha
    dated_path = os.path.join(results_dir, f"{today}.json")
    write_json(dated_path, payload)

    # “Último” (para el frontend)
    latest_path = os.path.join(results_dir, "latest.json")
    write_json(latest_path, payload)

    print(f"OK -> {dated_path}")
    print(f"OK -> {latest_path}")


if __name__ == "__main__":
    main()
