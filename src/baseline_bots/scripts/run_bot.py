"""ALLAN-DIP: Team ALLAN's Diplomacy Agent"""


import argparse
import asyncio
import time
from typing import Type

from diplomacy import connect
from diplomacy.client.network_game import NetworkGame

from baseline_bots.bots import BaselineBot, RandomProposerBot
from baseline_bots.utils import POWER_NAMES_DICT, return_logger

logger = return_logger(__name__)

POWERS = sorted(POWER_NAMES_DICT.values())
BOTS = [
    RandomProposerBot,
]
NAMES_TO_BOTS = {bot.__name__: bot for bot in BOTS}


async def play(
    hostname: str,
    port: int,
    game_id: str,
    power_name: str,
    bot_class: Type[BaselineBot],
) -> None:
    """
    Launches the bot for game play

    :param hostname: name of host on which games are hosted
    :param port: port to which the bot should connect on the host
    :param game_id: game id to connect to on host
    :param power_name: power name of the bot to be launched
    :param bot_class: the type of bot to be launched - NoPressDipBot/TransparentBot/SmartOrderAccepterBot/..
    :param sleep_delay: bool to indicate if bot should sleep randomly for 1-3s before execution
    """

    # Connect to the game
    logger.info("%s joining game %r as %s", bot_class.__name__, (game_id), power_name)
    connection = await connect(hostname, port)
    channel = await connection.authenticate(
        f"allan_{bot_class.__name__.lower()}_{power_name}", "password"
    )
    game: NetworkGame = await channel.join_game(
        game_id=game_id, power_name=power_name, player_type=bot_class.player_type
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
    logger.info("-" * 30 + "GAME COMPLETE" + "-" * 30)  # noqa: G003  # pylint: disable=logging-not-lazy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="host IP address (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8432,
        help="port to connect to the game (default: %(default)s)",
    )
    parser.add_argument(
        "--game_id",
        type=str,
        required=True,
        help="game id of game created in DATC diplomacy game",
    )
    parser.add_argument(
        "--power",
        choices=POWERS,
        required=True,
        help="power name",
    )
    parser.add_argument(
        "--bot_type",
        type=str,
        choices=list(NAMES_TO_BOTS),
        default=RandomProposerBot.__name__,
        help="type of bot to be launched (default: %(default)s)",
    )

    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
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
        )
    )


if __name__ == "__main__":
    main()
