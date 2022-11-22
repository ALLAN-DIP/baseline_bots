"""
Some functions that generate randomized orders from 
an already existing order / list of orders.
"""

__author__ = "Konstantine Kahadze"
__email__ = "konstantinekahadze@gmail.com"

import random
import re
from typing import List, Tuple

# The comments below signal the formatter not to expand these dicts to multiple lines
# fmt: off

# This dictionary represents every adjacent province and coast from any given province or coast
ADJACENCY = {'ADR': ['ALB', 'APU', 'ION', 'TRI', 'VEN'], 'AEG': ['BUL/SC', 'CON', 'EAS', 'GRE', 'ION', 'SMY'], 'ALB': ['ADR', 'GRE', 'ION', 'SER', 'TRI'], 'ANK': ['ARM', 'BLA', 'CON', 'SMY'], 'APU': ['ADR', 'ION', 'NAP', 'ROM', 'VEN'], 'ARM': ['ANK', 'BLA', 'SEV', 'SMY', 'SYR'], 'BAL': ['BER', 'BOT', 'DEN', 'LVN', 'KIE', 'PRU', 'SWE'], 'BAR': ['NWY', 'NWG', 'STP/NC'], 'BEL': ['BUR', 'ENG', 'HOL', 'NTH', 'PIC', 'RUH'], 'BER': ['BAL', 'KIE', 'MUN', 'PRU', 'SIL'], 'BLA': ['ANK', 'ARM', 'BUL/EC', 'CON', 'RUM', 'SEV'], 'BOH': ['GAL', 'MUN', 'SIL', 'TYR', 'VIE'], 'BOT': ['BAL', 'FIN', 'LVN', 'STP/SC', 'SWE'], 'BRE': ['ENG', 'GAS', 'MAO', 'PAR', 'PIC'], 'BUD': ['GAL', 'RUM', 'SER', 'TRI', 'VIE'], 'BUL/EC': ['BLA', 'CON', 'RUM'], 'BUL/SC': ['AEG', 'CON', 'GRE'], 'BUL': ['AEG', 'BLA', 'CON', 'GRE', 'RUM', 'SER'], 'BUR': ['BEL', 'GAS', 'RUH', 'MAR', 'MUN', 'PAR', 'PIC', 'SWI'], 'CLY': ['EDI', 'LVP', 'NAO', 'NWG'], 'CON': ['AEG', 'BUL/EC', 'BUL/SC', 'BLA', 'ANK', 'SMY'], 'DEN': ['BAL', 'HEL', 'KIE', 'NTH', 'SKA', 'SWE'], 'EAS': ['AEG', 'ION', 'SMY', 'SYR'], 'EDI': ['CLY', 'LVP', 'NTH', 'NWG', 'YOR'], 'ENG': ['BEL', 'BRE', 'IRI', 'LON', 'MAO', 'NTH', 'PIC', 'WAL'], 'FIN': ['BOT', 'NWY', 'STP/SC', 'SWE'], 'GAL': ['BOH', 'BUD', 'RUM', 'SIL', 'UKR', 'VIE', 'WAR'], 'GAS': ['BUR', 'BRE', 'MAO', 'MAR', 'PAR', 'SPA/NC'], 'GRE': ['AEG', 'ALB', 'BUL/SC', 'ION', 'SER'], 'HEL': ['DEN', 'HOL', 'KIE', 'NTH'], 'HOL': ['BEL', 'HEL', 'KIE', 'NTH', 'RUH'], 'ION': ['ADR', 'AEG', 'ALB', 'APU', 'EAS', 'GRE', 'NAP', 'TUN', 'TYS'], 'IRI': ['ENG', 'LVP', 'MAO', 'NAO', 'WAL'], 'KIE': ['BAL', 'BER', 'DEN', 'HEL', 'HOL', 'MUN', 'RUH'], 'LON': ['ENG', 'NTH', 'YOR', 'WAL'], 'LVN': ['BAL', 'BOT', 'MOS', 'PRU', 'STP/SC', 'WAR'], 'LVP': ['CLY', 'EDI', 'IRI', 'NAO', 'WAL', 'YOR'], 'LYO': ['MAR', 'PIE', 'SPA/SC', 'TUS', 'TYS', 'WES'], 'MAO': ['BRE', 'ENG', 'GAS', 'IRI', 'NAF', 'NAO', 'POR', 'SPA/NC', 'SPA/SC', 'WES'], 'MAR': ['BUR', 'GAS', 'LYO', 'PIE', 'SPA/SC', 'SWI'], 'MOS': ['LVN', 'SEV', 'STP', 'UKR', 'WAR'], 'MUN': ['BER', 'BOH', 'BUR', 'KIE', 'RUH', 'SIL', 'TYR', 'SWI'], 'NAF': ['MAO', 'TUN', 'WES'], 'NAO': ['CLY', 'IRI', 'LVP', 'MAO', 'NWG'], 'NAP': ['APU', 'ION', 'ROM', 'TYS'], 'NWY': ['BAR', 'FIN', 'NTH', 'NWG', 'SKA', 'STP/NC', 'SWE'], 'NTH': ['BEL', 'DEN', 'EDI', 'ENG', 'LON', 'HEL', 'HOL', 'NWY', 'NWG', 'SKA', 'YOR'], 'NWG': ['BAR', 'CLY', 'EDI', 'NAO', 'NWY', 'NTH'], 'PAR': ['BUR', 'BRE', 'GAS', 'PIC'], 'PIC': ['BEL', 'BRE', 'BUR', 'ENG', 'PAR'], 'PIE': ['LYO', 'MAR', 'TUS', 'TYR', 'VEN', 'SWI'], 'POR': ['MAO', 'SPA/NC', 'SPA/SC'], 'PRU': ['BAL', 'BER', 'LVN', 'SIL', 'WAR'], 'ROM': ['APU', 'NAP', 'TUS', 'TYS', 'VEN'], 'RUH': ['BEL', 'BUR', 'HOL', 'KIE', 'MUN'], 'RUM': ['BLA', 'BUD', 'BUL/EC', 'GAL', 'SER', 'SEV', 'UKR'], 'SER': ['ALB', 'BUD', 'BUL', 'GRE', 'RUM', 'TRI'], 'SEV': ['ARM', 'BLA', 'MOS', 'RUM', 'UKR'], 'SIL': ['BER', 'BOH', 'GAL', 'MUN', 'PRU', 'WAR'], 'SKA': ['DEN', 'NWY', 'NTH', 'SWE'], 'SMY': ['AEG', 'ANK', 'ARM', 'CON', 'EAS', 'SYR'], 'SPA/NC': ['GAS', 'MAO', 'POR'], 'SPA/SC': ['LYO', 'MAO', 'MAR', 'POR', 'WES'], 'SPA': ['GAS', 'LYO', 'MAO', 'MAR', 'POR', 'WES'], 'STP/NC': ['BAR', 'NWY'], 'STP/SC': ['BOT', 'FIN', 'LVN'], 'STP': ['BAR', 'BOT', 'FIN', 'LVN', 'MOS', 'NWY'], 'SWE': ['BAL', 'BOT', 'DEN', 'FIN', 'NWY', 'SKA'], 'SYR': ['ARM', 'EAS', 'SMY'], 'TRI': ['ADR', 'ALB', 'BUD', 'SER', 'TYR', 'VEN', 'VIE'], 'TUN': ['ION', 'NAF', 'TYS', 'WES'], 'TUS': ['LYO', 'PIE', 'ROM', 'TYS', 'VEN'], 'TYR': ['BOH', 'MUN', 'PIE', 'TRI', 'VEN', 'VIE', 'SWI'], 'TYS': ['ION', 'LYO', 'ROM', 'NAP', 'TUN', 'TUS', 'WES'], 'UKR': ['GAL', 'MOS', 'RUM', 'SEV', 'WAR'], 'VEN': ['ADR', 'APU', 'PIE', 'ROM', 'TRI', 'TUS', 'TYR'], 'VIE': ['BOH', 'BUD', 'GAL', 'TRI', 'TYR'], 'WAL': ['ENG', 'IRI', 'LON', 'LVP', 'YOR'], 'WAR': ['GAL', 'LVN', 'MOS', 'PRU', 'SIL', 'UKR'], 'WES': ['MAO', 'LYO', 'NAF', 'SPA/SC', 'TUN', 'TYS'], 'YOR': ['EDI', 'LON', 'LVP', 'NTH', 'WAL'], 'SWI': ['MAR', 'BUR', 'MUN', 'TYR', 'PIE']}

# This dict defines the type of every province. Every province is either "COAST", "WATER", "LAND" or "SHUT"
TYPES = {'ADR': 'WATER', 'AEG': 'WATER', 'ALB': 'COAST', 'ANK': 'COAST', 'APU': 'COAST', 'ARM': 'COAST', 'BAL': 'WATER', 'BAR': 'WATER', 'BEL': 'COAST', 'BER': 'COAST', 'BLA': 'WATER', 'BOH': 'LAND', 'BOT': 'WATER', 'BRE': 'COAST', 'BUD': 'LAND', 'BUL/EC': 'COAST', 'BUL/SC': 'COAST', 'bul': 'COAST', 'BUR': 'LAND', 'CLY': 'COAST', 'CON': 'COAST', 'DEN': 'COAST', 'EAS': 'WATER', 'EDI': 'COAST', 'ENG': 'WATER', 'FIN': 'COAST', 'GAL': 'LAND', 'GAS': 'COAST', 'GRE': 'COAST', 'HEL': 'WATER', 'HOL': 'COAST', 'ION': 'WATER', 'IRI': 'WATER', 'KIE': 'COAST', 'LON': 'COAST', 'LVN': 'COAST', 'LVP': 'COAST', 'LYO': 'WATER', 'MAO': 'WATER', 'MAR': 'COAST', 'MOS': 'LAND', 'MUN': 'LAND', 'NAF': 'COAST', 'NAO': 'WATER', 'NAP': 'COAST', 'NWY': 'COAST', 'NTH': 'WATER', 'NWG': 'WATER', 'PAR': 'LAND', 'PIC': 'COAST', 'PIE': 'COAST', 'POR': 'COAST', 'PRU': 'COAST', 'ROM': 'COAST', 'RUH': 'LAND', 'RUM': 'COAST', 'SER': 'LAND', 'SEV': 'COAST', 'SIL': 'LAND', 'SKA': 'WATER', 'SMY': 'COAST', 'SPA/NC': 'COAST', 'SPA/SC': 'COAST', 'spa': 'COAST', 'STP/NC': 'COAST', 'STP/SC': 'COAST', 'stp': 'COAST', 'SWE': 'COAST', 'SYR': 'COAST', 'TRI': 'COAST', 'TUN': 'COAST', 'TUS': 'COAST', 'TYR': 'LAND', 'TYS': 'WATER', 'UKR': 'LAND', 'VEN': 'COAST', 'VIE': 'LAND', 'WAL': 'COAST', 'WAR': 'LAND', 'WES': 'WATER', 'YOR': 'COAST', 'SWI': 'SHUT'}

# This nested dict represents the areas that certain types of units can support others into. The format is
# as follows: COMBOS[ SUPPORTING_UNIT_TYPE ] [ SUPPORTED_UNIT_TYPE ] = {SET OF ALL PROVINCE TYPES THAT SUPPORT CAN OCCUR INTO} 
COMBOS = { 
    "FLT" : {"FLT": {"WATER", "COAST"}, "AMY": {"COAST"}},
    "AMY" : {"FLT": {"COAST"}, "AMY": {"LAND", "COAST"}}
}

joiners = {'AND', 'ORR'} # This represents the DAIDE commands that join orders which are handled in this file
# fmt: on


def randomize_order(order: str) -> str:
    """
    This function only takes in non-nested ANDs or ORRs (joiners) and returns a randomized version
    of those orders.

    :param order: A string that contains an joiner followed by orders: "AND ((FRA AMY BUR) MTO PAR) ((FRA AMY PIC) HLD)"
    :type order: str
    :return: A string in the same format as the input with deviant orders.
    :rtype: str
    """
    with_joiner = re.sub(r"[\s+]?(AND|ORR)", r"\1", order)
    joiner = with_joiner[0:3]  # extracts the "AND" or "ORR" string
    just_moves = with_joiner[
        3:
    ]  # removes the "AND" or "ORR" with all preceding whitespace
    with_inner_commas = re.sub(
        r"(.*?[^(])\s+?([^)].*?)", r"\1, \2", just_moves
    )  # adds commas within tuples
    with_outer_commas = re.sub(
        r"(\(\(.+\)\)|\(.+?WVE\)) ", r"\1,", with_inner_commas
    )  # adds commas between strings and tuples
    with_quotes = re.sub(
        r"([(, ])([A-Z]+)([), ])", r"\1'\2'\3", with_outer_commas
    )  # adds quotes around strings
    order_list = eval("[" + with_quotes + "]")  # turns string into list of tuples
    rand = random_list_orders(order_list)  # randomizing orders
    str_orders = joiner + " "
    for ord in rand:
        str_orders += "(" + (tuple_to_string(ord)) + ") "
    return str_orders


def random_list_orders(orders: List) -> List:
    """
    Generates a randomly deviant orders in the same form.

    :param orders: A list of DAIDE orders in the following format. [((FRA AMY PIC) MTO BRE), ((FRA AMY PIC) HLD), ((FRA AMY BUR) HLD)]
    :type orders: List[Tuple]
    :return: The list of deviant orders
    :rtype: List[Tuple]
    """
    correspondences = orders_correspondence(
        orders
    )  # this returns a list of tuples representing correspondences or an empty list

    # if correspondences:
    #     cor_orders = orders.copy()
    #     replacements = (
    #         []
    #     )  # this represents the orders that the corresponding orders will get replaced with
    #     for correspondence in correspondences:
    #         for move in correspondence:
    #             if move[1] == "CTO" or move[1] == "CVY":
    #                 cor_orders.remove(move)  # the corresponding are removed
    #                 replacements.append(
    #                     random_hold((move[0], "HLD"))
    #                 )  # the corresponding order is replaced with a HLD or MTO order
    #             elif move[1] == "SUP":
    #                 cor_orders.remove(move)  # the corresponding are removed
    #                 if (move[2], move[3], move[4]) in cor_orders:
    #                     cor_orders.remove((move[2], move[3], move[4]))
    #                 if len(move) <= 3:  # if it is supporting a hold
    #                     replacements.append((move[2], move[1], move[0]))
    #                 else:  # if it is supporting a move
    #                     replacements.append(
    #                         (move[2], move[1], move[0], move[3], move[4])
    #                     )
    #                     replacements.append(((move[2], move[3], move[4])))

    #     cor_orders = list(
    #         map(lambda order: randomize(order), cor_orders)
    #     )  # all the orders that don't correspond are randomized by themselves
    #     cor_orders.extend(replacements)  # replacements are added back to the list
    #     return cor_orders
    # else:
    cor_orders = list(
        map(lambda order: randomize(order), orders)
    )  # if there are no correspondences, every order is randomized alone
    return cor_orders


def orders_correspondence(orders: List) -> List:
    """
    Checks if there are corresponding orders in the list of orders it
    takes in. Corresponding orders are orders such as (x SUP y MTO LIV)
    and (y MTO LIV). The same principle applies to supported holds and
    convoys.

    :param orders: A list of DAIDE orders in the following format. [((FRA AMY PIC) MTO BRE), ((FRA AMY PIC) HLD), ((FRA AMY BUR) HLD)]
    :type orders: List[Tuple]
    :return: The list of all sets (as tuples) of corresponding orders.
    :rtype: List[Tuple]
    """
    correspondences = []  # a list of tuples represing all correspondences
    for i, order in enumerate(orders):
        if order[1] == "SUP":
            if len(order) > 3:  # if it is supporting a move
                u1, _, u2, _, province = order
                if (u2, "MTO", province) in orders:
                    correspondences.append((order, (u2, "MTO", province)))
            else:  # if it is supporting a hold
                u1, _, u2 = order
                if (u2, "HLD") in orders:
                    correspondences.append((order, (u2, "HLD")))
        elif order[1] == "CVY":
            convoy_moves = filter(  # filter all the convoy related moves
                lambda order: order[1] == "CTO" or order[1] == "CVY", orders
            )
            correspondences.append(tuple(convoy_moves))
    return correspondences


def randomize(order: Tuple) -> Tuple:
    """
    Takes in an order and returns a randomly deviant verson of it.

    :param order: A DAIDE order
    :type order: Tuple
    :return: A deviant order (with some chance of being the same order).
    :rtype: Tuple
    """
    tag = order[1]
    tag_to_func = {
        "MTO": random_movement,
        "RTO": random_movement,
        "HLD": random_hold,
        "SUP": random_support,
        "CVY": random_convoy,
        "CTO": random_convoy_to,
        "WVE": lambda order: order,
        "BLD": lambda order: order,
        "REM": lambda order: order,
        "DSB": lambda order: order,
    }

    return tag_to_func[tag](order)


def random_convoy_to(order: Tuple) -> Tuple:
    """
    This takes a convoy order and returns the longest alternate convoy.

    :param order: A "convoy to" (CTO) order
    :type order: Tuple
    :return: A deviant order (with some chance of being the same order).
    :rtype: Tuple
    """
    (_, _, amy_loc), _, province, _, sea_provinces = order
    if isinstance(sea_provinces, Tuple):
        sea_provinces = list(reversed(sea_provinces))
    else:
        sea_provinces = [sea_provinces]
    for i, sea in enumerate(
        sea_provinces
    ):  # searches through the sea provinces in reversed order to find the longest possible alternate convoy
        # fmt : off
        valid = [
            loc
            for loc in ADJACENCY[sea]
            if TYPES[loc] == "COAST"
            and loc != [province]
            and loc not in ADJACENCY[amy_loc]
        ]  # the location must not be the one the unit is already convoying to
        # fmt: on
        if valid:
            route = tuple(
                (reversed(sea_provinces[i:]))
            )  # the list must be reversed back to the correct order before returning
            return (order[0], "CTO", random.choice(valid), "VIA", route)
    return order


def random_convoy(order: Tuple) -> Tuple:
    """
    This takes in the order and produces a convoy to a different destination if it is possible
    and believable. An unbelievable convoy would be one that convoys a unit to a province the
    unit can move to by itself.

    :param order: A "convoy" (CVY) order
    :type order: Tuple
    :return: A deviant order (with some chance of being the same order).
    :rtype: Tuple
    """
    # fmt: off
    tag = order[1]
    ((flt_country, flt_type, flt_loc), _, (amy_country, amy_type, amy_loc), _, province) = order
    assert (amy_type == "AMY" and flt_type == "FLT"), "The unit type is neither army nor fleet so it is invalid."
    # It is necessary to check whether a possible alternate "convoy-to" location is adjacent to the unit being convoyed
    # since convoying to a province adjacent to you would be less believable
    adj = [loc for loc in ADJACENCY[flt_loc] if TYPES[loc] == "COAST" and loc not in ADJACENCY[amy_loc] and loc != province] 
    # fmt: on
    if adj:  # if valid adjacencies exist
        return (order[0], tag, order[2], "CTO", random.choice(adj))
    else:
        return order


def random_support(order: Tuple) -> Tuple:
    """
    Takes in a support order and returns a believable but randomized version of it.

    :param order: A "support" (SUP) order
    :type order: Tuple
    :return: A deviant order (with some chance of being the same order).
    :rtype: Tuple
    """
    tag = order[1]
    if len(order) <= 3:  # if it is supporting to hold
        # fmt : off
        (
            (_, supporter_type, supporter_loc),
            _,
            (_, supported_type, supported_loc),
        ) = order
        supporter_adjacent, supported_adjacent = (
            ADJACENCY[supporter_loc],
            ADJACENCY[supported_loc],
        )
        dest_choices = COMBOS[supporter_type][
            supported_type
        ]  # Set of possible destinations
        adj_to_both = [
            adjacency
            for adjacency in supporter_adjacent  # this finds all provinces adjacent to the supportee and suporter locations
            if adjacency in supported_adjacent
            and (not dest_choices or TYPES[adjacency] in dest_choices)
        ]
        # fmt: on
        chance_of_move = 0.5  # the chance of a support hold becoming a move is 50/50
        if adj_to_both and random.random() < chance_of_move:
            return (order[0], "SUP", order[2], "MTO", random.choice(adj_to_both))
        else:
            return (
                order[0],
                tag,
                order[2],
            )  # returns the same support hold order if there is no value adjacent to both
    else:  # if it is supporting to move
        # fmt: off
        ((sup_country, sup_type, sup_loc), _, (rec_country, rec_type, rec_loc), _, province) = order
        sup_adjacent, rec_adjacent = ADJACENCY[sup_loc], ADJACENCY[rec_loc] 
        # COMBOS and TYPES must be used to determine the possible locations a unit can support into/from based on the unit type and province type
        dest_choices = COMBOS[sup_type][rec_type]
        adj_to_both = [adjacency for adjacency in sup_adjacent if adjacency in rec_adjacent and adjacency != province and TYPES[adjacency]]
        # fmt: on
        if adj_to_both:
            return (order[0], tag, order[2], "MTO", random.choice(adj_to_both))
        else:
            return order  # returns original order if no "trickier" option is found


def random_movement(order: Tuple, chance_of_move=0.5):
    """
    Takes in a movement order and returns a similar but randomly different version of it.
    This may turn a movement order into a hold order.

    :param order: A "move to" (MTO) or "retreat to" (RTO) order
    :type order: Tuple
    :return: A deviant order (with some chance of being the same order).
    :rtype: Tuple
    """
    (country, unit_type, loc), tag, dest = order
    if (
        random.random() < chance_of_move or tag == "RTO"
    ):  # There is a 50/50 chance of switching a move to a hold, 0 for a retreat since that may make one less believable
        all_adjacent = ADJACENCY[loc].copy()
        if dest in all_adjacent:
            all_adjacent.remove(
                dest
            )  # removing the already picked choice from the possible destinations
        new_dest = random.choice(all_adjacent)
        return ((country, unit_type, loc), tag, new_dest)
    else:
        return ((country, unit_type, loc), "HLD")


def random_hold(order: Tuple, chance_of_move=0.8) -> Tuple:
    """
    Takes in a hold order and returns a move from the same location or possibly
    the same hold order.

    :param order: A "hold" (HLD) order
    :type order: Tuple
    :return: A deviant order (with some chance of being the same order).
    :rtype: Tuple
    """

    if (
        random.random() < chance_of_move
    ):  # The chance of changing the hold to a move is high
        ((country, unit_type, loc), _) = order
        move_loc = random.choice(
            ADJACENCY[loc]
        )  # randomly chooses an adjacent location
        return ((country, unit_type, loc), "MTO", move_loc)
    else:
        return order


def tuple_to_string(order: Tuple) -> str:
    """
    Takes in a tuple representing an order and returns a string
    representing the same order in DAIDE format
    Ex. tuple_to_string((('FRA', 'AMY', 'BUR'), 'MTO', 'PAR'))  -> "(FRA AMY BUR) MTO PAR"

    :param order: A Tuple with the format: (('FRA', 'AMY', 'BUR'), 'MTO', 'PAR')
    :type order: Tuple
    :return: The same order converted to a string in DAIDE format: (FRA AMY BUR) MTO PAR
    :rtype: str
    """
    # fmt: off
    for i, sub in enumerate(order):
        if isinstance(sub, Tuple):  # if a recursive call is necessary to parse a nested tuple
            if i == 0 or i == 1:  # if a comma must be added before the parenthesis
                return (" ".join(str(item) for item in order[:i]) + "(" + tuple_to_string(sub) + ") " + tuple_to_string(order[i + 1 :]))
            else:
                return (" ".join(str(item) for item in order[:i]) + " (" + tuple_to_string(sub) + ") " + tuple_to_string(order[i + 1 :]))

    # otherwise joins the tuple without recursion
    # fmt: on
    return " ".join(str(item) for item in order)


def string_to_tuple(orders: str) -> Tuple:
    """
    Takes as string representing an order in DAIDE format and
    returns a tuple representing the same order.

    :param order: A string with the format: "((FRA AMY BUR) MTO PAR)"
    :type order: str
    :return: A Tuple that captures the structure of the DAIDE syntax through nesting.
    :rtype: Tuple
    """
    with_commas = re.sub(
        r"(.*?[^(])\s+?([^)].*?)", r"\1, \2", orders
    )  # inserts commas in between tuples and strings
    with_quotes = re.sub(
        r"([(, ])([A-Z|\/]+)([), ])", r"\1'\2'\3", with_commas
    )  # inserts quotes around strings
    return eval(with_quotes)


def lst_to_daide(orders: List) -> str:
    """
    This function should take DAIDE orders as a list of strings and wrap them so: FCT ( ORR ( XDO(ORD1) XDO(ORD2) ) )
    """
    daide_ords = "FCT (ORR"
    for ord in orders:
        daide_ords += " (XDO (" + ord + "))"
    daide_ords += ")"
    return daide_ords
