"""Run any implemented Diplomacy agent."""


import argparse
import asyncio
import time
from typing import Type

from diplomacy import connect
from diplomacy.client.network_game import NetworkGame

from chiron_utils.bots import BaselineBot, RandomProposerAdvisor, RandomProposerPlayer
from chiron_utils.game_utils import DEFAULT_HOST, DEFAULT_PORT
from chiron_utils.utils import POWER_NAMES_DICT, return_logger

logger = return_logger(__name__)

POWERS = sorted(POWER_NAMES_DICT.values())
BOTS = [
    RandomProposerAdvisor,
    RandomProposerPlayer,
]
NAMES_TO_BOTS = {bot.__name__: bot for bot in BOTS}


async def play(
    hostname: str,
    port: int,
    game_id: str,
    power_name: str,
    bot_class: Type[BaselineBot],
    *,
    use_ssl: bool,
) -> None:
    """Launches the bot for game play.

    Args:
        hostname: Host name of game server.
        port: Port of game server.
        game_id: ID of game to join.
        power_name: Name of power bot will play as or advise.
        bot_class: Type of bot to launch.
        use_ssl: Whether to use SSL to connect to the game server.
    """
    # Connect to the game
    logger.info("%s joining game %r as %s", bot_class.__name__, (game_id), power_name)
    connection = await connect(hostname, port, use_ssl=use_ssl)
    channel = await connection.authenticate(
        f"allan_{bot_class.__name__.lower()}_{power_name}"
        if bot_class.bot_type == "player"
        else "admin",
        "password",
    )
    game: NetworkGame = await channel.join_game(
        game_id=game_id,
        power_name=power_name if bot_class.bot_type == "player" else None,
        player_type=bot_class.player_type if bot_class.bot_type == "player" else None,
    )

    bot = bot_class(power_name, game)

    # Wait while game is still being formed
    logger.info("Waiting for game to start")
    while game.is_game_forming:
        await asyncio.sleep(2)
        logger.info("Still waiting")

    game_start_time = time.perf_counter()

    # Playing game
    logger.info("Started playing")
    while not game.is_game_done:
        current_phase = game.get_current_phase()

        phase_start_time = time.time()
        logger.info("Starting phase: %s", current_phase)

        # Do not take a turn if no moves can be made
        # Attempting to take a turn when not needed can cause state
        # to desync between the bot and the server, causing the former to crash
        if game.get_orderable_locations(bot.power_name):
            # Fetch orders from bot
            orders_data = await bot()

            # Always send orders so engine knows turn is over
            await bot.send_orders(orders_data)

        phase_end_time = time.time()
        logger.info(
            "Time taken for phase %s: %0.4fs", current_phase, phase_end_time - phase_start_time
        )

        while current_phase == game.get_current_phase():
            await asyncio.sleep(2)

    game_end_time = time.perf_counter()
    logger.info("Time taken for game: %0.4f", game_end_time - game_start_time)
    logger.info("-" * 30 + "GAME COMPLETE" + "-" * 30)  # noqa: G003


def main() -> None:
    """Run Diplomacy agent."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help="Host name of game server. (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port of game server. (default: %(default)s)",
    )
    parser.add_argument(
        "--use-ssl",
        action="store_true",
        help="Whether to use SSL to connect to the game server. (default: %(default)s)",
    )
    parser.add_argument(
        "--game_id",
        type=str,
        required=True,
        help="ID of game to join.",
    )
    parser.add_argument(
        "--power",
        choices=POWERS,
        required=True,
        help="Name of power bot will play as or advise.",
    )
    parser.add_argument(
        "--bot_type",
        type=str,
        choices=list(NAMES_TO_BOTS),
        default=RandomProposerPlayer.__name__,
        help="Type of bot to launch. (default: %(default)s)",
    )

    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
    use_ssl: bool = args.use_ssl
    game_id: str = args.game_id
    power: str = args.power
    bot_type: str = args.bot_type

    bot_class: Type[BaselineBot] = NAMES_TO_BOTS[bot_type]

    asyncio.run(
        play(
            hostname=host,
            port=port,
            game_id=game_id,
            power_name=power,
            bot_class=bot_class,
            use_ssl=use_ssl,
        )
    )


if __name__ == "__main__":
    main()
