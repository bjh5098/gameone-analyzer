from dataclasses import dataclass

from gameone_analyzer.events import classify, parse_cell, split_plate_appearances, EventType


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
    EventType.HIT_DOUBLE: 2,
    EventType.HIT_TRIPLE: 3,
    EventType.HOME_RUN: 4,
}

FORCE_ADVANCE_EVENTS = {
    EventType.WALK,
    EventType.INTENTIONAL_WALK,
    EventType.HBP,
    EventType.ERROR,
    EventType.FIELDERS_CHOICE,
    EventType.CATCHER_INTERFERENCE,
    EventType.STRIKEOUT_REACHED,
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


def _force_advance(state: RunnerState):
    """Batter reaches first (walk/HBP/error/fielders choice). Only runners in
    a forced chain starting from first base are pushed forward - e.g. a runner
    on 3rd with 1st open does NOT advance on a walk, unlike a hit."""
    runs = 0
    new_first = True
    if state.first:
        new_second = True
        if state.second:
            new_third = True
            if state.third:
                runs += 1
        else:
            new_third = state.third
    else:
        new_second = state.second
        new_third = state.third

    new_state = RunnerState(first=new_first, second=new_second, third=new_third)
    return new_state, runs


def _advance_from_base(state: RunnerState, base: int):
    """Advances the runner on the given base (1/2/3) by one base. Returns
    (new_state, runs, new_active_base) where new_active_base is None if the
    runner scored or the base was empty."""
    if base == 1 and state.first:
        if state.second:
            return state, 0, 1  # can't advance into occupied base; treat as no-op
        return RunnerState(first=False, second=True, third=state.third), 0, 2
    if base == 2 and state.second:
        if state.third:
            return state, 0, 2
        return RunnerState(first=state.first, second=False, third=True), 0, 3
    if base == 3 and state.third:
        return RunnerState(first=state.first, second=state.second, third=False), 1, None
    return state, 0, None


def _advance_lead_runner(state: RunnerState):
    """Advances the most-advanced occupied base by one (steal/wild pitch with
    no clearer target - existing runner play, not tied to the batter)."""
    if state.third:
        return _advance_from_base(state, 3)
    if state.second:
        return _advance_from_base(state, 2)
    if state.first:
        return _advance_from_base(state, 1)
    return state, 0, None


def _remove_from_base(state: RunnerState, base: int) -> RunnerState:
    if base == 1:
        return RunnerState(first=False, second=state.second, third=state.third)
    if base == 2:
        return RunnerState(first=state.first, second=False, third=state.third)
    if base == 3:
        return RunnerState(first=state.first, second=state.second, third=False)
    return state


def _remove_lead_runner(state: RunnerState) -> RunnerState:
    """A runner is thrown/picked out with no clearer target - existing runner
    play, not tied to the batter. Approximate by removing the most advanced
    runner."""
    if state.third:
        return _remove_from_base(state, 3)
    if state.second:
        return _remove_from_base(state, 2)
    if state.first:
        return _remove_from_base(state, 1)
    return state


RUNNER_ADVANCE_EVENTS = {EventType.STOLEN_BASE, EventType.WILD_PITCH}
RUNNER_OUT_EVENTS = {EventType.CAUGHT_STEALING, EventType.RUNNER_OUT}


def apply_events(state: RunnerState, outs: int, event_codes: list):
    """Replays one plate appearance's event chain.

    gameone.kr chains events like "4구,도루,도루자" in the order they
    happened. When an event puts the batter on base (walk/hit/error/etc,
    or 낫아웃+), any 도루/폭투/도루자/주자아웃/런다운 immediately following
    it refers to THAT runner (verified: 320+ chained-event cells in the
    dataset, 0 counterexamples). Only when the preceding event was an out
    with no new runner created does a bare steal/caught-stealing code refer
    to an existing runner - approximated as the most advanced one, since
    which specific runner is genuinely ambiguous from the code alone (see
    CLAUDE.md known limitation)."""
    total_runs = 0
    active_base = None  # base the batter/most-recent runner is currently on

    for code in event_codes:
        if outs >= 3:
            break
        event_type = classify(code)

        if event_type == EventType.NOT_A_PLATE_APPEARANCE:
            continue

        if event_type == EventType.DOUBLE_PLAY:
            outs = min(outs + 2, 3)
            active_base = None
            continue

        if event_type in (EventType.STRIKEOUT, EventType.GROUNDOUT, EventType.FLYOUT,
                           EventType.LINEOUT, EventType.SAC_FLY, EventType.SAC_BUNT):
            outs += 1
            active_base = None
            continue

        if event_type in RUNNER_OUT_EVENTS:
            outs += 1
            if active_base is not None:
                state = _remove_from_base(state, active_base)
            else:
                state = _remove_lead_runner(state)
            active_base = None
            continue

        if event_type in RUNNER_ADVANCE_EVENTS:
            if active_base is not None:
                state, runs, active_base = _advance_from_base(state, active_base)
            else:
                state, runs, active_base = _advance_lead_runner(state)
            total_runs += runs
            continue

        if event_type in FORCE_ADVANCE_EVENTS:
            state, runs = _force_advance(state)
            total_runs += runs
            active_base = 1
            continue

        if event_type in ADVANCE_BASES:
            bases = ADVANCE_BASES[event_type]
            state, runs = _advance_runners(state, bases, batter_reaches=True)
            total_runs += runs
            active_base = bases if bases < 4 else None
            continue

        # UNKNOWN, BALK, PASSED_BALL, CATCHER_INTERFERENCE 등은 상태 변화 없음으로 처리
        active_base = None
        continue

    return state, outs, total_runs


def simulate_team_innings(rows: list, team: str) -> list:
    team_rows = [row for row in rows if row.team == team]
    if not team_rows:
        return []
    lineup_size = max(row.order for row in team_rows)

    # order -> list of (name, single_pa_text) queued in the sequence they
    # occurred this inning. A cell can hold multiple plate appearances by the
    # same lineup slot ("/"-separated) when the order wraps around mid-inning.
    by_inning = {}
    for row in team_rows:
        for inning_idx, cell in enumerate(row.cells, start=1):
            if not cell:
                continue
            pa_texts = split_plate_appearances(cell)
            slot_queue = by_inning.setdefault(inning_idx, {}).setdefault(row.order, [])
            slot_queue.extend((row.name, pa_text) for pa_text in pa_texts)

    result = []
    last_order = 0
    for inning in sorted(by_inning.keys()):
        state = RunnerState(False, False, False)
        outs = 0
        order_queues = by_inning[inning]
        rotation = sorted(
            order_queues.keys(),
            key=lambda o: (o - last_order - 1) % lineup_size,
        )
        pointers = {order: 0 for order in rotation}
        remaining = sum(len(q) for q in order_queues.values())

        cycle_idx = 0
        while remaining > 0 and outs < 3:
            order = rotation[cycle_idx % len(rotation)]
            ptr = pointers[order]
            if ptr < len(order_queues[order]):
                name, pa_text = order_queues[order][ptr]
                pointers[order] += 1
                remaining -= 1

                is_risp = state.second or state.third
                events_list = parse_cell(pa_text)
                result.append(
                    PlateAppearance(
                        team=team,
                        inning=inning,
                        order=order,
                        name=name,
                        outs_before=outs,
                        runners_before=state,
                        cell_text=pa_text,
                        events=events_list,
                        is_risp=is_risp,
                    )
                )
                state, outs, _runs = apply_events(state, outs, events_list)
                last_order = order
            cycle_idx += 1

    return result
