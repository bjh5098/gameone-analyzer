import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.export import export_all_plate_appearances

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "gameone.db"
BATTER_OUT_PATH = ROOT / "docs" / "data_batter.json"


def main():
    conn = sqlite3.connect(DB_PATH)
    records = export_all_plate_appearances(conn)
    conn.close()

    BATTER_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATTER_OUT_PATH.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(records)} batter records to {BATTER_OUT_PATH}")


if __name__ == "__main__":
    main()
