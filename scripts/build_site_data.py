import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.export import (
    export_all_plate_appearances,
    export_pitcher_view_records,
    assign_pitcher_to_innings,
    collect_appearance_names,
)
from gameone_analyzer.parser import parse_pitcher_rows
from gameone_analyzer.fetch import fetch_boxscore_html

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "gameone.db"
CACHE_DIR = ROOT / "data" / "raw"
BATTER_OUT_PATH = ROOT / "docs" / "data_batter.json"
PITCHER_OUT_PATH = ROOT / "docs" / "data_pitcher.json"
ROSTER_OUT_PATH = ROOT / "docs" / "data_roster.json"

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


def _build_roster_records(conn: sqlite3.Connection) -> list:
    records = []
    games = conn.execute(
        "SELECT game_idx, season, league, venue, home_team, away_team FROM games"
    ).fetchall()
    for game_idx, season, league, venue, home_team, away_team in games:
        html = fetch_boxscore_html(game_idx, CACHE_DIR, delay_sec=0)
        our_side = "home" if home_team == OUR_TEAM else "away"
        for name, roles in collect_appearance_names(html, our_side).items():
            records.append({
                "game_idx": game_idx,
                "season": season,
                "league": league,
                "venue": venue,
                "player_name": name,
                "is_batter": roles["is_batter"],
                "is_pitcher": roles["is_pitcher"],
            })
    return records


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

    roster_records = _build_roster_records(conn)
    ROSTER_OUT_PATH.write_text(json.dumps(roster_records, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(roster_records)} roster records to {ROSTER_OUT_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
