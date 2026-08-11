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
