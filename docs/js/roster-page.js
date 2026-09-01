const SEASONS = [2024, 2025, 2026];

function groupByPlayer(records) {
  const map = new Map();
  for (const record of records) {
    if (!map.has(record.player_name)) {
      const stats = { total: 0 };
      for (const season of SEASONS) stats[season] = 0;
      map.set(record.player_name, stats);
    }
    const stats = map.get(record.player_name);
    stats.total += 1;
    if (stats[record.season] !== undefined) {
      stats[record.season] += 1;
    }
  }
  return map;
}

export { groupByPlayer, SEASONS };
