from gameone_analyzer.simulator import apply_events


def compute_inning_runs(pas: list) -> dict:
    runs_by_inning = {}
    for pa in pas:
        _state, _outs, runs = apply_events(pa.runners_before, pa.outs_before, pa.events)
        runs_by_inning[pa.inning] = runs_by_inning.get(pa.inning, 0) + runs
    return runs_by_inning


def compare_with_scoreboard(sim_runs: dict, scoreboard_innings: list) -> list:
    mismatches = []
    for idx, expected in enumerate(scoreboard_innings, start=1):
        if expected is None:
            continue
        actual = sim_runs.get(idx, 0)
        if actual != expected:
            mismatches.append(
                f"inning {idx}: simulated={actual} scoreboard={expected}"
            )
    return mismatches
