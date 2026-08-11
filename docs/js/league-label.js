// 부수가 확인된 정기 리그만 "N부"로 표기한다. 나머지는 확인 전까지 원래
// 리그명을 그대로 사용한다(추측으로 잘못된 부수를 표기하지 않기 위함 -
// 사용자 확인 필요).
const LEAGUE_TAGS = {
  "일요 싱글": "3부",
  "일요리그(C조)": "4부",
  "일요메이져": "3부",
  "일요 3부": "3부",
  "수요 야간": "4부",
};

// 대회성 리그(정기 리그가 아닌 단발성 대회)는 부수 표기 대상이 아니다.
// 이런 리그는 항상 원래 명칭을 유지한다.
const TOURNAMENT_LEAGUES = new Set([
  "성동구청장기 야구대회",
  "친선경기",
  "[OB]야구&티볼 페스티벌 IN 양구",
  "제 2회 제천시의림지배 전국대학동아리야구대회(2024 제천 졸업생부문)",
]);

function isTournamentLeague(league) {
  return TOURNAMENT_LEAGUES.has(league);
}

const VENUE_ABBR = {
  "살곶이야구장": "살곶이",
  "살곶이 야구장": "살곶이",
  "배재고야구장": "배재고",
  "배명중,고 야구장": "배명",
  "[서울] 성남고 야구장": "성남고",
  "[서울] 성남중 운동장": "성남중",
  "난지야구장": "난지",
  "난지구장": "난지",
  "신월야구장": "신월",
  "구의야구장": "구의",
  "구의 야구장": "구의",
  "하리야구장": "하리",
  "제천시 금성야구장": "제천금성",
  "제천시 송학야구장": "제천송학",
};

function abbreviateVenue(venue) {
  return VENUE_ABBR[venue] || venue.replace(/\s+/g, "");
}

function abbreviateLeagueTag(league) {
  if (isTournamentLeague(league)) {
    return league;
  }
  if (LEAGUE_TAGS[league]) {
    return LEAGUE_TAGS[league];
  }
  // Division/tier not yet confirmed for this regular league - use the
  // original name as-is rather than guessing a tag.
  return league;
}

function formatLeagueLabel(season, league, venue) {
  if (isTournamentLeague(league)) {
    return `${league} (대회)`;
  }
  const yy = String(season).slice(-2);
  return `${yy}${abbreviateVenue(venue)}${abbreviateLeagueTag(league)}`;
}

// League checkbox filters are keyed by league name alone (independent of
// season/venue), so the checkbox label shows the original name with its
// division tag or tournament marker appended, e.g. "일요 싱글 (3부)" or
// "성동구청장기 야구대회 (대회)" - never the season/venue-qualified form
// from formatLeagueLabel, which would misleadingly imply the checkbox is
// scoped to one season/venue.
function leagueCheckboxLabel(league) {
  if (isTournamentLeague(league)) {
    return `${league} (대회)`;
  }
  if (LEAGUE_TAGS[league]) {
    return `${league} (${LEAGUE_TAGS[league]})`;
  }
  return league;
}

export {
  formatLeagueLabel,
  leagueCheckboxLabel,
  abbreviateVenue,
  abbreviateLeagueTag,
  isTournamentLeague,
};
