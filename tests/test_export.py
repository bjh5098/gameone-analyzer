import sqlite3

from gameone_analyzer.export import (
    classify_result,
    assign_pitcher_to_innings,
    export_all_plate_appearances,
    export_pitcher_view_records,
    is_intentional_walk,
    is_gidp,
    has_wild_pitch,
    has_balk,
)
from gameone_analyzer.parser import PitcherRow


def test_classify_result_single():
    assert classify_result(["좌안"]) == "1B"


def test_classify_result_home_run():
    assert classify_result(["중월홈"]) == "HR"


def test_classify_result_walk():
    assert classify_result(["4구"]) == "BB"


def test_classify_result_strikeout():
    assert classify_result(["삼진"]) == "SO"


def test_classify_result_groundout():
    assert classify_result(["유땅"]) == "OUT"


def test_classify_result_double_play():
    assert classify_result(["유땅병살"]) == "OUT"


def test_classify_result_sac_fly():
    assert classify_result(["중희플"]) == "SF"


def test_classify_result_skips_pinch_runner_prefix():
    assert classify_result(["대주자", "삼진"]) == "SO"


def test_classify_result_error():
    assert classify_result(["실책"]) == "ERROR"


def test_classify_result_fielders_choice():
    assert classify_result(["투야선"]) == "FC"


def test_classify_result_unknown_defaults_other():
    assert classify_result(["존재하지않는코드XYZ"]) == "OTHER"


def test_classify_result_strikeout_reached_counts_as_reached_on_error_style():
    assert classify_result(["낫아웃+"]) == "REACHED"


def test_is_intentional_walk_true():
    assert is_intentional_walk(["고의4구"]) is True


def test_is_intentional_walk_false_for_regular_walk():
    assert is_intentional_walk(["4구"]) is False


def test_is_gidp_true():
    assert is_gidp(["유땅병살"]) is True


def test_is_gidp_false_for_regular_groundout():
    assert is_gidp(["유땅"]) is False


def test_has_wild_pitch_true_when_present_anywhere_in_chain():
    assert has_wild_pitch(["4구", "도루", "폭투"]) is True


def test_has_wild_pitch_false_when_absent():
    assert has_wild_pitch(["4구", "도루"]) is False


def test_has_balk_true_when_present_anywhere_in_chain():
    assert has_balk(["4구", "보크"]) is True


def test_has_balk_false_when_absent():
    assert has_balk(["4구"]) is False


def test_assign_pitcher_to_innings_simple():
    rows = [
        PitcherRow(team="home", name="민호진", uniform_no="21", innings_pitched_str="2 ⅓", order=1),
        PitcherRow(team="home", name="박준호", uniform_no="53", innings_pitched_str="0 ⅔", order=2),
        PitcherRow(team="home", name="민윤기", uniform_no="45", innings_pitched_str="1", order=3),
    ]
    mapping = assign_pitcher_to_innings(rows)
    assert mapping[1] == "민호진"
    assert mapping[2] == "민호진"
    assert mapping[3] == "민호진"
    assert mapping[4] == "박준호"
    assert mapping[5] == "민윤기"


def test_assign_pitcher_to_innings_no_fraction():
    rows = [
        PitcherRow(team="home", name="A", uniform_no="1", innings_pitched_str="3", order=1),
        PitcherRow(team="home", name="B", uniform_no="2", innings_pitched_str="2", order=2),
    ]
    mapping = assign_pitcher_to_innings(rows)
    assert mapping[1] == "A"
    assert mapping[3] == "A"
    assert mapping[4] == "B"
    assert mapping[5] == "B"


def test_export_pitcher_view_records(tmp_path):
    db_path = tmp_path / "t.db"
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
        "INSERT INTO games VALUES (1, 2025, '일요 싱글', '살곶이야구장', 'd', 'OPP', "
        "'한양대학교 D-Dogs OB', 3, 5, 1)"
    )
    conn.execute(
        "INSERT INTO plate_appearances VALUES "
        "(1, 1, 'away', 0, 1, 1, 'OppBatter', 0, 0, 0, 0, 0, '좌안')"
    )
    conn.commit()

    pitcher_innings_by_game = {1: {1: "민호진"}}
    records = export_pitcher_view_records(conn, pitcher_innings_by_game)
    assert len(records) == 1
    assert records[0]["pitcher_name"] == "민호진"
    assert records[0]["player_name"] == "OppBatter"
    assert records[0]["result"] == "1B"
    assert records[0]["batting_order"] == 1


def test_export_all_plate_appearances_includes_batting_order(tmp_path):
    db_path = tmp_path / "t.db"
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
        "INSERT INTO games VALUES (1, 2025, '일요 싱글', '살곶이야구장', 'd', 'OPP', "
        "'한양대학교 D-Dogs OB', 3, 5, 1)"
    )
    conn.execute(
        "INSERT INTO plate_appearances VALUES "
        "(1, 1, 'home', 1, 1, 4, 'OurBatter', 0, 0, 0, 0, 0, '좌안')"
    )
    conn.commit()

    records = export_all_plate_appearances(conn)
    assert len(records) == 1
    assert records[0]["batting_order"] == 4
    assert records[0]["player_name"] == "OurBatter"
