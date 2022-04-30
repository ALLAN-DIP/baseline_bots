import asyncio
import random

from diplomacy.agents.baseline_bots.loyal_bot import LoyalBot
from diplomacy.agents.baseline_bots.pushover_bot import PushoverBot
from diplomacy.agents.baseline_bots.random_allier_proposer_bot import RandomAllierProposerBot
from diplomacy.agents.baseline_bots.random_honest_bot import RandomHonestBot
from diplomacy.agents.baseline_bots.random_honest_order_accepter_bot import RandomHonestAccepterBot
from diplomacy.agents.baseline_bots.random_proposer_bot import RandomProposerBot
from diplomacy.agents.baseline_bots.random_support_proposer_bot import RandomSupportProposerBot
from diplomacy.client.connection import connect
from diplomacy.utils import exceptions
from diplomacy import Message
import argparse

POWERS = ['AUSTRIA', 'ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'RUSSIA', 'TURKEY']
# POWERS = ['TURKEY']

# async def create_game(game_id, hostname='localhost', port=8432):
#     """ Creates a game on the server """
#     connection = await connect(hostname, port)
#     channel = await connection.authenticate('random_user', 'password')
#     # await channel.create_game(game_id=game_id, rules={'REAL_TIME', 'NO_DEADLINE', 'POWER_CHOICE'})
#     print(channel.list_games(game_id=game_id))
#     await channel.join_game(game_id=game_id)

async def play(game_id, botname, power_name, hostname='localhost', port=8432):
    """ Play as the specified power """
    connection = await connect(hostname, port)
    channel = await connection.authenticate('user_' + power_name, 'password')

    # Waiting for the game, then joining it
    while not (await channel.list_games(game_id=game_id)):
        await asyncio.sleep(1.)
    game = await channel.join_game(game_id=game_id, power_name=power_name)
    bot = None
    if botname == 'random_support_proposer':
        bot = RandomSupportProposerBot(power_name, game)
    elif botname == 'random_honest':
        bot = RandomHonestBot(power_name, game)
    elif botname == 'random_honest_order_acceptor':
        bot = RandomHonestAccepterBot(power_name, game)
    elif botname == 'random_proposer':
        bot = RandomProposerBot(power_name, game)
    elif botname == 'loyal':
        bot = LoyalBot(power_name, game)
    elif botname == 'pushover':
        bot = PushoverBot(power_name, game)
    elif botname == 'random_allier_proposer':
        bot = RandomAllierProposerBot(power_name, game)

# Playing game
    while not game.is_game_done:
        current_phase = game.get_current_phase()
        if botname == 'random':
            # Submitting orders
            if game.get_orderable_locations(power_name):
                possible_orders = game.get_all_possible_orders()
                orders = [random.choice(possible_orders[loc]) for loc in game.get_orderable_locations(power_name)
                          if possible_orders[loc]]
                print('[%s/%s] - Submitted: %s' % (power_name, game.get_current_phase(), orders))
                await game.set_orders(power_name=power_name, orders=orders, wait=False)

            # Messages can be sent with game.send_message
            # await game.send_game_message(message=game.new_power_message('FRANCE', 'This is the message'))
        else:
            messages, orders = bot.act()
            if messages:
                # print(power_name, messages)
                for msg in messages:
                    msg_obj = Message(
                        sender=power_name,
                        recipient=msg['recipient'],
                        message=msg['message'],
                        phase=game.get_current_phase(),
                    )
                    await game.send_game_message(message=msg_obj)
            # print("Submitted orders")
            if orders is not None:
                await game.set_orders(power_name=power_name, orders=orders, wait=False)
        # Waiting for game to be processed
        while current_phase == game.get_current_phase():
            await asyncio.sleep(0.1)

    # A local copy of the game can be saved with to_saved_game_format
    # To download a copy of the game with messages from all powers, you need to export the game as an admin
    # by logging in as 'admin' / 'password'

async def launch(game_id, hostname, botname, powers=None):
    """ Creates and plays a network game """
    # await create_game(game_id, hostname)
    if powers is None:
        await asyncio.gather(*[play(game_id, botname, power_name, hostname) for power_name in POWERS])
    else:
        await asyncio.gather(*[play(game_id, botname, power_name, hostname) for power_name in powers.split(",")])

def parse_args():
    parser = argparse.ArgumentParser(description='RAND-DIP: Random Diplomacy Agent')
    parser.add_argument('--gameid', '-g', type=str, help='game id of game created in DATC diplomacy game')
    parser.add_argument('--powers', '-p', type=str, help='comma-seperated country names (AUSTRIA, ENGLAND, FRANCE, GERMANY, ITALY, RUSSIA, TURKEY)')
    parser.add_argument('--hostname', '-H', type=str, default='localhost', help='host IP address (defaults to localhost)')
    parser.add_argument('--bots', '-B', type=str, default='random',
                        help='botname for all powers')

    args = parser.parse_args()
    print(args)
    return args

if __name__ == '__main__':
    args = parse_args()
    asyncio.run(launch(args.gameid, args.hostname, args.bots, args.powers))

