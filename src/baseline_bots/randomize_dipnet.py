"""
Some functions that generate randomized orders from 
an already existing order / list of orders.
"""

__author__ = "Konstantine Kahadze"
__email__ = "konstantinekahadze@gmail.com"

import random
from typing import List

# the comments below signal the formatter not to expand these dicts to multiple lines
# fmt: off
ADJACENCY = {'ADR': ['ALB', 'APU', 'ION', 'TRI', 'VEN'], 'AEG': ['BUL/SC', 'CON', 'EAS', 'GRE', 'ION', 'SMY'], 'ALB': ['ADR', 'GRE', 'ION', 'SER', 'TRI'], 'ANK': ['ARM', 'BLA', 'CON', 'SMY'], 'APU': ['ADR', 'ION', 'NAP', 'ROM', 'VEN'], 'ARM': ['ANK', 'BLA', 'SEV', 'SMY', 'SYR'], 'BAL': ['BER', 'BOT', 'DEN', 'LVN', 'KIE', 'PRU', 'SWE'], 'BAR': ['NWY', 'NWG', 'STP/NC'], 'BEL': ['BUR', 'ENG', 'HOL', 'NTH', 'PIC', 'RUH'], 'BER': ['BAL', 'KIE', 'MUN', 'PRU', 'SIL'], 'BLA': ['ANK', 'ARM', 'BUL/EC', 'CON', 'RUM', 'SEV'], 'BOH': ['GAL', 'MUN', 'SIL', 'TYR', 'VIE'], 'BOT': ['BAL', 'FIN', 'LVN', 'STP/SC', 'SWE'], 'BRE': ['ENG', 'GAS', 'MAO', 'PAR', 'PIC'], 'BUD': ['GAL', 'RUM', 'SER', 'TRI', 'VIE'], 'BUL/EC': ['BLA', 'CON', 'RUM'], 'BUL/SC': ['AEG', 'CON', 'GRE'], 'BUL': ['AEG', 'BLA', 'CON', 'GRE', 'RUM', 'SER'], 'BUR': ['BEL', 'GAS', 'RUH', 'MAR', 'MUN', 'PAR', 'PIC', 'SWI'], 'CLY': ['EDI', 'LVP', 'NAO', 'NWG'], 'CON': ['AEG', 'BUL/EC', 'BUL/SC', 'BLA', 'ANK', 'SMY'], 'DEN': ['BAL', 'HEL', 'KIE', 'NTH', 'SKA', 'SWE'], 'EAS': ['AEG', 'ION', 'SMY', 'SYR'], 'EDI': ['CLY', 'LVP', 'NTH', 'NWG', 'YOR'], 'ENG': ['BEL', 'BRE', 'IRI', 'LON', 'MAO', 'NTH', 'PIC', 'WAL'], 'FIN': ['BOT', 'NWY', 'STP/SC', 'SWE'], 'GAL': ['BOH', 'BUD', 'RUM', 'SIL', 'UKR', 'VIE', 'WAR'], 'GAS': ['BUR', 'BRE', 'MAO', 'MAR', 'PAR', 'SPA/NC'], 'GRE': ['AEG', 'ALB', 'BUL/SC', 'ION', 'SER'], 'HEL': ['DEN', 'HOL', 'KIE', 'NTH'], 'HOL': ['BEL', 'HEL', 'KIE', 'NTH', 'RUH'], 'ION': ['ADR', 'AEG', 'ALB', 'APU', 'EAS', 'GRE', 'NAP', 'TUN', 'TYS'], 'IRI': ['ENG', 'LVP', 'MAO', 'NAO', 'WAL'], 'KIE': ['BAL', 'BER', 'DEN', 'HEL', 'HOL', 'MUN', 'RUH'], 'LON': ['ENG', 'NTH', 'YOR', 'WAL'], 'LVN': ['BAL', 'BOT', 'MOS', 'PRU', 'STP/SC', 'WAR'], 'LVP': ['CLY', 'EDI', 'IRI', 'NAO', 'WAL', 'YOR'], 'LYO': ['MAR', 'PIE', 'SPA/SC', 'TUS', 'TYS', 'WES'], 'MAO': ['BRE', 'ENG', 'GAS', 'IRI', 'NAF', 'NAO', 'POR', 'SPA/NC', 'SPA/SC', 'WES'], 'MAR': ['BUR', 'GAS', 'LYO', 'PIE', 'SPA/SC', 'SWI'], 'MOS': ['LVN', 'SEV', 'STP', 'UKR', 'WAR'], 'MUN': ['BER', 'BOH', 'BUR', 'KIE', 'RUH', 'SIL', 'TYR', 'SWI'], 'NAF': ['MAO', 'TUN', 'WES'], 'NAO': ['CLY', 'IRI', 'LVP', 'MAO', 'NWG'], 'NAP': ['APU', 'ION', 'ROM', 'TYS'], 'NWY': ['BAR', 'FIN', 'NTH', 'NWG', 'SKA', 'STP/NC', 'SWE'], 'NTH': ['BEL', 'DEN', 'EDI', 'ENG', 'LON', 'HEL', 'HOL', 'NWY', 'NWG', 'SKA', 'YOR'], 'NWG': ['BAR', 'CLY', 'EDI', 'NAO', 'NWY', 'NTH'], 'PAR': ['BUR', 'BRE', 'GAS', 'PIC'], 'PIC': ['BEL', 'BRE', 'BUR', 'ENG', 'PAR'], 'PIE': ['LYO', 'MAR', 'TUS', 'TYR', 'VEN', 'SWI'], 'POR': ['MAO', 'SPA/NC', 'SPA/SC'], 'PRU': ['BAL', 'BER', 'LVN', 'SIL', 'WAR'], 'ROM': ['APU', 'NAP', 'TUS', 'TYS', 'VEN'], 'RUH': ['BEL', 'BUR', 'HOL', 'KIE', 'MUN'], 'RUM': ['BLA', 'BUD', 'BUL/EC', 'GAL', 'SER', 'SEV', 'UKR'], 'SER': ['ALB', 'BUD', 'BUL', 'GRE', 'RUM', 'TRI'], 'SEV': ['ARM', 'BLA', 'MOS', 'RUM', 'UKR'], 'SIL': ['BER', 'BOH', 'GAL', 'MUN', 'PRU', 'WAR'], 'SKA': ['DEN', 'NWY', 'NTH', 'SWE'], 'SMY': ['AEG', 'ANK', 'ARM', 'CON', 'EAS', 'SYR'], 'SPA/NC': ['GAS', 'MAO', 'POR'], 'SPA/SC': ['LYO', 'MAO', 'MAR', 'POR', 'WES'], 'SPA': ['GAS', 'LYO', 'MAO', 'MAR', 'POR', 'WES'], 'STP/NC': ['BAR', 'NWY'], 'STP/SC': ['BOT', 'FIN', 'LVN'], 'STP': ['BAR', 'BOT', 'FIN', 'LVN', 'MOS', 'NWY'], 'SWE': ['BAL', 'BOT', 'DEN', 'FIN', 'NWY', 'SKA'], 'SYR': ['ARM', 'EAS', 'SMY'], 'TRI': ['ADR', 'ALB', 'BUD', 'SER', 'TYR', 'VEN', 'VIE'], 'TUN': ['ION', 'NAF', 'TYS', 'WES'], 'TUS': ['LYO', 'PIE', 'ROM', 'TYS', 'VEN'], 'TYR': ['BOH', 'MUN', 'PIE', 'TRI', 'VEN', 'VIE', 'SWI'], 'TYS': ['ION', 'LYO', 'ROM', 'NAP', 'TUN', 'TUS', 'WES'], 'UKR': ['GAL', 'MOS', 'RUM', 'SEV', 'WAR'], 'VEN': ['ADR', 'APU', 'PIE', 'ROM', 'TRI', 'TUS', 'TYR'], 'VIE': ['BOH', 'BUD', 'GAL', 'TRI', 'TYR'], 'WAL': ['ENG', 'IRI', 'LON', 'LVP', 'YOR'], 'WAR': ['GAL', 'LVN', 'MOS', 'PRU', 'SIL', 'UKR'], 'WES': ['MAO', 'LYO', 'NAF', 'SPA/SC', 'TUN', 'TYS'], 'YOR': ['EDI', 'LON', 'LVP', 'NTH', 'WAL'], 'SWI': ['MAR', 'BUR', 'MUN', 'TYR', 'PIE']}
TYPES = {'ADR': 'WATER', 'AEG': 'WATER', 'ALB': 'COAST', 'ANK': 'COAST', 'APU': 'COAST', 'ARM': 'COAST', 'BAL': 'WATER', 'BAR': 'WATER', 'BEL': 'COAST', 'BER': 'COAST', 'BLA': 'WATER', 'BOH': 'LAND', 'BOT': 'WATER', 'BRE': 'COAST', 'BUD': 'LAND', 'BUL/EC': 'COAST', 'BUL/SC': 'COAST', 'bul': 'COAST', 'BUR': 'LAND', 'CLY': 'COAST', 'CON': 'COAST', 'DEN': 'COAST', 'EAS': 'WATER', 'EDI': 'COAST', 'ENG': 'WATER', 'FIN': 'COAST', 'GAL': 'LAND', 'GAS': 'COAST', 'GRE': 'COAST', 'HEL': 'WATER', 'HOL': 'COAST', 'ION': 'WATER', 'IRI': 'WATER', 'KIE': 'COAST', 'LON': 'COAST', 'LVN': 'COAST', 'LVP': 'COAST', 'LYO': 'WATER', 'MAO': 'WATER', 'MAR': 'COAST', 'MOS': 'LAND', 'MUN': 'LAND', 'NAF': 'COAST', 'NAO': 'WATER', 'NAP': 'COAST', 'NWY': 'COAST', 'NTH': 'WATER', 'NWG': 'WATER', 'PAR': 'LAND', 'PIC': 'COAST', 'PIE': 'COAST', 'POR': 'COAST', 'PRU': 'COAST', 'ROM': 'COAST', 'RUH': 'LAND', 'RUM': 'COAST', 'SER': 'LAND', 'SEV': 'COAST', 'SIL': 'LAND', 'SKA': 'WATER', 'SMY': 'COAST', 'SPA/NC': 'COAST', 'SPA/SC': 'COAST', 'spa': 'COAST', 'STP/NC': 'COAST', 'STP/SC': 'COAST', 'stp': 'COAST', 'SWE': 'COAST', 'SYR': 'COAST', 'TRI': 'COAST', 'TUN': 'COAST', 'TUS': 'COAST', 'TYR': 'LAND', 'TYS': 'WATER', 'UKR': 'LAND', 'VEN': 'COAST', 'VIE': 'LAND', 'WAL': 'COAST', 'WAR': 'LAND', 'WES': 'WATER', 'YOR': 'COAST', 'SWI': 'SHUT'}
COMBOS = {
    "FLT" : {"FLT": {"WATER", "COAST"}, "AMY": {"COAST"}},
    "AMY" : {"FLT": {"COAST"}, "AMY": {"LAND", "COAST"}}
}
# fmt: on


def random_orders(orders: List):
    """
    Takes in a list of orders in the following form:

    [(("FRA", "AMY", "PIC"), "MTO", "PAR"), (("FRA", "AMY", "BUR"), "SUP", ('FRA', 'AMY', "PIC"),"MTO", "PAR")]

    and returns randomly deviant orders in the same form.
    """
    correspondences = orders_correspondence(orders)

    if correspondences:
        new = orders
        replacements = []
        for correspondence in correspondences:
            for move in correspondence:
                if move[1] == "CTO" or move[1] == "CVY":
                    new.remove(move)
                    replacements.append(random_hold((move[0], "HLD")))
                elif move[1] == "SUP":
                    new.remove(move)
                    new.remove((move[2], move[3], move[4]))
                    if len(move) <= 3:  # if it is supporting a hold
                        replacements.append((move[2], move[1], move[0]))
                    else:
                        replacements.append(
                            (move[2], move[1], move[0], move[3], move[4])
                        )
                        replacements.append(((move[4], move[3], move[2])))

        new = list(map(lambda order: randomize(order), new))
        new.extend(replacements)
        return new
    else:
        new = list(map(lambda order: randomize(order), orders))
        return new


def orders_correspondence(orders: List) -> List:
    """
    Checks if there are corresponding orders in the list of orders it
    takes in. Corresponding orders are orders such as (x SUP y MTO LIV)
    and (y MTO LIV). The same principle applies to supported holds and
    convoys.
    """
    correspondences = []
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
            convoy_moves = filter(
                lambda order: order[1] == "CTO" or order[1] == "CVY", orders
            )
            correspondences.append(tuple(convoy_moves))
    return correspondences


def randomize(order: tuple) -> tuple:
    """
    Takes in an order and returns a randomly deviant verson of it.
    """
    tag = order[1]
    tag_to_func = {
        "WVE": {lambda: order},
        "BLD": random_build,
        "REM": random_build,
        "DSB": random_build,
        "MTO": random_movement,
        "RTO": random_movement,
        "HLD": random_hold,
        "SUP": random_support,
        "CVY": random_convoy,
        "CTO": random_convoy_to,
    }

    return tag_to_func[tag](order)


def random_convoy_to(order: tuple) -> tuple:
    """
    This takes a convoy order and returns the longest alternate convoy.
    """
    (_, _, amy_loc), _, province, _, (sea_provinces) = order
    reversed(sea_provinces)
    for i, sea in enumerate(sea_provinces):
        valid = [
            loc
            for loc in ADJACENCY[sea]
            if TYPES[loc] == "COAST"
            and loc != [province]
            and loc not in ADJACENCY[amy_loc]
        ]
        if valid:
            route = sea_provinces[i:]
            reversed(route)
            return (order[0], "CTO", random.choice(valid), "VIA", route)
    return order


def random_convoy(order: tuple) -> tuple:
    """
    This takes in the order and produces a convoy to a different destination if it is possible
    and believable. An unbelievable convoy would be one that convoys a unit to a province the
    unit can move to by itself.
    """
    tag = order[1]
    (
        (amy_country, amy_type, amy_loc),
        _,
        (flt_country, flt_type, flt_loc),
        _,
        province,
    ) = order
    assert amy_type == "AMY" and flt_type == "FLT"
    adj = [
        loc
        for loc in ADJACENCY[flt_loc]
        if TYPES[loc] == "COAST" and loc not in ADJACENCY[amy_loc] and loc != province
    ]
    if adj:
        return (order[0], tag, order[2], "CTO", random.choice(adj))
    else:
        return order


def random_support(order: tuple) -> tuple:
    """
    Takes in a support order and returns a believable but randomized version of it.
    """
    tag = order[1]
    if len(order) <= 3:  # if it is supporting to hold
        (
            (_, supporter_type, supporter_loc),
            _,
            (_, supported_type, supported_loc),
        ) = order
        supporter_adjacent, supported_adjacent = (
            ADJACENCY[supporter_loc],
            ADJACENCY[supported_loc],
        )
        adj_to_both = [
            adjacency
            for adjacency in supporter_adjacent
            if adjacency in supported_adjacent
            and (not dest_choices or TYPES[adjacency] in dest_choices)
        ]
        chance_of_move = 0.5
        dest_choices = COMBOS[supporter_type][supported_type]
        if adj_to_both and random.random() < chance_of_move:
            return (order[0], "SUP", order[2], "MTO", random.choice(adj_to_both))
        else:
            return (order[0], tag, order[2])
    else:  # if it is supporting to move
        (
            (sup_country, sup_type, sup_loc),
            _,
            (rec_country, rec_type, rec_loc),
            _,
            province,
        ) = order
        sup_adjacent, rec_adjacent = ADJACENCY[sup_loc], ADJACENCY[rec_loc]
        dest_choices = COMBOS[sup_type][rec_type]
        adj_to_both = [
            adjacency
            for adjacency in sup_adjacent
            if adjacency in rec_adjacent and adjacency != province and TYPES[adjacency]
        ]
        if adj_to_both:
            return (order[0], tag, order[2], "MTO", random.choice(adj_to_both))
        else:
            return order


def random_movement(order, chance_of_move=0.3):
    """
    Takes in a movement order and returns a similar but randomly different version of it.
    This may turn a movement order into a hold order.
    """
    (country, unit_type, loc), tag, dest = order
    if random.random() < chance_of_move or tag == "RTO":
        all_adjacent = ADJACENCY[loc].copy()
        all_adjacent.remove(dest)
        new_dest = random.choice(all_adjacent)
        return ((country, unit_type, loc), tag, new_dest)
    else:
        return ((country, unit_type, loc), "HLD")


def random_hold(order: tuple, chance_of_move=0.8) -> tuple:
    """
    Takes in a hold order and returns a move from the same location or possibly
    the same hold order.
    """
    if random.random() < chance_of_move:
        ((country, unit_type, loc), _) = order
        move_loc = random.choice(ADJACENCY[loc])
        return ((country, unit_type, loc), "MTO", move_loc)
    else:
        return order


def random_build(order: tuple) -> tuple:
    return order
