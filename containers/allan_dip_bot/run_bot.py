"""ALLAN-DIP: Team ALLAN's Diplomacy Agent"""

__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

import argparse
import asyncio
import json as json
import random
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.append("..")  # Adds higher directory to python modules path.


from diplomacy import connect
from diplomacy.client.network_game import NetworkGame
from diplomacy.utils.export import to_saved_game_format
from diplomacy_research.utils.cluster import is_port_opened

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.bots.dipnet.no_press_bot import NoPressDipBot
from baseline_bots.bots.dipnet.transparent_bot import TransparentBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot_AsyncBot
from baseline_bots.bots.smart_order_accepter_bot import (
    Aggressiveness,
    SmartOrderAccepterBot,
)

POWERS = ["AUSTRIA", "ENGLAND", "FRANCE", "GERMANY", "ITALY", "RUSSIA", "TURKEY"]
BOTS = [
    NoPressDipBot.__name__,
    RandomProposerBot_AsyncBot.__name__,
    SmartOrderAccepterBot.__name__,
    TransparentBot.__name__,
]


async def test(hostname: str = "localhost", port: int = 8432) -> None:
    """
    Tests the game connection

    :param hostname: name of host on which games are hosted
    :param port: port to which the bot should connect on the host
    """
    connection = await connect(hostname, port)
    channel = await connection.authenticate("random_user", "password")
    games = await channel.list_games()
    for game in games:
        game_info = {
            "game_id": game.game_id,
            "phase": game.phase,
            "timestamp": game.timestamp,
            "timestamp_created": game.timestamp_created,
            "map_name": game.map_name,
            "observer_level": game.observer_level,
            "controlled_powers": game.controlled_powers,
            "rules": game.rules,
            "status": game.status,
            "n_players": game.n_players,
            "n_controls": game.n_controls,
            "deadline": game.deadline,
            "registration_password": game.registration_password,
        }
        print(game_info)
    print(games)


async def launch(
    hostname: str,
    port: int,
    game_id: str,
    power_name: str,
    bot_type: str,
    sleep_delay: bool,
    discount_factor: float,
    outdir: Optional[Path],
    aggressiveness: Aggressiveness = Aggressiveness.moderate,
) -> None:
    """
    Waits for dipnet model to load and then starts the bot execution

    :param hostname: name of host on which games are hosted
    :param port: port to which the bot should connect on the host
    :param game_id: game id to connect to on host
    :param power_name: power name of the bot to be launched
    :param bot_type: the type of bot to be launched - NoPressDipBot/TransparentBot/SmartOrderAccepterBot/..
    :param sleep_delay: bool to indicate if bot should sleep randomly for 1-3s before execution
    :param outdir: the output directory where game json files should be stored
    """

    print("Waiting for tensorflow server to come online", end=" ")
    serving_flag = False
    while not serving_flag:
        serving_flag = is_port_opened(9501)
        print("", end=".")
        await asyncio.sleep(1)
    print()
    print("Tensorflow server online")

    await play(
        hostname,
        port,
        game_id,
        power_name,
        bot_type,
        sleep_delay,
        discount_factor,
        outdir,
        aggressiveness,
    )


async def play(
    hostname: str,
    port: int,
    game_id: str,
    power_name: str,
    bot_type: str,
    sleep_delay: bool,
    discount_factor: float,
    outdir: Optional[Path],
    aggressiveness: Aggressiveness = Aggressiveness.moderate,
) -> None:
    """
    Launches the bot for game play

    :param hostname: name of host on which games are hosted
    :param port: port to which the bot should connect on the host
    :param game_id: game id to connect to on host
    :param power_name: power name of the bot to be launched
    :param bot_type: the type of bot to be launched - NoPressDipBot/TransparentBot/SmartOrderAccepterBot/..
    :param sleep_delay: bool to indicate if bot should sleep randomly for 1-3s before execution
    :param outdir: the output directory where game json files should be stored
    """
    # Connect to the game
    print("DipNetSL joining game: " + game_id + " as " + power_name)
    connection = await connect(hostname, port)
    channel = await connection.authenticate(
        f"allan_{bot_type.lower()}_{power_name}", "password"
    )
    game: NetworkGame = await channel.join_game(game_id=game_id, power_name=power_name)

    if bot_type == NoPressDipBot.__name__:
        bot: BaselineBot = NoPressDipBot(power_name, game)
    elif bot_type == TransparentBot.__name__:
        bot = TransparentBot(power_name, game)
    elif bot_type == RandomProposerBot_AsyncBot.__name__:
        bot = RandomProposerBot_AsyncBot(power_name, game)
    elif bot_type == SmartOrderAccepterBot.__name__:
        bot = SmartOrderAccepterBot(
            power_name, game, discount_factor, aggressiveness=aggressiveness
        )
    else:
        raise ValueError(f"{bot_type!r} is not a valid bot type")

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
            # sleep randomly for 1-3s before retrieving new messages for the power
            await asyncio.sleep(random.random() * 90)

        phase_start_time = time.time()

        # Retrieve messages
        rcvd_messages = game.filter_messages(
            messages=game.messages, game_role=bot.power_name
        )
        rcvd_messages = sorted(rcvd_messages.items())

        if not game.powers[bot.power_name].is_eliminated():
            # Send messages to bots and fetch messages from bot
            # Fetch orders from bot
            ret_data = await bot(rcvd_messages)
            messages_data = ret_data["messages"]
            orders_data = ret_data["orders"]

            # # If messages are to be sent, send them
            # to_send_msgs = {}
            # if messages_data and messages_data.messages:
            #     to_send_msgs[bot.power_name] = messages_data.messages
            #
            # for sender in to_send_msgs:
            #     for msg in to_send_msgs[sender]:
            #         msg_obj = Message(
            #             sender=sender,
            #             recipient=msg["recipient"],
            #             message=msg["message"],
            #             phase=game.get_current_phase(),
            #         )
            #         await game.send_game_message(message=msg_obj)

            if len(messages_data.messages):
                print(f"Messages sent: {len(messages_data.messages)}")

            # If orders are present, send them
            if orders_data is not None:
                await game.set_orders(
                    power_name=power_name, orders=orders_data, wait=False
                )

            print("Phase: " + current_phase)
            print("Orders: ")
            print(orders_data)
        phase_end_time = time.time()
        print(
            f"Time taken for phase {current_phase}: {phase_end_time - phase_start_time}s"
        )

        while current_phase == game.get_current_phase():
            await asyncio.sleep(2)

        if outdir:
            with open(outdir / f"{power_name}_output.json", mode="w") as file:
                json.dump(
                    to_saved_game_format(game), file, ensure_ascii=False, indent=2
                )
                file.write("\n")

    t2 = time.perf_counter()
    print(f"TIMING: {t2-t1}:0.4")
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
        choices=BOTS,
        default=TransparentBot.__name__,
        help="type of bot to be launched (default: %(default)s)",
    )
    parser.add_argument(
        "--no_sleep_delay",
        action="store_false",
        help="disable bot sleeping randomly for 1-3s before execution",
    )
    parser.add_argument(
        "--discount_factor",
        type=float,
        default=0.5,
        help="discount factor for ActionBasedStance (default: %(default)s)",
    )
    parser.add_argument(
        "--outdir", type=Path, help="output directory for game json to be stored"
    )
    parser.add_argument(
        "--aggressiveness",
        type=str,
        choices=[str(a.value) for a in Aggressiveness],
        default=Aggressiveness.moderate.value,
        help="aggressiveness of the bot (default: %(default)s)",
    )
    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
    game_id: str = args.game_id
    power: str = args.power
    bot_type: str = args.bot_type
    sleep_delay: bool = args.no_sleep_delay
    discount_factor: float = args.discount_factor
    outdir: Optional[Path] = args.outdir
    aggressiveness: Aggressiveness = Aggressiveness(args.aggressiveness)

    if outdir is not None and not outdir.is_dir():
        outdir.mkdir(parents=True, exist_ok=True)

    asyncio.run(
        launch(
            hostname=host,
            port=port,
            game_id=game_id,
            power_name=power,
            bot_type=bot_type,
            sleep_delay=sleep_delay,
            discount_factor=discount_factor,
            outdir=outdir,
            aggressiveness=aggressiveness,
        )
    )


if __name__ == "__main__":
    main()
