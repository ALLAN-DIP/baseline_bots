__authors__ = ["Sander Schulhoff", "Kartik Shenoy"]
__email__ = "sanderschulhoff@gmail.com"

from typing import List
import sys
sys.path.append("..")

from diplomacy import Game, Message
from diplomacy.utils.export import to_saved_game_format

from bots.baseline_bot import BaselineBot, BaselineMsgRoundBot

class GamePlay():
    """
    A simple framework to test multiple bots together
    """
    def __init__(self, game:Game, bots:List[BaselineBot], msg_rounds:int, save_json=False):
        assert(len(bots) <= 7), "too many bots"
        # if no game is passed, assume bots is a list of bot classes to
        # be instantiated. 
        if game is None:
            # make game
            game = Game()
            # get list of powers
            power_names = list(game.get_map_power_names())
            inst_bots = []
            # instantiate each bot
            for i, bot_class in enumerate(bots):
                inst_bots.append(bot_class(power_names[i], game))
            self.bots = inst_bots
        else:
            self.bots = bots 

        self.game = game
        self.msg_rounds = msg_rounds
        self.save_json = save_json
        

    def play(self):
        """play a game with the bots"""

        while not self.game.is_game_done:
            # reset bot round info
            for bot in self.bots:
                if type(bot) == BaselineMsgRoundBot:
                    bot.phase_init()

            # ensure that we are in movement phase
            if self.game.get_current_phase()[-1] == 'M':
                # Iterate through multiple rounds of msgs
                for _ in range(self.msg_rounds):
                    round_msgs = self.game.messages
                    msgs_to_send = {}
                    for bot in self.bots:
                        # retrieve messages sent to bot
                        # an array of Message objects
                        rcvd_messages = self.game.filter_messages(messages=round_msgs, game_role=bot.power_name)
                        rcvd_messages = list(rcvd_messages.items())
                        rcvd_messages.sort()
                        
                        # get messages to be sent from bot
                        bot_messages = bot.gen_messages(rcvd_messages)

                        msgs_to_send[bot.power_name] = bot_messages

                    # Send all messages after all bots decide
                    for power_name in msgs_to_send:
                        msgs = msgs_to_send[power_name]
                        for msg in msgs:
                            msg_obj = Message(
                                sender=power_name,
                                recipient=msg['recipient'],
                                message=msg['message'],
                                phase=self.game.get_current_phase(),
                            )
                            self.game.add_message(message=msg_obj)

            # get/set orders
            for bot in self.bots:
                orders = bot.gen_orders()
                if orders is not None:
                    self.game.set_orders(power_name=bot.power_name, orders=orders.get_list_of_orders())

            self.game.process()

        if self.save_json:
            to_saved_game_format(self.game, output_path='GamePlayFramework.json')

                
if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from utils import OrdersData, MessagesData, get_order_tokens
    from bots.random_proposer_bot import RandomProposerBot

    game_play_obj = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3, True)

    game_play_obj.play()