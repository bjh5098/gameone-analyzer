from dataclasses import dataclass

from gameone_analyzer.events import classify, parse_cell, EventType


@dataclass(frozen=True)
class RunnerState:
    first: bool
    second: bool
    third: bool


@dataclass
class PlateAppearance:
    team: str
    inning: int
    order: int
    name: str
    outs_before: int
    runners_before: RunnerState
    cell_text: str
    events: list
    is_risp: bool


ADVANCE_BASES = {
    EventType.HIT_SINGLE: 1,
    EventType.WALK: 1,
    EventType.INTENTIONAL_WALK: 1,
    EventType.HBP: 1,
    EventType.ERROR: 1,
    EventType.FIELDERS_CHOICE: 1,
    EventType.HIT_DOUBLE: 2,
    EventType.HIT_TRIPLE: 3,
    EventType.HOME_RUN: 4,
}


def _advance_runners(state: RunnerState, bases: int, batter_reaches: bool):
    occupied = []
    if state.first:
        occupied.append(1)
    if state.second:
        occupied.append(2)
    if state.third:
        occupied.append(3)

    runs = 0
    new_bases = set()
    for base in occupied:
        target = base + bases
        if target >= 4:
            runs += 1
        else:
            new_bases.add(target)

    if batter_reaches:
        batter_target = bases
        if batter_target >= 4:
            runs += 1
        else:
            new_bases.add(batter_target)

    new_state = RunnerState(
        first=1 in new_bases,
        second=2 in new_bases,
        third=3 in new_bases,
    )
    return new_state, runs


def _advance_one_runner_for_steal_or_wildpitch(state: RunnerState) -> RunnerState:
    if state.third:
        return state
    if state.second:
        return RunnerState(first=state.first, second=False, third=True)
    if state.first:
        return RunnerState(first=False, second=True, third=state.third)
    return state


def apply_events(state: RunnerState, outs: int, event_codes: list):
    total_runs = 0
    for code in event_codes:
        if outs >= 3:
            break
        event_type = classify(code)

        if event_type == EventType.NOT_A_PLATE_APPEARANCE:
            continue

        if event_type == EventType.DOUBLE_PLAY:
            outs = min(outs + 2, 3)
            continue

        if event_type in (EventType.STRIKEOUT, EventType.GROUNDOUT, EventType.FLYOUT,
                           EventType.LINEOUT, EventType.SAC_FLY, EventType.SAC_BUNT):
            outs += 1
            continue

        if event_type in (EventType.CAUGHT_STEALING, EventType.RUNNER_OUT):
            outs += 1
            continue

        if event_type == EventType.STOLEN_BASE:
            state = _advance_one_runner_for_steal_or_wildpitch(state)
            continue

        if event_type == EventType.WILD_PITCH:
            state = _advance_one_runner_for_steal_or_wildpitch(state)
            continue

        if event_type in ADVANCE_BASES:
            bases = ADVANCE_BASES[event_type]
            state, runs = _advance_runners(state, bases, batter_reaches=True)
            total_runs += runs
            continue

        # UNKNOWN, BALK, PASSED_BALL, CATCHER_INTERFERENCE 등은 상태 변화 없음으로 처리
        continue

    return state, outs, total_runs


def simulate_team_innings(rows: list, team: str) -> list:
    by_inning = {}
    for row in rows:
        if row.team != team:
            continue
        for inning_idx, cell in enumerate(row.cells, start=1):
            if cell:
                by_inning.setdefault(inning_idx, []).append((row.order, row.name, cell))

    result = []
    for inning in sorted(by_inning.keys()):
        state = RunnerState(False, False, False)
        outs = 0
        for order, name, cell_text in by_inning[inning]:
            is_risp = state.second or state.third
            events_list = parse_cell(cell_text)
            result.append(
                PlateAppearance(
                    team=team,
                    inning=inning,
                    order=order,
                    name=name,
                    outs_before=outs,
                    runners_before=state,
                    cell_text=cell_text,
                    events=events_list,
                    is_risp=is_risp,
                )
            )
            state, outs, _runs = apply_events(state, outs, events_list)

    return result
