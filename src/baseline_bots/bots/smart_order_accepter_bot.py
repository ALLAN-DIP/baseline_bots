__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from typing import Dict, List, Tuple

from DAIDE import FCT, ORR, XDO
from diplomacy import Message
from stance_vector import ScoreBasedStance

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_best_orders,
    get_other_powers,
    parse_orr_xdo,
    parse_PRP,
    dipnet_to_daide_parsing,
    daide_to_dipnet_parsing
)


class SmartOrderAccepterBot(DipnetBot):
    """
    This bot uses dipnet to generate orders.

    When it receives messages, it will check if any of them are proposed orders.
    Then, it will use a rollout policy to decide whether to accept or reject the order.

    If the order is accepted, it will be added to the orders that the bot will
    execute and a positive response will be sent to the proposer.

    If the order is rejected, a negative response will be sent to the proposer.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.alliance_props_sent = False
        self.stance = ScoreBasedStance(power_name, game)

    def get_proposals(
        self, rcvd_messages: List[Tuple[int, Message]]
    ) -> Dict[str, List[str]]:
        """
        Extract proposal messages from received messages and checks for valid syntax before returning it
        """
        # Extract messages containing PRP string
        order_msgs = [msg[1] for msg in rcvd_messages if "PRP" in msg[1].message]

        proposals = {}
        for order_msg in order_msgs:
            try:
                proposals[order_msg.sender] = (
                    [daide_to_dipnet_parsing(order) for order in parse_orr_xdo(parse_PRP(order_msg.message))]
                )
            except Exception as e:
                print(e)
                pass

        return proposals

    def gen_pos_stance_messages(
        self, msgs_data: MessagesData, orders_list: List[str]
    ) -> None:
        """
        Add messages to be sent to powers with positive stance.
        These messages would contain factual information about the orders that current power would execute in current round
        """
        orders_decided = FCT(ORR(XDO(dipnet_to_daide_parsing(orders_list))))
        for pow in self.stance.stance[self.power_name]:
            if self.stance.stance[self.power_name][pow] > 0:
                msgs_data.add_message(pow, str(orders_decided))

    def gen_messages(self, orders_list: List[str]):
        msgs_data = MessagesData()

        # generate messages: we should  be sending our true orders to allies (positive stance)
        self.gen_pos_stance_messages(msgs_data, orders_list)

        return msgs_data

    def __call__(self, rcvd_messages: List[Tuple[int, Message]]):
        # compute pos/neg stance on other bots using Tony's stance vector
        self.stance.get_stance()

        # get dipnet order
        orders = yield self.brain.get_orders(self.game, self.power_name)

        # extract only the proposed orders from the messages the bot has just received
        prp_orders = self.get_proposals(rcvd_messages)

        # include base order to prp_orders.
        # This is to avoid having double calculation for the best list of orders between (self-generated) base orders vs proposal orders
        # e.g. if we are playing as ENG and the base orders are generated from DipNet, we would want to consider
        # if there is any better proposal orders that has a state value more than ours, then do it. If not, just follow the base orders.
        prp_orders[bot.power_name] = orders

        best_proposer, best_orders = get_best_orders(self, prp_orders, shared_order)

        # add orders
        orders_data = OrdersData()
        orders_data.add_orders(best_orders)

        # generate messages
        messages = self.gen_messages(orders_data)
        return {"messages": messages, "orders": orders_data.get_list_of_orders()}
