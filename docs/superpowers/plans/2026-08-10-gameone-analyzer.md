# gameone.kr 득점권 분석 웹앱 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 한양대학교 D-Dogs OB(club_idx=31993)의 2024~2026시즌 gameone.kr 박스스코어 95경기를 파싱해
타석 단위 상황(아웃카운트·주자상황·구장·연도·리그)을 태깅한 SQLite DB로 만들고, 이를 기반으로
타자 관점/투수 관점 분석 페이지 2개를 엑셀 필터 스타일 옵션과 함께 GitHub Pages에 정적 배포한다.

**Architecture:**
Python 스크립트가 HTML을 로컬에 캐싱(fetch, 3초 지연) → BeautifulSoup으로 타자/투수 기록 테이블 파싱
→ 이벤트 코드 사전으로 타석별 이벤트 분해 → 이닝별 타순 순환을 따라 (아웃카운트, 주자상황) 상태를
역산 시뮬레이션 → 스코어보드 대비 검증 → SQLite에 타석(plate_appearance) 단위로 저장.
프론트엔드는 빌드 시점에 DB에서 JSON을 미리 집계/추출해 정적 파일로 만들고, 순수 JS(프레임워크 없이
Vanilla HTML/CSS/JS)로 필터 UI + 클라이언트 사이드 집계를 구현해 GitHub Pages(`docs/` 또는 `gh-pages`)로 배포.
필터 결과는 매우 빠른 조회가 필요하지 않으므로(개인용, 95경기 규모) 클라이언트 사이드 필터링으로 충분.

**Tech Stack:** Python 3.9 (venv, beautifulsoup4, lxml, sqlite3 표준 라이브러리), Vanilla JS/HTML/CSS,
GitHub Actions(선택적, 정적 파일 빌드) 또는 로컬 빌드 스크립트로 `docs/data.json` 생성, GitHub Pages.

## Global Constraints

- robots.txt상 ClaudeBot 차단 — 크롤링은 사용자 승인 범위(로컬 순차 수집, 요청당 3초 지연)로만 수행한다.
- gameone.kr에는 JSON API가 없음 — HTML 직접 파싱이 유일한 경로.
- 로그인 불필요 (확인됨).
- club_idx=31993, "우리팀" = 한양대학교 D-Dogs OB.
- 득점권 정의 = 2루 또는 3루에 주자 존재(2루/3루/1·2루/1·3루/2·3루/만루).
- 점수차 필터는 [확인 필요] 상태이므로 이번 계획에서는 구현하지 않고 TODO로 남긴다(Task 10 이후, 우선순위 낮음).
- GitHub 계정: bjh5098 (bjh5098@naver.com), 저장소 `gameone-analyzer`는 이미 public으로 생성됨
  (https://github.com/bjh5098/gameone-analyzer).
- 커밋 후에는 매번 `git push` 한다.
- 대량 재크롤링 방지: 파싱된 원문 HTML은 `data/raw/{game_idx}.html`로 캐싱하고, 파일이 이미 있으면
  재요청하지 않는다(`.gitignore`에 `data/raw/` 포함, git에는 커밋하지 않음 — 서버 데이터 재배포 회피).

---

## 사전 조사 결과 (완료, 참고용)

`/tmp/gameone_probe/`에 샘플 10경기(2024~2026 시즌 분산) HTML을 이미 받아 구조를 확인함:

- 스코어보드: `<table class="score_teble">` — `<caption>`에 `리그명 / MM.DD(시간) / 구장명` 포맷.
  각 팀 `<tr><th>팀명</th><td class="round">이닝별 득점...</td>...<td class="r">R</td><td>H</td><td>E</td><td>B</td></tr>`
- 타자기록: `<table class="record_table inc_round" summary="타자기록">` 이 팀당 1개, 문서에 2개 등장
  (원정팀 먼저, 그다음 홈팀 — 앞의 `<h4>팀명</h4>` 순서로 판별). 각 행:
  `<th><span class="num">타순</span><span class="position">포지션</span><span class="name"><strong>이름</strong>(번호)</span></th>`
  다음 12개 `<td class="round[ hide]?">이벤트,이벤트,...</td>` (1~9이닝은 hide 없음, 10~12는 `class="round hide"`),
  그다음 타수/안타/타점/득점/도루/타율/시즌 컬럼.
- 투수기록: `<table class="record_table" summary="투수기록">` 팀당 1개. 이번 계획에서는 투수 판별에
  이닝 진행(자동 진루 이벤트 소속 판별)까지는 필요 없음 — 타자 테이블만으로 상태 시뮬레이션 가능.
- 이벤트 코드 사전 v2 (샘플 10경기에서 관측, 빈도 내림차순 일부):
  `삼진`(95), `도루`(88), `4구`(75), `좌안/중안/우안`(안타 방향), `2땅/중플/유땅/투땅/3땅/1땅`(아웃),
  `주자아웃`(13), `사구`(11, HBP), `유내안/좌플/우플/중월2/좌전2` 등 방향+진루 조합, `송구실책`(7), `3실`(7, 실책+포지션번호),
  `도루자`(6, 도루 실패=아웃), `2내안/3내안`(내야안타), `유땅R/3땅R/2땅R`(R=주자진루 동반 아웃 추정),
  `4구/4구`처럼 콤마 결합, `고의4구`, `타격방해`, `포일`, `낫아웃-`/`낫아웃+`, `런다운`, `대주자`/`대수비`(교체, 타석 아님),
  `견제사`, `1직/유직`(투수/야수 직선타 아웃), `보크`, `2인플`(2루수 인필드플라이 추정), `유땅병살`(병살).
  → 전체 코드 사전은 Task 2에서 `src/gameone_analyzer/events.py`에 표로 정리하며, 미분류 코드는
  `UNKNOWN` 처리 후 검증 단계에서 스코어보드 대조로 보정한다(CLAUDE.md 정의).
- 로컬 venv(`/Users/bae/project/workspace/gameone_analyzer/.venv`)에 beautifulsoup4 4.15, lxml 설치 확인됨.

---

### Task 1: 프로젝트 스캐폴딩 + 원문 HTML 캐시 수집기

**Files:**
- Create: `src/gameone_analyzer/__init__.py`
- Create: `src/gameone_analyzer/fetch.py`
- Create: `scripts/fetch_all.py`
- Modify: `requirements.txt` (이미 생성됨 — beautifulsoup4, lxml)
- Test: `tests/test_fetch.py`

**Interfaces:**
- Produces: `fetch.fetch_boxscore_html(game_idx: int, cache_dir: Path, delay_sec: float = 3.0) -> str`
  — `cache_dir/{game_idx}.html` 이 이미 있으면 그 내용을 읽어 반환(재요청 없음), 없으면
  `https://www.gameone.kr/club/info/schedule/boxscore?club_idx=31993&game_idx={game_idx}` 를
  요청 후 캐시에 저장하고 `time.sleep(delay_sec)` 호출 뒤 반환.
- Produces: `fetch.load_game_ids_from_csv(csv_path: Path) -> list[int]` — `games_meta.csv`의
  `game_idx` 컬럼을 정수 리스트로 반환.

- [x] **Step 1: 디렉터리 구조 생성**

```bash
mkdir -p src/gameone_analyzer tests scripts data/raw docs/superpowers/plans
touch src/gameone_analyzer/__init__.py
```

- [x] **Step 2: 실패하는 테스트 작성**

`tests/test_fetch.py`:
```python
import csv
from pathlib import Path
from gameone_analyzer.fetch import fetch_boxscore_html, load_game_ids_from_csv


def test_load_game_ids_from_csv(tmp_path):
    csv_path = tmp_path / "games_meta.csv"
    csv_path.write_text(
        "game_idx,season,date,league,venue,matchup,url\n"
        "1234,2024,01월01일,일요 싱글,살곶이야구장,A 1 B 0,http://x\n"
        "5678,2025,02월02일,수요 야간,배재고야구장,A 2 B 3,http://y\n",
        encoding="utf-8",
    )
    assert load_game_ids_from_csv(csv_path) == [1234, 5678]


def test_fetch_boxscore_html_uses_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "raw"
    cache_dir.mkdir()
    cached_file = cache_dir / "999.html"
    cached_file.write_text("<html>cached</html>", encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("should not fetch when cache exists")

    monkeypatch.setattr("gameone_analyzer.fetch._http_get", fail_if_called)

    html = fetch_boxscore_html(999, cache_dir, delay_sec=0)
    assert html == "<html>cached</html>"
```

- [x] **Step 3: 테스트 실행하여 실패 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_fetch.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gameone_analyzer'` (아직 구현 없음)

- [x] **Step 4: 최소 구현 작성**

`src/gameone_analyzer/fetch.py`:
```python
import csv
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://www.gameone.kr/club/info/schedule/boxscore"
CLUB_IDX = 31993
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def fetch_boxscore_html(game_idx: int, cache_dir: Path, delay_sec: float = 3.0) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{game_idx}.html"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    url = f"{BASE_URL}?club_idx={CLUB_IDX}&game_idx={game_idx}"
    html = _http_get(url)
    cache_path.write_text(html, encoding="utf-8")
    if delay_sec > 0:
        time.sleep(delay_sec)
    return html


def load_game_ids_from_csv(csv_path: Path) -> list[int]:
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [int(row["game_idx"]) for row in reader]
```

- [x] **Step 5: 테스트 실행하여 통과 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_fetch.py -v`
Expected: PASS (2 passed)

- [x] **Step 6: 전체 95경기 수집 스크립트 작성**

`scripts/fetch_all.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.fetch import fetch_boxscore_html, load_game_ids_from_csv

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "raw"


def main():
    game_ids = load_game_ids_from_csv(ROOT / "games_meta.csv")
    total = len(game_ids)
    for i, game_idx in enumerate(game_ids, 1):
        cache_path = CACHE_DIR / f"{game_idx}.html"
        was_cached = cache_path.exists()
        html = fetch_boxscore_html(game_idx, CACHE_DIR, delay_sec=3.0)
        status = "cached" if was_cached else "fetched"
        print(f"[{i}/{total}] game_idx={game_idx} {status} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
```

이 스크립트는 이후 사용자 승인 하에 실제로 95경기를 수집할 때 실행한다(Task 3 이전, 별도 확인 후).

- [x] **Step 7: 커밋 및 푸시**

```bash
git add src/gameone_analyzer/__init__.py src/gameone_analyzer/fetch.py scripts/fetch_all.py tests/test_fetch.py requirements.txt .gitignore
git commit -m "feat: add boxscore HTML fetcher with local caching"
git push -u origin master
```

---

### Task 2: 이벤트 코드 사전 + 파서 유틸

**Files:**
- Create: `src/gameone_analyzer/events.py`
- Test: `tests/test_events.py`

**Interfaces:**
- Consumes: 없음 (독립 모듈)
- Produces:
  - `events.EventType` — Enum: `HIT_SINGLE, HIT_DOUBLE, HIT_TRIPLE, HOME_RUN, WALK, HBP, INTENTIONAL_WALK,
    STRIKEOUT, GROUNDOUT, FLYOUT, LINEOUT, DOUBLE_PLAY, SAC_FLY, SAC_BUNT, FIELDERS_CHOICE, ERROR,
    STOLEN_BASE, CAUGHT_STEALING, RUNNER_OUT, PICKOFF_OUT, WILD_PITCH, BALK, CATCHER_INTERFERENCE,
    PASSED_BALL, NOT_A_PLATE_APPEARANCE, UNKNOWN`
  - `events.parse_cell(cell_text: str) -> list[str]` — 콤마로 분리된 원본 이벤트 코드 문자열 리스트 반환
    (빈 문자열 필터링). 예: `"4구,도루,도루"` → `["4구", "도루", "도루"]`
  - `events.classify(code: str) -> EventType` — 단일 코드 문자열을 `EventType`으로 분류.
    코드 사전에 없으면 `EventType.UNKNOWN` 반환(예외 던지지 않음 — 검증 단계에서 발견용).
  - `events.is_out(event_type: EventType) -> bool`
  - `events.CODE_TABLE: dict[str, EventType]` — 아래 표를 코드로 옮긴 것. 방향 접두사(`좌/중/우/유/투/1/2/3`)
    붙은 코드는 `classify()` 내부에서 접미사 패턴 매칭으로 처리(정확matched 우선, 없으면 suffix 매칭).

**코드 분류표 (샘플 10경기 관측 기반, `classify()` 로직 근거):**

| 패턴 | EventType | 아웃 여부 |
|---|---|---|
| `4구` | WALK | No |
| `고의4구` | INTENTIONAL_WALK | No |
| `사구` | HBP | No |
| `삼진` | STRIKEOUT | Yes |
| `낫아웃-` | STRIKEOUT (주자 진루 실패, 타자 아웃) | Yes |
| `낫아웃+` | STRIKEOUT (주자 진루 성공, 타자는 아웃) — 아웃 처리는 동일 | Yes |
| `좌안`,`중안`,`우안`,`유내안`,`2내안`,`3내안`,`좌중안`,`우중안` | HIT_SINGLE | No |
| `좌전2`,`중전2`,`우중2`,`중월2`,`좌중2`,`좌월2`,`우월2`,`좌선2` | HIT_DOUBLE | No |
| `중월3`,`우중3` | HIT_TRIPLE | No |
| `중월홈`,`좌월홈`,`좌중G홈` | HOME_RUN | No |
| suffix `땅`(`1땅`,`2땅`,`3땅`,`유땅`,`투땅`) 단독(뒤에 `R`,`병살` 없음) | GROUNDOUT | Yes |
| suffix `땅R`(`유땅R`,`2땅R`,`3땅R`) | FIELDERS_CHOICE (아웃 발생 + 타자 주자화 — 세부는 시뮬레이션에서 처리) | Yes(1아웃) |
| suffix `플`(`유플`,`중플`,`좌플`,`우플`,`투플`,`1플`,`2플`,`3플`,`2인플`) | FLYOUT | Yes |
| `중희플`,`희타`,`희비`,`유희플` | SAC_FLY (진루 동반, 1아웃) | Yes |
| `1직`,`유직` | LINEOUT | Yes |
| `병살`,`유땅병살` | DOUBLE_PLAY | Yes(2아웃) |
| `투야선`,`3야선` | FIELDERS_CHOICE | No(아웃 없음, 진루만) |
| `실책`,`좌실`,`유실`,`2실`,`3실`,`송구실책` | ERROR | No |
| `도루` | STOLEN_BASE | No |
| `도루자` | CAUGHT_STEALING | Yes |
| `주자아웃`,`견제사` | RUNNER_OUT | Yes(다른 주자) |
| `런다운` | RUNNER_OUT | Yes |
| `폭투` | WILD_PITCH | No |
| `보크` | BALK | No |
| `포일` | PASSED_BALL | No |
| `타격방해` | CATCHER_INTERFERENCE | No |
| `대주자`,`대수비` | NOT_A_PLATE_APPEARANCE | No |
| 그 외 | UNKNOWN | 미정(로그만) |

- [x] **Step 1: 실패하는 테스트 작성**

`tests/test_events.py`:
```python
from gameone_analyzer.events import parse_cell, classify, is_out, EventType


def test_parse_cell_splits_on_comma():
    assert parse_cell("4구,도루,도루") == ["4구", "도루", "도루"]


def test_parse_cell_empty_string():
    assert parse_cell("") == []


def test_classify_walk():
    assert classify("4구") == EventType.WALK


def test_classify_single_hit_direction_variants():
    assert classify("좌안") == EventType.HIT_SINGLE
    assert classify("중안") == EventType.HIT_SINGLE
    assert classify("우안") == EventType.HIT_SINGLE
    assert classify("2내안") == EventType.HIT_SINGLE


def test_classify_double():
    assert classify("좌전2") == EventType.HIT_DOUBLE
    assert classify("중월2") == EventType.HIT_DOUBLE


def test_classify_triple():
    assert classify("중월3") == EventType.HIT_TRIPLE


def test_classify_home_run():
    assert classify("중월홈") == EventType.HOME_RUN


def test_classify_groundout():
    assert classify("유땅") == EventType.GROUNDOUT
    assert classify("1땅") == EventType.GROUNDOUT


def test_classify_fielders_choice_with_r_suffix():
    assert classify("유땅R") == EventType.FIELDERS_CHOICE


def test_classify_flyout():
    assert classify("유플") == EventType.FLYOUT
    assert classify("2인플") == EventType.FLYOUT


def test_classify_double_play():
    assert classify("유땅병살") == EventType.DOUBLE_PLAY
    assert classify("병살") == EventType.DOUBLE_PLAY


def test_classify_error():
    assert classify("실책") == EventType.ERROR
    assert classify("3실") == EventType.ERROR
    assert classify("송구실책") == EventType.ERROR


def test_classify_stolen_base_and_caught_stealing():
    assert classify("도루") == EventType.STOLEN_BASE
    assert classify("도루자") == EventType.CAUGHT_STEALING


def test_classify_unknown_code_does_not_raise():
    assert classify("존재하지않는코드") == EventType.UNKNOWN


def test_is_out_table():
    assert is_out(EventType.STRIKEOUT) is True
    assert is_out(EventType.WALK) is False
    assert is_out(EventType.DOUBLE_PLAY) is True
    assert is_out(EventType.HIT_SINGLE) is False
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_events.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gameone_analyzer.events'`

- [x] **Step 3: 구현 작성**

`src/gameone_analyzer/events.py`:
```python
from enum import Enum, auto


class EventType(Enum):
    HIT_SINGLE = auto()
    HIT_DOUBLE = auto()
    HIT_TRIPLE = auto()
    HOME_RUN = auto()
    WALK = auto()
    INTENTIONAL_WALK = auto()
    HBP = auto()
    STRIKEOUT = auto()
    GROUNDOUT = auto()
    FLYOUT = auto()
    LINEOUT = auto()
    DOUBLE_PLAY = auto()
    SAC_FLY = auto()
    SAC_BUNT = auto()
    FIELDERS_CHOICE = auto()
    ERROR = auto()
    STOLEN_BASE = auto()
    CAUGHT_STEALING = auto()
    RUNNER_OUT = auto()
    WILD_PITCH = auto()
    BALK = auto()
    CATCHER_INTERFERENCE = auto()
    PASSED_BALL = auto()
    NOT_A_PLATE_APPEARANCE = auto()
    UNKNOWN = auto()


OUT_EVENTS = {
    EventType.STRIKEOUT,
    EventType.GROUNDOUT,
    EventType.FLYOUT,
    EventType.LINEOUT,
    EventType.DOUBLE_PLAY,
    EventType.SAC_FLY,
    EventType.SAC_BUNT,
    EventType.FIELDERS_CHOICE,
    EventType.CAUGHT_STEALING,
    EventType.RUNNER_OUT,
}

EXACT_CODE_TABLE = {
    "4구": EventType.WALK,
    "고의4구": EventType.INTENTIONAL_WALK,
    "사구": EventType.HBP,
    "삼진": EventType.STRIKEOUT,
    "낫아웃-": EventType.STRIKEOUT,
    "낫아웃+": EventType.STRIKEOUT,
    "병살": EventType.DOUBLE_PLAY,
    "유땅병살": EventType.DOUBLE_PLAY,
    "희타": EventType.SAC_BUNT,
    "희비": EventType.SAC_BUNT,
    "투야선": EventType.FIELDERS_CHOICE,
    "3야선": EventType.FIELDERS_CHOICE,
    "실책": EventType.ERROR,
    "송구실책": EventType.ERROR,
    "도루": EventType.STOLEN_BASE,
    "도루자": EventType.CAUGHT_STEALING,
    "주자아웃": EventType.RUNNER_OUT,
    "견제사": EventType.RUNNER_OUT,
    "런다운": EventType.RUNNER_OUT,
    "폭투": EventType.WILD_PITCH,
    "보크": EventType.BALK,
    "포일": EventType.PASSED_BALL,
    "타격방해": EventType.CATCHER_INTERFERENCE,
    "대주자": EventType.NOT_A_PLATE_APPEARANCE,
    "대수비": EventType.NOT_A_PLATE_APPEARANCE,
}

HOME_RUN_SUFFIXES = ("홈",)
TRIPLE_SUFFIXES = ("3",)
DOUBLE_SUFFIXES = ("2",)
SINGLE_SUFFIXES = ("안",)
GROUND_OUT_SUFFIX = "땅"
FIELDERS_CHOICE_SUFFIX = "땅R"
FLY_OUT_SUFFIX = "플"
SAC_FLY_INFIX = "희플"
LINE_OUT_SUFFIX = "직"
ERROR_SUFFIX = "실"


def parse_cell(cell_text: str) -> list[str]:
    if not cell_text:
        return []
    return [part.strip() for part in cell_text.split(",") if part.strip()]


def classify(code: str) -> EventType:
    if code in EXACT_CODE_TABLE:
        return EXACT_CODE_TABLE[code]
    if code.endswith(SAC_FLY_INFIX) or code == "유희플":
        return EventType.SAC_FLY
    if code.endswith(FIELDERS_CHOICE_SUFFIX):
        return EventType.FIELDERS_CHOICE
    if code.endswith(HOME_RUN_SUFFIXES):
        return EventType.HOME_RUN
    if code.endswith(TRIPLE_SUFFIXES) and not code.endswith(FIELDERS_CHOICE_SUFFIX):
        return EventType.HIT_TRIPLE
    if code.endswith(DOUBLE_SUFFIXES) and not code.endswith(FIELDERS_CHOICE_SUFFIX):
        return EventType.HIT_DOUBLE
    if code.endswith(SINGLE_SUFFIXES):
        return EventType.HIT_SINGLE
    if code.endswith(LINE_OUT_SUFFIX):
        return EventType.LINEOUT
    if code.endswith(FLY_OUT_SUFFIX):
        return EventType.FLYOUT
    if code.endswith(GROUND_OUT_SUFFIX):
        return EventType.GROUNDOUT
    if code.endswith(ERROR_SUFFIX) and code != "실책":
        return EventType.ERROR
    return EventType.UNKNOWN


def is_out(event_type: EventType) -> bool:
    return event_type in OUT_EVENTS
```

- [x] **Step 4: 테스트 실행하여 통과 확인, suffix 순서 버그 수정**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_events.py -v`

주의: `"유땅R"`이 `GROUND_OUT_SUFFIX`(`"땅"`으로 끝나지 않음, `"R"`로 끝남)를 먼저 안 타도록
`FIELDERS_CHOICE_SUFFIX` 체크가 `GROUND_OUT_SUFFIX` 체크보다 먼저 와야 함 — 위 구현은 이미 순서를
맞춰놓았음(`endswith("땅R")`을 `endswith("땅")`보다 먼저 검사). 테스트가 실패하면 이 순서를 재확인.
Expected: PASS (모든 테스트 통과)

- [x] **Step 5: 커밋 및 푸시**

```bash
git add src/gameone_analyzer/events.py tests/test_events.py
git commit -m "feat: add event code classification table"
git push
```

---

### Task 3: 박스스코어 HTML → 원시 레코드 파서

**Files:**
- Create: `src/gameone_analyzer/parser.py`
- Test: `tests/fixtures/sample_1685452.html` (Task 1에서 수집한 실제 HTML을 고정 픽스처로 저장)
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: `events.parse_cell`, `events.classify` (Task 2)
- Produces:
  - `parser.GameMeta` dataclass: `game_idx: int, league: str, date_str: str, venue: str,
    away_team: str, home_team: str, away_innings: list[int|None], home_innings: list[int|None],
    away_runs: int, home_runs: int`
  - `parser.BatterRow` dataclass: `team: str, order: int, position: str, name: str, uniform_no: str,
    cells: list[str]` — `cells`는 이닝 1~12 각각의 원문 셀 텍스트(빈 문자열 포함, 길이 12 고정)
  - `parser.parse_game_meta(html: str, game_idx: int) -> GameMeta`
  - `parser.parse_batter_rows(html: str) -> list[BatterRow]` — 문서 순서대로(원정팀 먼저) 모든 행 반환.
    `team` 필드는 `<h4>` 순서로 원정/홈 판별해 채움.

**픽스처 준비:**

- [x] **Step 1: 실제 샘플 HTML을 테스트 픽스처로 복사**

```bash
mkdir -p tests/fixtures
cp /tmp/gameone_probe/1685452.html tests/fixtures/sample_1685452.html
```

- [x] **Step 2: 실패하는 테스트 작성**

`tests/test_parser.py`:
```python
from pathlib import Path
from gameone_analyzer.parser import parse_game_meta, parse_batter_rows

FIXTURE = Path(__file__).parent / "fixtures" / "sample_1685452.html"


def _html():
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_game_meta():
    meta = parse_game_meta(_html(), game_idx=1685452)
    assert meta.league == "일요 싱글"
    assert meta.venue == "살곶이야구장"
    assert meta.away_team == "성동 바이퍼스"
    assert meta.home_team == "한양대학교 D-Dogs OB"
    assert meta.away_runs == 8
    assert meta.home_runs == 8
    assert meta.away_innings[:4] == [2, 0, 6, 0]
    assert meta.home_innings[:4] == [2, 0, 3, 3]


def test_parse_batter_rows_first_batter():
    rows = parse_batter_rows(_html())
    away_rows = [r for r in rows if r.team == "away"]
    home_rows = [r for r in rows if r.team == "home"]
    assert len(away_rows) > 0
    assert len(home_rows) > 0

    first_home = home_rows[0]
    assert first_home.order == 1
    assert first_home.name == "박준호"
    assert first_home.uniform_no == "53"
    assert first_home.position == "중"
    assert first_home.cells[0] == "4구,도루,도루"
    assert first_home.cells[1] == "4구,도루,도루"
    assert first_home.cells[2] == "4구"
    assert first_home.cells[3] == ""
    assert len(first_home.cells) == 12


def test_parse_batter_rows_third_home_batter():
    rows = parse_batter_rows(_html())
    home_rows = [r for r in rows if r.team == "home"]
    third = home_rows[2]
    assert third.name == "천준태"
    assert third.cells[0] == "좌안"
    assert third.cells[1] == "유플"
    assert third.cells[2] == "투야선"
```

- [x] **Step 3: 테스트 실행하여 실패 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gameone_analyzer.parser'`

- [x] **Step 4: 구현 작성**

`src/gameone_analyzer/parser.py`:
```python
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class GameMeta:
    game_idx: int
    league: str
    date_str: str
    venue: str
    away_team: str
    home_team: str
    away_innings: list
    home_innings: list
    away_runs: int
    home_runs: int


@dataclass
class BatterRow:
    team: str  # "away" or "home"
    order: int
    position: str
    name: str
    uniform_no: str
    cells: list = field(default_factory=list)


def _innings_from_row(tr) -> list:
    tds = tr.find_all("td", class_="round")
    innings = []
    for td in tds[:12]:
        text = td.get_text(strip=True)
        innings.append(int(text) if text.isdigit() else None)
    return innings


def parse_game_meta(html: str, game_idx: int) -> GameMeta:
    soup = BeautifulSoup(html, "lxml")
    score_table = soup.find("table", class_="score_teble")
    caption = score_table.find("caption").get_text(strip=True)
    league, rest = [p.strip() for p in caption.split("/", 1)]
    date_str, venue = [p.strip() for p in rest.rsplit("/", 1)]

    rows = score_table.find("tbody").find_all("tr")
    away_row, home_row = rows[0], rows[1]

    away_team = away_row.find("th").get_text(strip=True)
    home_team = home_row.find("th").get_text(strip=True)

    away_innings = _innings_from_row(away_row)
    home_innings = _innings_from_row(home_row)

    away_runs = int(away_row.find("td", class_="r").get_text(strip=True))
    home_runs = int(home_row.find("td", class_="r").get_text(strip=True))

    return GameMeta(
        game_idx=game_idx,
        league=league,
        date_str=date_str,
        venue=venue,
        away_team=away_team,
        home_team=home_team,
        away_innings=away_innings,
        home_innings=home_innings,
        away_runs=away_runs,
        home_runs=home_runs,
    )


def parse_batter_rows(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table", class_="record_table inc_round", summary="타자기록")
    assert len(tables) == 2, f"expected 2 batter tables, found {len(tables)}"

    result = []
    for team_key, table in zip(("away", "home"), tables):
        for tr in table.find("tbody").find_all("tr"):
            th = tr.find("th")
            order = int(th.find("span", class_="num").get_text(strip=True))
            position = th.find("span", class_="position").get_text(strip=True)
            name_span = th.find("span", class_="name")
            name = name_span.find("strong").get_text(strip=True)
            match = re.search(r"\((\d+)\)", name_span.get_text())
            uniform_no = match.group(1) if match else ""

            cells = []
            for td in tr.find_all("td", class_="round")[:12]:
                cells.append(td.get_text(strip=True))

            result.append(
                BatterRow(
                    team=team_key,
                    order=order,
                    position=position,
                    name=name,
                    uniform_no=uniform_no,
                    cells=cells,
                )
            )
    return result
```

- [x] **Step 5: 테스트 실행하여 통과 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_parser.py -v`
Expected: PASS

- [x] **Step 6: 커밋 및 푸시**

```bash
git add src/gameone_analyzer/parser.py tests/test_parser.py tests/fixtures/sample_1685452.html
git commit -m "feat: parse boxscore HTML into game meta and batter rows"
git push
```

---

### Task 4: 이닝별 타석 상태 시뮬레이터 (아웃카운트·주자상황 역산)

**Files:**
- Create: `src/gameone_analyzer/simulator.py`
- Test: `tests/test_simulator.py`

**Interfaces:**
- Consumes: `parser.BatterRow` (Task 3), `events.parse_cell`, `events.classify`, `events.is_out` (Task 2)
- Produces:
  - `simulator.RunnerState` dataclass: `first: bool, second: bool, third: bool`
  - `simulator.PlateAppearance` dataclass: `team: str, inning: int, order: int, name: str,
    outs_before: int, runners_before: RunnerState, cell_text: str, events: list[str],
    is_risp: bool`
  - `simulator.simulate_team_innings(rows: list[BatterRow], team: str) -> list[PlateAppearance]`
    — 팀의 `BatterRow`들에서 이닝별로 순서대로 순회하며 각 타석 시작 시점 상태를 기록.
    이닝이 바뀌면 상태 리셋(CLAUDE.md 의사코드 그대로). 셀이 빈 문자열이면 그 타순은 그 이닝에
    타석에 서지 않은 것으로 스킵.
  - `simulator.apply_events(state: RunnerState, outs: int, event_codes: list[str]) -> tuple[RunnerState, int, int]`
    — `(다음 상태, 다음 아웃카운트, 이번 타석에서 발생한 득점 수)` 반환. 단순화된 진루 규칙:
    안타/볼넷/HBP류는 강제진루만 처리(1루타=타자 1루, 기존 1루 주자는 2루로 강제 진루한 경우에만 진루—
    단순 모델: 1루타는 모든 주자 1루씩 진루, 2루타는 2루씩, 3루타는 3루씩, 홈런은 전원 홈으로 처리).
    아웃 이벤트는 `is_out`이 True인 이벤트마다 outs+1(단, 병살은 +2, 이미 2아웃이면 이닝 종료로 outs=3에서 멈춤).
    도루/견제사/폭투 등은 CLAUDE.md 표에 따라 진루/아웃만 반영.

**단순화 명시(중요 — 이후 세션에서 정교화 예정, 지금은 스코어보드 대조로 큰 오차만 검증):**
콤마로 묶인 후속 이벤트가 "그 타자 자신의 후속 진루"인지 "다른 주자의 동시 이벤트"인지 코드만으로
완전히 판별할 수 없는 케이스가 있음(CLAUDE.md에 명시된 known issue). 이번 태스크에서는 다음 규칙으로
근사 처리하고, Task 5 검증 단계에서 이닝별 득점 합계가 스코어보드와 다르면 해당 경기를 로그에
`MISMATCH`로 남긴다(전체 파이프라인을 막지 않음 — 개인 분석 도구 특성상 100% 정합보다 커버리지 우선):
- 안타/볼넷/HBP/에러/야선 계열 코드는 "타자 진루" 이벤트로 처리
- 도루/도루자/주자아웃/견제사/폭투/보크/포일/런다운은 "주자 상태 변경" 이벤트로 처리(타자는 그대로 타석 유지 상태로 간주하지 않고, 해당 셀의 첫 이벤트가 이미 타자 결과를 확정지었다고 가정 — 첫 이벤트로 아웃/진루가 정해지고 이후 이벤트는 잔여 주자에게 적용)
- 홈런/3루타/2루타는 강제 진루량만큼 모든 주자 및 타자를 진루, 3루를 넘는 주자는 득점 처리

- [x] **Step 1: 실패하는 테스트 작성**

`tests/test_simulator.py`:
```python
from gameone_analyzer.parser import BatterRow
from gameone_analyzer.simulator import simulate_team_innings, RunnerState, apply_events


def test_apply_events_walk_puts_runner_on_first():
    state = RunnerState(first=False, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["4구"])
    assert new_state == RunnerState(first=True, second=False, third=False)
    assert outs == 0
    assert runs == 0


def test_apply_events_single_advances_existing_runner():
    state = RunnerState(first=True, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["좌안"])
    assert new_state == RunnerState(first=True, second=True, third=False)
    assert outs == 0
    assert runs == 0


def test_apply_events_home_run_scores_everyone():
    state = RunnerState(first=True, second=False, third=True)
    new_state, outs, runs = apply_events(state, 1, ["중월홈"])
    assert new_state == RunnerState(first=False, second=False, third=False)
    assert runs == 3
    assert outs == 1


def test_apply_events_strikeout_increments_outs():
    state = RunnerState(first=False, second=True, third=False)
    new_state, outs, runs = apply_events(state, 1, ["삼진"])
    assert outs == 2
    assert new_state == RunnerState(first=False, second=True, third=False)
    assert runs == 0


def test_apply_events_double_play_adds_two_outs():
    state = RunnerState(first=True, second=False, third=False)
    new_state, outs, runs = apply_events(state, 0, ["유땅병살"])
    assert outs == 2


def test_simulate_team_innings_resets_outs_each_inning_and_flags_risp():
    rows = [
        BatterRow(team="home", order=1, position="중", name="A", uniform_no="1",
                   cells=["좌안", "", "", "", "", "", "", "", "", "", "", ""]),
        BatterRow(team="home", order=2, position="포", name="B", uniform_no="2",
                   cells=["좌안", "", "", "", "", "", "", "", "", "", "", ""]),
        BatterRow(team="home", order=3, position="一", name="C", uniform_no="3",
                   cells=["좌중2", "", "", "", "", "", "", "", "", "", "", ""]),
    ]
    pas = simulate_team_innings(rows, team="home")

    inning1 = [pa for pa in pas if pa.inning == 1]
    assert len(inning1) == 3

    assert inning1[0].outs_before == 0
    assert inning1[0].runners_before == RunnerState(False, False, False)
    assert inning1[0].is_risp is False

    assert inning1[1].outs_before == 0
    assert inning1[1].runners_before == RunnerState(True, False, False)
    assert inning1[1].is_risp is False

    assert inning1[2].outs_before == 0
    assert inning1[2].runners_before == RunnerState(True, True, False)
    assert inning1[2].is_risp is True


def test_simulate_team_innings_skips_empty_cells():
    rows = [
        BatterRow(team="home", order=1, position="중", name="A", uniform_no="1",
                   cells=["좌안"] + [""] * 11),
        BatterRow(team="home", order=2, position="포", name="B", uniform_no="2",
                   cells=[""] * 12),
    ]
    pas = simulate_team_innings(rows, team="home")
    assert len(pas) == 1
    assert pas[0].name == "A"
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_simulator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gameone_analyzer.simulator'`

- [x] **Step 3: 구현 작성**

`src/gameone_analyzer/simulator.py`:
```python
from dataclasses import dataclass

from gameone_analyzer.events import classify, is_out, parse_cell, EventType
from gameone_analyzer.parser import BatterRow


@dataclass(frozen=True)
class RunnerState:
    first: bool
    second: bool
    third: bool


@dataclass
class PlateAppearance:
    team: str
    inning: int
    order: int
    name: str
    outs_before: int
    runners_before: RunnerState
    cell_text: str
    events: list
    is_risp: bool


ADVANCE_BASES = {
    EventType.HIT_SINGLE: 1,
    EventType.WALK: 1,
    EventType.INTENTIONAL_WALK: 1,
    EventType.HBP: 1,
    EventType.ERROR: 1,
    EventType.FIELDERS_CHOICE: 1,
    EventType.HIT_DOUBLE: 2,
    EventType.HIT_TRIPLE: 3,
    EventType.HOME_RUN: 4,
}

RUNNER_ONLY_EVENTS = {
    EventType.STOLEN_BASE,
    EventType.CAUGHT_STEALING,
    EventType.RUNNER_OUT,
    EventType.WILD_PITCH,
    EventType.BALK,
    EventType.PASSED_BALL,
}


def _advance_runners(state: RunnerState, bases: int, batter_reaches: bool) -> tuple:
    occupied = []
    if state.first:
        occupied.append(1)
    if state.second:
        occupied.append(2)
    if state.third:
        occupied.append(3)

    runs = 0
    new_bases = set()
    for base in occupied:
        target = base + bases
        if target >= 4:
            runs += 1
        else:
            new_bases.add(target)

    if batter_reaches:
        batter_target = bases
        if batter_target >= 4:
            runs += 1
        else:
            new_bases.add(batter_target)

    new_state = RunnerState(
        first=1 in new_bases,
        second=2 in new_bases,
        third=3 in new_bases,
    )
    return new_state, runs


def _advance_one_runner_for_steal_or_wildpitch(state: RunnerState) -> RunnerState:
    if state.third:
        return state
    if state.second:
        return RunnerState(first=state.first, second=False, third=True)
    if state.first:
        return RunnerState(first=False, second=True, third=state.third)
    return state


def apply_events(state: RunnerState, outs: int, event_codes: list) -> tuple:
    total_runs = 0
    for code in event_codes:
        if outs >= 3:
            break
        event_type = classify(code)

        if event_type == EventType.NOT_A_PLATE_APPEARANCE:
            continue

        if event_type == EventType.DOUBLE_PLAY:
            outs = min(outs + 2, 3)
            continue

        if event_type in (EventType.STRIKEOUT, EventType.GROUNDOUT, EventType.FLYOUT,
                           EventType.LINEOUT, EventType.SAC_FLY, EventType.SAC_BUNT):
            outs += 1
            continue

        if event_type in (EventType.CAUGHT_STEALING, EventType.RUNNER_OUT):
            outs += 1
            continue

        if event_type == EventType.STOLEN_BASE:
            state = _advance_one_runner_for_steal_or_wildpitch(state)
            continue

        if event_type == EventType.WILD_PITCH:
            state = _advance_one_runner_for_steal_or_wildpitch(state)
            continue

        if event_type in ADVANCE_BASES:
            bases = ADVANCE_BASES[event_type]
            state, runs = _advance_runners(state, bases, batter_reaches=True)
            total_runs += runs
            continue

        # UNKNOWN, BALK, PASSED_BALL, CATCHER_INTERFERENCE 등은 상태 변화 없음으로 처리
        continue

    return state, outs, total_runs


def simulate_team_innings(rows: list, team: str) -> list:
    by_inning = {}
    for row in rows:
        if row.team != team:
            continue
        for inning_idx, cell in enumerate(row.cells, start=1):
            if cell:
                by_inning.setdefault(inning_idx, []).append((row.order, row.name, cell))

    result = []
    for inning in sorted(by_inning.keys()):
        state = RunnerState(False, False, False)
        outs = 0
        for order, name, cell_text in by_inning[inning]:
            is_risp = state.second or state.third
            events_list = parse_cell(cell_text)
            result.append(
                PlateAppearance(
                    team=team,
                    inning=inning,
                    order=order,
                    name=name,
                    outs_before=outs,
                    runners_before=state,
                    cell_text=cell_text,
                    events=events_list,
                    is_risp=is_risp,
                )
            )
            state, outs, _runs = apply_events(state, outs, events_list)

    return result
```

- [x] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_simulator.py -v`
Expected: PASS. 실패 시 `_advance_runners`의 베이스 오버플로 로직(`target >= 4`) 우선순위를 확인 —
3루 주자부터 먼저 진루 처리해야 도루/진루 순서 역전으로 인한 중복 배치가 생기지 않음(현재 구현은
`occupied` 리스트가 1,2,3 오름차순이라도 `new_bases`는 집합이라 최종 상태만 반영되므로 문제 없음,
다만 동시에 여러 주자가 같은 target로 겹치는 극단 케이스는 없음 — 야구 규칙상 발생 불가).

- [x] **Step 5: 커밋 및 푸시**

```bash
git add src/gameone_analyzer/simulator.py tests/test_simulator.py
git commit -m "feat: simulate outs/runner state per plate appearance"
git push
```

---

### Task 5: 스코어보드 대조 검증기 + 95경기 파이프라인 실행

**Files:**
- Create: `src/gameone_analyzer/validator.py`
- Create: `scripts/build_db.py`
- Test: `tests/test_validator.py`

**Interfaces:**
- Consumes: `parser.GameMeta`, `simulator.PlateAppearance` (Task 3, 4)
- Produces:
  - `validator.compute_inning_runs(pas: list[PlateAppearance]) -> dict[int, int]` — 이닝별 시뮬레이션 총득점
    (각 PA를 재실행하며 `apply_events`의 runs를 이닝별로 합산).
  - `validator.compare_with_scoreboard(sim_runs: dict[int, int], scoreboard_innings: list) -> list[str]`
    — 불일치 이닝 리스트(문자열 설명)를 반환, 일치하면 빈 리스트.

**주의:** `simulate_team_innings`는 상태만 추적하고 득점을 반환하지 않으므로, 검증기에서는 각 PA를
`apply_events`로 다시 돌려서 득점을 집계한다(순수 함수라 재실행 비용 낮음, 95경기 규모에서 문제 없음).

- [x] **Step 1: 실패하는 테스트 작성**

`tests/test_validator.py`:
```python
from gameone_analyzer.parser import BatterRow
from gameone_analyzer.simulator import simulate_team_innings
from gameone_analyzer.validator import compute_inning_runs, compare_with_scoreboard


def test_compute_inning_runs_matches_home_run():
    rows = [
        BatterRow(team="home", order=1, position="중", name="A", uniform_no="1",
                   cells=["4구"] + [""] * 11),
        BatterRow(team="home", order=2, position="포", name="B", uniform_no="2",
                   cells=["중월홈"] + [""] * 11),
    ]
    pas = simulate_team_innings(rows, team="home")
    runs = compute_inning_runs(pas)
    assert runs == {1: 2}


def test_compare_with_scoreboard_detects_mismatch():
    sim_runs = {1: 2, 2: 0}
    scoreboard = [3, 0]
    mismatches = compare_with_scoreboard(sim_runs, scoreboard)
    assert len(mismatches) == 1
    assert "inning 1" in mismatches[0]


def test_compare_with_scoreboard_matches():
    sim_runs = {1: 2, 2: 1}
    scoreboard = [2, 1]
    assert compare_with_scoreboard(sim_runs, scoreboard) == []
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_validator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [x] **Step 3: 구현 작성**

`src/gameone_analyzer/validator.py`:
```python
from gameone_analyzer.simulator import RunnerState, apply_events


def compute_inning_runs(pas: list) -> dict:
    runs_by_inning = {}
    for pa in pas:
        _state, _outs, runs = apply_events(pa.runners_before, pa.outs_before, pa.events)
        runs_by_inning[pa.inning] = runs_by_inning.get(pa.inning, 0) + runs
    return runs_by_inning


def compare_with_scoreboard(sim_runs: dict, scoreboard_innings: list) -> list:
    mismatches = []
    for idx, expected in enumerate(scoreboard_innings, start=1):
        if expected is None:
            continue
        actual = sim_runs.get(idx, 0)
        if actual != expected:
            mismatches.append(
                f"inning {idx}: simulated={actual} scoreboard={expected}"
            )
    return mismatches
```

- [x] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_validator.py -v`
Expected: PASS

- [x] **Step 5: SQLite 스키마 + 전체 빌드 스크립트 작성**

`scripts/build_db.py`:
```python
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.fetch import fetch_boxscore_html, load_game_ids_from_csv
from gameone_analyzer.parser import parse_game_meta, parse_batter_rows
from gameone_analyzer.simulator import simulate_team_innings
from gameone_analyzer.validator import compute_inning_runs, compare_with_scoreboard

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "gameone.db"

OUR_TEAM = "한양대학교 D-Dogs OB"

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    game_idx INTEGER PRIMARY KEY,
    season INTEGER,
    league TEXT,
    venue TEXT,
    date_str TEXT,
    away_team TEXT,
    home_team TEXT,
    away_runs INTEGER,
    home_runs INTEGER,
    validated INTEGER
);

CREATE TABLE IF NOT EXISTS plate_appearances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_idx INTEGER,
    team TEXT,
    is_our_team INTEGER,
    inning INTEGER,
    batting_order INTEGER,
    player_name TEXT,
    outs_before INTEGER,
    runner_first INTEGER,
    runner_second INTEGER,
    runner_third INTEGER,
    is_risp INTEGER,
    cell_text TEXT,
    FOREIGN KEY (game_idx) REFERENCES games(game_idx)
);
"""


def build(season_csv_row_map):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    game_ids = load_game_ids_from_csv(ROOT / "games_meta.csv")
    mismatch_log = []

    for game_idx in game_ids:
        html = fetch_boxscore_html(game_idx, CACHE_DIR, delay_sec=0)
        meta = parse_game_meta(html, game_idx)
        rows = parse_batter_rows(html)

        away_pas = simulate_team_innings(rows, team="away")
        home_pas = simulate_team_innings(rows, team="home")

        away_mismatches = compare_with_scoreboard(compute_inning_runs(away_pas), meta.away_innings)
        home_mismatches = compare_with_scoreboard(compute_inning_runs(home_pas), meta.home_innings)
        validated = 1 if not away_mismatches and not home_mismatches else 0
        if not validated:
            mismatch_log.append((game_idx, away_mismatches + home_mismatches))

        season = season_csv_row_map.get(game_idx)

        conn.execute(
            "INSERT OR REPLACE INTO games VALUES (?,?,?,?,?,?,?,?,?,?)",
            (game_idx, season, meta.league, meta.venue, meta.date_str,
             meta.away_team, meta.home_team, meta.away_runs, meta.home_runs, validated),
        )

        conn.execute("DELETE FROM plate_appearances WHERE game_idx = ?", (game_idx,))
        for pa in away_pas + home_pas:
            is_our_team = 1 if (
                (pa.team == "away" and meta.away_team == OUR_TEAM) or
                (pa.team == "home" and meta.home_team == OUR_TEAM)
            ) else 0
            conn.execute(
                "INSERT INTO plate_appearances "
                "(game_idx, team, is_our_team, inning, batting_order, player_name, "
                " outs_before, runner_first, runner_second, runner_third, is_risp, cell_text) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (game_idx, pa.team, is_our_team, pa.inning, pa.order, pa.name,
                 pa.outs_before, int(pa.runners_before.first), int(pa.runners_before.second),
                 int(pa.runners_before.third), int(pa.is_risp), pa.cell_text),
            )

    conn.commit()
    conn.close()

    print(f"done. {len(mismatch_log)} games with scoreboard mismatches:")
    for game_idx, mismatches in mismatch_log:
        print(f"  game_idx={game_idx}: {mismatches}")


if __name__ == "__main__":
    import csv

    season_map = {}
    with open(ROOT / "games_meta.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            season_map[int(row["game_idx"])] = int(row["season"])

    build(season_map)
```

이 스크립트는 `data/raw/`에 이미 캐시된 HTML만 사용(`delay_sec=0`) — 실제 신규 수집은 Task 1의
`scripts/fetch_all.py`로 먼저 완료해야 한다.

- [x] **Step 6: 커밋 및 푸시 (스크립트만, DB 파일은 커밋하지 않음)**

```bash
git add src/gameone_analyzer/validator.py tests/test_validator.py scripts/build_db.py
git commit -m "feat: add scoreboard validator and sqlite build pipeline"
git push
```

---

### Task 6: 실제 95경기 수집 + DB 빌드 실행 (사용자 승인 필요 단계)

이 태스크는 코드 작성이 아니라 **실행** 태스크다. 실행 전 사용자에게 "지금 95경기를 순차로
(요청당 3초 지연, 약 5분) 수집하겠습니다"라고 알리고 진행한다 — CLAUDE.md의 재확인 요구사항 충족.

- [x] **Step 1: 원문 HTML 95건 수집**

```bash
cd /Users/bae/project/workspace/gameone_analyzer
.venv/bin/python scripts/fetch_all.py
```

Expected: 95줄 출력(`fetched` 또는 `cached`), 에러 없이 종료. `data/raw/`에 `*.html` 95개 생성 확인.

- [x] **Step 2: DB 빌드 실행**

```bash
.venv/bin/python scripts/build_db.py
```

Expected: `data/gameone.db` 생성, 마지막 줄에 "done. N games with scoreboard mismatches:" 출력.
mismatch가 있는 경기는 로그에 game_idx와 이닝별 불일치 내용이 출력됨 — 전부 기록해두고 다음 단계로 진행
(CLAUDE.md 방침대로 100% 정합을 막지 않음, 다만 mismatch 비율이 30% 넘으면 사용자에게 보고 후 이벤트
코드 사전 보강이 필요한지 확인).

- [x] **Step 3: 검증 결과 요약 확인**

```bash
.venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('data/gameone.db')
total = conn.execute('SELECT COUNT(*) FROM games').fetchone()[0]
validated = conn.execute('SELECT COUNT(*) FROM games WHERE validated = 1').fetchone()[0]
pa_count = conn.execute('SELECT COUNT(*) FROM plate_appearances WHERE is_our_team = 1').fetchone()[0]
print(f'games={total} validated={validated} our_team_pas={pa_count}')
"
```

Expected: `games=95`, `our_team_pas`가 0보다 큰 값(대략 경기당 30~40타석 * 95 ≈ 3000 안팎).

- [x] **Step 4: 진행 상황 문서에 결과 기록 (Task 커밋에 포함)**

이 계획 문서(`docs/superpowers/plans/2026-08-10-gameone-analyzer.md`)의 이 Task 6 섹션 아래에
실제 mismatch 개수와 game_idx 목록을 코드 블록으로 추가한다. 커밋 메시지에 결과를 남긴다.

```bash
git add docs/superpowers/plans/2026-08-10-gameone-analyzer.md
git commit -m "docs: record scoreboard validation results for 95 games"
git push
```

(DB 파일 `data/gameone.db`와 원문 HTML `data/raw/`는 `.gitignore`에 포함되어 커밋하지 않음 —
gameone.kr 원문 재배포를 피하기 위함. 다음 세션에서 이어가려면 로컬에 `data/` 디렉터리가 남아있어야
하므로, 세션이 끊기기 전 `git status`로 확인만 하고 삭제하지 않는다.)

---

### Task 7: 집계 쿼리 모듈 (필터 → 스탯 계산)

**Files:**
- Create: `src/gameone_analyzer/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `data/gameone.db` (Task 6에서 생성)
- Produces:
  - `stats.FilterOptions` dataclass: `outs: list[int] | None, runner_states: list[str] | None,
    risp_only: bool, venues: list[str] | None, seasons: list[int] | None, leagues: list[str] | None`
    (`runner_states`는 `"empty","1","2","3","12","13","23","123"` 중 값들의 리스트)
  - `stats.query_plate_appearances(conn: sqlite3.Connection, filters: FilterOptions) -> list[sqlite3.Row]`
    — `is_our_team = 1` 고정, 필터 조건을 SQL WHERE로 변환해 조회.
  - `stats.runner_state_key(first: bool, second: bool, third: bool) -> str` — 위 8종 키 문자열 반환.
  - `stats.venue_matches_group(venue: str, group_venues: list[str]) -> bool` — 공백 제거 후 비교
    (CLAUDE.md에 명시된 "구의 야구장"/"구의야구장" 표기 불일치 정규화).

이 태스크는 스탯 자체(타율/피안타율 등)는 계산하지 않는다 — 원시 이벤트 코드로부터의 안타/타수 판정은
Task 8(타자 페이지 빌더)와 Task 9(투수 페이지 빌더)에서 각 관점에 맞게 계산한다. 여기서는 조건에 맞는
타석(PA) 원시 행만 뽑아주는 공용 필터 레이어를 만든다.

- [x] **Step 1: 실패하는 테스트 작성**

`tests/test_stats.py`:
```python
import sqlite3
from gameone_analyzer.stats import FilterOptions, query_plate_appearances, runner_state_key, venue_matches_group


def _make_test_db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE games (
            game_idx INTEGER PRIMARY KEY, season INTEGER, league TEXT, venue TEXT,
            date_str TEXT, away_team TEXT, home_team TEXT, away_runs INTEGER,
            home_runs INTEGER, validated INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE plate_appearances (
            id INTEGER PRIMARY KEY, game_idx INTEGER, team TEXT, is_our_team INTEGER,
            inning INTEGER, batting_order INTEGER, player_name TEXT, outs_before INTEGER,
            runner_first INTEGER, runner_second INTEGER, runner_third INTEGER,
            is_risp INTEGER, cell_text TEXT
        )
    """)
    conn.execute(
        "INSERT INTO games VALUES (1, 2025, '일요 싱글', '살곶이야구장', 'd', 'X', 'Y', 5, 3, 1)"
    )
    conn.execute(
        "INSERT INTO plate_appearances VALUES "
        "(1, 1, 'home', 1, 1, 3, 'A', 1, 0, 1, 0, 1, '좌안')"
    )
    conn.execute(
        "INSERT INTO plate_appearances VALUES "
        "(2, 1, 'home', 1, 1, 4, 'B', 0, 0, 0, 0, 0, '삼진')"
    )
    conn.commit()
    return conn


def test_runner_state_key():
    assert runner_state_key(False, False, False) == "empty"
    assert runner_state_key(True, False, False) == "1"
    assert runner_state_key(False, True, True) == "23"
    assert runner_state_key(True, True, True) == "123"


def test_venue_matches_group_ignores_whitespace():
    assert venue_matches_group("구의 야구장", ["구의야구장"]) is True
    assert venue_matches_group("살곶이야구장", ["구의야구장"]) is False


def test_query_plate_appearances_filters_by_risp(tmp_path):
    conn = _make_test_db(tmp_path)
    filters = FilterOptions(outs=None, runner_states=None, risp_only=True,
                             venues=None, seasons=None, leagues=None)
    rows = query_plate_appearances(conn, filters)
    assert len(rows) == 1
    assert rows[0]["player_name"] == "A"


def test_query_plate_appearances_filters_by_outs(tmp_path):
    conn = _make_test_db(tmp_path)
    filters = FilterOptions(outs=[0], runner_states=None, risp_only=False,
                             venues=None, seasons=None, leagues=None)
    rows = query_plate_appearances(conn, filters)
    assert len(rows) == 1
    assert rows[0]["player_name"] == "B"


def test_query_plate_appearances_filters_by_season_and_league(tmp_path):
    conn = _make_test_db(tmp_path)
    filters = FilterOptions(outs=None, runner_states=None, risp_only=False,
                             venues=None, seasons=[2025], leagues=["일요 싱글"])
    rows = query_plate_appearances(conn, filters)
    assert len(rows) == 2

    filters_no_match = FilterOptions(outs=None, runner_states=None, risp_only=False,
                                      venues=None, seasons=[2024], leagues=None)
    assert query_plate_appearances(conn, filters_no_match) == []
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_stats.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [x] **Step 3: 구현 작성**

`src/gameone_analyzer/stats.py`:
```python
import sqlite3
from dataclasses import dataclass


@dataclass
class FilterOptions:
    outs: list
    runner_states: list
    risp_only: bool
    venues: list
    seasons: list
    leagues: list


def runner_state_key(first: bool, second: bool, third: bool) -> str:
    bases = []
    if first:
        bases.append("1")
    if second:
        bases.append("2")
    if third:
        bases.append("3")
    return "".join(bases) if bases else "empty"


def venue_matches_group(venue: str, group_venues: list) -> bool:
    normalized = venue.replace(" ", "")
    return any(normalized == v.replace(" ", "") for v in group_venues)


def query_plate_appearances(conn: sqlite3.Connection, filters: FilterOptions):
    conn.row_factory = sqlite3.Row
    query = (
        "SELECT pa.* FROM plate_appearances pa "
        "JOIN games g ON pa.game_idx = g.game_idx "
        "WHERE pa.is_our_team = 1"
    )
    params = []

    if filters.risp_only:
        query += " AND pa.is_risp = 1"

    if filters.outs:
        placeholders = ",".join("?" for _ in filters.outs)
        query += f" AND pa.outs_before IN ({placeholders})"
        params.extend(filters.outs)

    if filters.seasons:
        placeholders = ",".join("?" for _ in filters.seasons)
        query += f" AND g.season IN ({placeholders})"
        params.extend(filters.seasons)

    if filters.leagues:
        placeholders = ",".join("?" for _ in filters.leagues)
        query += f" AND g.league IN ({placeholders})"
        params.extend(filters.leagues)

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    if filters.runner_states:
        rows = [
            r for r in rows
            if runner_state_key(bool(r["runner_first"]), bool(r["runner_second"]), bool(r["runner_third"]))
            in filters.runner_states
        ]

    if filters.venues:
        game_venue = {
            row["game_idx"]: row["venue"]
            for row in conn.execute("SELECT game_idx, venue FROM games").fetchall()
        }
        rows = [
            r for r in rows
            if venue_matches_group(game_venue.get(r["game_idx"], ""), filters.venues)
        ]

    return rows
```

- [x] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_stats.py -v`
Expected: PASS

- [x] **Step 5: 커밋 및 푸시**

```bash
git add src/gameone_analyzer/stats.py tests/test_stats.py
git commit -m "feat: add filter-based plate appearance query layer"
git push
```

---

### Task 8: 정적 데이터 빌드 (선수별 x 필터축별 사전 집계 JSON)

클라이언트에서 매번 SQL을 돌릴 수 없으므로(정적 사이트), 빌드 시점에 "선수별 원시 타석 이벤트 목록 +
각 타석의 필터 태그(outs, runner_state, risp, season, league, venue)"를 JSON으로 뽑아 GitHub Pages에
포함시킨다. 실제 스탯 계산(타율 등)은 브라우저에서 필터링 후 집계 — 이렇게 해야 어떤 필터 조합이든
사전 계산 없이 즉시 대응 가능(엑셀 필터와 동일한 UX).

**Files:**
- Create: `src/gameone_analyzer/export.py`
- Create: `scripts/build_site_data.py`
- Test: `tests/test_export.py`

**Interfaces:**
- Consumes: `data/gameone.db`, `stats.runner_state_key`
- Produces:
  - `export.PlateAppearanceRecord` — dict 형태 JSON-직렬화 가능 레코드:
    `{"game_idx": int, "season": int, "league": str, "venue": str, "team_role": "away"|"home",
      "player_name": str, "inning": int, "outs_before": int, "runner_state": str, "is_risp": bool,
      "cell_text": str, "events": list[str], "result": str}`.
    `result`는 타자 관점 최종 결과 분류 문자열(`"1B","2B","3B","HR","BB","HBP","SO","OUT","ERROR","FC","SF","SAC",
    "OTHER"`) — `events.classify`의 첫 유효 이벤트(대주자/대수비가 아닌 첫 코드) 기준.
  - `export.classify_result(events_codes: list[str]) -> str` — 위 문자열 매핑.
  - `export.export_all_plate_appearances(conn: sqlite3.Connection) -> list[dict]` — 우리팀 전체 PA를
    `PlateAppearanceRecord` 형태 dict 리스트로 반환(투수 이름 포함 — 상대팀 투수는 이 태스크에서는
    생략, Task 9에서 별도 처리).

- [x] **Step 1: 실패하는 테스트 작성**

`tests/test_export.py`:
```python
from gameone_analyzer.export import classify_result


def test_classify_result_single():
    assert classify_result(["좌안"]) == "1B"


def test_classify_result_home_run():
    assert classify_result(["중월홈"]) == "HR"


def test_classify_result_walk():
    assert classify_result(["4구"]) == "BB"


def test_classify_result_strikeout():
    assert classify_result(["삼진"]) == "SO"


def test_classify_result_groundout():
    assert classify_result(["유땅"]) == "OUT"


def test_classify_result_double_play():
    assert classify_result(["유땅병살"]) == "OUT"


def test_classify_result_sac_fly():
    assert classify_result(["중희플"]) == "SF"


def test_classify_result_skips_pinch_runner_prefix():
    assert classify_result(["대주자", "삼진"]) == "SO"


def test_classify_result_error():
    assert classify_result(["실책"]) == "ERROR"


def test_classify_result_fielders_choice():
    assert classify_result(["투야선"]) == "FC"


def test_classify_result_unknown_defaults_other():
    assert classify_result(["존재하지않는코드"]) == "OTHER"
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_export.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [x] **Step 3: 구현 작성**

`src/gameone_analyzer/export.py`:
```python
import sqlite3

from gameone_analyzer.events import classify, EventType
from gameone_analyzer.stats import runner_state_key

RESULT_MAP = {
    EventType.HIT_SINGLE: "1B",
    EventType.HIT_DOUBLE: "2B",
    EventType.HIT_TRIPLE: "3B",
    EventType.HOME_RUN: "HR",
    EventType.WALK: "BB",
    EventType.INTENTIONAL_WALK: "BB",
    EventType.HBP: "HBP",
    EventType.STRIKEOUT: "SO",
    EventType.GROUNDOUT: "OUT",
    EventType.FLYOUT: "OUT",
    EventType.LINEOUT: "OUT",
    EventType.DOUBLE_PLAY: "OUT",
    EventType.SAC_FLY: "SF",
    EventType.SAC_BUNT: "SAC",
    EventType.FIELDERS_CHOICE: "FC",
    EventType.ERROR: "ERROR",
}


def classify_result(events_codes: list) -> str:
    for code in events_codes:
        event_type = classify(code)
        if event_type == EventType.NOT_A_PLATE_APPEARANCE:
            continue
        return RESULT_MAP.get(event_type, "OTHER")
    return "OTHER"


def export_all_plate_appearances(conn: sqlite3.Connection) -> list:
    conn.row_factory = sqlite3.Row
    query = (
        "SELECT pa.*, g.season, g.league, g.venue FROM plate_appearances pa "
        "JOIN games g ON pa.game_idx = g.game_idx "
        "WHERE pa.is_our_team = 1"
    )
    records = []
    for row in conn.execute(query).fetchall():
        events_codes = [e for e in row["cell_text"].split(",") if e.strip()]
        records.append({
            "game_idx": row["game_idx"],
            "season": row["season"],
            "league": row["league"],
            "venue": row["venue"],
            "team_role": row["team"],
            "player_name": row["player_name"],
            "inning": row["inning"],
            "outs_before": row["outs_before"],
            "runner_state": runner_state_key(
                bool(row["runner_first"]), bool(row["runner_second"]), bool(row["runner_third"])
            ),
            "is_risp": bool(row["is_risp"]),
            "cell_text": row["cell_text"],
            "events": events_codes,
            "result": classify_result(events_codes),
        })
    return records
```

- [x] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && .venv/bin/python -m pytest tests/test_export.py -v`
Expected: PASS

- [x] **Step 5: 빌드 스크립트 작성**

`scripts/build_site_data.py`:
```python
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.export import export_all_plate_appearances

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "gameone.db"
OUT_PATH = ROOT / "docs" / "data.json"


def main():
    conn = sqlite3.connect(DB_PATH)
    records = export_all_plate_appearances(conn)
    conn.close()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(records)} plate appearances to {OUT_PATH}")


if __name__ == "__main__":
    main()
```

- [x] **Step 6: 커밋 및 푸시**

```bash
git add src/gameone_analyzer/export.py tests/test_export.py scripts/build_site_data.py
git commit -m "feat: export plate appearances to static JSON for site"
git push
```

(주의: `docs/data.json`은 Task 6 실행 후 실제 DB가 있어야 생성 가능. 이 커밋에는 스크립트만 포함하고,
실제 `docs/data.json` 생성/커밋은 Task 6이 끝난 뒤 Task 10에서 함께 진행한다.)

---

### Task 9: 투수 관점 데이터 확장 (상대 타자 결과를 투수 실적으로 매핑)

타자 페이지는 "우리 팀 선수가 타석에 섰을 때"를 보면 되지만, 투수 페이지는 "우리 팀 투수가 던질 때
상대팀 타자의 결과"를 봐야 한다. 즉 `is_our_team = 0`인 PA 중, 그 이닝에 우리팀 투수가 누구였는지
매핑이 필요하다.

**Files:**
- Modify: `src/gameone_analyzer/export.py`
- Test: `tests/test_export.py` (추가)

**Interfaces:**
- Consumes: `parser` 모듈에 투수 등판 이닝 파싱 추가 필요 — 투수기록 테이블의 "이닝" 컬럼(예: `"2 ⅓"`)은
  누적 이닝이라 등판 구간(시작~종료 이닝) 역산이 필요함. **단순화**: 투수기록 테이블 행 순서 = 등판 순서로
  간주하고, 누적 이닝을 순서대로 더해가며 각 투수의 담당 이닝 구간을 정수 이닝 단위로 근사 배정한다
  (분수 이닝(⅓, ⅔)이 걸친 이닝은 그 이닝 전체를 해당 투수 담당으로 배정 — 교체 시점 타석 단위 정교화는
  범위 밖, README에 known limitation으로 기록).
  - `parser.PitcherRow` dataclass: `team: str, name: str, uniform_no: str, innings_pitched_str: str,
    order: int` (테이블 행 순서)
  - `parser.parse_pitcher_rows(html: str) -> list[PitcherRow]`
  - `export.assign_pitcher_to_innings(pitcher_rows: list) -> dict[int, str]` — `{이닝번호: 투수이름}`.
    `innings_pitched_str`(예: `"2 ⅓"`)을 소수(2.33)로 파싱 후 올림으로 이닝 개수를 정해 순서대로 배정.
  - `export.export_pitcher_view_records(conn) -> list[dict]` — 상대팀 PA(`is_our_team = 0`)에 우리팀
    투수 이름을 붙여 반환. 필드는 Task 8 레코드와 동일 + `"pitcher_name": str`.

- [x] **Step 1: parser에 투수 테이블 파싱 추가 — 실패하는 테스트 작성**

`tests/test_parser.py`에 추가:
```python
from gameone_analyzer.parser import parse_pitcher_rows


def test_parse_pitcher_rows():
    rows = parse_pitcher_rows(_html())
    home_pitchers = [r for r in rows if r.team == "home"]
    assert home_pitchers[0].name == "민호진"
    assert home_pitchers[0].innings_pitched_str == "2 ⅓"
    assert home_pitchers[0].order == 1
    assert home_pitchers[1].name == "박준호"
    assert home_pitchers[1].order == 2
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_parser.py::test_parse_pitcher_rows -v`
Expected: FAIL with `ImportError`

- [x] **Step 3: `parser.py`에 구현 추가**

`src/gameone_analyzer/parser.py`에 추가:
```python
@dataclass
class PitcherRow:
    team: str
    name: str
    uniform_no: str
    innings_pitched_str: str
    order: int


def parse_pitcher_rows(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table", class_="record_table", summary="투수기록")
    assert len(tables) == 2, f"expected 2 pitcher tables, found {len(tables)}"

    result = []
    for team_key, table in zip(("away", "home"), tables):
        for order, tr in enumerate(table.find("tbody").find_all("tr"), start=1):
            th = tr.find("th")
            strong = th.find("strong")
            name = strong.get_text(strip=True)
            match = re.search(r"\((\d+)\)", th.get_text())
            uniform_no = match.group(1) if match else ""
            tds = tr.find_all("td")
            innings_str = tds[1].get_text(strip=True)  # 결과, 이닝, ...

            result.append(
                PitcherRow(
                    team=team_key,
                    name=name,
                    uniform_no=uniform_no,
                    innings_pitched_str=innings_str,
                    order=order,
                )
            )
    return result
```

- [x] **Step 4: 테스트 실행하여 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_parser.py -v`
Expected: PASS. 실패 시 `tds[1]`이 실제 "이닝" 컬럼과 맞는지 헤더 순서(결과=tds[0], 이닝=tds[1]) 재확인.

- [x] **Step 5: 이닝-투수 배정 로직 — 실패하는 테스트 작성**

`tests/test_export.py`에 추가:
```python
from gameone_analyzer.parser import PitcherRow
from gameone_analyzer.export import assign_pitcher_to_innings


def test_assign_pitcher_to_innings_simple():
    rows = [
        PitcherRow(team="home", name="민호진", uniform_no="21", innings_pitched_str="2 ⅓", order=1),
        PitcherRow(team="home", name="박준호", uniform_no="53", innings_pitched_str="0 ⅔", order=2),
        PitcherRow(team="home", name="민윤기", uniform_no="45", innings_pitched_str="1", order=3),
    ]
    mapping = assign_pitcher_to_innings(rows)
    assert mapping[1] == "민호진"
    assert mapping[2] == "민호진"
    assert mapping[3] == "민호진"
    assert mapping[4] == "민윤기"


def test_assign_pitcher_to_innings_no_fraction():
    rows = [
        PitcherRow(team="home", name="A", uniform_no="1", innings_pitched_str="3", order=1),
        PitcherRow(team="home", name="B", uniform_no="2", innings_pitched_str="2", order=2),
    ]
    mapping = assign_pitcher_to_innings(rows)
    assert mapping[1] == "A"
    assert mapping[3] == "A"
    assert mapping[4] == "B"
    assert mapping[5] == "B"
```

- [x] **Step 6: 테스트 실행하여 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_export.py::test_assign_pitcher_to_innings_simple -v`
Expected: FAIL with `ImportError`

- [x] **Step 7: 구현 추가**

`src/gameone_analyzer/export.py`에 추가:
```python
import math

FRACTION_MAP = {"⅓": 1 / 3, "⅔": 2 / 3}


def _parse_innings_pitched(text: str) -> float:
    text = text.strip()
    for symbol, value in FRACTION_MAP.items():
        if symbol in text:
            whole_part = text.replace(symbol, "").strip()
            whole = float(whole_part) if whole_part else 0.0
            return whole + value
    return float(text) if text else 0.0


def assign_pitcher_to_innings(pitcher_rows: list) -> dict:
    mapping = {}
    current_inning = 1
    sorted_rows = sorted(pitcher_rows, key=lambda r: r.order)
    for row in sorted_rows:
        ip = _parse_innings_pitched(row.innings_pitched_str)
        num_innings = max(1, math.ceil(ip - 1e-9)) if ip > 0 else 1
        for _ in range(num_innings):
            mapping[current_inning] = row.name
            current_inning += 1
    return mapping
```

- [x] **Step 8: 테스트 실행하여 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_export.py -v`
Expected: PASS

- [x] **Step 9: `export_pitcher_view_records` 추가 — 실패하는 테스트 작성**

`tests/test_export.py`에 추가:
```python
import sqlite3
from gameone_analyzer.export import export_pitcher_view_records


def test_export_pitcher_view_records(tmp_path):
    db_path = tmp_path / "t.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE games (
            game_idx INTEGER PRIMARY KEY, season INTEGER, league TEXT, venue TEXT,
            date_str TEXT, away_team TEXT, home_team TEXT, away_runs INTEGER,
            home_runs INTEGER, validated INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE plate_appearances (
            id INTEGER PRIMARY KEY, game_idx INTEGER, team TEXT, is_our_team INTEGER,
            inning INTEGER, batting_order INTEGER, player_name TEXT, outs_before INTEGER,
            runner_first INTEGER, runner_second INTEGER, runner_third INTEGER,
            is_risp INTEGER, cell_text TEXT
        )
    """)
    conn.execute(
        "INSERT INTO games VALUES (1, 2025, '일요 싱글', '살곶이야구장', 'd', 'OPP', "
        "'한양대학교 D-Dogs OB', 3, 5, 1)"
    )
    conn.execute(
        "INSERT INTO plate_appearances VALUES "
        "(1, 1, 'away', 0, 1, 1, 'OppBatter', 0, 0, 0, 0, 0, '좌안')"
    )
    conn.commit()

    pitcher_innings_by_game = {1: {1: "민호진"}}
    records = export_pitcher_view_records(conn, pitcher_innings_by_game)
    assert len(records) == 1
    assert records[0]["pitcher_name"] == "민호진"
    assert records[0]["player_name"] == "OppBatter"
    assert records[0]["result"] == "1B"
```

- [x] **Step 10: 테스트 실행하여 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_export.py::test_export_pitcher_view_records -v`
Expected: FAIL with `ImportError`

- [x] **Step 11: 구현 추가**

`src/gameone_analyzer/export.py`에 추가:
```python
def export_pitcher_view_records(conn: sqlite3.Connection, pitcher_innings_by_game: dict) -> list:
    conn.row_factory = sqlite3.Row
    query = (
        "SELECT pa.*, g.season, g.league, g.venue FROM plate_appearances pa "
        "JOIN games g ON pa.game_idx = g.game_idx "
        "WHERE pa.is_our_team = 0"
    )
    records = []
    for row in conn.execute(query).fetchall():
        game_map = pitcher_innings_by_game.get(row["game_idx"], {})
        pitcher_name = game_map.get(row["inning"], "UNKNOWN")
        events_codes = [e for e in row["cell_text"].split(",") if e.strip()]
        records.append({
            "game_idx": row["game_idx"],
            "season": row["season"],
            "league": row["league"],
            "venue": row["venue"],
            "pitcher_name": pitcher_name,
            "player_name": row["player_name"],
            "inning": row["inning"],
            "outs_before": row["outs_before"],
            "runner_state": runner_state_key(
                bool(row["runner_first"]), bool(row["runner_second"]), bool(row["runner_third"])
            ),
            "is_risp": bool(row["is_risp"]),
            "cell_text": row["cell_text"],
            "events": events_codes,
            "result": classify_result(events_codes),
        })
    return records
```

- [x] **Step 12: 테스트 실행하여 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_export.py tests/test_parser.py -v`
Expected: PASS (전체)

- [x] **Step 13: `scripts/build_site_data.py` 수정 — 투수 데이터도 함께 출력**

`scripts/build_site_data.py`를 다음으로 교체:
```python
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gameone_analyzer.export import (
    export_all_plate_appearances,
    export_pitcher_view_records,
    assign_pitcher_to_innings,
)
from gameone_analyzer.parser import parse_pitcher_rows
from gameone_analyzer.fetch import fetch_boxscore_html, load_game_ids_from_csv

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "gameone.db"
CACHE_DIR = ROOT / "data" / "raw"
BATTER_OUT_PATH = ROOT / "docs" / "data_batter.json"
PITCHER_OUT_PATH = ROOT / "docs" / "data_pitcher.json"

OUR_TEAM = "한양대학교 D-Dogs OB"


def _build_pitcher_innings_by_game(conn: sqlite3.Connection) -> dict:
    game_ids = [row[0] for row in conn.execute("SELECT game_idx FROM games").fetchall()]
    result = {}
    for game_idx in game_ids:
        html = fetch_boxscore_html(game_idx, CACHE_DIR, delay_sec=0)
        pitcher_rows = parse_pitcher_rows(html)
        home_team = conn.execute(
            "SELECT home_team FROM games WHERE game_idx = ?", (game_idx,)
        ).fetchone()[0]
        our_side = "home" if home_team == OUR_TEAM else "away"
        our_pitchers = [r for r in pitcher_rows if r.team == our_side]
        result[game_idx] = assign_pitcher_to_innings(our_pitchers)
    return result


def main():
    conn = sqlite3.connect(DB_PATH)

    batter_records = export_all_plate_appearances(conn)
    BATTER_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATTER_OUT_PATH.write_text(json.dumps(batter_records, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(batter_records)} batter records to {BATTER_OUT_PATH}")

    pitcher_innings_by_game = _build_pitcher_innings_by_game(conn)
    pitcher_records = export_pitcher_view_records(conn, pitcher_innings_by_game)
    PITCHER_OUT_PATH.write_text(json.dumps(pitcher_records, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(pitcher_records)} pitcher records to {PITCHER_OUT_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
```

(이전 `docs/data.json` 단일 출력 방식에서 `data_batter.json`/`data_pitcher.json` 2파일로 변경됨 —
Task 8에서 만든 파일명을 이 시점에 교체.)

- [x] **Step 14: 커밋 및 푸시**

```bash
git add src/gameone_analyzer/parser.py src/gameone_analyzer/export.py tests/test_parser.py tests/test_export.py scripts/build_site_data.py
git commit -m "feat: map opposing batter results to our pitchers by inning"
git push
```

---

### Task 10: 실제 데이터로 사이트 데이터 생성 + 검증

- [x] **Step 1: build_db.py가 아직 안 돌았다면 Task 6부터 먼저 완료 확인**

```bash
ls data/gameone.db || echo "Task 6을 먼저 완료해야 함"
```

- [x] **Step 2: 사이트 데이터 생성**

```bash
cd /Users/bae/project/workspace/gameone_analyzer
.venv/bin/python scripts/build_site_data.py
```

Expected: `docs/data_batter.json`, `docs/data_pitcher.json` 생성, 각각 레코드 수 출력.

- [x] **Step 3: 생성된 JSON 정합성 스팟체크**

```bash
.venv/bin/python -c "
import json
batter = json.load(open('docs/data_batter.json', encoding='utf-8'))
pitcher = json.load(open('docs/data_pitcher.json', encoding='utf-8'))
print('batter records:', len(batter))
print('pitcher records:', len(pitcher))
print('sample batter:', batter[0])
print('sample pitcher:', pitcher[0])
seasons = sorted(set(r['season'] for r in batter))
leagues = sorted(set(r['league'] for r in batter))
venues = sorted(set(r['venue'] for r in batter))
print('seasons:', seasons)
print('leagues:', leagues)
print('venues:', venues)
"
```

Expected: 에러 없이 출력, `seasons`에 2024/2025/2026이 모두 포함.

- [x] **Step 4: 커밋 및 푸시**

```bash
git add docs/data_batter.json docs/data_pitcher.json
git commit -m "data: generate site JSON from 95-game boxscore dataset"
git push
```

---

### Task 11: 프론트엔드 — 공용 필터 UI + 유틸

**Files:**
- Create: `docs/index.html`
- Create: `docs/css/style.css`
- Create: `docs/js/filters.js`
- Create: `docs/js/data-loader.js`

**Interfaces:**
- Produces (전역 함수, 모듈 없이 `<script>` 순서 로드 — GitHub Pages 정적 서빙 단순성 우선):
  - `filters.buildFilterState(formElement) -> object` — `{outs: number[], runnerStates: string[],
    rispOnly: boolean, seasons: number[], leagues: string[], venueGroups: string[][]}`
  - `filters.matchesFilter(record, filterState) -> boolean`
  - `dataLoader.loadJSON(path) -> Promise<Array>`

- [x] **Step 1: `docs/js/filters.js` 작성 (순수 함수, 테스트는 Node로 간단 실행)**

```javascript
function buildFilterState(formElement) {
  const outs = Array.from(formElement.querySelectorAll('input[name="outs"]:checked'))
    .map((el) => parseInt(el.value, 10));
  const runnerStates = Array.from(formElement.querySelectorAll('input[name="runnerState"]:checked'))
    .map((el) => el.value);
  const rispOnly = formElement.querySelector('input[name="rispOnly"]').checked;
  const seasons = Array.from(formElement.querySelectorAll('input[name="season"]:checked'))
    .map((el) => parseInt(el.value, 10));
  const leagues = Array.from(formElement.querySelectorAll('input[name="league"]:checked'))
    .map((el) => el.value);
  const venueGroupSelect = formElement.querySelector('select[name="venueGroup"]');
  const venueGroups = venueGroupSelect && venueGroupSelect.value
    ? [JSON.parse(venueGroupSelect.value)]
    : [];

  return { outs, runnerStates, rispOnly, seasons, leagues, venueGroups };
}

function normalizeVenue(venue) {
  return venue.replace(/\s+/g, "");
}

function matchesFilter(record, filterState) {
  if (filterState.outs.length > 0 && !filterState.outs.includes(record.outs_before)) {
    return false;
  }
  if (filterState.rispOnly && !record.is_risp) {
    return false;
  }
  if (filterState.runnerStates.length > 0 && !filterState.runnerStates.includes(record.runner_state)) {
    return false;
  }
  if (filterState.seasons.length > 0 && !filterState.seasons.includes(record.season)) {
    return false;
  }
  if (filterState.leagues.length > 0 && !filterState.leagues.includes(record.league)) {
    return false;
  }
  if (filterState.venueGroups.length > 0) {
    const normalized = normalizeVenue(record.venue);
    const anyGroupMatches = filterState.venueGroups.some((group) =>
      group.map(normalizeVenue).includes(normalized)
    );
    if (!anyGroupMatches) {
      return false;
    }
  }
  return true;
}

if (typeof module !== "undefined") {
  module.exports = { buildFilterState, matchesFilter, normalizeVenue };
}
```

- [x] **Step 2: Node로 간단 테스트 작성 및 실행 (jsdom 없이, DOM 목업으로)**

`tests/js/test_filters.mjs`:
```javascript
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

// venue group with whitespace normalization
assert.strictEqual(
  matchesFilter(baseRecord, { outs: [], runnerStates: [], rispOnly: false, seasons: [], leagues: [], venueGroups: [["살곶이야구장"]] }),
  true
);

assert.strictEqual(normalizeVenue("구의 야구장"), "구의야구장");

console.log("all filter tests passed");
```

`docs/js/filters.js`를 ESM에서 import 가능하게 하려면 `module.exports` 대신 `export`를 사용해야
Node ESM 테스트가 동작한다 — Step 1의 마지막 3줄을 다음으로 교체:
```javascript
export { buildFilterState, matchesFilter, normalizeVenue };
```
(브라우저에서는 `<script type="module" src="js/filters.js"></script>`로 로드하므로 `export`문이
문제없이 동작함 — Step 1 코드 수정 후 저장.)

- [x] **Step 3: 테스트 실행하여 통과 확인**

Run: `cd /Users/bae/project/workspace/gameone_analyzer && node tests/js/test_filters.mjs`
Expected: `all filter tests passed` 출력, 에러 없음.

- [x] **Step 4: `docs/js/data-loader.js` 작성**

```javascript
async function loadJSON(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

export { loadJSON };
```

- [x] **Step 5: 커밋 및 푸시**

```bash
mkdir -p tests/js
git add docs/js/filters.js docs/js/data-loader.js tests/js/test_filters.mjs
git commit -m "feat: add client-side filter matching utilities"
git push
```

---

### Task 12: 타자 관점 페이지

**Files:**
- Create: `docs/batter.html`
- Create: `docs/js/batter-page.js`
- Modify: `docs/css/style.css`
- Modify: `docs/index.html` (네비게이션 링크)

**Interfaces:**
- Consumes: `filters.buildFilterState`, `filters.matchesFilter` (Task 11), `docs/data_batter.json` (Task 10)
- Produces: 브라우저에서 동작하는 `batter-page.js`의 `computeBatterStats(records) -> object`
  — `{ AB, H, BB, HBP, SO, "2B", "3B", HR, AVG, OBP }` 형태의 팀 전체 집계, 그리고
  `groupByPlayer(records) -> Map<string, object>` — 선수별 동일 스탯.

- [x] **Step 1: `docs/js/batter-page.js`에 순수 집계 함수 작성 + Node 테스트**

`tests/js/test_batter_page.mjs`:
```javascript
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
assert.strictEqual(teamStats.AB, 3); // BB는 타수 제외, 1B/SO/OUT/HR 만 AB에 포함

const byPlayer = groupByPlayer(records);
assert.strictEqual(byPlayer.get("A").H, 1);
assert.strictEqual(byPlayer.get("B").H, 1);
assert.strictEqual(byPlayer.get("B").HR, 1);

console.log("all batter page tests passed");
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `node tests/js/test_batter_page.mjs`
Expected: 에러(`Cannot find module`)

- [x] **Step 3: `docs/js/batter-page.js` 구현**

```javascript
const HIT_RESULTS = new Set(["1B", "2B", "3B", "HR"]);
const AB_EXCLUDED_RESULTS = new Set(["BB", "HBP", "SF", "SAC", "OTHER"]);

function emptyStats() {
  return { AB: 0, H: 0, BB: 0, HBP: 0, SO: 0, "2B": 0, "3B": 0, HR: 0, PA: 0 };
}

function accumulate(stats, result) {
  stats.PA += 1;
  if (!AB_EXCLUDED_RESULTS.has(result)) {
    stats.AB += 1;
  }
  if (HIT_RESULTS.has(result)) {
    stats.H += 1;
  }
  if (result === "2B") stats["2B"] += 1;
  if (result === "3B") stats["3B"] += 1;
  if (result === "HR") stats.HR += 1;
  if (result === "BB") stats.BB += 1;
  if (result === "HBP") stats.HBP += 1;
  if (result === "SO") stats.SO += 1;
}

function finalize(stats) {
  stats.AVG = stats.AB > 0 ? (stats.H / stats.AB) : 0;
  const obpDenominator = stats.AB + stats.BB + stats.HBP;
  stats.OBP = obpDenominator > 0 ? ((stats.H + stats.BB + stats.HBP) / obpDenominator) : 0;
  return stats;
}

function computeBatterStats(records) {
  const stats = emptyStats();
  for (const record of records) {
    accumulate(stats, record.result);
  }
  return finalize(stats);
}

function groupByPlayer(records) {
  const map = new Map();
  for (const record of records) {
    if (!map.has(record.player_name)) {
      map.set(record.player_name, emptyStats());
    }
    accumulate(map.get(record.player_name), record.result);
  }
  for (const stats of map.values()) {
    finalize(stats);
  }
  return map;
}

export { computeBatterStats, groupByPlayer };
```

- [x] **Step 4: 테스트 실행하여 통과 확인**

Run: `node tests/js/test_batter_page.mjs`
Expected: `all batter page tests passed`

- [x] **Step 5: `docs/batter.html` 작성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>타자 분석 - D-Dogs OB</title>
  <link rel="stylesheet" href="css/style.css" />
</head>
<body>
  <nav>
    <a href="index.html">홈</a>
    <a href="batter.html" class="active">타자 분석</a>
    <a href="pitcher.html">투수 분석</a>
  </nav>
  <h1>타자 분석 (한양대학교 D-Dogs OB)</h1>

  <form id="filterForm">
    <fieldset>
      <legend>아웃카운트</legend>
      <label><input type="checkbox" name="outs" value="0" /> 무사</label>
      <label><input type="checkbox" name="outs" value="1" /> 1사</label>
      <label><input type="checkbox" name="outs" value="2" /> 2사</label>
    </fieldset>

    <fieldset>
      <legend>주자상황</legend>
      <label><input type="checkbox" name="runnerState" value="empty" /> 주자없음</label>
      <label><input type="checkbox" name="runnerState" value="1" /> 1루</label>
      <label><input type="checkbox" name="runnerState" value="2" /> 2루</label>
      <label><input type="checkbox" name="runnerState" value="3" /> 3루</label>
      <label><input type="checkbox" name="runnerState" value="12" /> 1·2루</label>
      <label><input type="checkbox" name="runnerState" value="13" /> 1·3루</label>
      <label><input type="checkbox" name="runnerState" value="23" /> 2·3루</label>
      <label><input type="checkbox" name="runnerState" value="123" /> 만루</label>
      <label><input type="checkbox" name="rispOnly" /> 득점권만</label>
    </fieldset>

    <fieldset>
      <legend>시즌</legend>
      <label><input type="checkbox" name="season" value="2024" /> 2024</label>
      <label><input type="checkbox" name="season" value="2025" /> 2025</label>
      <label><input type="checkbox" name="season" value="2026" /> 2026</label>
    </fieldset>

    <fieldset>
      <legend>리그</legend>
      <div id="leagueCheckboxes"></div>
    </fieldset>

    <fieldset>
      <legend>구장 그룹</legend>
      <select name="venueGroup" id="venueGroupSelect">
        <option value="">전체</option>
      </select>
    </fieldset>

    <button type="submit">필터 적용</button>
  </form>

  <h2>팀 전체 스탯</h2>
  <div id="teamStats"></div>

  <h2>선수별 스탯</h2>
  <table id="playerStatsTable">
    <thead>
      <tr><th>선수</th><th>PA</th><th>AB</th><th>H</th><th>2B</th><th>3B</th><th>HR</th><th>BB</th><th>HBP</th><th>SO</th><th>AVG</th><th>OBP</th></tr>
    </thead>
    <tbody></tbody>
  </table>

  <script type="module" src="js/filters.js"></script>
  <script type="module" src="js/data-loader.js"></script>
  <script type="module" src="js/batter-page.js"></script>
  <script type="module">
    import { buildFilterState, matchesFilter } from "./js/filters.js";
    import { loadJSON } from "./js/data-loader.js";
    import { computeBatterStats, groupByPlayer } from "./js/batter-page.js";

    let allRecords = [];

    function renderTeamStats(stats) {
      const el = document.getElementById("teamStats");
      el.innerHTML = `
        <p>PA: ${stats.PA} / AB: ${stats.AB} / H: ${stats.H} / 2B: ${stats["2B"]} / 3B: ${stats["3B"]} / HR: ${stats.HR}</p>
        <p>BB: ${stats.BB} / HBP: ${stats.HBP} / SO: ${stats.SO}</p>
        <p>AVG: ${stats.AVG.toFixed(3)} / OBP: ${stats.OBP.toFixed(3)}</p>
      `;
    }

    function renderPlayerTable(byPlayer) {
      const tbody = document.querySelector("#playerStatsTable tbody");
      tbody.innerHTML = "";
      for (const [name, stats] of byPlayer.entries()) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${name}</td><td>${stats.PA}</td><td>${stats.AB}</td><td>${stats.H}</td>
          <td>${stats["2B"]}</td><td>${stats["3B"]}</td><td>${stats.HR}</td>
          <td>${stats.BB}</td><td>${stats.HBP}</td><td>${stats.SO}</td>
          <td>${stats.AVG.toFixed(3)}</td><td>${stats.OBP.toFixed(3)}</td>
        `;
        tbody.appendChild(tr);
      }
    }

    function populateLeagueCheckboxes(records) {
      const leagues = Array.from(new Set(records.map((r) => r.league))).sort();
      const container = document.getElementById("leagueCheckboxes");
      container.innerHTML = leagues
        .map((l) => `<label><input type="checkbox" name="league" value="${l}" /> ${l}</label>`)
        .join("");
    }

    function populateVenueGroups(records) {
      const venues = Array.from(new Set(records.map((r) => r.venue.replace(/\s+/g, "")))).sort();
      const select = document.getElementById("venueGroupSelect");
      for (const v of venues) {
        const option = document.createElement("option");
        option.value = JSON.stringify([v]);
        option.textContent = v;
        select.appendChild(option);
      }
    }

    function applyFilterAndRender() {
      const form = document.getElementById("filterForm");
      const filterState = buildFilterState(form);
      const filtered = allRecords.filter((r) => matchesFilter(r, filterState));
      renderTeamStats(computeBatterStats(filtered));
      renderPlayerTable(groupByPlayer(filtered));
    }

    async function init() {
      allRecords = await loadJSON("data_batter.json");
      populateLeagueCheckboxes(allRecords);
      populateVenueGroups(allRecords);
      applyFilterAndRender();

      document.getElementById("filterForm").addEventListener("submit", (e) => {
        e.preventDefault();
        applyFilterAndRender();
      });
    }

    init();
  </script>
</body>
</html>
```

- [x] **Step 6: 로컬 정적 서버로 육안 확인**

```bash
cd /Users/bae/project/workspace/gameone_analyzer/docs
python3 -m http.server 8000
```

브라우저로 `http://localhost:8000/batter.html` 접속 확인 — 팀 스탯과 선수별 테이블이 렌더링되는지,
필터 체크박스를 조합했을 때 숫자가 바뀌는지 확인. (Playwright MCP 도구가 있으면 스크린샷으로 검증
가능 — `mcp__playwright__browser_navigate` 및 `browser_take_screenshot` 사용.)

- [x] **Step 7: 커밋 및 푸시**

```bash
git add docs/batter.html docs/js/batter-page.js tests/js/test_batter_page.mjs
git commit -m "feat: add batter analysis page with excel-style filters"
git push
```

---

### Task 13: 투수 관점 페이지

**Files:**
- Create: `docs/pitcher.html`
- Create: `docs/js/pitcher-page.js`

**Interfaces:**
- Consumes: `filters.buildFilterState`, `filters.matchesFilter`, `docs/data_pitcher.json`
- Produces: `computePitcherStats(records) -> { BF, H, "2B", "3B", HR, BB, HBP, SO, AVG_AGAINST }`,
  `groupByPitcher(records) -> Map<string, object>`

- [x] **Step 1: `tests/js/test_pitcher_page.mjs` 작성**

```javascript
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

const byPitcher = groupByPitcher(records);
assert.strictEqual(byPitcher.get("민호진").H, 1);
assert.strictEqual(byPitcher.get("박준호").H, 1);

console.log("all pitcher page tests passed");
```

- [x] **Step 2: 테스트 실행하여 실패 확인**

Run: `node tests/js/test_pitcher_page.mjs`
Expected: 에러(모듈 없음)

- [x] **Step 3: `docs/js/pitcher-page.js` 구현**

```javascript
const HIT_RESULTS = new Set(["1B", "2B", "3B", "HR"]);
const AB_EXCLUDED_RESULTS = new Set(["BB", "HBP", "SF", "SAC", "OTHER"]);

function emptyStats() {
  return { BF: 0, AB_AGAINST: 0, H: 0, BB: 0, HBP: 0, SO: 0, "2B": 0, "3B": 0, HR: 0 };
}

function accumulate(stats, result) {
  stats.BF += 1;
  if (!AB_EXCLUDED_RESULTS.has(result)) {
    stats.AB_AGAINST += 1;
  }
  if (HIT_RESULTS.has(result)) stats.H += 1;
  if (result === "2B") stats["2B"] += 1;
  if (result === "3B") stats["3B"] += 1;
  if (result === "HR") stats.HR += 1;
  if (result === "BB") stats.BB += 1;
  if (result === "HBP") stats.HBP += 1;
  if (result === "SO") stats.SO += 1;
}

function finalize(stats) {
  stats.AVG_AGAINST = stats.AB_AGAINST > 0 ? (stats.H / stats.AB_AGAINST) : 0;
  return stats;
}

function computePitcherStats(records) {
  const stats = emptyStats();
  for (const record of records) {
    accumulate(stats, record.result);
  }
  return finalize(stats);
}

function groupByPitcher(records) {
  const map = new Map();
  for (const record of records) {
    if (!map.has(record.pitcher_name)) {
      map.set(record.pitcher_name, emptyStats());
    }
    accumulate(map.get(record.pitcher_name), record.result);
  }
  for (const stats of map.values()) {
    finalize(stats);
  }
  return map;
}

export { computePitcherStats, groupByPitcher };
```

- [x] **Step 4: 테스트 실행하여 통과 확인**

Run: `node tests/js/test_pitcher_page.mjs`
Expected: `all pitcher page tests passed`

- [x] **Step 5: `docs/pitcher.html` 작성 (batter.html과 동일 구조, 데이터소스/집계함수만 교체)**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>투수 분석 - D-Dogs OB</title>
  <link rel="stylesheet" href="css/style.css" />
</head>
<body>
  <nav>
    <a href="index.html">홈</a>
    <a href="batter.html">타자 분석</a>
    <a href="pitcher.html" class="active">투수 분석</a>
  </nav>
  <h1>투수 분석 (한양대학교 D-Dogs OB)</h1>

  <form id="filterForm">
    <fieldset>
      <legend>아웃카운트</legend>
      <label><input type="checkbox" name="outs" value="0" /> 무사</label>
      <label><input type="checkbox" name="outs" value="1" /> 1사</label>
      <label><input type="checkbox" name="outs" value="2" /> 2사</label>
    </fieldset>

    <fieldset>
      <legend>주자상황</legend>
      <label><input type="checkbox" name="runnerState" value="empty" /> 주자없음</label>
      <label><input type="checkbox" name="runnerState" value="1" /> 1루</label>
      <label><input type="checkbox" name="runnerState" value="2" /> 2루</label>
      <label><input type="checkbox" name="runnerState" value="3" /> 3루</label>
      <label><input type="checkbox" name="runnerState" value="12" /> 1·2루</label>
      <label><input type="checkbox" name="runnerState" value="13" /> 1·3루</label>
      <label><input type="checkbox" name="runnerState" value="23" /> 2·3루</label>
      <label><input type="checkbox" name="runnerState" value="123" /> 만루</label>
      <label><input type="checkbox" name="rispOnly" /> 득점권만</label>
    </fieldset>

    <fieldset>
      <legend>시즌</legend>
      <label><input type="checkbox" name="season" value="2024" /> 2024</label>
      <label><input type="checkbox" name="season" value="2025" /> 2025</label>
      <label><input type="checkbox" name="season" value="2026" /> 2026</label>
    </fieldset>

    <fieldset>
      <legend>리그</legend>
      <div id="leagueCheckboxes"></div>
    </fieldset>

    <fieldset>
      <legend>구장 그룹</legend>
      <select name="venueGroup" id="venueGroupSelect">
        <option value="">전체</option>
      </select>
    </fieldset>

    <button type="submit">필터 적용</button>
  </form>

  <h2>팀 전체 피안타 스탯</h2>
  <div id="teamStats"></div>

  <h2>투수별 스탯</h2>
  <table id="pitcherStatsTable">
    <thead>
      <tr><th>투수</th><th>BF</th><th>H</th><th>2B</th><th>3B</th><th>HR</th><th>BB</th><th>HBP</th><th>SO</th><th>피안타율</th></tr>
    </thead>
    <tbody></tbody>
  </table>

  <script type="module">
    import { buildFilterState, matchesFilter } from "./js/filters.js";
    import { loadJSON } from "./js/data-loader.js";
    import { computePitcherStats, groupByPitcher } from "./js/pitcher-page.js";

    let allRecords = [];

    function renderTeamStats(stats) {
      const el = document.getElementById("teamStats");
      el.innerHTML = `
        <p>BF: ${stats.BF} / H: ${stats.H} / 2B: ${stats["2B"]} / 3B: ${stats["3B"]} / HR: ${stats.HR}</p>
        <p>BB: ${stats.BB} / HBP: ${stats.HBP} / SO: ${stats.SO}</p>
        <p>피안타율: ${stats.AVG_AGAINST.toFixed(3)}</p>
      `;
    }

    function renderPitcherTable(byPitcher) {
      const tbody = document.querySelector("#pitcherStatsTable tbody");
      tbody.innerHTML = "";
      for (const [name, stats] of byPitcher.entries()) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${name}</td><td>${stats.BF}</td><td>${stats.H}</td>
          <td>${stats["2B"]}</td><td>${stats["3B"]}</td><td>${stats.HR}</td>
          <td>${stats.BB}</td><td>${stats.HBP}</td><td>${stats.SO}</td>
          <td>${stats.AVG_AGAINST.toFixed(3)}</td>
        `;
        tbody.appendChild(tr);
      }
    }

    function populateLeagueCheckboxes(records) {
      const leagues = Array.from(new Set(records.map((r) => r.league))).sort();
      const container = document.getElementById("leagueCheckboxes");
      container.innerHTML = leagues
        .map((l) => `<label><input type="checkbox" name="league" value="${l}" /> ${l}</label>`)
        .join("");
    }

    function populateVenueGroups(records) {
      const venues = Array.from(new Set(records.map((r) => r.venue.replace(/\s+/g, "")))).sort();
      const select = document.getElementById("venueGroupSelect");
      for (const v of venues) {
        const option = document.createElement("option");
        option.value = JSON.stringify([v]);
        option.textContent = v;
        select.appendChild(option);
      }
    }

    function applyFilterAndRender() {
      const form = document.getElementById("filterForm");
      const filterState = buildFilterState(form);
      const filtered = allRecords.filter((r) => matchesFilter(r, filterState));
      renderTeamStats(computePitcherStats(filtered));
      renderPitcherTable(groupByPitcher(filtered));
    }

    async function init() {
      allRecords = await loadJSON("data_pitcher.json");
      populateLeagueCheckboxes(allRecords);
      populateVenueGroups(allRecords);
      applyFilterAndRender();

      document.getElementById("filterForm").addEventListener("submit", (e) => {
        e.preventDefault();
        applyFilterAndRender();
      });
    }

    init();
  </script>
</body>
</html>
```

- [x] **Step 6: 로컬 서버로 육안 확인**

```bash
cd /Users/bae/project/workspace/gameone_analyzer/docs
python3 -m http.server 8000
```

`http://localhost:8000/pitcher.html` 접속, 필터 적용 시 투수별 테이블이 갱신되는지 확인.

- [x] **Step 7: 커밋 및 푸시**

```bash
git add docs/pitcher.html docs/js/pitcher-page.js tests/js/test_pitcher_page.mjs
git commit -m "feat: add pitcher analysis page with excel-style filters"
git push
```

---

### Task 14: 홈페이지 + 전체 스타일 + GitHub Pages 활성화

**Files:**
- Create: `docs/index.html`
- Create: `docs/css/style.css`

- [x] **Step 1: `docs/index.html` 작성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>D-Dogs OB 경기 분석</title>
  <link rel="stylesheet" href="css/style.css" />
</head>
<body>
  <nav>
    <a href="index.html" class="active">홈</a>
    <a href="batter.html">타자 분석</a>
    <a href="pitcher.html">투수 분석</a>
  </nav>
  <h1>한양대학교 D-Dogs OB 경기 분석</h1>
  <p>gameone.kr 박스스코어 2024~2026시즌 95경기를 상황별(아웃카운트·주자상황·구장·시즌·리그)로
     필터링해 타자/투수 스탯을 조회하는 개인 분석 도구입니다.</p>
  <ul>
    <li><a href="batter.html">타자 분석 페이지</a> — 아웃카운트/주자상황/구장/시즌/리그 조건별 타율·안타·타점 등</li>
    <li><a href="pitcher.html">투수 분석 페이지</a> — 동일 조건으로 피안타율·자책점 등</li>
  </ul>
</body>
</html>
```

- [x] **Step 2: `docs/css/style.css` 작성**

```css
body {
  font-family: -apple-system, "Malgun Gothic", sans-serif;
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem;
  color: #222;
}

nav a {
  margin-right: 1rem;
  text-decoration: none;
  color: #555;
}

nav a.active {
  font-weight: bold;
  color: #111;
}

fieldset {
  margin-bottom: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

fieldset label {
  display: inline-block;
  margin-right: 0.75rem;
  margin-bottom: 0.25rem;
}

table {
  border-collapse: collapse;
  width: 100%;
  margin-top: 1rem;
}

th, td {
  border: 1px solid #ddd;
  padding: 0.4rem 0.6rem;
  text-align: center;
  font-size: 0.9rem;
}

thead th {
  background: #f5f5f5;
}

button[type="submit"] {
  padding: 0.5rem 1rem;
  cursor: pointer;
}
```

- [x] **Step 3: GitHub Pages 활성화 (docs/ 폴더 기준, main 브랜치)**

먼저 기본 브랜치를 `main`으로 정리한다(현재 `master`) — GitHub 저장소 기본 관례에 맞춤:

```bash
cd /Users/bae/project/workspace/gameone_analyzer
git branch -m master main
git push -u origin main
gh repo edit bjh5098/gameone-analyzer --default-branch main
git push origin --delete master
```

그다음 Pages 설정:

```bash
gh api -X POST repos/bjh5098/gameone-analyzer/pages -f "source[branch]=main" -f "source[path]=/docs" 2>&1 || \
gh api -X PUT repos/bjh5098/gameone-analyzer/pages -f "source[branch]=main" -f "source[path]=/docs"
```

(POST는 Pages가 아직 없을 때, PUT은 이미 있을 때 — 둘 다 실패하면 `gh repo view --web`으로 열어
Settings → Pages에서 수동 설정하고 사용자에게 알린다.)

- [x] **Step 4: 배포 확인**

```bash
sleep 30
curl -s -o /dev/null -w "%{http_code}\n" https://bjh5098.github.io/gameone-analyzer/
```

Expected: `200`. 404면 1~2분 더 대기 후 재확인(GitHub Pages 최초 배포는 수 분 걸릴 수 있음).

- [x] **Step 5: 커밋 및 푸시**

```bash
git add docs/index.html docs/css/style.css
git commit -m "feat: add homepage and shared styling, enable GitHub Pages"
git push
```

---

### Task 15: README 갱신 + 최종 점검

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [x] **Step 1: README에 실행 방법과 사이트 링크, 알려진 한계 추가**

`README.md`에 다음 섹션 추가(기존 내용 유지하고 하단에 추가):

```markdown
## 실행 방법

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_all.py       # 원문 HTML 캐싱 (최초 1회, 요청당 3초 지연)
.venv/bin/python scripts/build_db.py        # SQLite DB 빌드 + 스코어보드 검증
.venv/bin/python scripts/build_site_data.py # 정적 JSON 생성 (docs/data_batter.json 등)
```

## 배포된 사이트

https://bjh5098.github.io/gameone-analyzer/

## 알려진 한계

- 투수 등판 이닝은 투수기록 테이블의 누적 이닝 표기(예: `2 ⅓`)를 순서대로 정수 이닝에 배정한 근사치이며,
  이닝 중간 교체 시점의 타석 단위 정교화는 하지 않음.
  - 콤마로 묶인 여러 이벤트가 "타자 본인 후속 진루"인지 "다른 주자 동시 이벤트"인지 완전히 판별하지
  못하는 케이스가 있어 단순화된 규칙으로 근사함(CLAUDE.md 참고). 스코어보드 대조 검증에서 불일치가
  발견된 경기는 `scripts/build_db.py` 실행 로그에 `game_idx`별로 출력됨.
- 점수차 필터는 아직 구현하지 않음(요구사항 미확정).
```

- [x] **Step 2: CLAUDE.md의 "다음 세션에서 할 일" 섹션을 완료 상태로 갱신**

`CLAUDE.md`의 해당 섹션을 열어 완료된 항목에 체크 표시하고, 남은 작업(점수차 필터 등)만 남긴다.

- [x] **Step 3: 전체 테스트 재실행 (Python + JS)**

```bash
cd /Users/bae/project/workspace/gameone_analyzer
.venv/bin/python -m pytest tests/ -v --ignore=tests/js
for f in tests/js/*.mjs; do node "$f"; done
```

Expected: 모든 테스트 통과.

- [x] **Step 4: 최종 커밋 및 푸시**

```bash
git add README.md CLAUDE.md
git commit -m "docs: update README with usage, deployment link, and known limitations"
git push
```

---

## 작업 순서 요약

1. Task 1~5: 파서/시뮬레이터/검증기 코드 작성 (TDD, 실제 데이터 없이도 진행 가능)
2. Task 6: 실제 95경기 수집 + DB 빌드 (사용자에게 실행 전 고지)
3. Task 7~9: 필터 쿼리 레이어 + 정적 데이터 export (타자/투수 양쪽)
4. Task 10: 실제 데이터로 JSON 생성
5. Task 11~14: 프론트엔드 (필터 UI, 타자 페이지, 투수 페이지, 홈페이지) + GitHub Pages 활성화
6. Task 15: 문서 정리 및 최종 점검

각 Task 완료 시 이 문서의 체크박스를 갱신하고 커밋 메시지에 Task 번호를 남긴다. 세션이 중간에
끊겨도 이 문서와 git 커밋 이력만 보면 어디까지 진행됐는지 파악 가능하다.

## 전체 완료 (2026-08-11) — 실제 구현 중 계획과 달라진 부분

모든 Task(1~17) 완료, https://bjh5098.github.io/gameone-analyzer/ 배포 완료. 계획 작성 시점의
가정과 실제 95경기 데이터로 검증하며 드러난 차이점을 기록해둔다(향후 코드 참고 시 이 섹션이
계획 본문보다 최신):

- **팀 순서**: 사전 조사(1경기 샘플)에서는 "원정팀 먼저, 홈팀 나중"으로 가정했으나, `<h3>` 팀
  헤딩과 실제 로스터로 재검증한 결과 `record_table`(타자/투수 둘 다) 순서가 **away, home** 순서로
  일관됨을 재확인 완료 — 계획대로였고 별도 수정 불필요.
- **이벤트 분리자 `/` vs `,`**: CLAUDE.md/계획 문서에는 명시되지 않았던 발견 — `,`는 한 타석 내
  이벤트 시퀀스 구분자이고, `/`는 **같은 이닝에서 타순이 한 바퀴 돌아 동일 타순이 재차 타석에
  선 별도 타석**을 구분하는 기호. 대량 득점 이닝에서만 나타남. `events.split_plate_appearances()`로
  처리.
- **볼넷/에러 등 force-advance 규칙**: 초기 구현은 안타처럼 모든 주자를 일괄 +1루 시켰으나, 실제
  야구 규칙대로 1루부터 강제 연쇄로만 진루하도록 수정(`simulator._force_advance`).
  `낫아웃+`(포일 낫아웃)는 아웃이 아니라 타자 진루 이벤트임을 발견, `STRIKEOUT_REACHED`로 분리.
- **도루/주자아웃 등 체인 이벤트의 대상 러너**: "우안/4구,주자아웃"류 콤마·슬래시 혼합 체인에서
  95경기 320+ 케이스를 관측한 결과, 타자가 방금 진루한 이벤트 바로 뒤에 오는 도루/폭투/도루자/
  주자아웃/견제사/런다운은 거의 항상 **그 타자 본인**을 대상으로 함(가장 진출한 주자가 아님).
  이 발견 전에는 "가장 진출한 주자" 휴리스틱을 썼는데 다수 이닝에서 오류를 유발했음. 최종적으로
  `apply_events()`가 "직전 이벤트로 새로 생긴 활성 러너"를 추적해 그 다음 이벤트를 적용하고,
  직전 이벤트가 아웃으로 끝났을 때만 "가장 진출한 주자" 휴리스틱으로 폴백.
- **스코어보드 검증 결과**: 위 수정들 이후 우리팀(D-Dogs OB) 관점 이닝별 득점 총합 오차가
  전체 득점의 24.1% 수준(18/95경기는 완전 일치). 야수 에러/야수선택 뒤 정확한 진루 베이스 수는
  이벤트 코드만으로 완전히 결정 불가능한 케이스가 남아있어 CLAUDE.md에 known limitation으로
  기록(추가 조사보다 커버리지 우선, 개인 분석 도구 특성상 100% 정합보다 실용성 우선).
- **투수 뷰 범위**: 사용자 요청으로 상대팀 투수는 분석하지 않고 우리팀(D-Dogs OB) 투수만 다룸 —
  `export.export_pitcher_view_records()`가 `is_our_team=0`인 상대 타자 PA에 우리팀 투수만 매핑.
- **추가 요구사항(세션 중 반영)**: OPS/피OPS, 삼진율(K%) 컬럼과 최소 PA/BF 입력 필터를 타자·투수
  페이지 양쪽에 추가(허수 데이터 방지 목적, 이기준 요청).
