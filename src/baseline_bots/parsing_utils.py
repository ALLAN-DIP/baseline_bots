"""
Some quickly built parsing utils mostly for DAIDE stuff
"""

__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Union

from DAIDE.utils.exceptions import ParseError
from diplomacy import Game, Message

from baseline_bots.utils import *


def dipnet_to_daide_parsing(
    dipnet_style_order_strs: List[Union[str, Tuple[str, str]]],
    game: Game,
    unit_power_tuples_included=False,
) -> List[str]:
    """
    Convert dipnet style single order to DAIDE style order. Needs game instance to determine the powers owning the units

    More details here: https://docs.google.com/document/d/16RODa6KDX7vNNooBdciI4NqSVN31lToto3MLTNcEHk0/edit?usp=sharing

    :param dipnet_style_order_strs: dipnet style list of orders to be converted to DAIDE. Either in format: {"RUSSIA": ["A SEV - RUM"]} or {"RUSSIA": [("A SEV - RUM", "RUS")]}
    :param game: game instance
    :param unit_power_tuples_included: this means the unit power will also be included in the input dipnet_style_order_strs along with the orders like this: ("A SEV - RUM", "RUS")
    :return: DAIDE style order string
    """

    def expand_prov_coast(prov: str) -> str:
        """
        If `prov` is a coastal province, expand coastal province from dipnet to DAIDE format
        Else return original `prov`
        E.g.
        BUL/EC         --> BUL ECS
        STP/SC         --> STP SCS
        PAR            --> PAR
        """
        if "/" in prov:
            prov = prov.replace("/", " ")
            prov = prov + "S"
            prov = "(" + prov + ")"
        return prov

    def daidefy_suborder(dipnet_suborder: str) -> str:
        """
        Translates dipnet style units to DAIDE style units
        E.g. for initial game state
        A BUD       --> AUS AMY BUD
        F TRI       --> AUS FLT TRI
        A PAR       --> FRA AMY PAR
        A MAR       --> FRA AMY MAR

        :param dipnet_suborder: dipnet suborder to be encoded
        :return: DAIDE-style suborder
        """
        if dipnet_suborder in unit_game_mapping:
            power = unit_game_mapping[dipnet_suborder]
        elif game._unit_owner(dipnet_suborder):
            power = game._unit_owner(dipnet_suborder)
        else:
            print(
                f"ALLAN: error from parsing_utils.dipnet_to_daide_parsing: unit {dipnet_suborder} not present in unit_game_mapping"
            )
            return None

        unit_type = "AMY" if dipnet_suborder[0] == "A" else "FLT"
        unit = expand_prov_coast(dipnet_suborder.split()[-1])

        return (
            "("
            + (
                " ".join(
                    [
                        power,
                        unit_type,
                        unit,
                    ]
                )
            )
            + ")"
        )

    convoy_map = defaultdict(list)
    dipnet_style_order_strs_tokens = [None for _ in range(len(dipnet_style_order_strs))]

    # Convert strings to order tokens and store a dictionary mapping of armies to be convoyed and fleets helping to convoy
    for i in range(len(dipnet_style_order_strs)):
        if not (unit_power_tuples_included):
            dipnet_style_order_strs_tokens[i] = get_order_tokens(
                dipnet_style_order_strs[i]
            )
            if dipnet_style_order_strs_tokens[i][1] == "C":
                convoy_map[
                    dipnet_style_order_strs_tokens[i][2]
                    + dipnet_style_order_strs_tokens[i][3]
                ].append(dipnet_style_order_strs_tokens[i][0].split()[-1])
        else:  # If unit powers are also included in the input, then use the right values
            dipnet_style_order_strs_tokens[i] = (
                get_order_tokens(dipnet_style_order_strs[i][0]),
                dipnet_style_order_strs[i][1],
            )
            if dipnet_style_order_strs_tokens[i][0][1] == "C":
                convoy_map[
                    dipnet_style_order_strs_tokens[i][0][2]
                    + dipnet_style_order_strs_tokens[i][0][3]
                ].append(dipnet_style_order_strs_tokens[i][0][0].split()[-1])

    daide_orders = []

    # For each order
    for dipnet_order_tokens in dipnet_style_order_strs_tokens:
        try:
            # If unit powers are also included in the input, then update representation
            if unit_power_tuples_included:
                dipnet_order_tokens, unit_power = dipnet_order_tokens

            # Create unit to power mapping for constructing DAIDE tokens
            unit_game_mapping = {}
            for power in list(game.powers.keys()):
                for unit in game.get_units(power):
                    unit_game_mapping[unit] = power[:3]

            # If unit powers are also included in the input, then add the unit - unit power mapping for DAIDE construction
            if unit_power_tuples_included:
                unit_game_mapping[dipnet_order_tokens[0]] = unit_power

            daide_order = []

            if dipnet_order_tokens[0] not in unit_game_mapping:
                continue
            if (
                len(dipnet_order_tokens) >= 3
                and dipnet_order_tokens[2] != "VIA"
                and dipnet_order_tokens[2] not in unit_game_mapping
            ):
                continue

            # Daidefy and add source unit as it is
            if daidefy_suborder(dipnet_order_tokens[0]):
                daide_order.append(daidefy_suborder(dipnet_order_tokens[0]))
            else:
                print(
                    f"ALLAN: error from parsing_utils.dipnet_to_daide_parsing() skipping message: {dipnet_order_tokens}"
                )
                continue
            if dipnet_order_tokens[1] == "S":
                # Support orders
                daide_order.append("SUP")
                if daidefy_suborder(dipnet_order_tokens[2]):
                    daide_order.append(daidefy_suborder(dipnet_order_tokens[2]))
                else:
                    print(
                        f"ALLAN: error from parsing_utils.dipnet_to_daide_parsing() skipping message: {dipnet_order_tokens}"
                    )
                    continue

                if len(dipnet_order_tokens) == 4 and dipnet_order_tokens[3] != "H":
                    daide_order.append("MTO")
                    daide_order.append(
                        expand_prov_coast(dipnet_order_tokens[3].split()[-1])
                    )
                elif len(dipnet_order_tokens) > 4:
                    print(
                        f"ALLAN: error from parsing_utils.dipnet_to_daide_parsing: order {dipnet_order_tokens} is UNEXPECTED. Update code to handle this case!!!"
                    )
                    continue
            elif dipnet_order_tokens[1] == "H":
                # Hold orders
                daide_order.append("HLD")
            elif dipnet_order_tokens[1] == "C":
                # Convoy orders
                daide_order.append("CVY")
                if daidefy_suborder(dipnet_order_tokens[2]):
                    daide_order.append(daidefy_suborder(dipnet_order_tokens[2]))
                else:
                    print(
                        f"ALLAN: error from parsing_utils.dipnet_to_daide_parsing() skipping message: {dipnet_order_tokens}"
                    )
                    continue

                daide_order.append("CTO")
                daide_order.append(
                    expand_prov_coast(dipnet_order_tokens[3].split()[-1])
                )
            elif len(dipnet_order_tokens) >= 3 and dipnet_order_tokens[2] == "VIA":
                # VIA/CTO orders
                daide_order.append("CTO")
                daide_order.append(
                    expand_prov_coast(dipnet_order_tokens[1].split()[-1])
                )
                daide_order.append("VIA")
                if dipnet_order_tokens[0] + dipnet_order_tokens[1] in convoy_map:
                    daide_order.append(
                        f"({' '.join(convoy_map[dipnet_order_tokens[0] + dipnet_order_tokens[1]])})"
                    )
                else:
                    print(
                        f"ALLAN: error parsing_utils.dipnet_to_daide_parsing. Found unexpected order {dipnet_order_tokens} which doesn't have convoying fleet in its own set of orders"
                    )
                    continue
            else:
                # Move orders
                daide_order.append("MTO")
                daide_order.append(
                    expand_prov_coast(dipnet_order_tokens[1].split()[-1])
                )
                if len(dipnet_order_tokens) > 2:
                    print(
                        f"ALLAN: error from parsing_utils.dipnet_to_daide_parsing: order {dipnet_order_tokens} is UNEXPECTED. Update code to handle this case!!!"
                    )
                    continue
            daide_orders.append(" ".join(daide_order))
        except Exception as e:
            print(f"ALLAN: main error from parsing_utils.dipnet_to_daide_parsing()")
            print(e)
            continue
    return daide_orders


def daide_to_dipnet_parsing(daide_style_order_str: str) -> Tuple[str, str]:
    """
    Convert DAIDE style single order to dipnet style order

    More details here: https://docs.google.com/document/d/16RODa6KDX7vNNooBdciI4NqSVN31lToto3MLTNcEHk0/edit?usp=sharing

    :param daide_style_order_str: DAIDE style string to be converted to dipnet style
    :return: dipnet style order string and unit's power name
    """

    def split_into_groups(daide_style_order_str: str) -> List[str]:
        """
        Split the string based on parenthesis or spaces
        E.g.
        "(FRA AMY PAR) SUP (FRA AMY MAR) MTO BUR" --> "FRA AMY PAR", "SUP", "FRA AMY MAR", "MTO", "BUR"

        :param daide_style_order_str: DAIDE style string
        :return: list of strings containing components of the order which makes it easy to convert to dipnet-style order
        """
        brack_cnt = 0
        stack = ""
        grouped_order = []
        for char in daide_style_order_str:
            if char == ")":
                brack_cnt -= 1
            if (brack_cnt == 0 and char == " ") or (brack_cnt == 0 and char == ")"):
                if brack_cnt == 0 and stack:
                    grouped_order.append(stack)
                    stack = ""
            elif char == "(":
                if brack_cnt > 0:
                    stack += char
                brack_cnt += 1
            else:
                stack += char
        if stack:
            grouped_order.append(stack)
        return grouped_order

    def compress_prov_coast(prov: str) -> str:
        """
        If `prov` is a coastal province, compress coastal province from DAIDE to dipnet format
        Else return original `prov`
        E.g.
        BUL ECS         --> BUL/EC
        STP SCS         --> STP/SC
        PAR             --> PAR
        """
        if len(prov.split()) == 2:
            prov = "/".join(prov.split())[:-1]
        return prov

    def dipnetify_suborder(suborder: str) -> str:
        """
        Translates DAIDE style units to dipnet style units

        :param suborder: DAIDE-style suborder to be encoded
        :return: dipnet suborder
        """
        suborder_tokens = split_into_groups(suborder)
        try:
            ans = suborder_tokens[1][0] + " " + compress_prov_coast(suborder_tokens[2])
        except Exception:
            print(
                f"ALLAN: error from parsing_utils.daide_to_dipnet_parsing.dipnetify_suborder() Failed for suborder: {suborder_tokens}"
            )
            ans = suborder_tokens[1][0] + " " + suborder_tokens[2]
        return ans, suborder_tokens[0]

    try:
        daide_style_order_groups = split_into_groups(daide_style_order_str)

        dipnet_order = []

        # Dipnetify source unit
        suborder, unit_power = dipnetify_suborder(daide_style_order_groups[0])
        dipnet_order.append(suborder)
        if daide_style_order_groups[1] == "SUP":
            # Support order
            dipnet_order.append("S")
            dipnet_order.append(dipnetify_suborder(daide_style_order_groups[2])[0])
            if (
                len(daide_style_order_groups) == 5
                and daide_style_order_groups[3] == "MTO"
            ):
                dipnet_order.append("-")
                dipnet_order.append(compress_prov_coast(daide_style_order_groups[4]))
            elif len(daide_style_order_groups) > 5:
                print(
                    f"ALLAN: error from parsing_utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!"
                )
                return None
        elif daide_style_order_groups[1] == "HLD":
            # Hold order
            dipnet_order.append("H")
        elif daide_style_order_groups[1] == "CTO":
            # CTO order
            dipnet_order.append("-")
            dipnet_order.append(compress_prov_coast(daide_style_order_groups[2]))
            dipnet_order.append("VIA")
        elif daide_style_order_groups[1] == "CVY":
            # Convoy order
            dipnet_order.append("C")
            dipnet_order.append(dipnetify_suborder(daide_style_order_groups[2])[0])
            dipnet_order.append("-")
            dipnet_order.append(compress_prov_coast(daide_style_order_groups[4]))
        elif daide_style_order_groups[1] == "MTO":
            # Move orders
            dipnet_order.append("-")
            dipnet_order.append(compress_prov_coast(daide_style_order_groups[2]))
            if len(daide_style_order_groups) > 3:
                print(
                    f"ALLAN: error from parsing_utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!"
                )
                return None
        else:
            print(
                f"ALLAN: error from parsing_utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!"
            )
            return None

        return " ".join(dipnet_order), unit_power
    except Exception as e:
        print(f"ALLAN: error from parsing_utils.daide_to_dipnet_parsing")
        print(e)
        return None


def parse_proposal_messages(
    rcvd_messages: List[Tuple[int, Message]], game: Game, power_name: str
) -> Dict[str, Dict[str, List[str]]]:
    """
    From received messages, extract the proposals (categorize as valid and invalid), shared orders and other orders. Use specified game state and power_name to check for validity of moves

    :param rcvd_messages: list of messages received from other players
    :param game: Game state
    :param power_name: power name against which the validity of moves need to be checked
    :return: dictionary of
        valid proposals,
        invalid proposals,
        shared orders (orders that the other power said it would execute),
        other orders (orders that the other power shared as gossip),
        alliance proposals
    """
    try:
        # Extract messages containing PRP string
        order_msgs = [msg[1] for msg in rcvd_messages if "PRP" in msg[1].message]
        print(f"Received {len(order_msgs)} messages")
        print([(order_msg.sender, order_msg.message) for order_msg in order_msgs])

        # Generate a dictionary of sender to list of orders (dipnet-style) for this sender
        proposals = defaultdict(list)

        invalid_proposals = defaultdict(list)
        valid_proposals = defaultdict(list)
        shared_orders = defaultdict(list)
        other_orders = defaultdict(list)
        alliance_proposals = defaultdict(list)

        for order_msg in order_msgs:
            try:
                if (
                    "AND" in order_msg.message
                ):  # works when AND is present in this format: XDO () AND XDO () AND XDO()
                    daide_style_orders = [
                        order_1
                        for order in (parse_PRP(order_msg.message)).split("AND")
                        for order_1 in parse_arrangement(order.strip(), xdo_only=False)
                    ]
                else:  # works for cases where ORR is present in PRP or nothing is present: ORR ( (XDO()) (XDO()))
                    daide_style_orders = [
                        order
                        for order in parse_arrangement(
                            parse_PRP(order_msg.message), xdo_only=False
                        )
                    ]
                for order_type, order in daide_style_orders:
                    if order_type == "XDO":
                        temp_message = daide_to_dipnet_parsing(order)
                        if temp_message:
                            proposals[order_msg.sender].append(temp_message)
                    elif order_type == "ALY":
                        for ally in parse_alliance_proposal(order, power_name):
                            alliance_proposals[ally].append((order_msg.sender, order))
                    else:
                        other_orders[order_msg.sender].append(order)
            except Exception as e:
                print(
                    f"ALLAN: error from parsing_utils.parse_proposal_messages() Unexpected message format: {order_msg.message}"
                )
                continue

        # Generate set of possible orders for the given power
        orderable_locs = game.get_orderable_locations(power_name)
        all_possible_orders = game.get_all_possible_orders()
        possible_orders = set(
            [
                ord
                for ord_key in all_possible_orders
                for ord in all_possible_orders[ord_key]
                if ord_key in orderable_locs
            ]
        )

        # For the set of proposed moves from each sender, check if the specified orders would be allowed. If not, mark them as invalid.
        for sender in proposals:
            for order, unit_power_name in proposals[sender]:
                if (
                    unit_power_name == power_name[:3]
                ):  # These are supposed to be proposal messages to me
                    if order in possible_orders:  # These would be valid proposals to me
                        valid_proposals[sender].append(order)
                    else:  # These would be invalid proposals
                        invalid_proposals[sender].append((order, unit_power_name))
                elif (
                    unit_power_name == sender[:3]
                ):  # These are supposed to be conditional orders that the sender is going to execute
                    shared_orders[sender].append(order)
                else:
                    other_orders[sender].append(order)

        if other_orders:
            print("ALLAN: Found other orders while extracting proposal messages:")
            print([msg.message for msg in order_msgs])
            print("ALLAN: Other orders found:")
            print(other_orders)

        return {
            "valid_proposals": valid_proposals,
            "invalid_proposals": invalid_proposals,
            "shared_orders": shared_orders,
            "other_orders": other_orders,
            "alliance_proposals": alliance_proposals,
        }
    except Exception as e:
        print(f"ALLAN: main error from parsing_utils.parse_proposal_messages()")
        print(e)
        return {
            "valid_proposals": {},
            "invalid_proposals": {},
            "shared_orders": {},
            "other_orders": {},
            "alliance_proposals": {},
        }
