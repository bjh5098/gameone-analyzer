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

// "N부"만으로는 어느 구장(리그)인지 구분이 안 된다는 피드백에 따라, 부수가
// 확인된 정기 리그는 요일+구장별칭+부수 형태의 명시적 체크박스 라벨을 쓴다
// (예: "일요배명3부", "수요성동4부" - 사용자가 준 예시 그대로).
// 살곶이야구장의 구장별칭은 "성동"으로 확정(사용자 확인).
const CONFIRMED_CHECKBOX_LABELS = {
  "일요 싱글": "일요성동3부",
  "수요 야간": "수요성동4부",
  "일요메이져": "일요배재고3부",
  "일요 3부": "일요배명3부",
  // 일요리그(C조)는 성남고/성남중 두 구장에 걸쳐 있어 특정 구장명 대신
  // 지역 별칭 "성남"을 씀(살곶이야구장 -> "성동"과 동일한 방식).
  "일요리그(C조)": "일요성남4부",
};

// 부수는 미확인이지만 구장은 확인된 리그 - 구장별칭만 붙여 위치는 식별
// 가능하게 하고, 부수를 추측하지는 않는다.
const VENUE_ONLY_CHECKBOX_LABELS = {
  "원외리그": "성동원외리그",
};

// 시즌에 따라 리그명 표기가 바뀌었을 뿐 동일한 리그인 경우(사용자 확인).
// "생활체육서울시민리그"(2024)와 "서울시민리그(S-리그)"(2025)는 하나의
// 체크박스로 묶어 "서울시민리그"로 표시한다.
const LEAGUE_GROUPS = [
  {
    label: "서울시민리그",
    members: ["생활체육서울시민리그", "서울시민리그(S-리그)"],
  },
];

function findLeagueGroup(league) {
  return LEAGUE_GROUPS.find((group) => group.members.includes(league));
}

// records에 등장하는 원본 리그명 목록을 체크박스 단위로 그룹핑한다.
// 반환값 각 항목은 { label, members } - members는 필터링에 쓸 원본
// 리그명 배열(그룹이 아니면 항목 1개), label은 화면에 표시할 텍스트.
function groupLeaguesForCheckboxes(leagues) {
  const seenGroupLabels = new Set();
  const result = [];
  for (const league of leagues) {
    const group = findLeagueGroup(league);
    if (group) {
      if (seenGroupLabels.has(group.label)) {
        continue;
      }
      seenGroupLabels.add(group.label);
      result.push({ label: group.label, members: group.members });
    } else {
      result.push({ label: leagueCheckboxLabel(league), members: [league] });
    }
  }
  return result;
}

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
// season/venue). A bare division tag like "일요싱글3부" doesn't say WHERE
// the league plays, so confirmed leagues get an explicit
// weekday+venue+division label instead, e.g. "일요배명3부", "수요성동4부"
// (matches the user's own examples). Tournament leagues keep their full
// spaced name with a "(대회)" suffix so they read as a distinct category.
function leagueCheckboxLabel(league) {
  if (isTournamentLeague(league)) {
    return `${league} (대회)`;
  }
  if (CONFIRMED_CHECKBOX_LABELS[league]) {
    return CONFIRMED_CHECKBOX_LABELS[league];
  }
  if (VENUE_ONLY_CHECKBOX_LABELS[league]) {
    return VENUE_ONLY_CHECKBOX_LABELS[league];
  }
  return league.replace(/\s+/g, "");
}

export {
  formatLeagueLabel,
  leagueCheckboxLabel,
  groupLeaguesForCheckboxes,
  abbreviateVenue,
  abbreviateLeagueTag,
  isTournamentLeague,
};
