import math
import sqlite3

from gameone_analyzer.events import classify, EventType
from gameone_analyzer.stats import runner_state_key

FRACTION_MAP = {"⅓": 1 / 3, "⅔": 2 / 3}

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


def _primary_event_type(events_codes: list):
    for code in events_codes:
        event_type = classify(code)
        if event_type == EventType.NOT_A_PLATE_APPEARANCE:
            continue
        return event_type
    return None


def classify_result(events_codes: list) -> str:
    event_type = _primary_event_type(events_codes)
    if event_type is None:
        return "OTHER"
    return RESULT_MAP.get(event_type, "OTHER")


def is_intentional_walk(events_codes: list) -> bool:
    return _primary_event_type(events_codes) == EventType.INTENTIONAL_WALK


def is_gidp(events_codes: list) -> bool:
    return _primary_event_type(events_codes) == EventType.DOUBLE_PLAY


def has_wild_pitch(events_codes: list) -> bool:
    return any(classify(code) == EventType.WILD_PITCH for code in events_codes)


def has_balk(events_codes: list) -> bool:
    return any(classify(code) == EventType.BALK for code in events_codes)


def _parse_innings_pitched(text: str) -> float:
    text = text.strip()
    for symbol, value in FRACTION_MAP.items():
        if symbol in text:
            whole_part = text.replace(symbol, "").strip()
            whole = float(whole_part) if whole_part else 0.0
            return whole + value
    return float(text) if text else 0.0


def assign_pitcher_to_innings(pitcher_rows: list) -> dict:
    mapping = {}
    current_inning = 1
    sorted_rows = sorted(pitcher_rows, key=lambda r: r.order)
    for row in sorted_rows:
        ip = _parse_innings_pitched(row.innings_pitched_str)
        num_innings = max(1, math.ceil(ip - 1e-9)) if ip > 0 else 1
        for _ in range(num_innings):
            mapping[current_inning] = row.name
            current_inning += 1
    return mapping


def export_pitcher_view_records(conn: sqlite3.Connection, pitcher_innings_by_game: dict) -> list:
    conn.row_factory = sqlite3.Row
    query = (
        "SELECT pa.*, g.season, g.league, g.venue FROM plate_appearances pa "
        "JOIN games g ON pa.game_idx = g.game_idx "
        "WHERE pa.is_our_team = 0"
    )
    records = []
    for row in conn.execute(query).fetchall():
        game_map = pitcher_innings_by_game.get(row["game_idx"], {})
        pitcher_name = game_map.get(row["inning"], "UNKNOWN")
        events_codes = [e for e in row["cell_text"].split(",") if e.strip()]
        records.append({
            "game_idx": row["game_idx"],
            "season": row["season"],
            "league": row["league"],
            "venue": row["venue"],
            "pitcher_name": pitcher_name,
            "player_name": row["player_name"],
            "batting_order": row["batting_order"],
            "inning": row["inning"],
            "outs_before": row["outs_before"],
            "runner_state": runner_state_key(
                bool(row["runner_first"]), bool(row["runner_second"]), bool(row["runner_third"])
            ),
            "is_risp": bool(row["is_risp"]),
            "cell_text": row["cell_text"],
            "events": events_codes,
            "result": classify_result(events_codes),
            "is_ibb": is_intentional_walk(events_codes),
            "is_gidp": is_gidp(events_codes),
            "has_wp": has_wild_pitch(events_codes),
            "has_bk": has_balk(events_codes),
        })
    return records


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
            "batting_order": row["batting_order"],
            "inning": row["inning"],
            "outs_before": row["outs_before"],
            "runner_state": runner_state_key(
                bool(row["runner_first"]), bool(row["runner_second"]), bool(row["runner_third"])
            ),
            "is_risp": bool(row["is_risp"]),
            "cell_text": row["cell_text"],
            "events": events_codes,
            "result": classify_result(events_codes),
            "is_ibb": is_intentional_walk(events_codes),
            "is_gidp": is_gidp(events_codes),
        })
    return records
