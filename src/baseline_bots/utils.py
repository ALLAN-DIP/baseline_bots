"""
Some quickly built utils mostly for DAIDE stuff
It would be preferable to use a real DAIDE parser in prod
"""


import asyncio
from collections import defaultdict
import collections.abc
from copy import deepcopy
import os
from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Sequence, Set, Tuple

import daidepp
from daidepp import (
    ALYVSS,
    AND,
    ORR,
    PCE,
    AnyDAIDEToken,
    Arrangement,
    DAIDEGrammar,
    create_daide_grammar,
    create_grammar_from_press_keywords,
    daide_visitor,
)
from daidepp.grammar.grammar import MAX_DAIDE_LEVEL
from diplomacy import Game
from diplomacy.utils import strings
import numpy as np

if TYPE_CHECKING:
    from baseline_bots.bots.dipnet_bot import DipnetBot


POWER_NAMES_DICT = {
    "AUS": "AUSTRIA",
    "ENG": "ENGLAND",
    "FRA": "FRANCE",
    "GER": "GERMANY",
    "ITA": "ITALY",
    "RUS": "RUSSIA",
    "TUR": "TURKEY",
}

# Option for debugging without specialized builds
DEBUG_MODE = False
if os.environ.get("ALLAN_DEBUG") is not None:
    print("Enabling debugging mode")
    DEBUG_MODE = True

MESSAGE_GRAMMAR = create_daide_grammar(level=MAX_DAIDE_LEVEL, string_type="message")
# Grammar for limited DAIDE subset used in communications protocol
LIMITED_MESSAGE_GRAMMAR = create_grammar_from_press_keywords(
    ["ALY_VSS", "AND", "DMZ", "HUH", "NAR", "PCE", "PRP", "REJ", "XDO", "YES"]
)
ALL_GRAMMAR = create_daide_grammar(level=MAX_DAIDE_LEVEL, string_type="all")


def is_valid_daide_message(string: str, grammar: Optional[DAIDEGrammar] = None) -> bool:
    """Determines whether a string is a valid DAIDE message.
    :param string: String to check for valid DAIDE.
    :param grammar: DAIDE grammar to use. Defaults to complete message grammar.
    :return: Whether the string is valid DAIDE or not.
    """
    if grammar is None:
        grammar = MESSAGE_GRAMMAR
    try:
        parse_tree = grammar.parse(string)
        daide_visitor.visit(parse_tree)
    except asyncio.CancelledError:
        raise
    except Exception:
        return False
    return True


def parse_daide(string: str) -> AnyDAIDEToken:
    """Parses a DAIDE string into `daidepp` objects.
    :param string: String to parse into DAIDE.
    :return: Parsed DAIDE object.
    :raises ValueError: If string is invalid DAIDE.
    """
    try:
        parse_tree = ALL_GRAMMAR.parse(string)
        return daide_visitor.visit(parse_tree)
    except asyncio.CancelledError:
        raise
    except Exception as ex:
        raise ValueError(f"Failed to parse DAIDE string: {string!r}") from ex


# Option needed for working better with other performers
USE_LIMITED_DAIDE = False
if os.environ.get("USE_LIMITED_DAIDE") is not None:
    print("Disabling DAIDE usage outside of limited subset")
    USE_LIMITED_DAIDE = True


def optional_ORR(arrangements: Sequence[Arrangement]) -> Arrangement:
    """Wraps a list of arrangements in an `ORR`.
    If the list has a single element, return that element instead.
    :param arrangements: List of arrangements.
    :return: Arrangement object.
    """
    arrangements = sorted(set(arrangements), key=str)
    if len(arrangements) > 1 and not USE_LIMITED_DAIDE:
        return ORR(*arrangements)
    else:
        return arrangements[0]


def optional_AND(arrangements: Sequence[Arrangement]) -> Arrangement:
    """Wraps a list of arrangements in an `AND`.
    If the list has a single element, return that element instead.
    :param arrangements: List of arrangements.
    :return: Arrangement object.
    """
    arrangements = sorted(set(arrangements), key=str)
    if len(arrangements) > 1:
        return AND(*arrangements)
    else:
        return arrangements[0]


def get_order_tokens(order: str) -> List[str]:
    """Retrieves the order tokens used in an order
    e.g. 'A PAR - MAR' would return ['A PAR', '-', 'MAR']
    NOTE: Stolen from diplomacy_research
    """
    # We need to keep 'A', 'F', and '-' in a temporary buffer to concatenate them with the next word
    # We replace 'R' orders with '-'
    # Tokenization would be: 'A PAR S A MAR - BUR' --> 'A PAR', 'S', 'A MAR', '- BUR'
    #                        'A PAR R MAR'         --> 'A PAR', '- MAR'
    buffer, order_tokens = [], []
    for word in order.replace(" R ", " - ").split():
        buffer += [word]
        if word not in {"A", "F", "-"}:
            order_tokens.append(" ".join(buffer))
            buffer = []
    return order_tokens


def get_other_powers(powers: List[str], game: Game) -> Set[str]:
    """
    :return: powers in the game other than those listed
    in the powers parameter
    """
    return set(game.get_map_power_names()) - set(powers)


def parse_arrangement(msg: str) -> List[str]:
    """
    Attempts to parse arrangements (may or may not have ORR keyword)

    Examples when xdo_only = False
    XDO (F BLA - CON) -> ("XDO", "F BLA - CON")
    ORR (XDO ((RUS FLT BLA) MTO CON)) (ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)) (ABC (F BLA - CON))
            -> ("XDO", "(RUS FLT BLA) MTO CON"), ("ALY", "ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)"), ("ABC", "ABC (F BLA - CON)")

    Examples when xdo_only = True
    ORR (XDO(F BLK - CON))(XDO(A RUM - BUD))(XDO(F BLK - BUD))
            -> "F BLK - CON", "A RUM - BUD", "F BLK - BUD"

    :param msg: message to be parsed
    :param xdo_only: flag indicating if subarrangement type should be included in the return structure
    :return: parsed subarrangements
    """
    parsed_msg = parse_daide(msg)
    if isinstance(parsed_msg.arrangement, (daidepp.AND, daidepp.ORR)):
        daide_style_orders = parsed_msg.arrangement.arrangements
    else:
        daide_style_orders = [parsed_msg.arrangement]
    return [str(o) for o in daide_style_orders]


def parse_alliance_proposal(msg: ALYVSS, recipient: str) -> List[str]:
    """Parses an alliance proposal

    E.g. (assuming the receiving country is RUSSIA)
    "ALY (GER RUS) VSS (AUS ENG FRA ITA TUR)" -> [GERMANY]

    :param recipient: the power which has received the alliance proposal
    :return: list of allies in the proposal
    """
    allies = list(msg.aly_powers)

    recipient = recipient[:3]
    if recipient not in allies:
        allies = []
        return allies

    allies.remove(recipient)

    return sorted(POWER_NAMES_DICT[ally] for ally in allies)


def parse_peace_proposal(msg: PCE, recipient: str) -> List[str]:
    """Parses a peace proposal

    E.g. (assuming the receiving country is RUSSIA)
    "PCE (GER RUS)" -> [GERMANY]

    :param recipient: the power which has received the peace proposal
    :return: list of allies in the proposal
    """
    peaces = list(msg.powers)

    recipient = recipient[:3]
    if recipient not in peaces:
        peaces = []
        return peaces

    peaces.remove(recipient)

    return sorted(POWER_NAMES_DICT[pea] for pea in peaces)


def is_order_aggressive(order: str, sender: str, game: Game) -> bool:
    """
    Checks if this is an aggressive order
    :param order: A string order, e.g. "A BUD S F TRI"
    NOTE: Adapted directly from Joy's code
    """
    order_token = get_order_tokens(order)
    if order_token[0].startswith("A") or order_token[0].startswith("F"):
        # get location - add order_token[0] ('A' or 'F') at front to check if it collides with other powers' units
        order_unit = order_token[0][0] + order_token[1][1:]
        # check if loc has some units of other powers on
        for power in game.powers:
            if sender != power and order_unit in game.powers[power].units:
                return True
    return False


def get_non_aggressive_orders(orders: List[str], sender: str, game: Game) -> List[str]:
    """
    :return: all non-aggressive orders in orders
    """
    return [order for order in orders if not is_order_aggressive(order, sender, game)]


def get_province_from_order(order: str) -> str:
    order_tokens = get_order_tokens(order)
    parts = order_tokens[0].split()
    if len(parts) >= 2:
        return parts[1]
    else:
        return order_tokens[0]


class MessagesData(collections.abc.Collection):
    def __init__(self):
        self.messages = []

    def add_message(
        self, recipient: str, message: str, allow_duplicates: bool = True
    ) -> bool:
        pair = {"recipient": recipient, "message": message}
        message_already_exists = pair in self
        if allow_duplicates or not message_already_exists:
            self.messages.append(pair)
        return message_already_exists

    def __contains__(self, item):
        return item in self.messages

    def __iter__(self):
        return iter(self.messages)

    def __len__(self):
        return len(self.messages)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.messages})"


class OrdersData:
    def __init__(self) -> None:
        self.orders: Dict[str, str] = defaultdict(str)

    def add_order(self, order: str) -> None:
        """
        Adds single order

        :param order: order to add
        """
        province = get_province_from_order(order)
        self.orders[province] = order

    def add_orders(self, orders: Sequence[str]) -> None:
        """
        Adds multiple orders

        :param orders: orders to add
        """
        for order in orders:
            self.add_order(order)

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self.orders.values()))

    def __len__(self) -> int:
        return len(self.orders)

    def __bool__(self) -> bool:
        return bool(self.orders)

    def __repr__(self) -> str:
        contents = dict(sorted(self.orders.items()))
        return f"{self.__class__.__name__}({contents})"

    def __str__(self) -> str:
        return str(list(self))


def deepcopy_game(game: Game) -> Game:
    """Fast deep copy implementation, from Paquette's game engine https://github.com/diplomacy/diplomacy"""
    if game.__class__.__name__ != "Game":
        cls = list(game.__class__.__bases__)[0]
        result = cls.__new__(cls)
    else:
        cls = game.__class__
        result = cls.__new__(cls)

    # Deep copying
    for key in game._slots:
        if key in [
            "map",
            "renderer",
            "powers",
            "channel",
            "notification_callbacks",
            "data",
            "__weakref__",
        ]:
            continue
        setattr(result, key, deepcopy(getattr(game, key)))
    result.map = game.map
    result.powers = {}
    for power in game.powers.values():
        result.powers[power.name] = deepcopy(power)
        result.powers[power.name].game = result
    result.role = strings.SERVER_TYPE
    return result


async def get_state_value(
    bot: "DipnetBot", game: Game, power_name: Optional[str], option: str = "default"
) -> int:
    # rollout the game --- orders in rollout are from dipnet
    # state value
    movement_phase = 0
    for i in range(3 * bot.rollout_length):
        if game.get_current_phase().endswith("M"):
            movement_phase += 1
        for power in game.map.powers:
            if option == "samplingbeam":
                list_order, prob_order = await bot.get_brain_beam_orders(game, power)

                if len(list_order) > 0:
                    prob_order = np.array(prob_order)
                    prob_order /= prob_order.sum()
                    orders_index = [i for i in range(len(list_order))]
                    select_index = np.random.choice(orders_index, p=prob_order)
                    orders = list_order[select_index]
                else:
                    orders = await bot.get_brain_orders(game, power)
            elif option == "default":
                orders = await bot.get_brain_orders(game, power)
            else:
                raise ValueError(f"invalid option {option!r}")

            game.set_orders(
                power_name=power,
                orders=orders[: min(bot.rollout_n_order, len(orders))],
            )
        game.process()
        if movement_phase >= bot.rollout_length:
            break
    return (
        len(game.get_centers(power_name))
        + 0.5 * len(game.powers[power_name].units)
        + 0.3 * len(game.get_power(power_name).influence)
    )


async def get_best_orders(
    bot: "DipnetBot",
    proposal_order: Dict[str, List[str]],
    shared_order: Dict[str, List[str]],
) -> Tuple[str, List[str]]:
    """
    input:
        bot: A bot instance e.g. RealPolitik
        proposal_order: a dictionary of key=power name of proposer, value=list of orders. This can include self base order
                        i.e. if a bot is RealPolitik, its base order is from DipNet
        shared_order: a dictionary of key=power name of proposer, value=list of orders. The proposers share info (or orders) about the current turn,
                    where we can use these shared order to our current turn in a simulated game to roll out with most correct info.
    output:
        best_proposer: best power that propose the best orders to a bot, this can be itself
        proposal_order[best_proposer]: the orders from the best proposer
    """
    # initialize state value for each proposal
    state_value = {power: float("-inf") for power in bot.game.powers}

    # get state value for each proposal
    for proposer, unit_orders in proposal_order.items():
        # if there is a proposal from this power
        if unit_orders:
            # simulate game by copying the current one
            simulated_game = deepcopy_game(bot.game)

            # censor aggressive orders
            unit_orders = get_non_aggressive_orders(
                unit_orders, bot.power_name, bot.game
            )

            # set orders as a proposal order
            simulated_game.set_orders(power_name=bot.power_name, orders=unit_orders)

            # consider shared orders in a simulated game
            for other_power in simulated_game.powers:
                # if they are not sharing any info about their orders then assume that they are DipNet-based
                if other_power in shared_order:
                    power_orders = shared_order[other_power]
                else:
                    power_orders = await bot.get_brain_orders(
                        simulated_game, other_power
                    )
                simulated_game.set_orders(power_name=other_power, orders=power_orders)

            # process current turn
            simulated_game.process()

            # rollout and get state value
            state_value[proposer] = await get_state_value(
                bot, simulated_game, bot.power_name
            )

    # get power name that gives the max state value
    best_proposer = max(state_value, key=state_value.get)
    return best_proposer, proposal_order[best_proposer]


def smart_select_support_proposals(
    possible_support_proposals: Dict[str, List[Tuple[str, str, str]]]
) -> Dict[str, List[Tuple[str, str, str]]]:
    optimal_possible_support_proposals = defaultdict(list)
    optimal_ordering_units = set()
    order_proposal_mapping = defaultdict(list)
    for ord_list in possible_support_proposals.values():
        for ordering_unit, move_to_support, order in ord_list:
            order_proposal_mapping[move_to_support].append(
                (ordering_unit, move_to_support, order)
            )
    order_proposal_mapping_sorted = [x for x in order_proposal_mapping.items()]
    order_proposal_mapping_sorted.sort(key=lambda x: len(x[1]), reverse=True)
    for move_to_support, order_list in order_proposal_mapping_sorted:
        for ordering_unit, move_to_support, order in order_list:
            if ordering_unit not in optimal_ordering_units:
                optimal_possible_support_proposals[ordering_unit].append(
                    (ordering_unit, move_to_support, order)
                )
            if len(order_list) > 1:
                optimal_ordering_units.add(ordering_unit)
    return optimal_possible_support_proposals


def neighboring_opps(
    game: Game,
    power_name: str,
    opponents: List[str],
) -> List[str]:
    """Return a list of powers that are neighbors of power_name"""
    neighbors = set()  # set to prevent duplicates
    adj_provs = set()  # provs adjacent to power_name territories
    for prov in game.powers[power_name].influence:
        adj_provs.update(set(x.upper() for x in game.map.abut_list(prov)))

    for opponent in opponents:
        for prov in game.powers[opponent].influence:
            if prov in adj_provs:
                neighbors.add(opponent)
                break
    return sorted(neighbors)
