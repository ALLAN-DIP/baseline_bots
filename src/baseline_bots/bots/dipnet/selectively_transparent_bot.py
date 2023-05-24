from typing import List

from daidepp import FCT, ORR, XDO
from diplomacy import Game, Message
from tornado import gen

from baseline_bots.bots.dipnet.transparent_bot import TransparentBot
from baseline_bots.utils import (
    MessagesData,
    is_order_aggressive,
    optional_ORR,
    parse_daide,
)


class SelectivelyTransparentBot(TransparentBot):
    """
    Execute orders computed by dipnet
    Sends out non-aggressive actions
    """

    def __init__(self, power_name: str, game: Game, total_msg_rounds: int = 3):
        super().__init__(power_name, game, total_msg_rounds)

    @gen.coroutine
    def gen_messages(self, rcvd_messages: List[Message]) -> MessagesData:
        """send out non-aggressive orders that is bot is taking"""
        # call super then find non-aggressive orders
        messages = yield super().gen_messages(rcvd_messages)
        for message in messages:
            parsed_message = parse_daide(message["message"])
            if isinstance(parsed_message, FCT):
                arrangement = parsed_message.arrangement_qry_not
                if isinstance(parsed_message, ORR):
                    xdo_arrangements = arrangement.arrangements
                    peaceful_orders = []
                    for xdo_arrangement in xdo_arrangements:
                        if isinstance(parsed_message, XDO):
                            if not is_order_aggressive(
                                str(xdo_arrangement.order),
                                self.power_name,
                                self.game,
                            ):
                                peaceful_orders.append(xdo_arrangement.order)

                    # reconstruct message
                    xdo_arrangements = [XDO(order) for order in peaceful_orders]
                    orr_arrangement = optional_ORR(xdo_arrangements)
                    fct_arrangement = FCT(orr_arrangement)
                    message["message"] = str(fct_arrangement)

        return messages
