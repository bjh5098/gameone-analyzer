import assert from "node:assert";
import {
  formatLeagueLabel,
  leagueCheckboxLabel,
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

// "일요 3부" already carries its division in its own name - the checkbox
// label must not double it up as "일요3부3부"
assert.strictEqual(leagueCheckboxLabel("일요 3부"), "일요3부");

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

// checkbox labels are season/venue-independent: whitespace-compacted league
// name with the division tag appended directly (e.g. "수요야간4부"), or the
// full spaced name + "(대회)" for tournaments
assert.strictEqual(leagueCheckboxLabel("일요 싱글"), "일요싱글3부");
assert.strictEqual(leagueCheckboxLabel("일요리그(C조)"), "일요리그(C조)4부");
assert.strictEqual(leagueCheckboxLabel("일요메이져"), "일요메이져3부");
assert.strictEqual(leagueCheckboxLabel("수요 야간"), "수요야간4부");
assert.strictEqual(leagueCheckboxLabel("성동구청장기 야구대회"), "성동구청장기 야구대회 (대회)");
assert.strictEqual(leagueCheckboxLabel("원외리그"), "원외리그");

console.log("all league-label tests passed");
