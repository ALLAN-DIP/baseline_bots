import argparse
from time import time

from bots.baseline_bot import BaselineMsgRoundBot
from bots.random_loyal_support_proposal import RandomLSPBot
from bots.random_no_press import RandomNoPressBot
from diplomacy import Game, Message
from diplomacy.utils.export import to_saved_game_format


def parse_args():
    parser = argparse.ArgumentParser(description="Analysis-Dip")
    parser.add_argument(
        "--powers",
        "-p",
        type=str,
        default="AUSTRIA,ITALY,ENGLAND,FRANCE,GERMANY,RUSSIA,TURKEY",
        help="comma-seperated country names (AUSTRIA,ITALY,ENGLAND,FRANCE,GERMANY,RUSSIA,TURKEY)",
    )
    parser.add_argument(
        "--filename",
        "-f",
        type=str,
        default="RandomLSPBotGame.json",
        help="json filename",
    )
    parser.add_argument(
        "--types",
        "-t",
        type=str,
        default="lspm,lsp,np,np,np,np,np",
        help="comma-seperated bottypes (lspm,lsp,np,np,np,np,np)",
    )

    args = parser.parse_args()
    print(args)
    return args


if __name__ == "__main__":
    args = parse_args()
    comms_rounds = 3

    # game instance
    game = Game()
    # powers = list(game.get_map_power_names())
    # powers = ['ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'AUSTRIA', 'RUSSIA', 'TURKEY']

    assert len(args.powers.split(",")) == 7, "Powers specified are not 7"

    alliance_all_in = sum(typ.startswith("lsp") for typ in args.types.split(",")) == 7
    if alliance_all_in:
        print("Alliances are all in")

    config = {"comms_rounds": comms_rounds, "alliance_all_in": alliance_all_in}

    bots = []

    for bot_power, bot_type in zip(args.powers.split(","), args.types.split(",")):
        if bot_type == "np":
            bot = RandomNoPressBot(bot_power, game)
        elif bot_type.startswith("lsp"):
            bot = RandomLSPBot(bot_power, game, 3, alliance_all_in)
            if bot_type.endswith("m"):
                bot.set_leader()
        # bot.config(config)
        bots.append(bot)

    start = time()

    while not game.is_game_done:
        for bot in bots:
            if not game.powers[bot.power_name].is_eliminated():
                if isinstance(bot, BaselineMsgRoundBot):
                    bot.phase_init()

        if game.get_current_phase()[-1] == "M":
            # Iterate through multiple rounds of comms during movement phases
            for _ in range(comms_rounds):
                round_msgs = game.messages
                to_send_msgs = {}
                for bot in bots:
                    if not game.powers[bot.power_name].is_eliminated():
                        # Retrieve messages
                        rcvd_messages = game.filter_messages(
                            messages=round_msgs, game_role=bot.power_name
                        )
                        rcvd_messages = list(rcvd_messages.items())
                        rcvd_messages.sort()

                        # Send messages to bots and fetch messages from bot
                        bot_messages = bot.gen_messages(rcvd_messages)

                        # If messages are to be sent, send them
                        if bot_messages and bot_messages.messages:
                            to_send_msgs[bot.power_name] = bot_messages.messages

                # Send all messages after all bots decide on comms
                for sender in to_send_msgs:
                    for msg in to_send_msgs[sender]:
                        msg_obj = Message(
                            sender=sender,
                            recipient=msg["recipient"],
                            message=msg["message"],
                            phase=game.get_current_phase(),
                        )
                        game.add_message(message=msg_obj)

        for bot in bots:
            if not game.powers[bot.power_name].is_eliminated():
                # Orders round
                orders = bot.gen_orders()
                # messages, orders = bot_state.messages, bot_state.orders

                if orders is not None:
                    game.set_orders(power_name=bot.power_name, orders=orders)

        game.process()

    print(time() - start)
    to_saved_game_format(game, output_path=args.filename)
