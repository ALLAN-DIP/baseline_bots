__authors__ = "Wichayaporn Wongkamjan"
__email__ = "wwongkam@umd.edu"

import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
sys.path.append("../../../dipnet_press")

from typing import List
import ujson as json
import random
from tornado import gen
from pytorch_DRL.common.utils import dict_to_arr
from DiplomacyEnv import DiplomacyEnv

from diplomacy import Game, Message
from DAIDE import ORR, XDO
from utils import OrdersData, MessagesData
from bots.RL.RLOrderBot import RLOrderBot
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop


class RLProposerBot(RLOrderBot):
    """Abstract Base Class for RL derivitive bots"""
    def __init__(self, power_name:str, game:Game, env:DiplomacyEnv, total_msg_rounds=3) -> None:
        super().__init__(power_name, game, env, total_msg_rounds)
        self.K_ORDERS = 5
        super().load_model('models/a2c_actor_diplomacy_proposer', 'models/a2c_critic_diplomacy_proposer')
        
    @gen.coroutine    
    def gen_messages(self, rcvd_messages:List[Message]) -> MessagesData:
        ret_obj = MessagesData()
        if self.curr_msg_round > self.total_msg_rounds:
            self.curr_msg_round += 1
            return ret_obj
        for recipient in self.game.powers:
            proposal_list = []
            if self.power_name != recipient and not self.powers[recipient].is_eliminated():
                orders = yield self.brain.get_orders(self.game, recipient)
                stance = self.env.dip_player.stance[self.power_name][recipient] 
                self.env.set_power_state(self.power_name, stance)
                n = len(orders)
                for order in orders[:min(self.K_ORDERS,n)]:
                    #state = no order in consideation
                    self.maa2c.env_state = dict_to_arr(self.env.cur_obs, self.maa2c.n_agents)
                    action = self.maa2c.exploration_action(self.maa2c.env_state)
                    action_dict = {agent_id: action[agent_id] for agent_id in range(self.maa2c.n_agents)}
                    self.env.step(action_dict, self.power_name, recipient, order)

                    #state = considering order
                    self.maa2c.env_state = dict_to_arr(self.env.cur_obs, self.maa2c.n_agents)
                    action = self.maa2c.exploration_action(self.maa2c.env_state)
                    action_dict = {agent_id: action[agent_id] for agent_id in range(self.maa2c.n_agents)}
                    self.env.step(action_dict, self.power_name, recipient, order)
                    # if action=propose, we add it to the list
                    if action_dict[self.env.power_mapping[self.power_name]]==1:
                        self.env.step(action_dict, self.power_name, recipient, order)
                        proposal_list.append(order)
                if len(proposal_list)>0:
                    suggested_orders = ORR([XDO(order) for order in proposal_list])
                    ret_obj.add_message(recipient, str(suggested_orders))
                self.env.reset_power_state(self.power_name, recipient)
        self.curr_msg_round += 1
        return ret_obj

@gen.coroutine
def main(): 
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    # game instance
    game = Game()
    # select the first name in the list of powers
    bot_power = list(game.get_map_power_names())[0]
   
    env = DiplomacyEnv()
    bot = RLProposerBot(bot_power, game, env)
    while not game.is_game_done:
        if game.phase_type =='M':
            bot.phase_init()
            messages = yield bot.gen_messages(None).messages
            for msg in messages:
                msg_obj = Message(
                    sender=bot.power_name,
                    recipient=msg['recipient'],
                    message=msg['message'],
                    phase=game.get_current_phase(),
                )
                game.add_message(message=msg_obj)
        bot_orders = yield bot.gen_orders()
        game.set_orders(bot_power, bot_orders)
        game.process()
    file_name = 'RLProposerBot.json'
    with open(file_name, 'w') as file:
        file.write(json.dumps(to_saved_game_format(game.game)))
    stop_io_loop()
if __name__ == "__main__":
    start_io_loop(main)
