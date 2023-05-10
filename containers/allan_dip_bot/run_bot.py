"""ALLAN-DIP: Team ALLAN's Diplomacy Agent"""


import argparse
import asyncio
import random
import sys
import time
from typing import Optional

sys.path.append("..")  # Adds higher directory to python modules path.


from diplomacy import connect
from diplomacy.client.network_game import NetworkGame
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


async def launch(
    hostname: str,
    port: int,
    game_id: str,
    power_name: str,
    bot_type: str,
    sleep_delay: bool,
    discount_factor: float,
    invasion_coef: float,
    conflict_coef: float,
    invasive_support_coef: float,
    conflict_support_coef: float,
    friendly_coef: float,
    unrealized_coef: float,
    aggressiveness: Optional[Aggressiveness] = Aggressiveness.moderate,
) -> None:
    """
    Waits for dipnet model to load and then starts the bot execution

    :param hostname: name of host on which games are hosted
    :param port: port to which the bot should connect on the host
    :param game_id: game id to connect to on host
    :param power_name: power name of the bot to be launched
    :param bot_type: the type of bot to be launched - NoPressDipBot/TransparentBot/SmartOrderAccepterBot/..
    :param sleep_delay: bool to indicate if bot should sleep randomly for 1-3s before execution
    """

    print("Waiting for TensorFlow server to come online", end=" ")
    serving_flag = False
    while not serving_flag:
        serving_flag = is_port_opened(9501)
        print("", end=".")
        await asyncio.sleep(1)
    print()
    print("TensorFlow server online")

    await play(
        hostname,
        port,
        game_id,
        power_name,
        bot_type,
        sleep_delay,
        discount_factor,
        invasion_coef,
        conflict_coef,
        invasive_support_coef,
        conflict_support_coef,
        friendly_coef,
        unrealized_coef,
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
    invasion_coef: float,
    conflict_coef: float,
    invasive_support_coef: float,
    conflict_support_coef: float,
    friendly_coef: float,
    unrealized_coef: float,
    aggressiveness: Optional[Aggressiveness] = Aggressiveness.moderate,
) -> None:
    """
    Launches the bot for game play

    :param hostname: name of host on which games are hosted
    :param port: port to which the bot should connect on the host
    :param game_id: game id to connect to on host
    :param power_name: power name of the bot to be launched
    :param bot_type: the type of bot to be launched - NoPressDipBot/TransparentBot/SmartOrderAccepterBot/..
    :param sleep_delay: bool to indicate if bot should sleep randomly for 1-3s before execution
    """
    # Connect to the game
    print(f"DipNetSL joining game: {game_id} as {power_name}")
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
            power_name,
            game,
            discount_factor,
            aggressiveness=aggressiveness,
            invasion_coef=invasion_coef,
            conflict_coef=conflict_coef,
            invasive_support_coef=invasive_support_coef,
            conflict_support_coef=conflict_support_coef,
            friendly_coef=friendly_coef,
            unrealized_coef=unrealized_coef,
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
        if sleep_delay and not isinstance(bot, SmartOrderAccepterBot):
            # sleep randomly for 2-5s before retrieving new messages for the power
            # SOA bot handles sleeping itself, so it's skipped here
            await asyncio.sleep(random.uniform(2, 5))

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

            if len(messages_data.messages):
                print(f"Messages sent: {len(messages_data.messages)}")

            # If orders are present, send them
            if orders_data is not None:
                await game.set_orders(
                    power_name=power_name, orders=orders_data, wait=False
                )

            print(f"Phase: {current_phase}")
            print(f"Orders: {orders_data}")

        phase_end_time = time.time()
        print(
            f"Time taken for phase {current_phase}: {phase_end_time - phase_start_time:0.4}s"
        )

        while current_phase == game.get_current_phase():
            await asyncio.sleep(2)

    t2 = time.perf_counter()
    print(f"TIMING: {t2-t1:0.4}")
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
        "--invasion_coef",
        type=float,
        default=1.0,
        help="Stance on nation k -= α1 * count(k’s hostile moves) (default: %(default)s)",
    )
    parser.add_argument(
        "--conflict_coef",
        type=float,
        default=0.5,
        help="Stance on nation k -= α2 * count(k’s conflict moves) (default: %(default)s)",
    )
    parser.add_argument(
        "--invasive_support_coef",
        type=float,
        default=1.0,
        help="Stance on nation k -=β1 * k’s count(hostile supports/convoys) (default: %(default)s)",
    )
    parser.add_argument(
        "--conflict_support_coef",
        type=float,
        default=0.5,
        help="Stance on nation k -= β2 * count(k’s conflict supports/convoys) (default: %(default)s)",
    )
    parser.add_argument(
        "--friendly_coef",
        type=float,
        default=1.0,
        help="Stance on nation k += γ1 * count(k’s friendly supports/convoys) (default: %(default)s)",
    )
    parser.add_argument(
        "--unrealized_coef",
        type=float,
        default=1.0,
        help="Stance on nation k += γ2 * count(k’s unrealized hostile moves) (default: %(default)s)",
    )
    parser.add_argument(
        "--aggressiveness",
        type=str,
        choices=[str(a.value) for a in Aggressiveness],
        help="aggressiveness of the bot, overrides individual coefficients (default: %(default)s)",
    )
    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
    game_id: str = args.game_id
    power: str = args.power
    bot_type: str = args.bot_type
    sleep_delay: bool = args.no_sleep_delay
    discount_factor: float = args.discount_factor
    invasion_coef: float = args.invasion_coef
    conflict_coef: float = args.conflict_coef
    invasive_support_coef: float = args.invasive_support_coef
    conflict_support_coef: float = args.conflict_support_coef
    friendly_coef: float = args.friendly_coef
    unrealized_coef: float = args.unrealized_coef
    aggressiveness: Optional[Aggressiveness] = (
        Aggressiveness(args.aggressiveness) if args.aggressiveness else None
    )

    asyncio.run(
        launch(
            hostname=host,
            port=port,
            game_id=game_id,
            power_name=power,
            bot_type=bot_type,
            sleep_delay=sleep_delay,
            discount_factor=discount_factor,
            invasion_coef=invasion_coef,
            conflict_coef=conflict_coef,
            invasive_support_coef=invasive_support_coef,
            conflict_support_coef=conflict_support_coef,
            friendly_coef=friendly_coef,
            unrealized_coef=unrealized_coef,
            aggressiveness=aggressiveness,
        )
    )


if __name__ == "__main__":
    main()
