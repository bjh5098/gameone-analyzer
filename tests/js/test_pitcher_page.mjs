import assert from "node:assert";
import { computePitcherStats, groupByPitcher } from "../../docs/js/pitcher-page.js";

const records = [
  { pitcher_name: "민호진", result: "1B" },
  { pitcher_name: "민호진", result: "SO" },
  { pitcher_name: "민호진", result: "BB" },
  { pitcher_name: "박준호", result: "HR" },
];

const teamStats = computePitcherStats(records);
assert.strictEqual(teamStats.H, 2);
assert.strictEqual(teamStats.SO, 1);
assert.strictEqual(teamStats.BB, 1);
assert.strictEqual(teamStats.BF, 4);
assert.strictEqual(teamStats.AB_AGAINST, 3);

const byPitcher = groupByPitcher(records);
assert.strictEqual(byPitcher.get("민호진").H, 1);
assert.strictEqual(byPitcher.get("민호진").AB_AGAINST, 2);
assert.strictEqual(byPitcher.get("박준호").H, 1);
assert.strictEqual(byPitcher.get("박준호").HR, 1);

// OPS-against and K rate (per batter faced)
const minho = byPitcher.get("민호진");
assert.ok(Math.abs(minho.SLG_AGAINST - 0.5) < 1e-9); // 1B in 2 AB
assert.ok(Math.abs(minho.OPS_AGAINST - (minho.OBP_AGAINST + minho.SLG_AGAINST)) < 1e-9);
assert.ok(Math.abs(minho.K_RATE - (1 / 3)) < 1e-9); // 1 SO out of 3 BF

const junho = byPitcher.get("박준호");
assert.ok(Math.abs(junho.SLG_AGAINST - 4) < 1e-9); // HR in 1 AB -> 4 total bases / 1 AB

const extraStatRecords = [
  { pitcher_name: "E", result: "BB", is_ibb: true },
  { pitcher_name: "E", result: "SAC" },
  { pitcher_name: "E", result: "SF" },
  { pitcher_name: "E", result: "OUT", has_wp: true },
  { pitcher_name: "E", result: "OUT", has_bk: true },
];
const eStats = groupByPitcher(extraStatRecords).get("E");
assert.strictEqual(eStats.IBB, 1);
assert.strictEqual(eStats.SAC, 1);
assert.strictEqual(eStats.SF, 1);
assert.strictEqual(eStats.WP, 1);
assert.strictEqual(eStats.BK, 1);

console.log("all pitcher page tests passed");
