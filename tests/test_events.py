from gameone_analyzer.events import parse_cell, split_plate_appearances, classify, is_out, EventType


def test_parse_cell_splits_on_comma():
    assert parse_cell("4구,도루,도루") == ["4구", "도루", "도루"]


def test_parse_cell_empty_string():
    assert parse_cell("") == []


def test_split_plate_appearances_splits_on_slash():
    assert split_plate_appearances("4구/삼진") == ["4구", "삼진"]


def test_split_plate_appearances_preserves_commas_within_segment():
    assert split_plate_appearances("4구,도루/좌월2") == ["4구,도루", "좌월2"]


def test_split_plate_appearances_no_slash_returns_single_segment():
    assert split_plate_appearances("좌안") == ["좌안"]


def test_split_plate_appearances_empty_string():
    assert split_plate_appearances("") == []


def test_classify_walk():
    assert classify("4구") == EventType.WALK


def test_classify_single_hit_direction_variants():
    assert classify("좌안") == EventType.HIT_SINGLE
    assert classify("중안") == EventType.HIT_SINGLE
    assert classify("우안") == EventType.HIT_SINGLE
    assert classify("2내안") == EventType.HIT_SINGLE


def test_classify_double():
    assert classify("좌전2") == EventType.HIT_DOUBLE
    assert classify("중월2") == EventType.HIT_DOUBLE


def test_classify_triple():
    assert classify("중월3") == EventType.HIT_TRIPLE


def test_classify_home_run():
    assert classify("중월홈") == EventType.HOME_RUN


def test_classify_groundout():
    assert classify("유땅") == EventType.GROUNDOUT
    assert classify("1땅") == EventType.GROUNDOUT


def test_classify_fielders_choice_with_r_suffix():
    assert classify("유땅R") == EventType.FIELDERS_CHOICE


def test_classify_flyout():
    assert classify("유플") == EventType.FLYOUT
    assert classify("2인플") == EventType.FLYOUT


def test_classify_double_play():
    assert classify("유땅병살") == EventType.DOUBLE_PLAY
    assert classify("병살") == EventType.DOUBLE_PLAY


def test_classify_error():
    assert classify("실책") == EventType.ERROR
    assert classify("3실") == EventType.ERROR
    assert classify("송구실책") == EventType.ERROR


def test_classify_stolen_base_and_caught_stealing():
    assert classify("도루") == EventType.STOLEN_BASE
    assert classify("도루자") == EventType.CAUGHT_STEALING


def test_classify_unknown_code_does_not_raise():
    assert classify("존재하지않는코드") == EventType.UNKNOWN


def test_classify_double_play_variants():
    assert classify("2땅병살") == EventType.DOUBLE_PLAY
    assert classify("투직병살") == EventType.DOUBLE_PLAY
    assert classify("유직병살") == EventType.DOUBLE_PLAY


def test_classify_fielders_choice_yaseon_variants():
    assert classify("유야선") == EventType.FIELDERS_CHOICE
    assert classify("2야선") == EventType.FIELDERS_CHOICE
    assert classify("1야선") == EventType.FIELDERS_CHOICE


def test_classify_strips_bracket_position_tag():
    assert classify("주자아웃[5C]") == EventType.RUNNER_OUT
    assert classify("송구실책[E6-3]") == EventType.ERROR
    assert classify("도루자[2-4T]") == EventType.CAUGHT_STEALING


def test_classify_pinch_hitter_is_not_plate_appearance():
    assert classify("대타") == EventType.NOT_A_PLATE_APPEARANCE


def test_classify_catcher_error_and_hit_by_ball_variants():
    assert classify("포구실책") == EventType.ERROR
    assert classify("타구맞음") == EventType.ERROR
    assert classify("주루방해") == EventType.RUNNER_OUT
    assert classify("2루타") == EventType.HIT_DOUBLE


def test_is_out_table():
    assert is_out(EventType.STRIKEOUT) is True
    assert is_out(EventType.WALK) is False
    assert is_out(EventType.DOUBLE_PLAY) is True
    assert is_out(EventType.HIT_SINGLE) is False
