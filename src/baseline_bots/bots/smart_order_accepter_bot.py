__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import asyncio
from collections import defaultdict
from enum import Enum
import os
import random
from typing import Dict, List, Optional, Set, Tuple

from DAIDE import FCT, HUH, ORR, PRP, REJ, XDO, YES
from diplomacy import Game, Message
from diplomacy.client.network_game import NetworkGame
from stance_vector import ActionBasedStance, ScoreBasedStance
from tornado import gen

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot
from baseline_bots.parsing_utils import dipnet_to_daide_parsing, parse_proposal_messages
from baseline_bots.randomize_order import (
    lst_to_daide,
    random_list_orders,
    string_to_tuple,
    tuple_to_string,
)
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_best_orders,
    get_order_tokens,
    smart_select_support_proposals,
)

if os.environ.get("DISABLE_ORR") is not None:
    print("Disabling ORR usage")

    def ORR(value):
        return value[0]

    def lst_to_daide(orders: List) -> str:
        """
        This function should take DAIDE orders as a list of strings and wrap them so: FCT ( ORR ( XDO(ORD1) XDO(ORD2) ) )
        """
        daide_ords = "FCT ("
        if orders:
            daide_ords += " XDO (" + orders[0] + ")"
        daide_ords += ")"
        return daide_ords


class Aggressiveness(Enum):
    """
    Enum for aggressiveness of the bot
    """

    aggressive = "aggressive"
    moderate = "moderate"
    friendly = "friendly"


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
        self,
        power_name: str,
        game: Game,
        discount_factor: float = 0.5,
        invasion_coef: float = 1.0,
        conflict_coef: float = 0.5,
        invasive_support_coef: float = 1.0,
        conflict_support_coef: float = 0.5,
        friendly_coef: float = 1.0,
        unrealized_coef: float = 1.0,
        stance_type: str = "A",
        aggressiveness: Optional[Aggressiveness] = Aggressiveness.moderate,
    ) -> None:
        """
        :param power_name: The name of the power
        :param game: Game object
        :param discount_factor: discount factor for ActionBasedStance
        :param test_mode: indicates if this bot is to be executed in test mode or not. In test_mode, async function `send_message` will not be used.
        :param stance_type: indicates if this bot should use ActionBasedStance (A) or ScoreBasedStance (S)
        :param aggressiveness: indicates if this bot should be aggressive (A), moderate (M) or friendly (F). Valid only if stance type is action-based
        """
        super().__init__(power_name, game)
        self.alliance_props_sent = False
        self.discount_factor = discount_factor
        self.invasion_coef = invasion_coef
        self.conflict_coef = conflict_coef
        self.invasive_support_coef = invasive_support_coef
        self.conflict_support_coef = conflict_support_coef
        self.friendly_coef = friendly_coef
        self.unrealized_coef = unrealized_coef
        self.stance_type = stance_type
        self.aggressiveness = aggressiveness
        if self.stance_type == "A":
            if self.aggressiveness == Aggressiveness.aggressive:
                self.stance = ActionBasedStance(
                    power_name,
                    game,
                    invasion_coef=2.0,
                    conflict_coef=1.0,
                    invasive_support_coef=2.0,
                    conflict_support_coef=1.0,
                    friendly_coef=1.0,
                    unrealized_coef=1.0,
                    discount_factor=self.discount_factor,
                )
            elif self.aggressiveness == Aggressiveness.moderate:
                # default hyperparameter values for ActionBasedStance module
                self.stance = ActionBasedStance(
                    power_name,
                    game,
                    invasion_coef=1.0,
                    conflict_coef=0.5,
                    invasive_support_coef=1.0,
                    conflict_support_coef=0.5,
                    friendly_coef=1.0,
                    unrealized_coef=1.0,
                    discount_factor=self.discount_factor,
                )
            elif self.aggressiveness == Aggressiveness.friendly:
                self.stance = ActionBasedStance(
                    power_name,
                    game,
                    invasion_coef=0.5,
                    conflict_coef=0.25,
                    invasive_support_coef=0.5,
                    conflict_support_coef=0.25,
                    friendly_coef=0.5,
                    unrealized_coef=1.0,
                    discount_factor=self.discount_factor,
                )
            elif self.aggressiveness is None:
                self.stance = ActionBasedStance(
                    power_name,
                    game,
                    invasion_coef=self.invasion_coef,
                    conflict_coef=self.conflict_coef,
                    invasive_support_coef=self.invasive_support_coef,
                    conflict_support_coef=self.conflict_support_coef,
                    friendly_coef=self.friendly_coef,
                    unrealized_coef=self.unrealized_coef,
                    discount_factor=self.discount_factor,
                )
            else:
                raise ValueError(
                    f"{Aggressiveness.__name__} should be {Aggressiveness.aggressive.value}, "
                    f"{Aggressiveness.moderate.value} or {Aggressiveness.friendly.value}. "
                    f"{self.aggressiveness!r} is not valid."
                )
        elif self.stance_type == "S":
            self.stance = ScoreBasedStance(power_name, game)
        else:
            raise ValueError(f"{self.stance_type!r} is not a valid stance type")
        self.opponents = sorted(
            power for power in game.get_map_power_names() if power != self.power_name
        )
        self.alliances_prps = defaultdict(list)
        self.peace_prps = defaultdict(list)
        self.rollout_length = 1
        self.rollout_n_order = 10
        self.allies_influence = set()
        self.orders = None
        self.my_influence = set()
        self.ally_threshold = 1.0
        self.enemy_threshold = -0.5
        self.accept_alliance_threshold = 5 * self.enemy_threshold
        self.accept_peace_threshold = 5 * self.enemy_threshold
        self.alliance_score = 2.5 * self.ally_threshold
        self.peace_score = 0.5 + self.ally_threshold
        self.allies = []
        self.foes = []
        self.neutral = []

    async def send_message(
        self, recipient: str, message: str, msg_data: MessagesData
    ) -> None:
        """
        Send message asynchronously to the server while the bot is still processing

        :param recipient: The name of the recipient power
        :param message: Message to be sent
        :param msg_data: MessagesData object containing set of all messages
        """
        msg_obj = Message(
            sender=self.power_name,
            recipient=recipient,
            message=message,
            phase=self.game.get_current_phase(),
        )
        message_already_exists = msg_data.add_message(
            msg_obj.recipient, msg_obj.message, allow_duplicates=False
        )
        if message_already_exists:
            return
        # Messages should not be sent in local games, only stored
        if isinstance(self.game, NetworkGame):
            await self.game.send_game_message(message=msg_obj)

    async def send_intent_log(self, log_msg: str) -> None:
        # Intent logging should not be sent in local games
        if not isinstance(self.game, NetworkGame):
            return
        log_data = self.game.new_log_data(body=log_msg)
        await self.game.send_log_data(log=log_data)

    async def log_stance_change(self, stance_log) -> None:
        for pw in self.opponents:
            await self.send_intent_log(stance_log[self.power_name][pw])

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
                    # Only send one FCT per recipient per phase
                    if any(
                        msg["recipient"] == pow and msg["message"].startswith("FCT")
                        for msg in msgs_data
                    ):
                        continue
                    if pow != self.power_name:
                        await self.send_message(pow, str(orders_decided), msgs_data)

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
                prp_msg = PRP(
                    ORR(
                        [
                            XDO(order)
                            for order in dipnet_to_daide_parsing(orders, self.game)
                        ]
                    )
                )
                if proposer == best_proposer and proposer in self.allies:
                    msg = YES(prp_msg)
                else:
                    msg = REJ(prp_msg)
                await self.send_message(proposer, str(msg), messages)
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
            await self.send_message(sender, str(message), messages_data)

    async def respond_to_alliance_messages(self, messages_data: MessagesData) -> None:
        """
        Send YES confirmation messages to all alliance proposals
        :param messages_data: Message Data object to add messages
        """
        unique_senders = {}
        for sender_message_tuple in self.alliances_prps.values():
            for sender, message in sender_message_tuple:
                unique_senders[sender] = message

        power_stance = self.stance.stance[self.power_name]
        for sender, message in unique_senders.items():
            if sender == self.power_name:
                continue

            # if the stance value is lower than accept_alliance_threshold (-2.5 by default)
            # we will reject the alliance proposal
            if power_stance[sender] <= self.accept_alliance_threshold:
                await self.send_message(sender, str(REJ(message)), messages_data)
                await self.send_intent_log(
                    "I reject the alliance proposal from {} because my stance to {} is no greater than {}".format(
                        sender, sender, self.accept_alliance_threshold
                    )
                )

            # otherwise accept the alliance proposal and update stance to alliance_score (+2.5 by default)
            else:
                await self.send_intent_log(
                    "I accept the alliance proposal from {} because my stance to {} is above {}".format(
                        sender, sender, self.accept_alliance_threshold
                    )
                )
                await self.send_intent_log(
                    "My stance to {} becomes {} after accepting the alliance proposal.".format(
                        sender, self.alliance_score
                    )
                )
                self.stance.update_stance(self.power_name, sender, self.alliance_score)
                await self.send_message(sender, str(YES(message)), messages_data)

        self.update_allies_and_foes()

    async def respond_to_peace_messages(self, messages_data: MessagesData) -> None:
        """
        Send YES confirmation messages to all alliance proposals
        :param messages_data: Message Data object to add messages
        """
        unique_senders = {}
        for sender_message_tuple in self.peace_prps.values():
            for sender, message in sender_message_tuple:
                unique_senders[sender] = message

        power_stance = self.stance.stance[self.power_name]
        for sender, message in unique_senders.items():
            if sender == self.power_name:
                continue

            # if the stance value is lower than accept_peace_threshold (-2.5 by default)
            # we will reject the peace proposal
            if power_stance[sender] <= self.accept_peace_threshold:
                await self.send_message(sender, str(REJ(message)), messages_data)
                await self.send_intent_log(
                    "I reject the peace proposal from {} because my stance to {} is no greater than {}".format(
                        sender, sender, self.accept_peace_threshold
                    )
                )

            # otherwise accept the peace proposal and update stance to peace_score (+1.5 by default)
            else:
                await self.send_intent_log(
                    "I accept the peace proposal from {} because my stance to {} is above {}".format(
                        sender, sender, self.accept_peace_threshold
                    )
                )
                await self.send_intent_log(
                    "My stance to {} becomes {} after accepting the peace proposal.".format(
                        sender, self.peace_score
                    )
                )
                self.stance.update_stance(self.power_name, sender, self.peace_score)
                await self.send_message(sender, str(YES(message)), messages_data)

        self.update_allies_and_foes()

    def is_support_for_selected_orders(self, support_order: str) -> bool:
        """
        Determine if selected support order for neighbour corresponds to a self order selected

        :param support_order: the support order to be determined for correspondence with self orders
        :return: boolean indicating the above mentioned detail
        """
        order_tokens = get_order_tokens(support_order)

        # Fetch our order for which the support order is determined using supported province name
        selected_order = get_order_tokens(
            self.orders.orders[order_tokens[2].split()[1]]
        )

        # Check if the support order is in correspondence with the order we have selected for our province
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
                prov2.upper()
                for prov2 in self.game.map.abut_list(prov)
                if prov2.upper().split("/")[0] not in provs
                and prov2.upper().split("/")[0] in self.allies_influence
            )

        # Agent's alliances provinces set:
        allies_provs = self.get_allies_orderable_locs()

        # Agent's 2-neighbourhood provinces (retained only alliance's provinces)
        n2n_provs = set()
        for prov in n_provs:
            if prov in allies_provs:
                n2n_provs.update(
                    prov2.upper()
                    for prov2 in self.game.map.abut_list(prov)
                    if prov2.upper().split("/")[0] not in provs
                    and prov2.upper().split("/")[0] not in n_provs
                    and prov2.upper().split("/")[0] in self.allies_influence
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

    def update_allies_and_foes(self) -> None:
        power_stance = self.stance.stance[self.power_name]

        self.allies = [
            pow for pow in self.opponents if power_stance[pow] > self.ally_threshold
        ]
        self.foes = [
            pow for pow in self.opponents if power_stance[pow] <= self.enemy_threshold
        ]
        assert self.enemy_threshold < self.ally_threshold
        self.neutral = [
            pow
            for pow in self.opponents
            if self.enemy_threshold < power_stance[pow] <= self.ally_threshold
        ]

    def support_move(self, order: str) -> bool:
        """
        Indicates if order is a support order and is not attacking on one of its provinces

        :param order: the order which is to be determined if it is a support move or not
        """
        order_tokens = get_order_tokens(order)
        return (
            3 <= len(order_tokens) <= 4
            and order_tokens[1] == "S"
            and not self.bad_move(order)
        )

    def cache_allies_influence(self) -> None:
        """Cache allies' influence"""
        self.allies_influence = set()
        for pow in [pow1 for pow1 in self.opponents if pow1 in self.allies]:
            self.allies_influence.update(set(self.game.get_power(pow).influence))

    def get_allies_orderable_locs(self) -> Set[str]:
        """
        Gets provinces which are orderable for the allies

        :return: set of provinces which are orderable for the allies
        """
        provinces = set()
        for ally in [pow1 for pow1 in self.opponents if pow1 in self.allies]:
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
                    raise ValueError("Coding Error")
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
                await self.send_message(recipient, str(suggested_proposals), comms_obj)

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
        if order_token[0].startswith("A") or order_token[0].startswith("F"):
            # for 1 and 2
            if order_token[1].startswith("-"):
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
            if order_token[1].startswith("S"):
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

            if order_token[1][0].startswith("C"):
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
            if current_order != order and not self.is_order_aggressive_to_powers(
                current_order, powers
            ):
                return f"{unit} S {current_order}"

        return f"{unit} H"

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
            # update stance and send logs
            _, stance_log = self.stance.get_stance(self.game, verbose=True)
            yield self.log_stance_change(stance_log)

        elif self.stance_type == "S":
            self.stance.get_stance()

        power_stance = self.stance.stance[self.power_name]
        print(f"Stance vector for {self.power_name}: {power_stance}")

        # get dipnet order
        orders = yield from self.brain.get_orders(self.game, self.power_name)
        orders_data = OrdersData()
        orders_data.add_orders(orders)
        print(f"Fetched orders: {orders}")

        msgs_data = MessagesData()

        for _ in range(3):
            # only in movement phase, we send PRP/ALY/FCT and consider get_best_proposer
            if not self.game.get_current_phase().endswith("M"):
                break

            # sleep randomly for 2-5s before retrieving new messages for the power
            yield asyncio.sleep(random.uniform(2, 5))

            rcvd_messages = self.game.filter_messages(
                messages=self.game.messages, game_role=self.power_name
            )
            rcvd_messages = sorted(rcvd_messages.items())

            # parse the proposal messages received by the bot
            parsed_messages_dict = parse_proposal_messages(
                rcvd_messages, self.game, self.power_name
            )
            valid_proposal_orders = parsed_messages_dict["valid_proposals"]
            invalid_proposal_orders = parsed_messages_dict["invalid_proposals"]
            shared_orders = parsed_messages_dict["shared_orders"]
            other_orders = parsed_messages_dict["other_orders"]
            self.alliances_prps = parsed_messages_dict["alliance_proposals"]

            # include base order to prp_orders.
            # This is to avoid having double calculation for the best list of orders between (self-generated) base orders vs proposal orders
            # e.g. if we are playing as ENG and the base orders are generated from DipNet, we would want to consider
            # if there is any better proposal orders that has a state value more than ours, then do it. If not, just follow the base orders.
            valid_proposal_orders[self.power_name] = orders

            self.update_allies_and_foes()

            best_proposer, best_orders = yield from get_best_orders(
                self, valid_proposal_orders, shared_orders
            )

            # add orders

            orders_data.add_orders(best_orders, overwrite=True)
            self.orders = orders_data

            # Intent message and filter aggressive moves to allies are disabled in S1901M
            if self.game.get_current_phase() != "S1901M":
                msg_allies = ",".join(self.allies) if self.allies else "no one"
                msg_foes = ",".join(self.foes) if self.foes else "no one"
                msg_neutral = ",".join(self.neutral) if self.neutral else "no one"
                stance_message = (
                    f"From my stance vector perspective, I see {msg_allies} as my allies, "
                    f"{msg_foes} as my foes and I am indifferent towards {msg_neutral}"
                )
                yield self.send_intent_log(stance_message)

                # filter out aggressive orders to allies
                if int(self.game.get_current_phase()[1:5]) < 1909:
                    yield self.replace_aggressive_order_to_allies()
            # Refresh local copy of orders to include replacements
            orders_data = self.orders

            # generate messages for FCT sharing info orders
            msgs_data = yield self.gen_messages(
                orders_data.get_list_of_orders(), msgs_data
            )

            # send ALY requests at the start of the game
            if self.game.phase == "SPRING 1901 MOVEMENT":
                for pow in self.opponents:
                    vss = [country[:3] for country in self.opponents if country != pow]
                    vss_str = " ".join(vss)
                    yield self.send_message(
                        pow,
                        f"PRP (ALY ({self.power_name[:3]} {pow[:3]}) VSS ({vss_str}))",
                        msgs_data,
                    )

            yield self.respond_to_invalid_orders(invalid_proposal_orders, msgs_data)

            # respond to to alliance message and update stance & allies
            yield self.respond_to_alliance_messages(msgs_data)

            # respond to to peace message and update stance & allies
            yield self.respond_to_peace_messages(msgs_data)

            # generate proposal response YES/NO to allies
            msgs_data = yield self.gen_proposal_reply(
                best_proposer, valid_proposal_orders, msgs_data
            )

            # randomize dipnet orders and send random orders to enemies
            dipnet_ords = list(self.orders.orders.values())
            lst_style_orders = dipnet_to_daide_parsing(dipnet_ords, self.game)
            lst_rand = list(
                map(lambda st: string_to_tuple(f"({st})"), lst_style_orders)
            )

            try:
                randomized_orders = random_list_orders(lst_rand)
                random_str_orders = list(map(tuple_to_string, randomized_orders))
                daide_orders = lst_to_daide(random_str_orders)
                print(f">>> {self.power_name} Actual Orders", dipnet_ords)
                print(
                    f">>> {self.power_name} Random Orders to {self.foes}", daide_orders
                )
                for foe in self.foes:
                    # Only send one FCT per recipient per phase
                    if any(
                        msg["recipient"] == foe and msg["message"].startswith("FCT")
                        for msg in msgs_data
                    ):
                        continue
                    yield self.send_message(foe, daide_orders, msgs_data)

            except Exception as e:
                print("Raised Exception in order randomization code block")
                print(e)
                print("Catching the error and resuming operations")

            # generate support proposals to allies
            yield self.generate_support_proposals(msgs_data)

        return {"messages": msgs_data, "orders": orders_data.get_list_of_orders()}
