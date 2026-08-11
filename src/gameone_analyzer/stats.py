import sqlite3
from dataclasses import dataclass


@dataclass
class FilterOptions:
    outs: list
    runner_states: list
    risp_only: bool
    venues: list
    seasons: list
    leagues: list


def runner_state_key(first: bool, second: bool, third: bool) -> str:
    bases = []
    if first:
        bases.append("1")
    if second:
        bases.append("2")
    if third:
        bases.append("3")
    return "".join(bases) if bases else "empty"


def venue_matches_group(venue: str, group_venues: list) -> bool:
    normalized = venue.replace(" ", "")
    return any(normalized == v.replace(" ", "") for v in group_venues)


def query_plate_appearances(conn: sqlite3.Connection, filters: FilterOptions):
    conn.row_factory = sqlite3.Row
    query = (
        "SELECT pa.* FROM plate_appearances pa "
        "JOIN games g ON pa.game_idx = g.game_idx "
        "WHERE pa.is_our_team = 1"
    )
    params = []

    if filters.risp_only:
        query += " AND pa.is_risp = 1"

    if filters.outs:
        placeholders = ",".join("?" for _ in filters.outs)
        query += f" AND pa.outs_before IN ({placeholders})"
        params.extend(filters.outs)

    if filters.seasons:
        placeholders = ",".join("?" for _ in filters.seasons)
        query += f" AND g.season IN ({placeholders})"
        params.extend(filters.seasons)

    if filters.leagues:
        placeholders = ",".join("?" for _ in filters.leagues)
        query += f" AND g.league IN ({placeholders})"
        params.extend(filters.leagues)

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    if filters.runner_states:
        rows = [
            r for r in rows
            if runner_state_key(bool(r["runner_first"]), bool(r["runner_second"]), bool(r["runner_third"]))
            in filters.runner_states
        ]

    if filters.venues:
        game_venue = {
            row["game_idx"]: row["venue"]
            for row in conn.execute("SELECT game_idx, venue FROM games").fetchall()
        }
        rows = [
            r for r in rows
            if venue_matches_group(game_venue.get(r["game_idx"], ""), filters.venues)
        ]

    return rows
