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


def load_game_ids_from_csv(csv_path: Path) -> list:
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [int(row["game_idx"]) for row in reader]
