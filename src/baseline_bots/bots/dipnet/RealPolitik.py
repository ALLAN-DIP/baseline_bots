__authors__ = "Wichayaporn Wongkamjan"
__email__ = "w.wongkamjan@gmail.com"


import random
import sys

from typing import List

from bots.dipnet.dipnet_bot import DipnetBot
from DAIDE import FCT, ORR, XDO
from diplomacy import Game, Message
from diplomacy_research.players.benchmark_player import DipNetRLPlayer
from tornado import gen
from utils import (
    REJ,
    YES,
    MessagesData,
    OrdersData,
    get_non_aggressive_orders,
    get_order_tokens,
    get_other_powers,
    parse_FCT,
    parse_orr_xdo,
)


class RealPolitik(DipnetBot):
    """
    select a set of orders that return maximum next state value
    where the next state is simulated by proposed orders and shared orders (recieved via in-game messages)
    """

    def __init__(self, power_name: str, game: Game, total_msg_rounds=3) -> None:
        super().__init__(power_name, game, total_msg_rounds)
        self.stance = None
        self.accum_messages = []
        self.rollout_length = 5
        self.rollout_n_order = 5

    def phase_init(self) -> None:
        super().phase_init()
        self.accum_messages = []

    @gen.coroutine
    def get_state_value(self, game, power_name):
        # rollout the game --- orders in rollout are from dipnet
        # state value
        for i in range(self.rollout_length):
            # print('rollout: ', i)
            for power in game.powers:
                orders = yield self.brain.get_orders(game, power)
                # print(power + ': ')
                # print(orders)
                game.set_orders(
                    power_name=power,
                    orders=orders[: min(self.rollout_n_order, len(orders))],
                )
            game.process()
        return len(game.get_centers(power_name))

    @gen.coroutine
    def gen_messages(self, rcvd_messages):
        # accum all messages from all rounds then reply YES to best proposer and set orders
        # for xdo order set (max at 6 for now) -> simulate worlds by execute all of shared orders + xdo order set
        # get current state value of simulated worlds
        # return set of order with highest state value
        # if no xdo order set -> then return dipnet orders
        self.orders = OrdersData()
        ret_obj = MessagesData()
        if self.curr_msg_round != self.total_msg_rounds:
            self.curr_msg_round += 1
            return ret_obj
        else:
            if len(rcvd_messages) == 0:
                orders = yield self.brain.get_orders(self.game, self.power_name)
                self.orders.add_orders(orders, overwrite=True)
                self.curr_msg_round += 1
                return ret_obj

            shared_order = {
                other_power: None
                for other_power in get_other_powers([self.power_name], self.game)
            }
            proposal_order = {
                other_power: None
                for other_power in get_other_powers([self.power_name], self.game)
            }

            # group messages into 2: (1) shared (with FCT) orders and (2) xdo (without FCT) orders
            for game_msg in rcvd_messages:
                # game_msg = game_msg[1]
                # this is for sharing info orders
                if "FCT" in game_msg.message:
                    shared_order[game_msg.sender] = parse_orr_xdo(
                        parse_FCT(game_msg.message)
                    )
                # this is for proposal orders
                else:
                    # print(game_msg.message)
                    proposal_order[game_msg.sender] = parse_orr_xdo(game_msg.message)
                    # print(proposal_order[game_msg.sender])

            # include dipnet order
            proposal_order[self.power_name] = yield self.brain.get_orders(
                self.game, self.power_name
            )
            proposed = False

            # for each xdo order set (max at 6 for now) -> simulate worlds by execute all of shared orders + xdo order set
            state_value = {
                other_power: -10000
                for other_power in get_other_powers([self.power_name], self.game)
            }
            for proposer, orders in proposal_order.items():
                if orders:
                    proposed = True
                    simulated_game = self.game.__deepcopy__(None)
                    orders = get_non_aggressive_orders(
                        orders, self.power_name, self.game
                    )
                    # print('from: ', proposer)
                    # print(orders)
                    simulated_game.set_orders(power_name=self.power_name, orders=orders)
                    for other_power, power_orders in shared_order.items():
                        if power_orders:
                            simulated_game.set_orders(
                                power_name=other_power, orders=power_orders
                            )
                    simulated_game.process()
                    state_value[proposer] = yield self.get_state_value(
                        simulated_game, self.power_name
                    )

            best_proposer = max(state_value, key=state_value.get)

            if not proposed and best_proposer != self.power_name:
                # if there is no proposal orders, set orders execute by dipnet
                orders = proposal_order[self.power_name]
                self.orders.add_orders(orders, overwrite=True)
                return ret_obj

            self.orders.add_orders(proposal_order[best_proposer], overwrite=True)
            for proposer, orders in proposal_order.items():
                if orders:
                    if proposer == best_proposer:
                        msg = YES(
                            ORR([XDO(order) for order in proposal_order[proposer]])
                        )
                    else:
                        msg = REJ(
                            ORR([XDO(order) for order in proposal_order[proposer]])
                        )
                    ret_obj.add_message(
                        proposer, str(msg) + " " + str(state_value[proposer])
                    )
            # print(self.power_name + ': ')
            # print(self.orders.get_list_of_orders())
            self.curr_msg_round += 1
            return ret_obj

    @gen.coroutine
    def gen_orders(self):
        return self.orders.get_list_of_orders()
