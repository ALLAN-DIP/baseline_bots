# SPDX-FileCopyrightText: 2022, Texas Advanced Computing Center
# SPDX-License-Identifier: BSD-3-Clause
"""Downloads Diplomacy games programmatically."""
# Based on https://github.com/SHADE-AI/diplomacy-playground/blob/989ec7be748257324a22132e632ac4927b8cb6c2/scripts/create_game.py
import argparse
import asyncio
import json
from pathlib import Path
from typing import Optional

from diplomacy.client.connection import connect
from diplomacy.client.network_game import NetworkGame
from diplomacy.utils.export import to_saved_game_format

DEFAULT_USER = "allanumd"
DEFAULT_PASSWORD = "password"


async def download_game(
    game_id: str,
    output_file: Path,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
    game_password: Optional[str] = None,
    hostname: str = "localhost",
    port: int = 8432,
) -> None:
    """Downloads a game from the Diplomacy server"""
    connection = await connect(hostname, port)
    channel = await connection.authenticate(user, password)
    game: NetworkGame = await channel.join_game(
        game_id=game_id, power_name=None, registration_password=game_password
    )

    with open(output_file, mode="w") as file:
        json.dump(to_saved_game_format(game), file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"Wrote game log to file {str(output_file)!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game_id", type=str, required=True, help="Game ID.")
    parser.add_argument("--output_file", type=Path, help="Output file path.")
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

    if args.output_file is None:
        repository_dir = Path(__file__).resolve().parent.parent
        output_file = repository_dir / "data" / f"{args.game_id}_log.json"
    else:
        output_file = args.output_file
    if not output_file.parent.is_dir():
        output_file.parent.mkdir(parents=True, exist_ok=True)

    asyncio.run(
        download_game(
            game_id=args.game_id,
            output_file=output_file,
            user=args.user,
            password=args.password,
            game_password=args.game_password,
            hostname=args.host,
            port=args.port,
        )
    )


if __name__ == "__main__":
    main()
