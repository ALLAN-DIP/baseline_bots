import argparse
from time import time

from random_loyal_supportproposal import RandomLSPBot
from random_no_press import RandomNoPressBot
from diplomacy import Message
from diplomacy import Game
from diplomacy.utils.export import to_saved_game_format

def parse_args():
    parser = argparse.ArgumentParser(description='Analysis-Dip')
    parser.add_argument('--powers', '-p', type=str, help='comma-seperated country names (AUSTRIA, ENGLAND, FRANCE, GERMANY, ITALY, RUSSIA, TURKEY)')
    parser.add_argument('--filename', '-f', type=str,
                        help='json filename')

    args = parser.parse_args()
    print(args)
    return args

if __name__ == "__main__":
    args = parse_args()
    from random_allier_proposer_bot import RandomAllierProposerBot

    # game instance
    game = Game()
    # powers = list(game.get_map_power_names())
    powers = ['ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'AUSTRIA', 'RUSSIA', 'TURKEY']

    lsp_bot_powers = args.powers.split(",")
    bots = [RandomNoPressBot(bot_power, game) if bot_power not in lsp_bot_powers else RandomLSPBot(bot_power, game)
            for bot_power in powers]
    start = time()
    cnt = 0
    while not game.is_game_done:
        for bot in bots:
            bot_state = bot.act()
            messages, orders = bot_state.messages, bot_state.orders
            if messages:
                # print(power_name, messages)
                for msg in messages:
                    msg_obj = Message(
                        sender=bot.power_name,
                        recipient=msg['recipient'],
                        message=msg['message'],
                        phase=game.get_current_phase(),
                    )
                    game.add_message(message=msg_obj)
            # print("Submitted orders")
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)
        game.process()
        if cnt <= 5:
            bots = bots[::-1]
            cnt += 1
    print(time() - start)
    to_saved_game_format(game, output_path=args.filename)