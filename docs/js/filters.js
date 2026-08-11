function buildFilterState(formElement) {
  const outs = Array.from(formElement.querySelectorAll('input[name="outs"]:checked'))
    .map((el) => parseInt(el.value, 10));
  const runnerStates = Array.from(formElement.querySelectorAll('input[name="runnerState"]:checked'))
    .map((el) => el.value);
  const rispOnly = formElement.querySelector('input[name="rispOnly"]').checked;
  const seasons = Array.from(formElement.querySelectorAll('input[name="season"]:checked'))
    .map((el) => parseInt(el.value, 10));
  const leagues = Array.from(formElement.querySelectorAll('input[name="league"]:checked'))
    .flatMap((el) => JSON.parse(el.value));
  const venueGroupSelect = formElement.querySelector('select[name="venueGroup"]');
  const venueGroups = venueGroupSelect && venueGroupSelect.value
    ? [JSON.parse(venueGroupSelect.value)]
    : [];

  return { outs, runnerStates, rispOnly, seasons, leagues, venueGroups };
}

function normalizeVenue(venue) {
  return venue.replace(/\s+/g, "");
}

function matchesFilter(record, filterState) {
  if (filterState.outs.length > 0 && !filterState.outs.includes(record.outs_before)) {
    return false;
  }
  if (filterState.rispOnly && !record.is_risp) {
    return false;
  }
  if (filterState.runnerStates.length > 0 && !filterState.runnerStates.includes(record.runner_state)) {
    return false;
  }
  if (filterState.seasons.length > 0 && !filterState.seasons.includes(record.season)) {
    return false;
  }
  if (filterState.leagues.length > 0 && !filterState.leagues.includes(record.league)) {
    return false;
  }
  if (filterState.venueGroups.length > 0) {
    const normalized = normalizeVenue(record.venue);
    const anyGroupMatches = filterState.venueGroups.some((group) =>
      group.map(normalizeVenue).includes(normalized)
    );
    if (!anyGroupMatches) {
      return false;
    }
  }
  return true;
}

export { buildFilterState, matchesFilter, normalizeVenue };
