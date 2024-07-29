# SPDX-FileCopyrightText: 2022, Texas Advanced Computing Center
# SPDX-License-Identifier: BSD-3-Clause
"""Create Diplomacy games programmatically."""
# Based on https://github.com/SHADE-AI/diplomacy-playground/blob/989ec7be748257324a22132e632ac4927b8cb6c2/scripts/create_game.py
import argparse
import asyncio
import json

from chiron_utils.game_utils import (
    DEFAULT_DEADLINE,
    DEFAULT_HOST,
    DEFAULT_NUM_PLAYERS,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_RULES,
    DEFAULT_USER,
    create_game,
)


def main() -> None:
    """Create Diplomacy game."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game_id", type=str, required=True, help="Game ID.")
    parser.add_argument("--rules", nargs="+", default=DEFAULT_RULES, help="Game rules.")
    parser.add_argument(
        "--deadline",
        type=int,
        default=DEFAULT_DEADLINE,
        help="Turn deadline in seconds.",
    )
    parser.add_argument(
        "--n_controls",
        type=int,
        default=DEFAULT_NUM_PLAYERS,
        help="Number of controlled powers (default: %(default)s)",
    )
    parser.add_argument("--user", type=str, default=DEFAULT_USER, help="SHADE user.")
    parser.add_argument("--password", type=str, default=DEFAULT_PASSWORD, help="SHADE password.")
    parser.add_argument("--game-password", type=str, help="Game password.")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Server hostname.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port.")
    args = parser.parse_args()

    if args.deadline < 0:
        raise ValueError("--deadline cannot be negative")
    if args.n_controls < 0:
        raise ValueError("--n_controls cannot be negative")
    if args.n_controls > 7:
        raise ValueError("--n_controls cannot be greater than 7")

    game_data = asyncio.run(
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
    print(json.dumps(game_data, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
