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

function countTeamGamesBySeason(records) {
  const bySeasonGames = new Map();
  for (const season of SEASONS) bySeasonGames.set(season, new Set());
  const allGames = new Set();
  for (const record of records) {
    allGames.add(record.game_idx);
    if (bySeasonGames.has(record.season)) {
      bySeasonGames.get(record.season).add(record.game_idx);
    }
  }
  const result = { total: allGames.size };
  for (const season of SEASONS) result[season] = bySeasonGames.get(season).size;
  return result;
}

export { groupByPlayer, countTeamGamesBySeason, SEASONS };
