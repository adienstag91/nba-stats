import datetime

from modules.utils import get_season_year, normalize_player_name


def test_get_season_year_october_maps_to_next_year():
    dt = datetime.date(2023, 10, 15)
    assert get_season_year(dt) == 2024


def test_normalize_player_name_removes_suffix_and_accents():
    name = "Luka Don\u010di\u0107 Jr."
    assert normalize_player_name(name) == "luka doncic"
