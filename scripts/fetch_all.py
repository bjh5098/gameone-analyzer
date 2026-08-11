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
