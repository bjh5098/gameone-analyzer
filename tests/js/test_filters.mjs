import assert from "node:assert";
import { matchesFilter, normalizeVenue } from "../../docs/js/filters.js";

const baseRecord = {
  outs_before: 1,
  is_risp: true,
  runner_state: "23",
  season: 2025,
  league: "일요 싱글",
  venue: "살곶이 야구장",
};

// risp filter
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: true, seasons: [], leagues: [], venueGroups: [] }),
  true
);
assert.strictEqual(
  matchesFilter({ ...baseRecord, is_risp: false }, { outs: [], runnerStates: [], rispOnly: true, seasons: [], leagues: [], venueGroups: [] }),
  false
);

// outs filter
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [1], runnerStates: [], rispOnly: false, seasons: [], leagues: [], venueGroups: [] }),
  true
);
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [0], runnerStates: [], rispOnly: false, seasons: [], leagues: [], venueGroups: [] }),
  false
);

// runner state filter
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: ["23"], rispOnly: false, seasons: [], leagues: [], venueGroups: [] }),
  true
);
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: ["1"], rispOnly: false, seasons: [], leagues: [], venueGroups: [] }),
  false
);

// season filter
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [2025], leagues: [], venueGroups: [] }),
  true
);
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [2024], leagues: [], venueGroups: [] }),
  false
);

// league filter
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: ["일요 싱글"], venueGroups: [] }),
  true
);
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: ["수요 야간"], venueGroups: [] }),
  false
);

// venue group with whitespace normalization
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: [], venueGroups: [["살곶이야구장"]] }),
  true
);
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: [], venueGroups: [["배재고야구장"]] }),
  false
);

// venue group with multiple venues combined (OR)
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: [], venueGroups: [["배재고야구장", "살곶이야구장"]] }),
  true
);

assert.strictEqual(normalizeVenue("구의 야구장"), "구의야구장");
assert.strictEqual(normalizeVenue("살곶이야구장"), "살곶이야구장");

// grouped league checkbox: buildFilterState flattens a checked box's
// JSON-array value (e.g. "서울시민리그" covering both "생활체육서울시민리그"
// and "서울시민리그(S-리그)") into filterState.leagues, so matchesFilter
// just needs both names present to match either season's record
assert.strictEqual(
  matchesFilter(
    { ...baseRecord, league: "생활체육서울시민리그" },
    { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: ["생활체육서울시민리그", "서울시민리그(S-리그)"], venueGroups: [] }
  ),
  true
);
assert.strictEqual(
  matchesFilter(
    { ...baseRecord, league: "서울시민리그(S-리그)" },
    { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: ["생활체육서울시민리그", "서울시민리그(S-리그)"], venueGroups: [] }
  ),
  true
);

console.log("all filter tests passed");
