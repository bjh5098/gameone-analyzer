import assert from "node:assert";
import { computeBatterStats, groupByPlayer } from "../../docs/js/batter-page.js";

const records = [
  { player_name: "A", result: "1B" },
  { player_name: "A", result: "SO" },
  { player_name: "A", result: "BB" },
  { player_name: "B", result: "HR" },
  { player_name: "B", result: "OUT" },
];

const teamStats = computeBatterStats(records);
assert.strictEqual(teamStats.H, 2);
assert.strictEqual(teamStats.BB, 1);
assert.strictEqual(teamStats.SO, 1);
assert.strictEqual(teamStats.HR, 1);
assert.strictEqual(teamStats.AB, 4); // BB는 타수 제외; 1B,SO,HR,OUT 4개가 AB에 포함
assert.strictEqual(teamStats.PA, 5);

const byPlayer = groupByPlayer(records);
assert.strictEqual(byPlayer.get("A").H, 1);
assert.strictEqual(byPlayer.get("A").AB, 2);
assert.strictEqual(byPlayer.get("B").H, 1);
assert.strictEqual(byPlayer.get("B").HR, 1);
assert.strictEqual(byPlayer.get("B").AB, 2);

// AVG/OBP sanity
assert.ok(Math.abs(byPlayer.get("A").AVG - 0.5) < 1e-9);

// SLG/OPS: A = 1B (1B counts as 1 total base) in 2 AB -> SLG 0.5, OPS = OBP+SLG
const aStats = byPlayer.get("A");
assert.ok(Math.abs(aStats.SLG - 0.5) < 1e-9);
assert.ok(Math.abs(aStats.OPS - (aStats.OBP + aStats.SLG)) < 1e-9);

// K rate: A has 1 SO out of 3 PA
assert.ok(Math.abs(aStats.K_RATE - (1 / 3)) < 1e-9);

const doublesTripleHrRecords = [
  { player_name: "C", result: "2B" },
  { player_name: "C", result: "3B" },
  { player_name: "C", result: "HR" },
  { player_name: "C", result: "OUT" },
];
const cStats = groupByPlayer(doublesTripleHrRecords).get("C");
// total bases = 2 + 3 + 4 = 9, AB = 4 -> SLG = 2.25
assert.ok(Math.abs(cStats.SLG - 2.25) < 1e-9);
assert.strictEqual(cStats.TB, 9);
assert.ok(Math.abs(cStats.XBH_H - 1) < 1e-9); // all 3 hits are extra-base hits

const extraStatRecords = [
  { player_name: "D", result: "1B" },
  { player_name: "D", result: "BB", is_ibb: true },
  { player_name: "D", result: "SAC" },
  { player_name: "D", result: "SF" },
  { player_name: "D", result: "OUT", is_gidp: true },
  { player_name: "D", result: "SO" },
];
const dStats = groupByPlayer(extraStatRecords).get("D");
assert.strictEqual(dStats.IBB, 1);
assert.strictEqual(dStats.SAC, 1);
assert.strictEqual(dStats.SF, 1);
assert.strictEqual(dStats.GIDP, 1);
assert.strictEqual(dStats["1B"], 1);
assert.ok(Math.abs(dStats.BB_K - 1) < 1e-9); // 1 BB / 1 SO

console.log("all batter page tests passed");
