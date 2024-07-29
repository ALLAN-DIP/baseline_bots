"""Functions that generate randomized orders from an already existing order or list of orders."""


import random
from typing import Iterable, List, Tuple, Union  # noqa: F401  # pylint: disable=unused-import

from daidepp import (
    BLD,
    CVY,
    DSB,
    HLD,
    MTO,
    REM,
    RTO,
    SUP,
    WVE,
    Command,
    Location,
    MoveByCVY,
)

from chiron_utils.parsing_utils import daidefy_location, dipnetify_location

# The comments below signal the formatter not to expand these dicts to multiple lines
# fmt: off

# This dictionary represents every adjacent province and coast from any given province or coast
ADJACENCY = {
    "ADR": ["ALB", "APU", "ION", "TRI", "VEN"],
    "AEG": ["BUL/SC", "CON", "EAS", "GRE", "ION", "SMY"],
    "ALB": ["ADR", "GRE", "ION", "SER", "TRI"],
    "ANK": ["ARM", "BLA", "CON", "SMY"],
    "APU": ["ADR", "ION", "NAP", "ROM", "VEN"],
    "ARM": ["ANK", "BLA", "SEV", "SMY", "SYR"],
    "BAL": ["BER", "BOT", "DEN", "LVN", "KIE", "PRU", "SWE"],
    "BAR": ["NWY", "NWG", "STP/NC"],
    "BEL": ["BUR", "ENG", "HOL", "NTH", "PIC", "RUH"],
    "BER": ["BAL", "KIE", "MUN", "PRU", "SIL"],
    "BLA": ["ANK", "ARM", "BUL/EC", "CON", "RUM", "SEV"],
    "BOH": ["GAL", "MUN", "SIL", "TYR", "VIE"],
    "BOT": ["BAL", "FIN", "LVN", "STP/SC", "SWE"],
    "BRE": ["ENG", "GAS", "MAO", "PAR", "PIC"],
    "BUD": ["GAL", "RUM", "SER", "TRI", "VIE"],
    "BUL/EC": ["BLA", "CON", "RUM"],
    "BUL/SC": ["AEG", "CON", "GRE"],
    "BUL": ["AEG", "BLA", "CON", "GRE", "RUM", "SER"],
    "BUR": ["BEL", "GAS", "RUH", "MAR", "MUN", "PAR", "PIC"],
    "CLY": ["EDI", "LVP", "NAO", "NWG"],
    "CON": ["AEG", "BUL/EC", "BUL/SC", "BLA", "ANK", "SMY"],
    "DEN": ["BAL", "HEL", "KIE", "NTH", "SKA", "SWE"],
    "EAS": ["AEG", "ION", "SMY", "SYR"],
    "EDI": ["CLY", "LVP", "NTH", "NWG", "YOR"],
    "ENG": ["BEL", "BRE", "IRI", "LON", "MAO", "NTH", "PIC", "WAL"],
    "FIN": ["BOT", "NWY", "STP/SC", "SWE"],
    "GAL": ["BOH", "BUD", "RUM", "SIL", "UKR", "VIE", "WAR"],
    "GAS": ["BUR", "BRE", "MAO", "MAR", "PAR", "SPA/NC"],
    "GRE": ["AEG", "ALB", "BUL/SC", "ION", "SER"],
    "HEL": ["DEN", "HOL", "KIE", "NTH"],
    "HOL": ["BEL", "HEL", "KIE", "NTH", "RUH"],
    "ION": ["ADR", "AEG", "ALB", "APU", "EAS", "GRE", "NAP", "TUN", "TYS"],
    "IRI": ["ENG", "LVP", "MAO", "NAO", "WAL"],
    "KIE": ["BAL", "BER", "DEN", "HEL", "HOL", "MUN", "RUH"],
    "LON": ["ENG", "NTH", "YOR", "WAL"],
    "LVN": ["BAL", "BOT", "MOS", "PRU", "STP/SC", "WAR"],
    "LVP": ["CLY", "EDI", "IRI", "NAO", "WAL", "YOR"],
    "LYO": ["MAR", "PIE", "SPA/SC", "TUS", "TYS", "WES"],
    "MAO": ["BRE", "ENG", "GAS", "IRI", "NAF", "NAO", "POR", "SPA/NC", "SPA/SC", "WES"],
    "MAR": ["BUR", "GAS", "LYO", "PIE", "SPA/SC"],
    "MOS": ["LVN", "SEV", "STP", "UKR", "WAR"],
    "MUN": ["BER", "BOH", "BUR", "KIE", "RUH", "SIL", "TYR"],
    "NAF": ["MAO", "TUN", "WES"],
    "NAO": ["CLY", "IRI", "LVP", "MAO", "NWG"],
    "NAP": ["APU", "ION", "ROM", "TYS"],
    "NWY": ["BAR", "FIN", "NTH", "NWG", "SKA", "STP/NC", "SWE"],
    "NTH": ["BEL", "DEN", "EDI", "ENG", "LON", "HEL", "HOL", "NWY", "NWG", "SKA", "YOR"],
    "NWG": ["BAR", "CLY", "EDI", "NAO", "NWY", "NTH"],
    "PAR": ["BUR", "BRE", "GAS", "PIC"],
    "PIC": ["BEL", "BRE", "BUR", "ENG", "PAR"],
    "PIE": ["LYO", "MAR", "TUS", "TYR", "VEN"],
    "POR": ["MAO", "SPA/NC", "SPA/SC"],
    "PRU": ["BAL", "BER", "LVN", "SIL", "WAR"],
    "ROM": ["APU", "NAP", "TUS", "TYS", "VEN"],
    "RUH": ["BEL", "BUR", "HOL", "KIE", "MUN"],
    "RUM": ["BLA", "BUD", "BUL/EC", "GAL", "SER", "SEV", "UKR"],
    "SER": ["ALB", "BUD", "BUL", "GRE", "RUM", "TRI"],
    "SEV": ["ARM", "BLA", "MOS", "RUM", "UKR"],
    "SIL": ["BER", "BOH", "GAL", "MUN", "PRU", "WAR"],
    "SKA": ["DEN", "NWY", "NTH", "SWE"],
    "SMY": ["AEG", "ANK", "ARM", "CON", "EAS", "SYR"],
    "SPA/NC": ["GAS", "MAO", "POR"],
    "SPA/SC": ["LYO", "MAO", "MAR", "POR", "WES"],
    "SPA": ["GAS", "LYO", "MAO", "MAR", "POR", "WES"],
    "STP/NC": ["BAR", "NWY"],
    "STP/SC": ["BOT", "FIN", "LVN"],
    "STP": ["BAR", "BOT", "FIN", "LVN", "MOS", "NWY"],
    "SWE": ["BAL", "BOT", "DEN", "FIN", "NWY", "SKA"],
    "SYR": ["ARM", "EAS", "SMY"],
    "TRI": ["ADR", "ALB", "BUD", "SER", "TYR", "VEN", "VIE"],
    "TUN": ["ION", "NAF", "TYS", "WES"],
    "TUS": ["LYO", "PIE", "ROM", "TYS", "VEN"],
    "TYR": ["BOH", "MUN", "PIE", "TRI", "VEN", "VIE"],
    "TYS": ["ION", "LYO", "ROM", "NAP", "TUN", "TUS", "WES"],
    "UKR": ["GAL", "MOS", "RUM", "SEV", "WAR"],
    "VEN": ["ADR", "APU", "PIE", "ROM", "TRI", "TUS", "TYR"],
    "VIE": ["BOH", "BUD", "GAL", "TRI", "TYR"],
    "WAL": ["ENG", "IRI", "LON", "LVP", "YOR"],
    "WAR": ["GAL", "LVN", "MOS", "PRU", "SIL", "UKR"],
    "WES": ["MAO", "LYO", "NAF", "SPA/SC", "TUN", "TYS"],
    "YOR": ["EDI", "LON", "LVP", "NTH", "WAL"],
}

# This dict defines the type of every province. Every province is either "COAST", "WATER", or "LAND"
TYPES = {
    "ADR": "WATER", "AEG": "WATER", "ALB": "COAST", "ANK": "COAST", "APU": "COAST", "ARM": "COAST",
    "BAL": "WATER", "BAR": "WATER", "BEL": "COAST", "BER": "COAST", "BLA": "WATER", "BOH": "LAND",
    "BOT": "WATER", "BRE": "COAST", "BUD": "LAND", "BUL/EC": "COAST", "BUL/SC": "COAST",
    "bul": "COAST", "BUR": "LAND", "CLY": "COAST", "CON": "COAST", "DEN": "COAST", "EAS": "WATER",
    "EDI": "COAST", "ENG": "WATER", "FIN": "COAST", "GAL": "LAND", "GAS": "COAST", "GRE": "COAST",
    "HEL": "WATER", "HOL": "COAST", "ION": "WATER", "IRI": "WATER", "KIE": "COAST", "LON": "COAST",
    "LVN": "COAST", "LVP": "COAST", "LYO": "WATER", "MAO": "WATER", "MAR": "COAST", "MOS": "LAND",
    "MUN": "LAND", "NAF": "COAST", "NAO": "WATER", "NAP": "COAST", "NWY": "COAST", "NTH": "WATER",
    "NWG": "WATER", "PAR": "LAND", "PIC": "COAST", "PIE": "COAST", "POR": "COAST", "PRU": "COAST",
    "ROM": "COAST", "RUH": "LAND", "RUM": "COAST", "SER": "LAND", "SEV": "COAST", "SIL": "LAND",
    "SKA": "WATER", "SMY": "COAST", "SPA/NC": "COAST", "SPA/SC": "COAST", "spa": "COAST",
    "STP/NC": "COAST", "STP/SC": "COAST", "stp": "COAST", "SWE": "COAST", "SYR": "COAST",
    "TRI": "COAST", "TUN": "COAST", "TUS": "COAST", "TYR": "LAND", "TYS": "WATER", "UKR": "LAND",
    "VEN": "COAST", "VIE": "LAND", "WAL": "COAST", "WAR": "LAND", "WES": "WATER", "YOR": "COAST",
}

# fmt: on

# This nested dict represents the areas that certain types of units can support others into. The format is
# as follows: COMBOS[ SUPPORTING_UNIT_TYPE ] [ SUPPORTED_UNIT_TYPE ] = {SET OF ALL PROVINCE TYPES THAT SUPPORT CAN OCCUR INTO}
COMBOS = {
    "FLT": {"FLT": {"WATER", "COAST"}, "AMY": {"COAST"}},
    "AMY": {"FLT": {"COAST"}, "AMY": {"LAND", "COAST"}},
}

# This represents the DAIDE commands that join orders which are handled in this file
joiners = {"AND", "ORR"}


def random_list_orders(orders: List[Command]) -> List[Command]:
    """Generates randomly deviant orders in the same forms as the originals.

    Args:
        orders: A list of DAIDE orders.

    Return:
        The list of deviant orders.
    """
    # if there are no correspondences, every order is randomized alone
    orders = list(map(randomize, orders))
    return orders


def randomize(order: Command) -> Command:
    """Takes an order and returns a randomly deviant version of it.

    Args:
        order: A DAIDE order.

    Return:
        A deviant order (with some chance of it being the original order).
    """
    if isinstance(order, (MTO, RTO)):
        return random_movement(order)
    elif isinstance(order, HLD):
        return random_hold(order)
    elif isinstance(order, SUP):
        return random_support(order)
    elif isinstance(order, CVY):
        return random_convoy(order)
    elif isinstance(order, MoveByCVY):
        return random_convoy_to(order)
    elif isinstance(order, (WVE, BLD, REM, DSB)):
        return order
    else:
        raise NotImplementedError(type(order))


def random_convoy_to(order: MoveByCVY) -> MoveByCVY:
    """Converts a convoy order to the longest alternate convoy.

    Args:
        order: A "convoy to" (CTO) order.

    Returns:
        A deviant order (with some chance of it being the original order).
    """
    amy_loc = dipnetify_location(order.unit.location)
    province = dipnetify_location(order.province)
    sea_provinces = [dipnetify_location(Location(sea)) for sea in order.province_seas]
    sea_provinces.reverse()
    for i, sea in enumerate(
        sea_provinces
    ):  # searches through the sea provinces in reversed order to find the longest possible alternate convoy
        # fmt : off
        valid = [
            loc
            for loc in ADJACENCY[sea]
            if TYPES[loc] == "COAST" and loc != province and loc not in ADJACENCY[amy_loc]
        ]  # the location must not be the one the unit is already convoying to
        # fmt: on
        if valid:
            # the list must be reversed back to the correct order before returning
            route: Iterable[str] = reversed(sea_provinces[i:])
            route = (daidefy_location(sea).province for sea in route)
            return MoveByCVY(order.unit, daidefy_location(random.choice(valid)), *route)
    return order


def random_convoy(order: CVY) -> CVY:
    """Generates a random variant of a convoy order.

    This takes in the order and produces a convoy to a different destination if it is possible
    and believable. An unbelievable convoy would be one that convoys a unit to a province the
    unit can move to by itself.

    Args:
        order: A "convoy" (CVY) order.

    Returns:
        A deviant order (with some chance of it being the original order).
    """
    # TODO: Add to `daidepp`?
    if order.convoyed_unit.unit_type != "AMY":
        raise ValueError("The convoyed unit is not an army, so it is invalid.")
    if order.convoying_unit.unit_type != "FLT":
        raise ValueError("The convoying unit is not a fleet, so it is invalid.")
    # It is necessary to check whether a possible alternate "convoy-to" location is adjacent to the unit being convoyed
    # since convoying to a province adjacent to you would be less believable
    flt_loc = dipnetify_location(order.convoying_unit.location)
    amy_loc = dipnetify_location(order.convoyed_unit.location)
    province = dipnetify_location(order.province)
    adj = [
        str(daidefy_location(loc))
        for loc in ADJACENCY[flt_loc]
        if TYPES[loc] == "COAST" and loc not in ADJACENCY[amy_loc] and loc != province
    ]
    if adj:  # if valid adjacencies exist
        return CVY(
            order.convoying_unit,
            order.convoyed_unit,
            daidefy_location(random.choice(adj)),
        )
    else:
        return order


def random_support(order: SUP) -> SUP:
    """Generates a believable but randomized version of a support order.

    Args:
        order: A "support" (SUP) order.

    Returns:
        A deviant order (with some chance of it being the original order).
    """
    if order.province_no_coast is None:  # if it is supporting to hold
        # fmt : off
        supporter_type = order.supporting_unit.unit_type
        supporter_loc = dipnetify_location(order.supporting_unit.location)
        supported_type = order.supported_unit.unit_type
        supported_loc = dipnetify_location(order.supported_unit.location)
        supporter_adjacent, supported_adjacent = (
            ADJACENCY[supporter_loc],
            ADJACENCY[supported_loc],
        )
        dest_choices = COMBOS[supporter_type][supported_type]  # Set of possible destinations
        adj_to_both = [
            daidefy_location(adjacency).province
            for adjacency in supporter_adjacent  # this finds all provinces adjacent to the supportee and suporter locations
            if adjacency in supported_adjacent
            and (not dest_choices or TYPES[adjacency] in dest_choices)
        ]
        # fmt: on
        chance_of_move = 0.5  # the chance of a support hold becoming a move is 50/50
        if adj_to_both and random.random() < chance_of_move:
            return SUP(order.supporting_unit, order.supported_unit, random.choice(adj_to_both))
        else:
            # returns the same support hold order if there is no value adjacent to both
            return order
    else:  # if it is supporting to move
        sup_type = order.supporting_unit.unit_type
        sup_loc = dipnetify_location(order.supporting_unit.location)
        rec_type = order.supported_unit.unit_type
        rec_loc = dipnetify_location(order.supported_unit.location)
        province = dipnetify_location(Location(order.province_no_coast))
        sup_adjacent, rec_adjacent = ADJACENCY[sup_loc], ADJACENCY[rec_loc]
        # COMBOS and TYPES must be used to determine the possible locations a unit can support into/from based on the unit type and province type
        dest_choices = COMBOS[sup_type][rec_type]
        adj_to_both = [
            daidefy_location(adjacency).province
            for adjacency in sup_adjacent
            if adjacency in rec_adjacent and adjacency != province and TYPES[adjacency]
        ]
        if adj_to_both:
            return SUP(order.supporting_unit, order.supported_unit, random.choice(adj_to_both))
        else:
            return order  # returns original order if no "trickier" option is found


def random_movement(order: Union[MTO, RTO], chance_of_move: float = 0.5) -> Union[MTO, RTO, HLD]:
    """Generates a believable but randomized version of a move order.

    Takes in a movement order and returns a similar but randomly different version of it.
    This may turn a movement order into a hold order.

    Args:
        order: A "move to" (MTO) or "retreat to" (RTO) order.
        chance_of_move: Probability that the move order will remain a move order.

    Returns:
        A deviant order (with some chance of it being the original order).
    """
    unit = order.unit
    if random.random() < chance_of_move or isinstance(
        order, RTO
    ):  # There is a 50/50 chance of switching a move to a hold, 0 for a retreat since that may make one less believable
        loc = dipnetify_location(unit.location)
        dest = dipnetify_location(order.location)
        all_adjacent = ADJACENCY[loc].copy()
        if dest in all_adjacent:
            all_adjacent.remove(
                dest
            )  # removing the already picked choice from the possible destinations
        new_dest = random.choice(all_adjacent)
        return type(order)(unit, daidefy_location(new_dest))
    else:
        return HLD(unit)


def random_hold(order: HLD, chance_of_move: float = 0.8) -> Union[MTO, HLD]:
    """Generates a believable but randomized version of a hold order.

    Takes in a hold order and returns a move from the same location or possibly the same hold order.

    Args:
        order: A "hold" (HLD) order.
        chance_of_move: Probability that the hold order will become a move order.

    Returns:
        A deviant order (with some chance of it being the original order).
    """
    if random.random() < chance_of_move:  # The chance of changing the hold to a move is high
        loc = dipnetify_location(order.unit.location)
        move_loc = random.choice(ADJACENCY[loc])  # randomly chooses an adjacent location
        return MTO(order.unit, daidefy_location(move_loc))
    else:
        return order
