from gameone_analyzer.parser import BatterRow
from gameone_analyzer.simulator import simulate_team_innings, RunnerState, apply_events


def test_apply_events_walk_puts_runner_on_first():
    state = RunnerState(first=False, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["4구"])
    assert new_state == RunnerState(first=True, second=False, third=False)
    assert outs == 0
    assert runs == 0


def test_apply_events_single_advances_existing_runner():
    state = RunnerState(first=True, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["좌안"])
    assert new_state == RunnerState(first=True, second=True, third=False)
    assert outs == 0
    assert runs == 0


def test_apply_events_home_run_scores_everyone():
    state = RunnerState(first=True, second=False, third=True)
    new_state, outs, runs = apply_events(state, 1, ["중월홈"])
    assert new_state == RunnerState(first=False, second=False, third=False)
    assert runs == 3
    assert outs == 1


def test_apply_events_strikeout_increments_outs():
    state = RunnerState(first=False, second=True, third=False)
    new_state, outs, runs = apply_events(state, 1, ["삼진"])
    assert outs == 2
    assert new_state == RunnerState(first=False, second=True, third=False)
    assert runs == 0


def test_apply_events_double_play_adds_two_outs():
    state = RunnerState(first=True, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["유땅병살"])
    assert outs == 2


def test_apply_events_walk_does_not_force_runner_on_third_with_first_open():
    state = RunnerState(first=False, second=False, third=True)
    new_state, outs, runs = apply_events(state, 0, ["4구"])
    assert new_state == RunnerState(first=True, second=False, third=True)
    assert runs == 0


def test_apply_events_walk_forces_runner_from_second_when_first_occupied():
    state = RunnerState(first=True, second=True, third=False)
    new_state, outs, runs = apply_events(state, 0, ["4구"])
    assert new_state == RunnerState(first=True, second=True, third=True)
    assert runs == 0


def test_apply_events_walk_with_bases_loaded_forces_run():
    state = RunnerState(first=True, second=True, third=True)
    new_state, outs, runs = apply_events(state, 0, ["4구"])
    assert new_state == RunnerState(first=True, second=True, third=True)
    assert runs == 1


def test_apply_events_steal_from_third_scores_a_run():
    state = RunnerState(first=True, second=True, third=True)
    new_state, outs, runs = apply_events(state, 0, ["도루"])
    assert new_state == RunnerState(first=True, second=True, third=False)
    assert runs == 1


def test_apply_events_steal_from_second_advances_to_third():
    state = RunnerState(first=True, second=True, third=False)
    new_state, outs, runs = apply_events(state, 0, ["도루"])
    assert new_state == RunnerState(first=True, second=False, third=True)
    assert runs == 0


def test_apply_events_caught_stealing_removes_lead_runner_and_adds_out():
    state = RunnerState(first=True, second=True, third=False)
    new_state, outs, runs = apply_events(state, 0, ["도루자"])
    assert new_state == RunnerState(first=True, second=False, third=False)
    assert outs == 1


def test_apply_events_runner_out_removes_lead_runner_and_adds_out():
    state = RunnerState(first=True, second=False, third=True)
    new_state, outs, runs = apply_events(state, 0, ["주자아웃"])
    assert new_state == RunnerState(first=True, second=False, third=False)
    assert outs == 1


def test_apply_events_walk_then_steal_advances_the_new_batter_not_existing_third_runner():
    # 3rd-base runner should NOT score off the batter's own steal - this is
    # the exact bug pattern from game 1563168 (walk, then steal advances
    # the batter from 1st to 2nd, not the runner already on 3rd).
    state = RunnerState(first=False, second=False, third=True)
    new_state, outs, runs = apply_events(state, 0, ["4구", "도루"])
    assert new_state == RunnerState(first=False, second=True, third=True)
    assert runs == 0


def test_apply_events_groundout_then_steal_advances_existing_runner():
    # When the plate appearance itself ends in an out, a later steal in the
    # same chain refers to an existing runner (no new runner was created).
    state = RunnerState(first=True, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["유땅", "도루"])
    assert outs == 1
    assert new_state == RunnerState(first=False, second=True, third=False)


def test_apply_events_single_then_caught_stealing_removes_the_new_batter():
    state = RunnerState(first=False, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["좌안", "도루자"])
    assert new_state == RunnerState(first=False, second=False, third=False)
    assert outs == 1


def test_apply_events_strikeout_reached_puts_batter_on_first_without_out():
    state = RunnerState(first=False, second=False, third=False)
    new_state, outs, runs = apply_events(state, 1, ["낫아웃+"])
    assert new_state == RunnerState(first=True, second=False, third=False)
    assert outs == 1


def test_apply_events_strikeout_not_reached_is_an_out():
    state = RunnerState(first=False, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["낫아웃-"])
    assert outs == 1
    assert new_state == RunnerState(first=False, second=False, third=False)


def test_simulate_team_innings_resets_outs_each_inning_and_flags_risp():
    rows = [
        BatterRow(team="home", order=1, position="중", name="A", uniform_no="1",
                   cells=["좌안", "", "", "", "", "", "", "", "", "", "", ""]),
        BatterRow(team="home", order=2, position="포", name="B", uniform_no="2",
                   cells=["좌안", "", "", "", "", "", "", "", "", "", "", ""]),
        BatterRow(team="home", order=3, position="一", name="C", uniform_no="3",
                   cells=["좌중2", "", "", "", "", "", "", "", "", "", "", ""]),
    ]
    pas = simulate_team_innings(rows, team="home")

    inning1 = [pa for pa in pas if pa.inning == 1]
    assert len(inning1) == 3

    assert inning1[0].outs_before == 0
    assert inning1[0].runners_before == RunnerState(False, False, False)
    assert inning1[0].is_risp is False

    assert inning1[1].outs_before == 0
    assert inning1[1].runners_before == RunnerState(True, False, False)
    assert inning1[1].is_risp is False

    assert inning1[2].outs_before == 0
    assert inning1[2].runners_before == RunnerState(True, True, False)
    assert inning1[2].is_risp is True


def test_simulate_team_innings_skips_empty_cells():
    rows = [
        BatterRow(team="home", order=1, position="중", name="A", uniform_no="1",
                   cells=["좌안"] + [""] * 11),
        BatterRow(team="home", order=2, position="포", name="B", uniform_no="2",
                   cells=[""] * 12),
    ]
    pas = simulate_team_innings(rows, team="home")
    assert len(pas) == 1
    assert pas[0].name == "A"
