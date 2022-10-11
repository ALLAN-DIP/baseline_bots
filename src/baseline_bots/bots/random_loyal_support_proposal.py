__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

import random
from collections import defaultdict

from DAIDE import ALY, ORR, XDO, YES
from diplomacy import Message

from baseline_bots.bots.baseline_bot import BaselineMsgRoundBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_non_aggressive_orders,
    get_order_tokens,
    get_other_powers,
    parse_alliance_proposal,
    parse_arrangement,
)


class RandomLSPBot(BaselineMsgRoundBot):
    """
    This bot either leads, proposes alliances and proposes support moves for moves proposed by Dipnet to the supporting allies or
    follows, accepts alliances, accepts support proposals and blindly follows them
    while filling the remaining units with Dipnet's orders
    """

    def __init__(
        self, power_name, game, total_msg_rounds=3, alliance_all_in=True
    ) -> None:
        super().__init__(power_name, game, total_msg_rounds)
        self.allies = []
        self.allies_influence = set()
        self.my_leader = None

        self.alliance_all_in = False

        # Alliance stages
        self.alliance_props_sent = False
        self.alliance_props_ack_sent = False
        self.support_proposals_sent = False

        self.leader_mode = False

        self.alliance_all_in = alliance_all_in
        self.my_influence = set()
        self.possible_orders = {}

    def set_leader(self):
        """Sets this bot as the leader"""
        self.leader_mode = True

    def set_follower(self):
        """Sets this bot as the follower"""
        self.leader_mode = False

    def interpret_orders(self, rcvd_messages):
        """
        Parses the received messages and extracts:

        Params:
        - rcvd_messages: List of messages received by current power with tuples of this format:
            * [0]: timestamp
            * [1]: Message object

        Returns:
        - Dictionary with these keys:
            * alliance_proposer: If alliance message received, set to sender power's name, else None
            * allies_proposed: If alliance message received, set to alliance powers list, else []
            * alliance_msg: If alliance message received, set to alliance message, else None
            * yes_allies_proposed: If alliance acceptance message receieved, set to alliance powers list, else []
            * orders_proposed: If suggested orders received, set to this list of orders, else []
        """
        alliance_msgs = [
            msg
            for msg in rcvd_messages
            if "ALY" in msg[1].message and msg[1].sender != self.power_name
        ]
        yes_alliance_msgs = [msg for msg in alliance_msgs if "YES" in msg[1].message]
        alliance_proposal_msgs = [
            msg for msg in alliance_msgs if "YES" not in msg[1].message
        ]

        order_msgs = [msg[1] for msg in rcvd_messages if "ALY" not in msg[1].message]

        # Alliance related interpretations
        # Interpret alliance acceptance message
        if yes_alliance_msgs:
            last_message = yes_alliance_msgs[-1][1]
            yes_allies = parse_alliance_proposal(
                last_message.message[5:-1], self.power_name
            )
        else:
            yes_allies = []

        # Interpret alliance proposal message
        if alliance_proposal_msgs:
            last_message = alliance_proposal_msgs[-1][1]
            allies_proposed = parse_alliance_proposal(
                last_message.message, self.power_name
            )
            alliance_proposer = last_message.sender
            alliance_msg = last_message.message
        else:
            allies_proposed = []
            alliance_proposer = None
            alliance_msg = None

        rcvd_orders = []
        if order_msgs:
            for msg in order_msgs:
                if msg.sender == self.my_leader:
                    rcvd_orders += parse_arrangement(msg.message)

        return {
            "alliance_proposer": alliance_proposer,
            "allies_proposed": allies_proposed,
            "alliance_msg": alliance_msg,
            "yes_allies_proposed": yes_allies,
            "orders_proposed": rcvd_orders,
        }

    def bad_move(self, order):
        """If order indicates attack on one of its provinces, return True, else return False"""
        order_tokens = get_order_tokens(order)

        if len(order_tokens) == 2:
            # Attack move
            if order_tokens[1].split()[-1] in self.my_influence:
                return True
        elif len(order_tokens) == 4 and order_tokens[1] == "S":
            # Support move
            if order_tokens[1].split()[-1] in self.my_influence:
                return True

        return False

    def support_move(self, order):
        """Indicates if order is a support order or not"""
        order_tokens = get_order_tokens(order)
        if 3 <= len(order_tokens) <= 4 and order_tokens[1] == "S":
            return True
        else:
            return False

    def get_allies_orderable_locs(self):
        """Gets provinces which are orderable for the allies"""
        provinces = set()
        for ally in self.allies:
            new_provs = {loc.upper() for loc in self.game.get_orderable_locations(ally)}
            provinces.update(new_provs)
        return provinces

    def get_2_neigh_provinces(self):
        """
        Determine set of orderable locations of allies which are 1-hop/2-hops away from the current power's orderable locations
        """
        provs = [
            loc.upper() for loc in self.game.get_orderable_locations(self.power_name)
        ]

        # Agent's 1-neighbourhood provinces
        n_provs = set()
        for prov in provs:
            n_provs.update(
                set(
                    [
                        prov2.upper()
                        for prov2 in self.game.map.abut_list(prov)
                        if prov2.upper().split("/")[0] not in provs
                        and prov2.upper().split("/")[0] in self.allies_influence
                    ]
                )
            )

        # Agent's alliances provinces set:
        allies_provs = self.get_allies_orderable_locs()

        # Agent's 2-neighbourhood provinces (retained only alliance's provinces)
        n2n_provs = set()
        for prov in n_provs:
            if prov in allies_provs:
                n2n_provs.update(
                    set(
                        [
                            prov2.upper()
                            for prov2 in self.game.map.abut_list(prov)
                            if prov2.upper().split("/")[0] not in provs
                            and prov2.upper().split("/")[0] not in n_provs
                            and prov2.upper().split("/")[0] in self.allies_influence
                        ]
                    )
                )
        n2n_provs.update(n_provs)
        return n2n_provs

    def is_support_for_selected_orders(self, support_order):
        """Determine if selected support order for neighbour corresponds to a self order selected"""
        order_tokens = get_order_tokens(support_order)
        selected_order = get_order_tokens(
            self.orders.orders[order_tokens[2].split()[1]]
        )

        if (
            len(order_tokens[2:]) == len(selected_order)
            and order_tokens[2:] == selected_order
        ):
            # Attack move
            return True
        elif selected_order[1].strip() == "H" and (
            len(order_tokens[2:]) == len(selected_order) - 1
        ):
            # Hold move
            return True
        return False

    def generate_support_proposals(self, comms_obj):
        final_messages = defaultdict(list)

        # TODO: Some scenario is getting missed out | Sanity check: If current phase fetched is not matching with server phase, skip execution
        if self.game.get_current_phase()[-1] == "M":
            # Fetch neighbour's orderable provinces
            n2n_provs = self.get_2_neigh_provinces()

            possible_support_proposals = defaultdict(list)
            for n2n_p in n2n_provs:
                if not (self.possible_orders[n2n_p]):
                    continue

                # Filter out support orders from list of all possible orders
                subset_possible_orders = [
                    ord for ord in self.possible_orders[n2n_p] if self.support_move(ord)
                ]

                for order in subset_possible_orders:
                    order_tokens = get_order_tokens(order)
                    if order_tokens[2].split()[
                        1
                    ] in self.orders.orders and self.is_support_for_selected_orders(
                        order
                    ):
                        # If this support move corresponds to one of the orders the current bot has selected, exec following

                        # Generate (source, destination) tuple for move or (source,) tuple for hold
                        location_comb = tuple(
                            [oc.split()[1] for oc in order_tokens[2:]]
                        )

                        # Add to list of possible support proposals for this location combination
                        possible_support_proposals[location_comb].append(
                            (order_tokens[0], order)
                        )

            for attack_key in possible_support_proposals:
                # For each location combination, randomly select one of the support orders
                selected_order = random.choice(possible_support_proposals[attack_key])
                if self.game._unit_owner(selected_order[0]) is None:
                    raise "Coding Error"
                final_messages[self.game._unit_owner(selected_order[0]).name].append(
                    selected_order[1]
                )

            for recipient in final_messages:
                # Construct message for each support proposal
                suggested_proposals = ORR(XDO(final_messages[recipient]))
                comms_obj.add_message(recipient, str(suggested_proposals))

    def cache_allies_influence(self):
        """Cache allies' influence"""
        self.allies_influence = set()
        for pow in self.allies:
            self.allies_influence.update(set(self.game.get_power(pow).influence))

    def phase_init(self):
        """Phase initialization code"""
        super().phase_init()
        self.my_influence = set(self.game.get_power(self.power_name).influence)
        self.possible_orders = self.game.get_all_possible_orders()
        self.support_proposals_sent = False
        self.orders = OrdersData()
        self.cache_allies_influence()

    # def config(self, configg):
    #     # super().config(configg)
    #     self.alliance_all_in = configg['alliance_all_in']

    def gen_messages(self, rcvd_messages):
        # self.possible_orders = self.game.get_all_possible_orders()

        # Only if it is the first comms round, do this
        if self.curr_msg_round == 1:
            # Select set of non-support orders which are not bad moves
            for loc in self.game.get_orderable_locations(self.power_name):
                if self.possible_orders[loc]:
                    subset_orders = [
                        order
                        for order in self.possible_orders[loc]
                        if not self.bad_move(order) and not self.support_move(order)
                    ]
                    sel_order = random.choice(subset_orders)
                    self.orders.add_order(sel_order, overwrite=True)

        comms_obj = MessagesData()

        if self.are_msg_rounds_done():
            raise "Wrapper's invocation error: Comms function called after comms rounds are over"

        # Parse comms receieved
        comms_rcvd = self.interpret_orders(rcvd_messages)

        # If no alliance formed
        if not self.allies:
            # if alliance proposal acceptance message received
            if comms_rcvd["yes_allies_proposed"]:
                if not self.alliance_props_sent:
                    raise "Received ALY YES without sending ALY"
                self.allies = comms_rcvd["yes_allies_proposed"]
            # if alliance proposal receieved
            elif comms_rcvd["allies_proposed"]:
                self.allies = comms_rcvd["allies_proposed"]
                self.my_leader = comms_rcvd["alliance_proposer"]
                comms_obj.add_message(
                    self.my_leader, str(YES(comms_rcvd["alliance_msg"]))
                )
            # else propose alliance if not already sent
            elif not self.alliance_props_sent and self.leader_mode:
                # Send 2-power alliance proposals to all powers
                if not self.alliance_all_in:
                    for other_power in get_other_powers([self.power_name], self.game):
                        alliance_message = ALY(
                            [other_power, self.power_name], self.game
                        )
                        comms_obj.add_message(other_power, alliance_message)
                # Send all-power alliance proposals to all powers
                else:
                    alliance_message = ALY(self.game.get_map_power_names(), self.game)
                    for other_power in get_other_powers([self.power_name], self.game):
                        comms_obj.add_message(other_power, alliance_message)
                self.alliance_props_sent = True
        # If alliance is formed already, depending on leader/follower, command or be commanded
        else:
            # Generate support proposal messages
            if not self.support_proposals_sent and self.leader_mode:
                self.generate_support_proposals(comms_obj)
                self.support_proposals_sent = True

        # Update all received proposed orders
        self.orders.add_orders(comms_rcvd["orders_proposed"], overwrite=True)

        return comms_obj

    def gen_orders(self):

        if self.game.get_current_phase()[-1] == "M":
            # Fill out orders randomly if not decided already
            filled_out_orders = [
                random.choice(self.possible_orders[loc])
                for loc in self.game.get_orderable_locations(self.power_name)
                if loc not in self.orders.orders and self.possible_orders[loc]
            ]
            self.orders.add_orders(filled_out_orders, overwrite=False)
        else:
            random_orders = [
                random.choice(self.possible_orders[loc])
                for loc in self.game.get_orderable_locations(self.power_name)
                if self.possible_orders[loc]
            ]
            self.orders.add_orders(random_orders, overwrite=False)

        return self.orders.get_list_of_orders()


if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    from random_allier_proposer_bot import RandomAllierProposerBot

    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    # select the first name in the list of powers
    bots = [RandomLSPBot(bot_power, game) for bot_power in powers]

    while not game.is_game_done:
        for bot in bots:
            bot_state = bot.act()
            messages, orders = bot_state.messages, bot_state.orders
            if messages:
                for msg in messages:
                    msg_obj = Message(
                        sender=bot.power_name,
                        recipient=msg["recipient"],
                        message=msg["message"],
                        phase=game.get_current_phase(),
                    )
                    game.add_message(message=msg_obj)
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)
        game.process()

    to_saved_game_format(game, output_path="RandomSupportProposerBot.json")
