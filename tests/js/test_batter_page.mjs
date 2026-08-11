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

console.log("all batter page tests passed");
