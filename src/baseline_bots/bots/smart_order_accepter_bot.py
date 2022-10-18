__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from typing import Dict, List, Tuple
from tornado import gen
from DAIDE import FCT, ORR, XDO, PRP, HUH, YES 
from diplomacy import Message
from stance_vector import ScoreBasedStance

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_best_orders,
    get_other_powers,
    parse_alliance_proposal,
    parse_arrangement,
    parse_PRP,
    REJ
)
from baseline_bots.parsing_utils import (
    dipnet_to_daide_parsing,
    daide_to_dipnet_parsing,
    parse_proposal_messages
)

from collections import defaultdict
from tornado import gen


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
        self.alliances = defaultdict(list)
        self.rollout_length = 10
        self.rollout_n_order = 5

    def gen_pos_stance_messages(
        self, msgs_data: MessagesData, orders_list: List[str]
    ) -> None:
        """
        Add messages to be sent to powers with positive stance.
        These messages would contain factual information about the orders that current power would execute in current round
        """
        if orders_list:
            orders_decided = FCT(ORR([XDO(order) for order in dipnet_to_daide_parsing(orders_list, self.game)]))
            if str(orders_decided) != "FCT ()":
                for pow in self.stance.stance[self.power_name]:
                    if pow != self.power_name and self.stance.stance[self.power_name][pow] > 0:
                        msgs_data.add_message(pow, str(orders_decided))
    
    def gen_messages(self, orders_list: List[str]):
        msgs_data = MessagesData()

        # generate messages: we should  be sending our true orders to allies (positive stance)
        self.gen_pos_stance_messages(msgs_data, orders_list)

        return msgs_data

    def gen_proposal_reply(self, best_proposer: str, prp_orders: dict, messages: MessagesData) -> MessagesData: 
        """
        Reply back to allies regarding their proposals whether we follow or not follow
        """
        for proposer, orders in prp_orders.items():
            if orders and self.power_name != proposer and self.stance.get_stance()[self.power_name][proposer]>=0:
                if proposer == best_proposer:
                    msg = YES(
                        PRP(ORR([XDO(order) for order in dipnet_to_daide_parsing(orders, self.game)]))
                    )
                else:
                    msg = REJ(
                        PRP(ORR([XDO(order) for order in dipnet_to_daide_parsing(orders, self.game)]))
                    )
                messages.add_message(
                    proposer, str(msg)
                )
        return messages
    
    def respond_to_invalid_orders(self, invalid_proposal_orders: Dict[str, List[Tuple[str, str]]], messages_data: MessagesData) -> None:
        """
        The bot responds by HUHing the invalid proposal orders received (this could occur if the move proposed is invalid)

        :param invalid_proposal_orders: dictionary of sender -> (invalid order, unit power)
        :param messages_data: Message Data object to add messages
        """
        if not invalid_proposal_orders:
            return
        for sender in invalid_proposal_orders:
            if sender == self.power_name:
                continue
            message = HUH(PRP(ORR([XDO(order) for order in dipnet_to_daide_parsing(invalid_proposal_orders[sender], self.game, unit_power_tuples_included=True)])))
            messages_data.add_message(
                sender, str(message)
            )
        
    def respond_to_alliance_messages(self, messages_data: MessagesData) -> None:
        """
        Send YES confirmation messages to all alliance proposals
        :param messages_data: Message Data object to add messages
        """
        unique_senders = {}
        for sender_message_tuple in self.alliances.values():
            for sender, message in sender_message_tuple:
                unique_senders[sender] = message
        for sender, message in unique_senders.items():
            if sender == self.power_name:
                continue
            messages_data.add_message(sender, str(YES(message)))

        if self.alliances:
            print("Alliances accepted")
            print(self.alliances)

    @gen.coroutine
    def __call__(self, rcvd_messages: List[Tuple[int, Message]]):
        # compute pos/neg stance on other bots using Tony's stance vector
        self.stance.get_stance()
        print("debug: Fetched stance")

        # get dipnet order
        orders = yield from self.brain.get_orders(self.game, self.power_name)
        print("debug: Fetched orders", orders)

        # parse the proposal messages received by the bot
        parsed_messages_dict = parse_proposal_messages(rcvd_messages, self.game, self.power_name)
        valid_proposal_orders = parsed_messages_dict['valid_proposals']
        invalid_proposal_orders = parsed_messages_dict['invalid_proposals']
        shared_orders = parsed_messages_dict['shared_orders']
        other_orders =  parsed_messages_dict['other_orders']
        self.alliances =  parsed_messages_dict['alliance_proposals']
        print("debug: Parsed proposal messages")

        # include base order to prp_orders.
        # This is to avoid having double calculation for the best list of orders between (self-generated) base orders vs proposal orders
        # e.g. if we are playing as ENG and the base orders are generated from DipNet, we would want to consider
        # if there is any better proposal orders that has a state value more than ours, then do it. If not, just follow the base orders.
        valid_proposal_orders[self.power_name] = orders

        # best_proposer, best_orders = yield from get_best_orders(self, valid_proposal_orders, shared_orders)
        best_orders, best_proposer = orders, list(self.alliances.keys())[0] if self.alliances else ""
        print("debug: Fetched best orders")

        # add orders
        orders_data = OrdersData()
        orders_data.add_orders(best_orders)

        # generate messages for FCT sharing info orders
        msgs_data = self.gen_messages(orders_data.get_list_of_orders())
        self.respond_to_invalid_orders(invalid_proposal_orders, msgs_data)
        self.respond_to_alliance_messages(msgs_data)
        msg_allies = ','.join([pow for pow in self.stance.stance[self.power_name] if (pow != self.power_name and self.stance.stance[self.power_name][pow] > 0)])
        msg_foes = ','.join([pow for pow in self.stance.stance[self.power_name] if (pow != self.power_name and self.stance.stance[self.power_name][pow] < 0)])
        msg_neutral = ','.join([pow for pow in self.stance.stance[self.power_name] if (pow != self.power_name and self.stance.stance[self.power_name][pow] == 0)])
        msgs_data.add_message("GLOBAL", str(f"{self.power_name}: From my stance vector perspective, I see {msg_allies if msg_allies else 'no one'} as my allies, \
                        {msg_foes if msg_foes else 'no one'} as my foes and I am indifferent towards {msg_neutral if msg_neutral else 'no one'}"))

        # generate proposal response YES/NO to allies
        msgs_data = self.gen_proposal_reply(best_proposer, valid_proposal_orders, msgs_data)
        return {"messages": msgs_data, "orders": orders_data.get_list_of_orders()}