__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import numpy as np
from DAIDE import FCT, HUH, ORR, PRP, XDO, YES
from diplomacy import Message
from stance_vector import ActionBasedStance, ScoreBasedStance
from tornado import gen

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot
from baseline_bots.parsing_utils import (
    daide_to_dipnet_parsing,
    dipnet_to_daide_parsing,
    parse_proposal_messages,
)
from baseline_bots.randomize_order import (
    lst_to_daide,
    random_list_orders,
    string_to_tuple,
    tuple_to_string,
)
from baseline_bots.utils import (
    REJ,
    MessagesData,
    OrdersData,
    get_best_orders,
    get_order_tokens,
    get_other_powers,
    smart_select_support_proposals,
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

    def __init__(
        self, power_name, game, discount_factor=0.5, test_mode=False, stance_type="A"
    ) -> None:
        """
        :param power_name: The name of the power
        :param game: Game object
        :param discount_factor: discount factor for ActionBasedStance
        :param test_mode: indicates if this bot is to be executed in test mode or not. In test_mode, async function `send_message` will not be used.
        :param stance_type: indicates if this bot should use ActionBasedStance (A) or ScoreBasedStance (S)
        """
        super().__init__(power_name, game)
        self.alliance_props_sent = False
        self.discount_factor = discount_factor
        self.stance_type = stance_type
        if self.stance_type == "A":
            self.stance = ActionBasedStance(
                power_name, game, discount_factor=self.discount_factor
            )
        elif self.stance_type == "S":
            self.stance = ScoreBasedStance(power_name, game)
        self.alliances = defaultdict(list)
        self.rollout_length = 5
        self.rollout_n_order = 5
        self.allies_influence = set()
        self.orders = None
        self.my_influence = set()
        self.ally_threshold = 1.0
        self.enemy_threshold = -0.5
        self.allies = []
        self.foes = []
        self.neutral = []
        self.test_mode = test_mode

    async def send_message(self, recipient: str, message: MessagesData) -> None:
        """
        Send message asynchronously to the server while the bot is still processing

        :param recipient: The name of the recipient power
        :param message: MessagesData object containing set of all messages
        """
        msg_obj = Message(
            sender=self.power_name,
            recipient=recipient,
            message=message,
            phase=self.game.get_current_phase(),
        )
        await self.game.send_game_message(message=msg_obj)

    async def gen_pos_stance_messages(
        self, msgs_data: MessagesData, orders_list: List[str]
    ) -> None:
        """
        Add messages to be sent to powers with positive stance.
        These messages would contain factual information about the orders that current power would execute in current round

        :param msgs_data: MessagesData object containing set of all messages
        :param orders_list: set of orders that are going to be executed by the bot
        """
        if orders_list:
            orders_decided = FCT(
                ORR(
                    [
                        XDO(order)
                        for order in dipnet_to_daide_parsing(orders_list, self.game)
                    ]
                )
            )
            if str(orders_decided) != "FCT ()":
                for pow in self.allies:
                    if pow != self.power_name:
                        msgs_data.add_message(pow, str(orders_decided))
                        if not (self.test_mode):
                            await self.send_message(pow, str(orders_decided))

    async def gen_messages(
        self, orders_list: List[str], msgs_data: MessagesData
    ) -> MessagesData:
        """
        This generates messages to be sent to the other powers.
        Note: Messages are also generated outside of this function invocation flow

        :param orders_list: final list of orders decided by the bot
        :param msgs_data: MessagesData object containing set of all messages
        """
        # generate messages: we should  be sending our true orders to allies (positive stance)
        await self.gen_pos_stance_messages(msgs_data, orders_list)

        return msgs_data

    async def gen_proposal_reply(
        self, best_proposer: str, prp_orders: dict, messages: MessagesData
    ) -> MessagesData:
        """
        Reply back to allies regarding their proposals whether we follow or not follow

        :param best_proposer: the name of the best proposer as determined by the bot in utils.get_best_orders
        :param prp_orders: dictionary of proposed orders
        :param messages: MessagesData object containing set of all messages
        :return: MessagesData object containing set of all messages
        """
        for proposer, orders in prp_orders.items():
            if orders and self.power_name != proposer:
                if proposer == best_proposer and proposer in self.allies:
                    msg = YES(
                        PRP(
                            ORR(
                                [
                                    XDO(order)
                                    for order in dipnet_to_daide_parsing(
                                        orders, self.game
                                    )
                                ]
                            )
                        )
                    )
                else:
                    msg = REJ(
                        PRP(
                            ORR(
                                [
                                    XDO(order)
                                    for order in dipnet_to_daide_parsing(
                                        orders, self.game
                                    )
                                ]
                            )
                        )
                    )
                messages.add_message(proposer, str(msg))
                if not (self.test_mode):
                    await self.send_message(proposer, str(msg))
        return messages

    async def respond_to_invalid_orders(
        self,
        invalid_proposal_orders: Dict[str, List[Tuple[str, str]]],
        messages_data: MessagesData,
    ) -> None:
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
            message = HUH(
                PRP(
                    ORR(
                        [
                            XDO(order)
                            for order in dipnet_to_daide_parsing(
                                invalid_proposal_orders[sender],
                                self.game,
                                unit_power_tuples_included=True,
                            )
                        ]
                    )
                )
            )
            messages_data.add_message(sender, str(message))
            if not (self.test_mode):
                await self.send_message(sender, str(message))

    async def respond_to_alliance_messages(self, messages_data: MessagesData) -> None:
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
            if not (self.test_mode):
                await self.send_message(sender, str(YES(message)))

        if self.alliances:
            print("Alliances accepted")
            print(self.alliances)

    def is_support_for_selected_orders(self, support_order: str) -> bool:
        """
        Determine if selected support order for neighbour corresponds to a self order selected

        :param support_order: the support order to be determined for correspondance with self orders
        :return: boolean indicating the above mentioned detail
        """
        order_tokens = get_order_tokens(support_order)

        # Fetch our order for which the support order is determined using supported province name
        selected_order = get_order_tokens(
            self.orders.orders[order_tokens[2].split()[1]]
        )

        # Check if the support order is in correspondance with the order we have selected for our province
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

    def get_2_neigh_provinces(self) -> Set[str]:
        """
        Determine set of orderable locations of allies which are 1-hop/2-hops away from the current power's orderable locations

        :return: set of orderable locations of neighbouring allies
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

    def bad_move(self, order: str) -> bool:
        """
        If order indicates attack on one of its provinces, return True, else return False

        :param order: the order representing the move which is to be determined if it is bad or not
        :return: boolean indicating the above detail
        """
        order_tokens = get_order_tokens(order)

        if len(order_tokens) == 2:
            # Attack move
            if order_tokens[1].split()[-1] in self.my_influence:
                return True
        elif len(order_tokens) == 4 and order_tokens[1] == "S":
            # Support move
            if order_tokens[3].split()[-1] in self.my_influence:
                return True

        return False

    def support_move(self, order: str) -> bool:
        """
        Indicates if order is a support order and is not attacking on one of its provinces

        :param order: the order which is to be determined if it is a support move or not
        """
        order_tokens = get_order_tokens(order)
        if (
            3 <= len(order_tokens) <= 4
            and order_tokens[1] == "S"
            and not self.bad_move(order)
        ):
            return True
        else:
            return False

    def cache_allies_influence(self) -> None:
        """Cache allies' influence"""
        self.allies_influence = set()
        for pow in [
            pow1
            for pow1 in self.stance.stance[self.power_name]
            if pow1 != self.power_name and pow1 in self.allies
        ]:
            self.allies_influence.update(set(self.game.get_power(pow).influence))

    def get_allies_orderable_locs(self) -> Set[str]:
        """
        Gets provinces which are orderable for the allies

        :return: set of provinces which are orderable for the allies
        """
        provinces = set()
        for ally in [
            pow1
            for pow1 in self.stance.stance[self.power_name]
            if pow1 != self.power_name and pow1 in self.allies
        ]:
            new_provs = {loc.upper() for loc in self.game.get_orderable_locations(ally)}
            provinces.update(new_provs)
        return provinces

    async def generate_support_proposals(
        self, comms_obj: MessagesData
    ) -> Dict[str, str]:
        """
        Using the orders already decided, search the neighbourhood provinces for allies' units and generate support proposals accordingly

        :param comms_obj: MessagesData object
        :return: Dictionary of recipient - support proposals message
        """
        self.possible_orders = self.game.get_all_possible_orders()
        self.cache_allies_influence()
        self.my_influence = set(self.game.get_power(self.power_name).influence)
        final_messages = defaultdict(list)

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

                        # Use neighbour's unit to keep track of multiple support orders possible
                        location_comb = order_tokens[0].split()[1]

                        # Add to list of possible support proposals for this location combination
                        possible_support_proposals[location_comb].append(
                            (order_tokens[0], " ".join(order_tokens[2:]), order)
                        )

            possible_support_proposals = smart_select_support_proposals(
                possible_support_proposals
            )

            for attack_key in possible_support_proposals:
                # For each location, randomly select one of the support orders
                selected_order = random.choice(possible_support_proposals[attack_key])
                if self.game._unit_owner(selected_order[0]) is None:
                    raise "Coding Error"
                final_messages[self.game._unit_owner(selected_order[0]).name].append(
                    selected_order[2]
                )

            for recipient in final_messages:
                # Construct message for each support proposal
                if not (final_messages[recipient]):
                    continue
                suggested_proposals = PRP(
                    ORR(
                        [
                            XDO(ord)
                            for ord in dipnet_to_daide_parsing(
                                final_messages[recipient],
                                self.game,
                                unit_power_tuples_included=False,
                            )
                        ]
                    )
                )
                final_messages[recipient] = str(suggested_proposals)
                comms_obj.add_message(recipient, str(suggested_proposals))
                if not (self.test_mode):
                    await self.send_message(recipient, str(suggested_proposals))

        return final_messages

    def is_order_aggressive_to_powers(self, order: str, powers: List[str]):
        """
        check if the order is aggressive by
        1. to attack ally unit
        2. to move to ally SC
        3. support attack ally unit
        4. support move to ally SC
        5. convoy attack ally unit
        6. convoy move to ally SC

        :param order: an order as string, e.g. "A BUD S F TRI"
        :param powers: powers that we want to check if a bot is having aggressive move to
        :return: Boolean

        """
        order_token = get_order_tokens(order)
        if order_token[0][0] == "A" or order_token[0][0] == "F":
            # for 1 and 2
            if order_token[1][0] == "-":
                # get location - add order_token[0] ('A' or 'F') at front to check if it collides with other powers' units
                order_unit = order_token[0][0] + order_token[1][1:]
                for power in powers:
                    if self.power_name != power:
                        # if the order is to attack allies' units
                        if order_unit in self.game.powers[power].units:
                            return True
                        # if the order is a move to allies' SC
                        if order_token[1][2:] in self.game.powers[power].centers:
                            return True
            # for 3 and 4
            if order_token[1][0] == "S":
                # if support hold
                if len(order_token) == 3:  # ['A BUD', 'S', 'A VIE']
                    return False
                order_unit = order_token[2][0] + order_token[3][1:]
                for power in powers:
                    if self.power_name != power:
                        # if the order is a support to attack allies' units
                        if order_unit in self.game.powers[power].units:
                            return True
                        # if the order is a support move to allies' SC
                        if order_token[3][2:] in self.game.powers[power].centers:
                            return True
                        # for 3 and 4

            if order_token[1][0] == "C":
                # if convoy
                order_unit = order_token[2][0] + order_token[3][1:]
                for power in powers:
                    if self.power_name != power:
                        # if the order is to convoy attack allies' units
                        if order_unit in self.game.powers[power].units:
                            return True
                        # if the order is a convoy move to allies' SC
                        if order_token[3][2:] in self.game.powers[power].centers:
                            return True
        return False

    @gen.coroutine
    def get_non_aggressive_order(self, order: str, powers: List[str]):
        """
        return a non-aggressive order with other options in dipnet beam order, if none left, support its own unit. if none around, support self hold.

        :param order: an order as string, e.g. "A BUD S F TRI"
        :param powers: powers that we want to check if a bot is having aggressive move to
        :return: order

        """
        order_token = get_order_tokens(order)
        unit = order_token[0]
        loc_unit = unit[2:]
        list_order, prob_order = yield self.brain.get_beam_orders(
            self.game, self.power_name
        )

        if len(list_order) > 1:
            for i in range(1, len(list_order)):
                dipnet_order = list_order[i]
                for candidate_order in dipnet_order:
                    if (
                        unit in candidate_order
                        and not self.is_order_aggressive_to_powers(
                            candidate_order, powers
                        )
                    ):
                        return candidate_order

        # if none in dipnet beam orders
        for current_order in self.orders.get_list_of_orders():
            if (
                current_order != order
                and not self.is_order_aggressive_to_powers(current_order, powers)
                and current_order in self.game.get_all_possible_orders()[loc_unit]
            ):
                return unit + " S " + current_order

        return unit + " H"

    @gen.coroutine
    def replace_aggressive_order_to_allies(self):
        """
        replace aggressive orders with non-aggressive orders (in-place replace self.orders)

        :return: nothing
        """
        ally = self.allies

        if not len(ally):
            return
        final_orders = []
        for order in self.orders.get_list_of_orders():
            if self.is_order_aggressive_to_powers(order, ally):
                new_order = yield from self.get_non_aggressive_order(order, ally)
            else:
                new_order = order
            final_orders.append(new_order)

        orders_data = OrdersData()
        orders_data.add_orders(final_orders)
        self.orders = orders_data

    @gen.coroutine
    def __call__(self, rcvd_messages: List[Tuple[int, Message]]):
        # compute pos/neg stance on other bots using Tony's stance vector

        # avoid get_stance in the first phase of game
        if self.game.get_current_phase() != "S1901M" and self.stance_type == "A":
            self.stance.get_stance(self.game)
        elif self.stance_type == "S":
            self.stance.get_stance()
        print(f"Stance vector for {self.power_name}")
        print(self.stance.stance[self.power_name])

        powers = self.stance.stance[self.power_name]

        print("current stance: ", powers)

        # get dipnet order
        orders = yield from self.brain.get_orders(self.game, self.power_name)
        orders_data = OrdersData()
        orders_data.add_orders(orders)

        msgs_data = MessagesData()

        print("debug: Fetched orders", orders)

        # only in movement phase, we send PRP/ALY/FCT and consider get_best_proposer
        if self.game.get_current_phase()[-1] == "M":

            # parse the proposal messages received by the bot
            parsed_messages_dict = parse_proposal_messages(
                rcvd_messages, self.game, self.power_name
            )
            valid_proposal_orders = parsed_messages_dict["valid_proposals"]
            invalid_proposal_orders = parsed_messages_dict["invalid_proposals"]
            shared_orders = parsed_messages_dict["shared_orders"]
            other_orders = parsed_messages_dict["other_orders"]
            self.alliances = parsed_messages_dict["alliance_proposals"]

            # include base order to prp_orders.
            # This is to avoid having double calculation for the best list of orders between (self-generated) base orders vs proposal orders
            # e.g. if we are playing as ENG and the base orders are generated from DipNet, we would want to consider
            # if there is any better proposal orders that has a state value more than ours, then do it. If not, just follow the base orders.
            valid_proposal_orders[self.power_name] = orders

            # fmt: off

            self.allies = [pow for pow in powers if (pow != self.power_name and powers[pow] > self.ally_threshold)]
            self.foes = [pow for pow in powers if (pow != self.power_name and powers[pow] <= self.enemy_threshold)]
            self.neutral = [pow for pow in powers if (pow != self.power_name and powers[pow] > self.enemy_threshold and powers[pow] <= self.ally_threshold)]

            best_proposer, best_orders = yield from get_best_orders(self, valid_proposal_orders, shared_orders)
            
            # add orders
            
            orders_data.add_orders(best_orders, overwrite=True)
            self.orders = orders_data

            # GLOBAL message and filter aggressive moves to allies are disabled in S1901M
            if self.game.get_current_phase()!='S1901M':
                msg_allies, msg_foes, msg_neutral = ','.join(self.allies), ','.join(self.foes), ','.join(self.neutral)
                msgs_data.add_message("GLOBAL", str(f"{self.power_name}: From my stance vector perspective, I see {msg_allies if msg_allies else 'no one'} as my allies, \
                                {msg_foes if msg_foes else 'no one'} as my foes and I am indifferent towards {msg_neutral if msg_neutral else 'no one'}"))
                if not(self.test_mode):
                    yield self.send_message("GLOBAL", str(f"{self.power_name}: From my stance vector perspective, I see {msg_allies if msg_allies else 'no one'} as my allies, \
                                {msg_foes if msg_foes else 'no one'} as my foes and I am indifferent towards {msg_neutral if msg_neutral else 'no one'}"))
            # fmt: on

                # filter out aggressive orders to allies
                yield self.replace_aggressive_order_to_allies()

            # generate messages for FCT sharing info orders
            opps = list(powers.keys()).copy()
            opps.remove(self.power_name) # list of opposing powers
            msgs_data = yield self.gen_messages(orders_data.get_list_of_orders(), msgs_data)
            if self.game.phase == "SPRING 1901 MOVEMENT":
                for pow in opps:
                    vss = [country for country in list(powers.copy().keys()) if country != pow and country != self.power_name]
                    vss_str = " ".join(vss)
                    msgs_data.add_message(pow, f"ALY ({self.power_name} {pow}) VSS ({vss_str})")
                    if not(self.test_mode):
                        yield self.send_message(pow, f"ALY ({self.power_name} {pow}) VSS ({vss_str})")

            # send ALY requests at the start of the game
            yield self.respond_to_invalid_orders(invalid_proposal_orders, msgs_data)
            yield self.respond_to_alliance_messages(msgs_data)
            # generate proposal response YES/NO to allies
            msgs_data = yield self.gen_proposal_reply(
                best_proposer, valid_proposal_orders, msgs_data
            )

            # randomize dipnet orders and send random orders to enemies
            dipnet_ords = list(self.orders.orders.values())
            lst_style_orders = dipnet_to_daide_parsing(dipnet_ords, self.game)
            lst_rand = list(
                map(lambda st: string_to_tuple("(" + st + ")"), lst_style_orders)
            )
            try:
                randomized_orders = random_list_orders(lst_rand)
                random_str_orders = list(
                    map(lambda ord: tuple_to_string(ord), randomized_orders)
                )
                daide_orders = lst_to_daide(random_str_orders)
                print(f">>> {self.power_name} Actual Orders", dipnet_ords)
                print(f">>> {self.power_name} Random Orders to {self.foes}", daide_orders)
                for foe in self.foes:
                    msgs_data.add_message(foe, daide_orders)
                    if not(self.test_mode):
                        yield self.send_message(foe, daide_orders)
            except Exception as e:
                print("Raised Excpetion in order randomization code block")
                print(e)
                print("Catching the error and resuming operations")

            # generate support proposals to allies
            proposals = yield self.generate_support_proposals(msgs_data)

        return {"messages": msgs_data, "orders": orders_data.get_list_of_orders()}
