__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

from collections import defaultdict
from lib2to3.pgen2.parse import ParseError

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from diplomacy.agents.baseline_bots.daide_utils import get_order_tokens, ORR, XDO

from daide_utils import BotReturnData, parse_orr_xdo, parse_alliance_proposal, get_non_aggressive_orders, YES, \
    BotReturnData, get_other_powers, ALY, CommsData, OrdersData


class RandomLSPBot(BaselineBot):
    """

    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.allies = []
        self.allies_influence = set()
        self.my_master = None

        self.alliance_all_in = False

        # Alliance stages
        self.alliance_props_sent = False
        self.alliance_props_ack_sent = False
        self.support_proposals_sent = False

        self.master_mode = False

    def set_master(self):
        self.master_mode = True

    def set_slave(self):
        self.master_mode = False

    def interpret_orders(self, rcvd_messages):
        alliance_msgs = [msg for msg in rcvd_messages if "ALY" in msg[1].message]
        yes_alliance_msgs = [msg for msg in alliance_msgs if "YES" in msg[1].message]
        alliance_proposal_msgs = [msg for msg in alliance_msgs if "YES" not in msg[1].message]

        order_msgs = [msg[1] for msg in rcvd_messages if "ALY" not in msg[1].message]

        # Alliance related interpretations
        # Interpret alliance acceptance message
        if yes_alliance_msgs:
            last_message = yes_alliance_msgs[-1][1]
            yes_allies = parse_alliance_proposal(last_message.message[5:-1], self.power_name)
        else:
            yes_allies = []

        # Interpret alliance proposal message
        if alliance_proposal_msgs:
            last_message = alliance_proposal_msgs[-1][1]
            allies_proposed = parse_alliance_proposal(last_message.message, self.power_name)
            alliance_proposer = last_message.sender
            alliance_msg = last_message.message
        else:
            allies_proposed = []
            alliance_proposer = None
            alliance_msg = None

        rcvd_orders = []
        if order_msgs:
            for msg in order_msgs:
                if msg.sender == self.my_master:
                    rcvd_orders += parse_orr_xdo(msg.message)

        return {
            'alliance_proposer': alliance_proposer,
            'allies_proposed': allies_proposed,
            'alliance_msg': alliance_msg,
            'yes_allies_proposed': yes_allies,
            'orders_proposed': rcvd_orders
        }

    def bad_move(self, order):
        order_tokens = get_order_tokens(order)

        if len(order_tokens) == 2:
            # Attack move
            if order_tokens[1].split()[-1] in self.my_influence:
                return True
        elif len(order_tokens) == 4 and order_tokens[1] == 'S':
            # Support move
            if order_tokens[1].split()[-1] in self.my_influence:
                return True

        return False

    def support_move(self, order):
        order_tokens = get_order_tokens(order)
        if 3 <= len(order_tokens) <= 4 and order_tokens[1] == 'S':
            return True
        else:
            return False

    def get_allies_orderable_locs(self):
        provinces = set()
        for ally in self.allies:
            new_provs = {loc.upper() for loc in self.game.get_orderable_locations(ally)}
            provinces.update(new_provs)
        return provinces

    def get_2_neigh_provinces(self):
        provs = [loc.upper() for loc in self.game.get_orderable_locations(self.power_name)]

        # Agent's 1-neighbourhood provinces
        n_provs = set()
        for prov in provs:
            n_provs.update(set([prov2.upper() for prov2 in self.game.map.abut_list(prov) if
                                prov2.upper().split('/')[0] not in provs and prov2.upper().split('/')[0] in self.allies_influence]))

        # Agent's alliances provinces set:
        allies_provs = self.get_allies_orderable_locs()

        # Agent's 2-neighbourhood provinces (retained only alliance's provinces)
        n2n_provs = set()
        for prov in n_provs:
            if prov in allies_provs:
                n2n_provs.update(
                    set([prov2.upper() for prov2 in self.game.map.abut_list(prov) if
                         prov2.upper().split('/')[0] not in provs and prov2.upper().split('/')[0] not in n_provs and prov2.upper().split('/')[0] in self.allies_influence]))
        n2n_provs.update(n_provs)
        return n2n_provs

    def is_support_for_selected_orders(self, support_order):
        order_tokens = get_order_tokens(support_order)
        selected_order = get_order_tokens(self.selected_orders.orders[order_tokens[2].split()[1]])

        if len(order_tokens[2:]) == len(selected_order) and order_tokens[2:] == selected_order:
            # Attack move
            return True
        elif selected_order[1].strip() == 'H' and (len(order_tokens[2:]) == len(selected_order) - 1):
            # Hold move
            return True
        return False

    def generate_support_proposals(self, comms_obj):
        final_messages = defaultdict(list)

        # TODO: Some scenario is getting missed out | Sanity check: If current phase fetched is not matching with server phase, skip execution
        if self.game.get_current_phase()[0] != 'W':
            n2n_provs = self.get_2_neigh_provinces()

            possible_support_proposals = defaultdict(list)
            for n2n_p in n2n_provs:
                if not (self.possible_orders[n2n_p]):
                    continue
                possible_orders = [ord for ord in self.possible_orders[n2n_p] if self.support_move(ord)]

                for order in possible_orders:
                    order_tokens = get_order_tokens(order)
                    if self.support_move(order) and \
                        (order_tokens[2].split()[1] in self.selected_orders.orders
                         and self.is_support_for_selected_orders(order)):
                            location_comb = tuple([oc.split()[1] for oc in order_tokens[2:]])
                            possible_support_proposals[location_comb].append(
                                        (order_tokens[0], order))
            for attack_key in possible_support_proposals:
                selected_order = random.choice(possible_support_proposals[attack_key])
                if self.game._unit_owner(selected_order[0]) is None:
                    raise "Coding Error"
                final_messages[self.game._unit_owner(selected_order[0]).name].append(selected_order[1])

            for recipient in final_messages:
                suggested_proposals = ORR(XDO(final_messages[recipient]))
                comms_obj.add_message(recipient, str(suggested_proposals))
        pass

    def cache_allies_influence(self):
        self.allies_influence = set()
        for pow in self.allies:
            self.allies_influence.update(set(self.game.get_power(pow).influence))

    def phase_init(self):
        super().phase_init()
        self.support_proposals_sent = False
        self.selected_orders = OrdersData()

    def config(self, configg):
        super().config(configg)
        self.alliance_all_in = configg['alliance_all_in']

    def comms(self, rcvd_messages):
        # Only if it is the first comms round, do this
        if self.curr_comms_round == 1:
            # Select set of non-support orders which are not bad moves
            for loc in self.game.get_orderable_locations(self.power_name):
                if self.possible_orders[loc]:
                    subset_orders = [order for order in self.possible_orders[loc]
                                     if not self.bad_move(order) and not self.support_move(order)]
                    self.selected_orders.add_order(random.choice(subset_orders))
        comms_obj = CommsData()

        if self.comms_rounds_completed():
            raise "Wrapper's invocation error: Comms function called after comms rounds are over"

        comms_rcvd = self.interpret_orders(rcvd_messages)

        # If no alliance formed
        if not self.allies:
            # if alliance proposal acceptance message received
            if comms_rcvd['yes_allies_proposed']:
                if not self.alliance_props_sent:
                    raise "Received ALY YES without sending ALY"
                self.allies = comms_rcvd['yes_allies_proposed']
                self.cache_allies_influence()
            # if alliance proposal receieved
            elif comms_rcvd['allies_proposed']:
                self.allies = comms_rcvd['allies_proposed']
                self.cache_allies_influence()
                self.my_master = comms_rcvd['alliance_proposer']
                comms_obj.add_message(self.my_master, str(YES(comms_rcvd['alliance_msg'])))
            # else propose alliance if not already sent
            elif not self.alliance_props_sent and self.master_mode:
                # Send 2-power alliance proposals to all powers
                if not self.alliance_all_in:
                    for other_power in get_other_powers([self.power_name], self.game):
                        alliance_message = ALY([other_power, self.power_name], self.game)
                        comms_obj.add_message(other_power, alliance_message)
                # Send all-power alliance proposals to all powers
                else:
                    alliance_message = ALY(game.get_map_power_names(), self.game)
                    for other_power in get_other_powers([self.power_name], self.game):
                        comms_obj.add_message(other_power, alliance_message)
                self.alliance_props_sent = True
        # If alliance is formed already, depending on master/slave, command or be commanded
        else:
            # Generate support proposal messages
            if not self.support_proposals_sent and self.master_mode:
                self.generate_support_proposals(comms_obj)
                self.support_proposals_sent = True

        # Update all received proposed orders
        self.selected_orders.update_orders(comms_rcvd['orders_proposed'])

        return comms_obj


    def act(self):
        if self.current_phase[-1] == 'M':
            # Fill out orders randomly if not decided already
            filled_out_orders = [random.choice(self.possible_orders[loc]) for loc in
                             self.game.get_orderable_locations(self.power_name)
                             if loc not in self.selected_orders.orders and self.possible_orders[loc]]
            self.selected_orders.add_all_orders(filled_out_orders)
        else:
            random_orders = [random.choice(self.possible_orders[loc]) for loc in
                             self.game.get_orderable_locations(self.power_name)
                             if self.possible_orders[loc]]
            self.selected_orders.add_all_orders(random_orders)

        return self.selected_orders.get_final_orders()

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
                # print(power_name, messages)
                for msg in messages:
                    msg_obj = Message(
                        sender=bot.power_name,
                        recipient=msg['recipient'],
                        message=msg['message'],
                        phase=game.get_current_phase(),
                    )
                    game.add_message(message=msg_obj)
            # print("Submitted orders")
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)
        game.process()

    to_saved_game_format(game, output_path='RandomSupportProposerBot.json')
