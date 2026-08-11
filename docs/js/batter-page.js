const HIT_RESULTS = new Set(["1B", "2B", "3B", "HR"]);
const AB_EXCLUDED_RESULTS = new Set(["BB", "HBP", "SF", "SAC", "OTHER"]);

function emptyStats() {
  return {
    AB: 0, H: 0, BB: 0, IBB: 0, HBP: 0, SO: 0, "1B": 0, "2B": 0, "3B": 0, HR: 0,
    SAC: 0, SF: 0, GIDP: 0, PA: 0,
  };
}

function accumulate(stats, record) {
  const result = record.result;
  stats.PA += 1;
  if (!AB_EXCLUDED_RESULTS.has(result)) {
    stats.AB += 1;
  }
  if (HIT_RESULTS.has(result)) {
    stats.H += 1;
  }
  if (result === "1B") stats["1B"] += 1;
  if (result === "2B") stats["2B"] += 1;
  if (result === "3B") stats["3B"] += 1;
  if (result === "HR") stats.HR += 1;
  if (result === "BB") stats.BB += 1;
  if (record.is_ibb) stats.IBB += 1;
  if (result === "HBP") stats.HBP += 1;
  if (result === "SO") stats.SO += 1;
  if (result === "SAC") stats.SAC += 1;
  if (result === "SF") stats.SF += 1;
  if (record.is_gidp) stats.GIDP += 1;
}

function finalize(stats) {
  stats.AVG = stats.AB > 0 ? (stats.H / stats.AB) : 0;
  const obpDenominator = stats.AB + stats.BB + stats.HBP;
  stats.OBP = obpDenominator > 0 ? ((stats.H + stats.BB + stats.HBP) / obpDenominator) : 0;
  stats.TB = stats["1B"] + stats["2B"] * 2 + stats["3B"] * 3 + stats.HR * 4;
  stats.SLG = stats.AB > 0 ? (stats.TB / stats.AB) : 0;
  stats.OPS = stats.OBP + stats.SLG;
  stats.K_RATE = stats.PA > 0 ? (stats.SO / stats.PA) : 0;
  stats.BB_K = stats.SO > 0 ? (stats.BB / stats.SO) : 0;
  stats.XBH_H = stats.H > 0 ? ((stats["2B"] + stats["3B"] + stats.HR) / stats.H) : 0;
  return stats;
}

function computeBatterStats(records) {
  const stats = emptyStats();
  for (const record of records) {
    accumulate(stats, record);
  }
  return finalize(stats);
}

function groupByPlayer(records) {
  const map = new Map();
  for (const record of records) {
    if (!map.has(record.player_name)) {
      map.set(record.player_name, emptyStats());
    }
    accumulate(map.get(record.player_name), record);
  }
  for (const stats of map.values()) {
    finalize(stats);
  }
  return map;
}

export { computeBatterStats, groupByPlayer };
