import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.fetch import fetch_boxscore_html, load_game_ids_from_csv
from gameone_analyzer.parser import parse_game_meta, parse_batter_rows
from gameone_analyzer.simulator import simulate_team_innings
from gameone_analyzer.validator import compute_inning_runs, compare_with_scoreboard

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "gameone.db"

OUR_TEAM = "한양대학교 D-Dogs OB"

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    game_idx INTEGER PRIMARY KEY,
    season INTEGER,
    league TEXT,
    venue TEXT,
    date_str TEXT,
    away_team TEXT,
    home_team TEXT,
    away_runs INTEGER,
    home_runs INTEGER,
    validated INTEGER
);

CREATE TABLE IF NOT EXISTS plate_appearances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_idx INTEGER,
    team TEXT,
    is_our_team INTEGER,
    inning INTEGER,
    batting_order INTEGER,
    player_name TEXT,
    outs_before INTEGER,
    runner_first INTEGER,
    runner_second INTEGER,
    runner_third INTEGER,
    is_risp INTEGER,
    cell_text TEXT,
    FOREIGN KEY (game_idx) REFERENCES games(game_idx)
);
"""


def build(season_csv_row_map):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    game_ids = load_game_ids_from_csv(ROOT / "games_meta.csv")
    mismatch_log = []

    for game_idx in game_ids:
        html = fetch_boxscore_html(game_idx, CACHE_DIR, delay_sec=0)
        meta = parse_game_meta(html, game_idx)
        rows = parse_batter_rows(html)

        away_pas = simulate_team_innings(rows, team="away")
        home_pas = simulate_team_innings(rows, team="home")

        away_mismatches = compare_with_scoreboard(compute_inning_runs(away_pas), meta.away_innings)
        home_mismatches = compare_with_scoreboard(compute_inning_runs(home_pas), meta.home_innings)
        validated = 1 if not away_mismatches and not home_mismatches else 0
        if not validated:
            mismatch_log.append((game_idx, away_mismatches + home_mismatches))

        season = season_csv_row_map.get(game_idx)

        conn.execute(
            "INSERT OR REPLACE INTO games VALUES (?,?,?,?,?,?,?,?,?,?)",
            (game_idx, season, meta.league, meta.venue, meta.date_str,
             meta.away_team, meta.home_team, meta.away_runs, meta.home_runs, validated),
        )

        conn.execute("DELETE FROM plate_appearances WHERE game_idx = ?", (game_idx,))
        for pa in away_pas + home_pas:
            is_our_team = 1 if (
                (pa.team == "away" and meta.away_team == OUR_TEAM) or
                (pa.team == "home" and meta.home_team == OUR_TEAM)
            ) else 0
            conn.execute(
                "INSERT INTO plate_appearances "
                "(game_idx, team, is_our_team, inning, batting_order, player_name, "
                " outs_before, runner_first, runner_second, runner_third, is_risp, cell_text) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (game_idx, pa.team, is_our_team, pa.inning, pa.order, pa.name,
                 pa.outs_before, int(pa.runners_before.first), int(pa.runners_before.second),
                 int(pa.runners_before.third), int(pa.is_risp), pa.cell_text),
            )

    conn.commit()
    conn.close()

    print(f"done. {len(mismatch_log)} games with scoreboard mismatches:")
    for game_idx, mismatches in mismatch_log:
        print(f"  game_idx={game_idx}: {mismatches}")


if __name__ == "__main__":
    season_map = {}
    with open(ROOT / "games_meta.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            season_map[int(row["game_idx"])] = int(row["season"])

    build(season_map)
