import sqlite3

from gameone_analyzer.events import classify, EventType
from gameone_analyzer.stats import runner_state_key

RESULT_MAP = {
    EventType.HIT_SINGLE: "1B",
    EventType.HIT_DOUBLE: "2B",
    EventType.HIT_TRIPLE: "3B",
    EventType.HOME_RUN: "HR",
    EventType.WALK: "BB",
    EventType.INTENTIONAL_WALK: "BB",
    EventType.HBP: "HBP",
    EventType.STRIKEOUT: "SO",
    EventType.STRIKEOUT_REACHED: "REACHED",
    EventType.GROUNDOUT: "OUT",
    EventType.FLYOUT: "OUT",
    EventType.LINEOUT: "OUT",
    EventType.DOUBLE_PLAY: "OUT",
    EventType.SAC_FLY: "SF",
    EventType.SAC_BUNT: "SAC",
    EventType.FIELDERS_CHOICE: "FC",
    EventType.ERROR: "ERROR",
}


def classify_result(events_codes: list) -> str:
    for code in events_codes:
        event_type = classify(code)
        if event_type == EventType.NOT_A_PLATE_APPEARANCE:
            continue
        return RESULT_MAP.get(event_type, "OTHER")
    return "OTHER"


def export_all_plate_appearances(conn: sqlite3.Connection) -> list:
    conn.row_factory = sqlite3.Row
    query = (
        "SELECT pa.*, g.season, g.league, g.venue FROM plate_appearances pa "
        "JOIN games g ON pa.game_idx = g.game_idx "
        "WHERE pa.is_our_team = 1"
    )
    records = []
    for row in conn.execute(query).fetchall():
        events_codes = [e for e in row["cell_text"].split(",") if e.strip()]
        records.append({
            "game_idx": row["game_idx"],
            "season": row["season"],
            "league": row["league"],
            "venue": row["venue"],
            "team_role": row["team"],
            "player_name": row["player_name"],
            "inning": row["inning"],
            "outs_before": row["outs_before"],
            "runner_state": runner_state_key(
                bool(row["runner_first"]), bool(row["runner_second"]), bool(row["runner_third"])
            ),
            "is_risp": bool(row["is_risp"]),
            "cell_text": row["cell_text"],
            "events": events_codes,
            "result": classify_result(events_codes),
        })
    return records
