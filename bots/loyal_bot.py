__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import sys
sys.path.append("..")

from diplomacy import Message
from DAIDE import ParseError
from DAIDE.utils.exceptions import ParseError
from DAIDE import YES, ALY, ORR, XDO

from utils import parse_orr_xdo, get_non_aggressive_orders, MessagesData, OrdersData, sort_messages_by_most_recent
import bots.baseline_bot as baseline_bot

class LoyalBot(baseline_bot.BaselineBot):
    """
    Accepts first alliance it receives. 
    Then only accepts orders bots in that alliance.
    NOTE: only executes non-aggressive actions
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        # will always follow this country's orders
        self.allies = None
        # orders to be provided by allies
        self.orders = OrdersData()

    def gen_messages(self, rcvd_messages):
        # Return data initialization
        ret_obj = MessagesData()

        if len(rcvd_messages) == 0:
            return ret_obj

        # sort from most recent to least recent
        sorted_rcvd_messages = sort_messages_by_most_recent(rcvd_messages)
        # get most recent message
        last_message = sorted_rcvd_messages[0]
        if self.allies:
            # ensure message sender is an ally
            if last_message.sender in self.allies:
                try:
                    orders = get_non_aggressive_orders(parse_orr_xdo(last_message.message), self.power_name, self.game)
                    self.orders.add_orders(orders)
                     
                except ParseError as e:
                    pass
        else:
            try:
                alliance_proposal = ALY.parse(last_message.message)
                if self.power_name in alliance_proposal.allies:
                    self.allies = alliance_proposal.allies
                    msg = YES(last_message.message)
                    ret_obj.add_message(last_message.sender, str(msg))

            except ParseError as e:
                pass

        return ret_obj

    def gen_orders(self):
        return self.orders
