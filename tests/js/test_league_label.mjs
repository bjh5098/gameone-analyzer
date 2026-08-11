import assert from "node:assert";
import {
  formatLeagueLabel,
  leagueCheckboxLabel,
  groupLeaguesForCheckboxes,
  abbreviateVenue,
  abbreviateLeagueTag,
  isTournamentLeague,
} from "../../docs/js/league-label.js";

// confirmed division mappings
assert.strictEqual(abbreviateLeagueTag("일요 싱글"), "3부");
assert.strictEqual(abbreviateLeagueTag("일요리그(C조)"), "4부");
assert.strictEqual(abbreviateLeagueTag("일요메이져"), "3부");
assert.strictEqual(abbreviateLeagueTag("일요 3부"), "3부");
assert.strictEqual(abbreviateLeagueTag("수요 야간"), "4부");


// season + venue + confirmed league tag combination
assert.strictEqual(formatLeagueLabel(2024, "일요 싱글", "살곶이야구장"), "24살곶이3부");
assert.strictEqual(formatLeagueLabel(2026, "일요 싱글", "살곶이야구장"), "26살곶이3부");
assert.strictEqual(formatLeagueLabel(2026, "일요리그(C조)", "[서울] 성남고 야구장"), "26성남고4부");
assert.strictEqual(formatLeagueLabel(2026, "일요메이져", "배재고야구장"), "26배재고3부");
assert.strictEqual(formatLeagueLabel(2025, "일요 3부", "배명중,고 야구장"), "25배명3부");
assert.strictEqual(formatLeagueLabel(2024, "수요 야간", "살곶이야구장"), "24살곶이4부");

// venue whitespace variants collapse to the same abbreviation
assert.strictEqual(abbreviateVenue("살곶이야구장"), "살곶이");
assert.strictEqual(abbreviateVenue("살곶이 야구장"), "살곶이");
assert.strictEqual(abbreviateVenue("구의야구장"), "구의");
assert.strictEqual(abbreviateVenue("구의 야구장"), "구의");
assert.strictEqual(abbreviateVenue("배재고야구장"), "배재고");
assert.strictEqual(abbreviateVenue("[서울] 성남고 야구장"), "성남고");

// leagues with unconfirmed division are kept as their original name - not
// guessed into a bogus tag
assert.strictEqual(abbreviateLeagueTag("원외리그"), "원외리그");
assert.strictEqual(abbreviateLeagueTag("생활체육서울시민리그"), "생활체육서울시민리그");
assert.strictEqual(abbreviateLeagueTag("서울시민리그(S-리그)"), "서울시민리그(S-리그)");
assert.strictEqual(abbreviateLeagueTag("디비전 6-강남구"), "디비전 6-강남구");

// tournament leagues are classified separately from regular (division) leagues
assert.strictEqual(isTournamentLeague("성동구청장기 야구대회"), true);
assert.strictEqual(isTournamentLeague("친선경기"), true);
assert.strictEqual(isTournamentLeague("[OB]야구&티볼 페스티벌 IN 양구"), true);
assert.strictEqual(
  isTournamentLeague("제 2회 제천시의림지배 전국대학동아리야구대회(2024 제천 졸업생부문)"),
  true
);
assert.strictEqual(isTournamentLeague("일요 싱글"), false);
assert.strictEqual(isTournamentLeague("수요 야간"), false);

// tournament leagues keep their full original name and get a "(대회)" suffix,
// never a division tag - even though the label mentions season/venue for
// regular leagues, tournaments are a fundamentally different category
assert.strictEqual(
  formatLeagueLabel(2024, "성동구청장기 야구대회", "살곶이야구장"),
  "성동구청장기 야구대회 (대회)"
);
assert.strictEqual(
  formatLeagueLabel(2025, "친선경기", "살곶이 야구장"),
  "친선경기 (대회)"
);

// checkbox labels for confirmed leagues use an explicit weekday+venue+
// division form so the venue is identifiable at a glance (a bare "N부"
// doesn't say where) - matches the user's own examples "일요배명3부"/
// "수요성동4부". 살곶이야구장's alias is "성동" (user-confirmed).
assert.strictEqual(leagueCheckboxLabel("일요 싱글"), "일요성동3부");
assert.strictEqual(leagueCheckboxLabel("수요 야간"), "수요성동4부");
assert.strictEqual(leagueCheckboxLabel("일요메이져"), "일요배재고3부");
assert.strictEqual(leagueCheckboxLabel("일요 3부"), "일요배명3부");
assert.strictEqual(leagueCheckboxLabel("일요리그(C조)"), "일요성남4부");

// venue confirmed but division not - venue alias only, no guessed division
assert.strictEqual(leagueCheckboxLabel("원외리그"), "성동원외리그");

// tournaments and unconfirmed leagues unaffected by the explicit map
assert.strictEqual(leagueCheckboxLabel("성동구청장기 야구대회"), "성동구청장기 야구대회 (대회)");
assert.strictEqual(leagueCheckboxLabel("디비전 6-강남구"), "디비전6-강남구");

// "생활체육서울시민리그"(2024) and "서울시민리그(S-리그)"(2025) are the
// same league under a different season's naming (user-confirmed) - they
// collapse into one checkbox labeled "서울시민리그" whose filter matches
// both original names, so the checkbox count doesn't double for what is
// actually one league across seasons.
const grouped = groupLeaguesForCheckboxes([
  "일요 싱글",
  "생활체육서울시민리그",
  "서울시민리그(S-리그)",
  "디비전 6-강남구",
]);
assert.strictEqual(grouped.length, 3);
const seoulCitizenGroup = grouped.find((g) => g.label === "서울시민리그");
assert.ok(seoulCitizenGroup, "expected a 서울시민리그 group entry");
assert.deepStrictEqual(
  seoulCitizenGroup.members.slice().sort(),
  ["생활체육서울시민리그", "서울시민리그(S-리그)"].sort()
);

// ungrouped leagues pass through as a single-member group with their
// normal checkbox label
const soleGroup = grouped.find((g) => g.label === "일요성동3부");
assert.deepStrictEqual(soleGroup.members, ["일요 싱글"]);

// if only one of the two grouped names appears in the data (e.g. records
// come from just one season), the group still forms with BOTH original
// names in members - matching stays correct even against data from other
// seasons that do use the other name
const partialGrouped = groupLeaguesForCheckboxes(["생활체육서울시민리그"]);
assert.strictEqual(partialGrouped.length, 1);
assert.strictEqual(partialGrouped[0].label, "서울시민리그");
assert.deepStrictEqual(
  partialGrouped[0].members.slice().sort(),
  ["생활체육서울시민리그", "서울시민리그(S-리그)"].sort()
);

console.log("all league-label tests passed");
