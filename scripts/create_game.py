# SPDX-FileCopyrightText: 2022, Texas Advanced Computing Center
# SPDX-License-Identifier: BSD-3-Clause
"""Create Diplomacy games programmatically."""
# Based on https://github.com/SHADE-AI/diplomacy-playground/blob/989ec7be748257324a22132e632ac4927b8cb6c2/scripts/create_game.py
import argparse
import asyncio
import json
from typing import Optional, Sequence

from diplomacy.client.connection import connect

DEFAULT_RULES = ("REAL_TIME", "POWER_CHOICE")
DEFAULT_USER = "allanumd"
DEFAULT_PASSWORD = "password"


async def create_game(
    game_id: str,
    rules: Sequence[str] = DEFAULT_RULES,
    deadline: int = 0,
    n_controls: int = 7,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
    game_password: Optional[str] = None,
    hostname: str = "localhost",
    port: int = 8432,
) -> None:
    """Creates a game on the Diplomacy server"""
    connection = await connect(hostname, port)
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
    print(json.dumps(game_data, ensure_ascii=False, indent=4))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game_id", type=str, required=True, help="Game ID.")
    parser.add_argument("--rules", nargs="+", default=DEFAULT_RULES, help="Game rules.")
    parser.add_argument(
        "--deadline", type=int, default=0, help="Turn deadline in seconds."
    )
    parser.add_argument(
        "--n_controls",
        type=int,
        default=7,
        help="Number of controlled powers (default: %(default)s)",
    )
    parser.add_argument("--user", type=str, default=DEFAULT_USER, help="SHADE user.")
    parser.add_argument(
        "--password", type=str, default=DEFAULT_PASSWORD, help="SHADE password."
    )
    parser.add_argument("--game-password", type=str, help="Game password.")
    parser.add_argument(
        "--host", type=str, default="localhost", help="Server hostname."
    )
    parser.add_argument("--port", type=int, default=8432, help="Server port.")
    args = parser.parse_args()

    if args.deadline < 0:
        raise ValueError("--deadline cannot be negative")
    if args.n_controls < 0:
        raise ValueError("--n_controls cannot be negative")
    if args.n_controls > 7:
        raise ValueError("--n_controls cannot be greater than 7")

    asyncio.run(
        create_game(
            game_id=args.game_id,
            rules=args.rules,
            deadline=args.deadline,
            n_controls=args.n_controls,
            user=args.user,
            password=args.password,
            game_password=args.game_password,
            hostname=args.host,
            port=args.port,
        )
    )


if __name__ == "__main__":
    main()
