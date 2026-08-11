from pathlib import Path

from gameone_analyzer.parser import parse_game_meta, parse_batter_rows, parse_pitcher_rows

FIXTURE = Path(__file__).parent / "fixtures" / "sample_1685452.html"


def _html():
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_game_meta():
    meta = parse_game_meta(_html(), game_idx=1685452)
    assert meta.league == "일요 싱글"
    assert meta.venue == "살곶이야구장"
    assert meta.away_team == "성동 바이퍼스"
    assert meta.home_team == "한양대학교 D-Dogs OB"
    assert meta.away_runs == 8
    assert meta.home_runs == 8
    assert meta.away_innings[:4] == [2, 0, 6, 0]
    assert meta.home_innings[:4] == [2, 0, 3, 3]


def test_parse_batter_rows_first_batter():
    rows = parse_batter_rows(_html())
    away_rows = [r for r in rows if r.team == "away"]
    home_rows = [r for r in rows if r.team == "home"]
    assert len(away_rows) > 0
    assert len(home_rows) > 0

    # h3 team headings verified: away batter table lists 박준호/기효석/천준태...
    # (성동 바이퍼스 roster), home batter table lists 홍정렬/김동욱/이준희...
    # (한양대학교 D-Dogs OB roster).
    first_away = away_rows[0]
    assert first_away.order == 1
    assert first_away.name == "박준호"
    assert first_away.uniform_no == "53"
    assert first_away.position == "중"
    assert first_away.cells[0] == "4구,도루,도루"
    assert first_away.cells[1] == "4구,도루,도루"
    assert first_away.cells[2] == "4구"
    assert first_away.cells[3] == ""
    assert len(first_away.cells) == 12

    first_home = home_rows[0]
    assert first_home.name == "홍정렬"


def test_parse_batter_rows_third_away_batter():
    rows = parse_batter_rows(_html())
    away_rows = [r for r in rows if r.team == "away"]
    third = away_rows[2]
    assert third.name == "천준태"
    assert third.cells[0] == "좌안"
    assert third.cells[1] == "유플"
    assert third.cells[2] == "투야선"


def test_parse_pitcher_rows():
    rows = parse_pitcher_rows(_html())
    away_pitchers = [r for r in rows if r.team == "away"]
    assert away_pitchers[0].name == "민호진"
    assert away_pitchers[0].innings_pitched_str == "2 ⅓"
    assert away_pitchers[0].order == 1
    assert away_pitchers[1].name == "박준호"
    assert away_pitchers[1].order == 2
