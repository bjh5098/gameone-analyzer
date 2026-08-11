const HIT_RESULTS = new Set(["1B", "2B", "3B", "HR"]);
const AB_EXCLUDED_RESULTS = new Set(["BB", "HBP", "SF", "SAC", "OTHER"]);

function emptyStats() {
  return { AB: 0, H: 0, BB: 0, HBP: 0, SO: 0, "2B": 0, "3B": 0, HR: 0, PA: 0 };
}

function accumulate(stats, result) {
  stats.PA += 1;
  if (!AB_EXCLUDED_RESULTS.has(result)) {
    stats.AB += 1;
  }
  if (HIT_RESULTS.has(result)) {
    stats.H += 1;
  }
  if (result === "2B") stats["2B"] += 1;
  if (result === "3B") stats["3B"] += 1;
  if (result === "HR") stats.HR += 1;
  if (result === "BB") stats.BB += 1;
  if (result === "HBP") stats.HBP += 1;
  if (result === "SO") stats.SO += 1;
}

function finalize(stats) {
  stats.AVG = stats.AB > 0 ? (stats.H / stats.AB) : 0;
  const obpDenominator = stats.AB + stats.BB + stats.HBP;
  stats.OBP = obpDenominator > 0 ? ((stats.H + stats.BB + stats.HBP) / obpDenominator) : 0;
  return stats;
}

function computeBatterStats(records) {
  const stats = emptyStats();
  for (const record of records) {
    accumulate(stats, record.result);
  }
  return finalize(stats);
}

function groupByPlayer(records) {
  const map = new Map();
  for (const record of records) {
    if (!map.has(record.player_name)) {
      map.set(record.player_name, emptyStats());
    }
    accumulate(map.get(record.player_name), record.result);
  }
  for (const stats of map.values()) {
    finalize(stats);
  }
  return map;
}

export { computeBatterStats, groupByPlayer };
