import assert from "node:assert";
import { sortEntries, nextSortState } from "../../docs/js/table-sort.js";

const entries = [
  ["A", { PA: 10, AVG: 0.300 }],
  ["B", { PA: 30, AVG: 0.250 }],
  ["C", { PA: 20, AVG: 0.400 }],
];

// numeric ascending
const ascByPa = sortEntries(entries, "PA", "asc");
assert.deepStrictEqual(ascByPa.map((e) => e[0]), ["A", "C", "B"]);

// numeric descending
const descByPa = sortEntries(entries, "PA", "desc");
assert.deepStrictEqual(descByPa.map((e) => e[0]), ["B", "C", "A"]);

// sort by a different stat
const descByAvg = sortEntries(entries, "AVG", "desc");
assert.deepStrictEqual(descByAvg.map((e) => e[0]), ["C", "A", "B"]);

// sort by name (string key uses entry[0], not a stats field)
const ascByName = sortEntries(entries, "name", "asc");
assert.deepStrictEqual(ascByName.map((e) => e[0]), ["A", "B", "C"]);
const descByName = sortEntries(entries, "name", "desc");
assert.deepStrictEqual(descByName.map((e) => e[0]), ["C", "B", "A"]);

// original array is not mutated
sortEntries(entries, "PA", "asc");
assert.strictEqual(entries[0][0], "A");
assert.strictEqual(entries[1][0], "B");
assert.strictEqual(entries[2][0], "C");

// nextSortState: clicking a new column defaults to descending
assert.deepStrictEqual(
  nextSortState({ key: "PA", direction: "desc" }, "AVG"),
  { key: "AVG", direction: "desc" }
);

// nextSortState: clicking the same column toggles direction
assert.deepStrictEqual(
  nextSortState({ key: "PA", direction: "desc" }, "PA"),
  { key: "PA", direction: "asc" }
);
assert.deepStrictEqual(
  nextSortState({ key: "PA", direction: "asc" }, "PA"),
  { key: "PA", direction: "desc" }
);

console.log("all table-sort tests passed");
