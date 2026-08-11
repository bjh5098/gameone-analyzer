import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.export import (
    export_all_plate_appearances,
    export_pitcher_view_records,
    assign_pitcher_to_innings,
)
from gameone_analyzer.parser import parse_pitcher_rows
from gameone_analyzer.fetch import fetch_boxscore_html

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "gameone.db"
CACHE_DIR = ROOT / "data" / "raw"
BATTER_OUT_PATH = ROOT / "docs" / "data_batter.json"
PITCHER_OUT_PATH = ROOT / "docs" / "data_pitcher.json"

OUR_TEAM = "한양대학교 D-Dogs OB"


def _build_pitcher_innings_by_game(conn: sqlite3.Connection) -> dict:
    game_ids = [row[0] for row in conn.execute("SELECT game_idx FROM games").fetchall()]
    result = {}
    for game_idx in game_ids:
        html = fetch_boxscore_html(game_idx, CACHE_DIR, delay_sec=0)
        pitcher_rows = parse_pitcher_rows(html)
        home_team = conn.execute(
            "SELECT home_team FROM games WHERE game_idx = ?", (game_idx,)
        ).fetchone()[0]
        our_side = "home" if home_team == OUR_TEAM else "away"
        our_pitchers = [r for r in pitcher_rows if r.team == our_side]
        result[game_idx] = assign_pitcher_to_innings(our_pitchers)
    return result


def main():
    conn = sqlite3.connect(DB_PATH)

    batter_records = export_all_plate_appearances(conn)
    BATTER_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATTER_OUT_PATH.write_text(json.dumps(batter_records, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(batter_records)} batter records to {BATTER_OUT_PATH}")

    pitcher_innings_by_game = _build_pitcher_innings_by_game(conn)
    pitcher_records = export_pitcher_view_records(conn, pitcher_innings_by_game)
    PITCHER_OUT_PATH.write_text(json.dumps(pitcher_records, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(pitcher_records)} pitcher records to {PITCHER_OUT_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
