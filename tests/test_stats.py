import sqlite3

from gameone_analyzer.stats import FilterOptions, query_plate_appearances, runner_state_key, venue_matches_group


def _make_test_db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE games (
            game_idx INTEGER PRIMARY KEY, season INTEGER, league TEXT, venue TEXT,
            date_str TEXT, away_team TEXT, home_team TEXT, away_runs INTEGER,
            home_runs INTEGER, validated INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE plate_appearances (
            id INTEGER PRIMARY KEY, game_idx INTEGER, team TEXT, is_our_team INTEGER,
            inning INTEGER, batting_order INTEGER, player_name TEXT, outs_before INTEGER,
            runner_first INTEGER, runner_second INTEGER, runner_third INTEGER,
            is_risp INTEGER, cell_text TEXT
        )
    """)
    conn.execute(
        "INSERT INTO games VALUES (1, 2025, '일요 싱글', '살곶이야구장', 'd', 'X', 'Y', 5, 3, 1)"
    )
    conn.execute(
        "INSERT INTO plate_appearances VALUES "
        "(1, 1, 'home', 1, 1, 3, 'A', 1, 0, 1, 0, 1, '좌안')"
    )
    conn.execute(
        "INSERT INTO plate_appearances VALUES "
        "(2, 1, 'home', 1, 1, 4, 'B', 0, 0, 0, 0, 0, '삼진')"
    )
    conn.commit()
    return conn


def test_runner_state_key():
    assert runner_state_key(False, False, False) == "empty"
    assert runner_state_key(True, False, False) == "1"
    assert runner_state_key(False, True, True) == "23"
    assert runner_state_key(True, True, True) == "123"


def test_venue_matches_group_ignores_whitespace():
    assert venue_matches_group("구의 야구장", ["구의야구장"]) is True
    assert venue_matches_group("살곶이야구장", ["구의야구장"]) is False


def test_query_plate_appearances_filters_by_risp(tmp_path):
    conn = _make_test_db(tmp_path)
    filters = FilterOptions(outs=None, runner_states=None, risp_only=True,
                             venues=None, seasons=None, leagues=None)
    rows = query_plate_appearances(conn, filters)
    assert len(rows) == 1
    assert rows[0]["player_name"] == "A"


def test_query_plate_appearances_filters_by_outs(tmp_path):
    conn = _make_test_db(tmp_path)
    filters = FilterOptions(outs=[0], runner_states=None, risp_only=False,
                             venues=None, seasons=None, leagues=None)
    rows = query_plate_appearances(conn, filters)
    assert len(rows) == 1
    assert rows[0]["player_name"] == "B"


def test_query_plate_appearances_filters_by_season_and_league(tmp_path):
    conn = _make_test_db(tmp_path)
    filters = FilterOptions(outs=None, runner_states=None, risp_only=False,
                             venues=None, seasons=[2025], leagues=["일요 싱글"])
    rows = query_plate_appearances(conn, filters)
    assert len(rows) == 2

    filters_no_match = FilterOptions(outs=None, runner_states=None, risp_only=False,
                                      venues=None, seasons=[2024], leagues=None)
    assert query_plate_appearances(conn, filters_no_match) == []
