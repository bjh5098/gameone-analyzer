function sortEntries(entries, key, direction) {
  const sign = direction === "asc" ? 1 : -1;
  const getValue = (entry) => (key === "name" ? entry[0] : entry[1][key]);

  return [...entries].sort((a, b) => {
    const va = getValue(a);
    const vb = getValue(b);
    if (typeof va === "string" || typeof vb === "string") {
      return sign * String(va).localeCompare(String(vb), "ko");
    }
    return sign * (va - vb);
  });
}

function nextSortState(currentState, clickedKey) {
  if (currentState.key === clickedKey) {
    return { key: clickedKey, direction: currentState.direction === "asc" ? "desc" : "asc" };
  }
  return { key: clickedKey, direction: "desc" };
}

export { sortEntries, nextSortState };
