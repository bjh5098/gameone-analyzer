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


@dataclass
class PitcherRow:
    team: str
    name: str
    uniform_no: str
    innings_pitched_str: str
    order: int


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
