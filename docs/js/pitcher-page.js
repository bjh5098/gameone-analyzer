const HIT_RESULTS = new Set(["1B", "2B", "3B", "HR"]);
const AB_EXCLUDED_RESULTS = new Set(["BB", "HBP", "SF", "SAC", "OTHER"]);

function emptyStats() {
  return { BF: 0, AB_AGAINST: 0, H: 0, BB: 0, HBP: 0, SO: 0, "2B": 0, "3B": 0, HR: 0 };
}

function accumulate(stats, result) {
  stats.BF += 1;
  if (!AB_EXCLUDED_RESULTS.has(result)) {
    stats.AB_AGAINST += 1;
  }
  if (HIT_RESULTS.has(result)) stats.H += 1;
  if (result === "2B") stats["2B"] += 1;
  if (result === "3B") stats["3B"] += 1;
  if (result === "HR") stats.HR += 1;
  if (result === "BB") stats.BB += 1;
  if (result === "HBP") stats.HBP += 1;
  if (result === "SO") stats.SO += 1;
}

function finalize(stats) {
  stats.AVG_AGAINST = stats.AB_AGAINST > 0 ? (stats.H / stats.AB_AGAINST) : 0;
  const obpDenominator = stats.AB_AGAINST + stats.BB + stats.HBP;
  stats.OBP_AGAINST = obpDenominator > 0 ? ((stats.H + stats.BB + stats.HBP) / obpDenominator) : 0;
  const singles = stats.H - stats["2B"] - stats["3B"] - stats.HR;
  const totalBases = singles + stats["2B"] * 2 + stats["3B"] * 3 + stats.HR * 4;
  stats.SLG_AGAINST = stats.AB_AGAINST > 0 ? (totalBases / stats.AB_AGAINST) : 0;
  stats.OPS_AGAINST = stats.OBP_AGAINST + stats.SLG_AGAINST;
  stats.K_RATE = stats.BF > 0 ? (stats.SO / stats.BF) : 0;
  return stats;
}

function computePitcherStats(records) {
  const stats = emptyStats();
  for (const record of records) {
    accumulate(stats, record.result);
  }
  return finalize(stats);
}

function groupByPitcher(records) {
  const map = new Map();
  for (const record of records) {
    if (!map.has(record.pitcher_name)) {
      map.set(record.pitcher_name, emptyStats());
    }
    accumulate(map.get(record.pitcher_name), record.result);
  }
  for (const stats of map.values()) {
    finalize(stats);
  }
  return map;
}

export { computePitcherStats, groupByPitcher };
