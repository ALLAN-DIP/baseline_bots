__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from random_proposer_bot import RandomProposerBot
from daide_utils import ALY, get_other_powers, BotReturnData


class RandomAllierProposerBot(RandomProposerBot):
    """
    The first time this bot acts, it sends an alliance message to 
    all other bots. Otherwise, it just sends random order proposals to 
    other bots.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.alliance_props_sent = False

    def act(self):
        # Return data initialization
        ret_obj = BotReturnData()

        if self.alliance_props_sent:
            # send random action proposals
            super().act()
        else:
            # send alliance proposals to other bots

            # for all other powers
            for other_power in get_other_powers([self.power_name], self.game):
                # encode alliance message in daide syntax
                alliance_message = ALY([other_power, self.power_name], self.game)
                # send the other power an ally request
                ret_obj.add_message(other_power, alliance_message)

            # dont sent alliance props again
            self.alliance_props_sent = True
        
        return ret_obj

if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    # game instance
    game = Game()
    # select the first name in the list of powers
    bot_power = list(game.get_map_power_names())[0]
    # instantiate random honest bot
    bot = RandomAllierProposerBot(bot_power, game)
    while not game.is_game_done:
        bot_state = bot.act()
        messages, orders = bot_state.messages, bot_state.orders
        if messages:
            print(bot.power_name, messages)
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

    to_saved_game_format(game, output_path='RandomAllierProposerBotGame.json')
