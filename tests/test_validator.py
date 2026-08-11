from gameone_analyzer.parser import BatterRow
from gameone_analyzer.simulator import simulate_team_innings
from gameone_analyzer.validator import compute_inning_runs, compare_with_scoreboard


def test_compute_inning_runs_matches_home_run():
    rows = [
        BatterRow(team="home", order=1, position="중", name="A", uniform_no="1",
                   cells=["4구"] + [""] * 11),
        BatterRow(team="home", order=2, position="포", name="B", uniform_no="2",
                   cells=["중월홈"] + [""] * 11),
    ]
    pas = simulate_team_innings(rows, team="home")
    runs = compute_inning_runs(pas)
    assert runs == {1: 2}


def test_compare_with_scoreboard_detects_mismatch():
    sim_runs = {1: 2, 2: 0}
    scoreboard = [3, 0]
    mismatches = compare_with_scoreboard(sim_runs, scoreboard)
    assert len(mismatches) == 1
    assert "inning 1" in mismatches[0]


def test_compare_with_scoreboard_matches():
    sim_runs = {1: 2, 2: 1}
    scoreboard = [2, 1]
    assert compare_with_scoreboard(sim_runs, scoreboard) == []
