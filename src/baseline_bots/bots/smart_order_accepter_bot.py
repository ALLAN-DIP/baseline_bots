__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from DAIDE import ALY, PRP
from diplomacy import Message

from baseline_bots.bots.random_proposer_bot import RandomProposerBot
from baseline_bots.utils import MessagesData, OrdersData, get_other_powers

# Using library https://github.com/SHADE-AI/daidepp
from daidepp import create_daide_grammar, daide_visitor

class SmartOrderAccepterBot(RandomProposerBot):
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

    def get_proposals(rcvd_messages) -> Dict[str, str]:
        """Extract proposal messages from receieved messages and checks for valid syntax before returning it"""
        grammar = create_daide_grammar(level=130)
        
        # Extract messages containing PRP string
        order_msgs = [msg[1] for msg in rcvd_messages if "PRP" in msg[1].message]

        proposals = {}
        for order_msg in order_msgs:
            try:
                # Parse using DAIDEPP functions
                parse_tree = grammar.parse(order_msg.message)
                output = daide_visitor.visit(parse_tree)
                
                if output[0] == 'PRP':
                    proposals[order_msg.sender] = order_msg.message
            except Exception as e:
                print(e)
                pass

        return proposals

    def gen_messages(self, rcvd_messages):
        ret_msgs = MessagesData()

        return ret_msgs

    def gen_orders(self):
        # from dipnet
        return None

    def __call__(self, rcvd_messages):
        messages = self.gen_messages(rcvd_messages)
        return {"messages": messages, "orders": self.gen_orders()}
