"""ALLAN-DIP: Team ALLAN's Diplomacy Agent"""


import argparse
import asyncio
import random
import time
from typing import Type

from diplomacy import connect
from diplomacy.client.network_game import NetworkGame
import socket

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot


POWERS = ["AUSTRIA", "ENGLAND", "FRANCE", "GERMANY", "ITALY", "RUSSIA", "TURKEY"]
BOTS = [
    RandomProposerBot,
]
NAMES_TO_BOTS = {bot.__name__: bot for bot in BOTS}


def is_port_opened(port, hostname='127.0.0.1'):
    """ Checks if the specified port is opened
        :param port: The port to check
        :param hostname: The hostname to check, defaults to '127.0.0.1'
    """
    # Copied from https://github.com/SHADE-AI/research/blob/27edb5b98abb4e0af8e551d88ece28cd8ced5e1e/diplomacy_research/utils/cluster.py#L228-L237
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((hostname, port))
    if result == 0:
        return True
    return False


async def launch() -> None:
    """
    Waits for dipnet model to load
    """

    print("Waiting for TensorFlow server to come online", end=" ")
    serving_flag = False
    while not serving_flag:
        serving_flag = is_port_opened(9501)
        print("", end=".")
        await asyncio.sleep(1)
    print()
    print("TensorFlow server online")


async def play(
    hostname: str,
    port: int,
    game_id: str,
    power_name: str,
    bot_class: Type[BaselineBot],
    sleep_delay: bool,
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
    await launch()

    # Connect to the game
    print(f"DipNetSL joining game: {game_id} as {power_name}")
    connection = await connect(hostname, port)
    channel = await connection.authenticate(
        f"allan_{bot_class.__name__.lower()}_{power_name}", "password"
    )
    game: NetworkGame = await channel.join_game(
        game_id=game_id, power_name=power_name, player_type=bot_class.player_type
    )

    if bot_class in [
        RandomProposerBot,
    ]:
        bot: BaselineBot = bot_class(power_name, game)
    else:
        raise ValueError(f"{bot_class.__name__!r} is not a valid bot type")

    # Wait while game is still being formed
    print("Waiting for game to start", end=" ")
    while game.is_game_forming:
        await asyncio.sleep(2)
        print("", end=".")
    print()

    t1 = time.perf_counter()

    # Playing game
    print("Started playing")
    while not game.is_game_done:
        current_phase = game.get_current_phase()
        if sleep_delay:
            # sleep randomly for 2-5s before retrieving new messages for the power
            # SOA bot handles sleeping itself, so it's skipped here
            await asyncio.sleep(random.uniform(2, 5))

        phase_start_time = time.time()
        print(f"Starting phase: {current_phase}")

        if not game.powers[bot.power_name].is_eliminated():
            # Fetch orders from bot
            orders_data = await bot()

            # Always send orders so engine knows turn is over
            await bot.send_orders(orders_data)

        phase_end_time = time.time()
        print(
            f"Time taken for phase {current_phase}: {phase_end_time - phase_start_time:0.4}s"
        )

        while current_phase == game.get_current_phase():
            await asyncio.sleep(2)

    t2 = time.perf_counter()
    print(f"Time taken for game: {t2-t1:0.4}")
    print("-" * 30 + "GAME COMPLETE" + "-" * 30)


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
    parser.add_argument(
        "--no_sleep_delay",
        action="store_false",
        help="disable bot sleeping randomly for 1-3s before execution",
    )

    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
    game_id: str = args.game_id
    power: str = args.power
    bot_type: str = args.bot_type
    sleep_delay: bool = args.no_sleep_delay

    bot_class: Type[BaselineBot] = NAMES_TO_BOTS[bot_type]

    asyncio.run(
        play(
            hostname=host,
            port=port,
            game_id=game_id,
            power_name=power,
            bot_class=bot_class,
            sleep_delay=sleep_delay,
        )
    )


if __name__ == "__main__":
    main()
