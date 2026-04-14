import json

import pytest

from dynamic_games.examples import build_centipede_game
from dynamic_games.io_json import GameFormatError, dump_game_to_dict, load_game_from_dict, load_game_from_file



def test_roundtrip_json_conversion():
    game = build_centipede_game(turns=3)
    restored = load_game_from_dict(dump_game_to_dict(game))
    assert restored.root == game.root
    assert restored.title == game.title
    assert set(restored.nodes) == set(game.nodes)


def test_load_game_from_file_supports_utf8_sig(tmp_path):
    game = build_centipede_game(turns=3)
    path = tmp_path / 'game.json'
    path.write_text(json.dumps(dump_game_to_dict(game), ensure_ascii=False), encoding='utf-8-sig')

    restored = load_game_from_file(path)

    assert restored.root == game.root
    assert restored.title == game.title


def test_load_game_from_file_reports_invalid_json(tmp_path):
    path = tmp_path / 'bad_game.json'
    path.write_text('{"title": 123', encoding='utf-8-sig')

    with pytest.raises(GameFormatError):
        load_game_from_file(path)
