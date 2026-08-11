from gameone_analyzer.export import classify_result


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
