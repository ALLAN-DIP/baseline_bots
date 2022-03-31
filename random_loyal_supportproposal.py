__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

from collections import defaultdict
from lib2to3.pgen2.parse import ParseError

from diplomacy import Message
from diplomacy.agents.baseline_bots.baseline_bot import BaselineBot
import random
from diplomacy.agents.baseline_bots.daide_utils import get_order_tokens, ORR, XDO

from daide_utils import BotReturnData, parse_orr_xdo, parse_alliance_proposal, get_non_aggressive_orders, YES, \
    BotReturnData, get_other_powers, ALY


class RandomLSPBot(BaselineBot):
    """

    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.allies = []
        self.alliance_props_sent = False
        self.alliance_props_ack_to_be_sent = None
        self.alliance_props_ack_recipient = None

    def parse_orders(self, rcvd_messages, ret_obj):
        '''
        possible paths:
          1. alliance proposal received - accept proposal, send YES msg, retain allies names from this message
          2. alliance affirmation receieved - retain allies names from this message
          3. if allies are known, filter orders only from allies' messages and from this point onwards no sending of
               alliance proposals or affirmations
        '''
        # convert to list for sorting/indexing
        rcvd_messages = list(rcvd_messages.items())
        rcvd_messages.sort()

        alliance_msgs = [msg for msg in rcvd_messages if "YES" in msg[1].message or "ALY" in msg[1].message]
        order_msgs = [msg for msg in rcvd_messages if "YES" not in msg[1].message and "ALY" not in msg[1].message]

        if self.allies:
            ret_orders = []
            for _, msg in order_msgs:
                if msg.sender in self.allies:
                    try:
                        ret_orders += parse_orr_xdo(msg.message)

                    except ParseError:
                        pass
                # set the orders
            return ret_orders, []
        elif len(alliance_msgs):
            # print(alliance_msgs)
            last_message = alliance_msgs[-1][1]
            try:
                if "YES" in last_message.message:
                    allies = parse_alliance_proposal(last_message.message[5:-1], self.power_name)
                elif "ALY" in last_message.message:
                    try:
                        allies = parse_alliance_proposal(last_message.message, self.power_name)
                        msg = YES(last_message.message)
                        # ret_obj.add_message(last_message.sender, str(msg))
                        self.alliance_props_ack_to_be_sent = msg
                        self.alliance_props_ack_recipient = last_message.sender
                    except TypeError:
                        print(last_message.message)
                        raise TypeError
                else:
                    allies = []
                return [], allies

            except ParseError:
                pass
        return [], []

    def filter_moves(self, orders):
        '''
        Retain only aggressive/non-aggressive attacks and hold moves
        '''
        # TODO: look into convoy moves
        filtered_orders = []
        filtered_orders_dict = defaultdict(str)
        for order in orders:
            order_tokens = get_order_tokens(order)
            if len(order_tokens) <= 2 and len(order_tokens[0].split()) == 2:
                try:
                    filtered_orders.append(order)
                    filtered_orders_dict[order_tokens[0].split()[1]] = order
                except IndexError:
                    print(order)
                    raise IndexError
        return filtered_orders, filtered_orders_dict

    def get_allies_orderable_locs(self):
        provinces = set()
        for ally in self.allies:
            new_provs = {loc.upper() for loc in self.game.get_orderable_locations(ally)}
            provinces.update(new_provs)
        return provinces

    def generate_support_proposals(self, selected_orders, ret_obj):
        # TODO: Ensure that supporting province and province to be attacked are not owned by the same power
        # TODO: Ensure that attack should not be to a province that the power already owns
        final_messages = defaultdict(list)
        messages = []

        # TODO: Some scenario is getting missed out | Sanity check: If current phase fetched is not matching with server phase, skip execution
        if self.game.get_current_phase()[0] != 'W':
            # TODO: Replace orderable locations with all possible units of a power if needed

            # Agent's provinces
            provs = [loc.upper() for loc in self.game.get_orderable_locations(self.power_name)]

            # Agent's 1-neighbourhood provinces
            n_provs = set()
            for prov in provs:
                n_provs.update(set([prov2.upper() for prov2 in self.game.map.abut_list(prov) if
                                    prov2.upper().split('/')[0] not in provs]))

            # Agent's alliances provinces set:
            allies_provs = self.get_allies_orderable_locs()

            # Agent's 2-neighbourhood provinces (retained only alliance's provinces)
            n2n_provs = set()
            for prov in n_provs:
                if prov in allies_provs:
                    n2n_provs.update(
                        set([prov2.upper() for prov2 in self.game.map.abut_list(prov) if
                             prov2.upper().split('/')[0] not in provs and prov2.upper().split('/')[0] not in n_provs]))

            possible_support_proposals = defaultdict(list)
            for n2n_p in n2n_provs:
                if not (self.possible_orders[n2n_p]):
                    continue
                possible_orders = self.possible_orders[n2n_p]

                for order in possible_orders:
                    order_tokens = get_order_tokens(order)
                    # Skip possible order if it is not a support move
                    if len(order_tokens) <= 1 or order_tokens[1] != 'S':
                        continue

                    # Skip possible order if attacking unit is not in agent's provinces
                    #    or the province to be attacked is not withing agent's 1-neighbourhood provinces
                    if len(order_tokens) != 4 or order_tokens[2].split()[1] not in provs or order_tokens[3].split()[
                        1] not in n_provs:
                        continue

                    # Support Order Pattern
                    # 'A PAR', 'S', 'A MAR', '- BUR'

                    # Skip possible order if the attacking order is not amongst
                    #    the randomly selected orders for the agent
                    # if order_tokens[2].split()[1] not in selected_orders \
                    #         or selected_orders[order_tokens[2].split()[1]].split()[-1] != order_tokens[3].split()[1]:
                    #     continue
                    possible_support_proposals[(order_tokens[2].split()[1], order_tokens[3].split()[1])].append(
                        (order_tokens[0], order))
            self_nonsupport_orders = []
            for attack_key in possible_support_proposals:
                selected_order = random.choice(possible_support_proposals[attack_key])
                if self.game._unit_owner(selected_order[0]) is None:
                    raise "Coding Error"
                final_messages[self.game._unit_owner(selected_order[0]).name].append(selected_order[1])
                self_nonsupport_orders.append(selected_order[1].split(" S ")[1])

            for recipient in final_messages:
                suggested_proposals = ORR(XDO(final_messages[recipient]))
                ret_obj.add_message(recipient, str(suggested_proposals))
            # print(len(final_messages))
            return self_nonsupport_orders
        return []

    def act(self):
        # Return data initialization
        ret_obj = BotReturnData()

        rcvd_messages = self.game.filter_messages(messages = self.game.messages, game_role=self.power_name)

        self.possible_orders = self.game.get_all_possible_orders()

        if self.alliance_props_ack_to_be_sent:
            print("Alliance ack sent")
            ret_obj.add_message(self.alliance_props_ack_recipient, str(self.alliance_props_ack_to_be_sent))
            self.alliance_props_ack_to_be_sent = None

        # parse messages
        rcvd_orders, allies = self.parse_orders(rcvd_messages, ret_obj)

        # select your orders
        random_orders = [random.choice(self.possible_orders[loc]) for loc in
                  self.game.get_orderable_locations(self.power_name)
                  if self.possible_orders[loc]]

        random_nonsupport_orders, random_nonsupport_orders_dict = self.filter_moves(random_orders)



        # if alliance already exists, exec received orders and self random orders
        if self.allies:
            if len(rcvd_orders) > 0:
                print("Orders received")
            # Exec received orders
            ret_obj.add_all_orders(rcvd_orders)

            # Send support proposals for selected random orders
            non_support_orders = self.generate_support_proposals(random_nonsupport_orders_dict, ret_obj)
            ret_obj.add_all_orders(non_support_orders)

            # Exec selected random orders
            ret_obj.add_all_orders(random_nonsupport_orders)


        # else if received new alliance, accept alliance, exec self selected random orders
        elif not self.allies and allies:
            print("Alliance accepted")
            self.allies = allies
            print(self.allies)

            # Send support proposals for selected random orders
            self.generate_support_proposals(random_nonsupport_orders_dict, ret_obj)

            ret_obj.add_all_orders(random_nonsupport_orders)

        # else if alliance proposal not yet sent, propose alliance, exec self selected random orders
        elif not self.alliance_props_sent:
            for other_power in get_other_powers([self.power_name], self.game):
                # encode alliance message in daide syntax
                alliance_message = ALY([other_power, self.power_name], self.game)
                # send the other power an ally request
                ret_obj.add_message(other_power, alliance_message)

            # dont sent alliance props again
            print("Alliances proposed")
            self.alliance_props_sent = True

            ret_obj.add_all_orders(random_nonsupport_orders)

        # else (if alliance proposal sent but no accept messages received), go on execing self random orders
        else:
            print("SHOULD NOT BE EXECINGGGGGGG")
            ret_obj.add_all_orders(random_nonsupport_orders)

        return ret_obj

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
