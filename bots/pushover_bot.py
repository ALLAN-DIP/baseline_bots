__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from DAIDE import ParseError
import DAIDE 
DAIDE.config.ORDERS_DAIDE = False

from . import baseline_bot
from utils import parse_orr_xdo, get_non_aggressive_orders, OrdersData, sort_messages_by_most_recent

class PushoverBot(baseline_bot.BaselineBot):
    """
    Does whatever the last message/bot told it to do
    NOTE: only executes non-aggressive action
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.orders = None

    def gen_messages(self, _):
        # Return data initialization
        return None

    def gen_orders(self):
        return self.orders

    def __call__(self, rcvd_messages):
        ret_obj = OrdersData()

        if len(rcvd_messages) == 0:
            return {"orders":ret_obj}

        sorted_rcvd_messages = sort_messages_by_most_recent(rcvd_messages)
        
        last_message = sorted_rcvd_messages[0]
        # parse may fail
        try:
            orders = get_non_aggressive_orders(parse_orr_xdo(last_message.message), self.power_name, self.game)
            # set the orders
            ret_obj.add_orders(orders)
        except ParseError as e:
            pass

        self.orders = ret_obj

        return {"orders": ret_obj}
