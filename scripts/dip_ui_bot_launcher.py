import asyncio
import random

from baseline_bots.bots.dipnet.loyal_support_proposal import LSP_DipBot
from baseline_bots.bots.dipnet.no_press_bot import NoPressDipBot
from diplomacy.client.connection import connect
from diplomacy.utils import exceptions
from diplomacy import Message
import argparse


def is_in_instance_list(obj, instance_list):
    boo_v = False
    for instance in instance_list:
        boo_v = isinstance(obj, instance)
        if boo_v:
            break
    return boo_v


POWERS = ["AUSTRIA", "ENGLAND", "FRANCE", "GERMANY", "ITALY", "RUSSIA", "TURKEY"]


async def play(game_id, botname, power_name, hostname="localhost", port=8432):
    """Play as the specified power"""
    connection = await connect(hostname, port)
    channel = await connection.authenticate("user_" + power_name, "password")

    # Waiting for the game, then joining it
    while not (await channel.list_games(game_id=game_id)):
        await asyncio.sleep(1.0)
    game = await channel.join_game(game_id=game_id, power_name=power_name)
    bot = None
    alliance_all_in = False
    if botname == "np":
        bot = NoPressDipBot(power_name, game, dipnet_type="rlp")
    elif botname.startswith("lsp"):
        bot = LSP_DipBot(power_name, game, 3, alliance_all_in)
        if botname.endswith("m"):
            bot.set_leader()
    elif botname.startswith("rlsp"):
        bot = LSP_DipBot(power_name, game, 3, alliance_all_in, dipnet_type="rlp")
        if botname.endswith("m"):
            bot.set_leader()

    # Wait while game is still being formed
    while game.is_game_forming:
        await asyncio.sleep(0.5)

    # Playing game
    print("Started playing")
    while not game.is_game_done:
        current_phase = game.get_current_phase()
        dip_instance_list = [
            NoPressDipBot,
            LSP_DipBot,
        ]  # TransparentBot, SelectivelyTransparentBot, TransparentProposerDipBot, ProposerDipBot, RealPolitik]
        if is_in_instance_list(bot, dip_instance_list):
            bot.phase_init()
        if game.get_current_phase()[-1] == "M":
            # Iterate through multiple rounds of comms during movement phases
            for _ in range(3):
                round_msgs = game.messages
                to_send_msgs = {}

                if not game.powers[bot.power_name].is_eliminated():
                    # Retrieve messages
                    rcvd_messages = game.filter_messages(
                        messages=round_msgs, game_role=bot.power_name
                    )
                    rcvd_messages = list(rcvd_messages.items())
                    rcvd_messages.sort()

                    # Send messages to bots and fetch messages from bot
                    bot_messages = await bot.gen_messages(rcvd_messages)

                    # If messages are to be sent, send them
                    if bot_messages and bot_messages.messages:
                        to_send_msgs[bot.power_name] = bot_messages.messages

                # Send all messages
                for sender in to_send_msgs:
                    for msg in to_send_msgs[sender]:
                        msg_obj = Message(
                            sender=sender,
                            recipient=msg["recipient"],
                            message=msg["message"],
                            phase=game.get_current_phase(),
                        )
                        await game.send_game_message(message=msg_obj)
                if len(to_send_msgs):
                    print(f"Messages sent: {len(to_send_msgs)}")
                await asyncio.sleep(1)

        if not game.powers[bot.power_name].is_eliminated():
            # Orders round
            orders = await bot.gen_orders()
            # messages, orders = bot_state.messages, bot_state.orders

            if orders is not None:
                await game.set_orders(power_name=power_name, orders=orders, wait=False)

        # Waiting for game to be processed
        print(current_phase)
        while current_phase == game.get_current_phase():
            await asyncio.sleep(0.1)

    # A local copy of the game can be saved with to_saved_game_format
    # To download a copy of the game with messages from all powers, you need to export the game as an admin
    # by logging in as 'admin' / 'password'


async def launch(game_id, hostname, botname, powers=None):
    """Creates and plays a network game"""
    # await create_game(game_id, hostname)
    if powers is None:
        await asyncio.gather(
            *[play(game_id, botname, power_name, hostname) for power_name in POWERS]
        )
    else:
        await asyncio.gather(
            *[
                play(game_id, botname, power_name, hostname)
                for power_name in powers.split(",")
            ]
        )


def parse_args():
    parser = argparse.ArgumentParser(description="RAND-DIP: Random Diplomacy Agent")
    parser.add_argument(
        "--gameid",
        "-g",
        type=str,
        help="game id of game created in DATC diplomacy game",
    )
    parser.add_argument(
        "--powers",
        "-p",
        type=str,
        help="comma-seperated country names (AUSTRIA, ENGLAND, FRANCE, GERMANY, ITALY, RUSSIA, TURKEY)",
    )
    parser.add_argument(
        "--hostname",
        "-H",
        type=str,
        default="localhost",
        help="host IP address (defaults to localhost)",
    )
    parser.add_argument(
        "--bots", "-B", type=str, default="random", help="botname for all powers"
    )

    args = parser.parse_args()
    print(args)
    return args


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(launch(args.gameid, args.hostname, args.bots, args.powers))
