# SPDX-FileCopyrightText: 2022, Texas Advanced Computing Center
# SPDX-License-Identifier: BSD-3-Clause
"""Control Diplomacy games programmatically."""
# Based on https://github.com/SHADE-AI/diplomacy-playground/blob/989ec7be748257324a22132e632ac4927b8cb6c2/scripts/create_game.py

from typing import Any, Optional, Sequence

from diplomacy.client.connection import connect
from diplomacy.client.network_game import NetworkGame
from diplomacy.utils.export import to_saved_game_format

DEFAULT_RULES = ("REAL_TIME", "POWER_CHOICE")
DEFAULT_DEADLINE = 0
DEFAULT_NUM_PLAYERS = 7
DEFAULT_USER = "allanumd"
DEFAULT_PASSWORD = "password"  # noqa: S105
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8433


async def create_game(
    game_id: str,
    rules: Sequence[str] = DEFAULT_RULES,
    deadline: int = DEFAULT_DEADLINE,
    n_controls: int = DEFAULT_NUM_PLAYERS,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
    game_password: Optional[str] = None,
    hostname: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    use_ssl: bool = True,
) -> Any:
    """Creates a game on the Diplomacy server."""
    connection = await connect(hostname, port, use_ssl=use_ssl)
    channel = await connection.authenticate(user, password)

    game = await channel.create_game(
        game_id=game_id,
        rules=rules,
        deadline=deadline,
        n_controls=n_controls,
        registration_password=game_password,
    )

    game_data = {
        "id": game.game_id,
        "deadline": game.deadline,
        "map_name": game.map_name,
        "registration_password": game.registration_password,
        "rules": game.rules,
        "n_controls": n_controls,
        "status": game.status,
        "daide_port": game.daide_port,
    }
    return game_data


async def download_game(
    game_id: str,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
    game_password: Optional[str] = None,
    hostname: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    use_ssl: bool = True,
) -> Any:
    """Downloads a game from the Diplomacy server."""
    connection = await connect(hostname, port, use_ssl=use_ssl)
    channel = await connection.authenticate(user, password)
    game: NetworkGame = await channel.join_game(
        game_id=game_id, power_name=None, registration_password=game_password
    )
    game_json = to_saved_game_format(game)
    return game_json
