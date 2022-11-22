import sys

sys.path.append("..")
sys.path.append("../dipnet_press")

import asyncio

from diplomacy import utils
from diplomacy.client.connection import connect
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop
from tornado import gen


@gen.coroutine
def save():
    """Play as the specified power"""
    game_id = "kshenoy-test32"
    hostname = "shade.tacc.utexas.edu"
    port = 8432
    output_path = "game_files/test_game_file.json"

    connection = yield connect(hostname, port)
    channel = yield connection.authenticate("admin", "password")

    # Waiting for the game, then joining it
    while not (yield channel.list_games(game_id=game_id)):
        yield asyncio.sleep(1.0)
    game = yield channel.join_game(game_id=game_id, power_name=None)
    utils.export.to_saved_game_format(game, output_path=output_path, output_mode="a")

    stop_io_loop()


start_io_loop(save)
