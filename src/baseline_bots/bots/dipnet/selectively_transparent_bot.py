__authors__ = ["Sander Schulhoff"]
__email__ = "sanderschulhoff@gmail.com"

import random
from collections import defaultdict

from DAIDE import config

from baseline_bots.bots.dipnet.transparent_bot import TransparentBot
from baseline_bots.utils import (
    MessagesData,
    get_other_powers,
    is_order_aggressive,
    parse_arrangement,
    parse_FCT,
)

config.ORDERS_DAIDE = False
from DAIDE import FCT, ORR, XDO, Order, parse
from tornado import gen


class SelectivelyTransparentBot(TransparentBot):
    """
    Execute orders computed by dipnet
    Sends out non-aggressive actions
    """

    def __init__(self, power_name, game, total_msg_rounds=3):
        super().__init__(power_name, game, total_msg_rounds)

    @gen.coroutine
    def gen_messages(self, rcvd_messages):
        """send out non-aggressive orders that is bot is taking"""
        # call super then find non-aggressive orders
        messages = yield super().gen_messages(rcvd_messages)
        for message in messages:
            parsed_message = parse(message["message"])
            if type(parsed_message) == FCT:
                arrangement = parsed_message.arrangement
                if type(arrangement) == ORR:
                    xdo_arrangements = arrangement.arrangements
                    peaceful_orders = []
                    for xdo_arrangement in xdo_arrangements:
                        if (
                            type(xdo_arrangement) == XDO
                            and type(xdo_arrangement.arrangement) == Order
                        ):
                            if not is_order_aggressive(
                                str(xdo_arrangement.arrangement),
                                self.power_name,
                                self.game,
                            ):
                                peaceful_orders.append(xdo_arrangement.arrangement)

                    # reconstruct message
                    xdo_arrangements = [XDO(order) for order in peaceful_orders]
                    orr_arrangement = ORR(xdo_arrangements)
                    fct_arrangement = FCT(orr_arrangement)
                    message["message"] = str(fct_arrangement)
                    # print(message["message"])

        return messages
