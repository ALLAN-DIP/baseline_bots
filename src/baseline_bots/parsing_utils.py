"""
Some quickly built utils mostly for DAIDE stuff
"""

__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"
import re
from collections import defaultdict
from typing import Dict, List, Tuple

from DAIDE.utils.exceptions import ParseError
from diplomacy import Game, Message
from baseline_bots.utils import *

def dipnet_to_daide_parsing(dipnet_style_order_strs: List[str], game: Game) -> List[str]:
    """
    Convert dipnet style single order to DAIDE style order. Needs game instance to determine the powers owning the units

    More details here: https://docs.google.com/document/d/16RODa6KDX7vNNooBdciI4NqSVN31lToto3MLTNcEHk0/edit?usp=sharing

    :param dipnet_style_order_strs: dipnet style list of orders to be converted to DAIDE
    :param game: game instance
    :return: DAIDE style order string
    """
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
        if dipnet_suborder not in unit_game_mapping:
            raise Exception(f"error from utils.dipnet_to_daide_parsing: unit {dipnet_suborder} not present in unit_game_mapping")
        return "(" + (" ".join(
            [
                unit_game_mapping[dipnet_suborder],
                "AMY" if dipnet_suborder[0] == "A" else "FLT",
                dipnet_suborder.split()[-1]
            ]
        ) ) + ")"
    
    convoy_map = defaultdict(list)
    dipnet_style_order_strs_tokens = [None for _ in range(len(dipnet_style_order_strs))]

    # Convert strings to order tokens and store a dictionary mapping of armies to be convoyed and fleets helping to convoy
    for i in range(len(dipnet_style_order_strs)):
        dipnet_style_order_strs_tokens[i] = get_order_tokens(dipnet_style_order_strs[i])
        if dipnet_style_order_strs_tokens[i][1] == 'C':
            convoy_map[dipnet_style_order_strs_tokens[i][2] + dipnet_style_order_strs_tokens[i][3]].append(dipnet_style_order_strs_tokens[i][0].split()[-1])
    
    daide_orders = []

    # For each order
    for dipnet_order_tokens in dipnet_style_order_strs_tokens:

        # Create unit to power mapping for constructing DAIDE tokens
        unit_game_mapping = {}
        for power in list(game.powers.keys()):
            for unit in game.get_units(power):
                unit_game_mapping[unit] = power[:3]

        daide_order = []

        # Daidefy and add source unit as it is
        daide_order.append(daidefy_suborder(dipnet_order_tokens[0]))
        if dipnet_order_tokens[1] == "S":
            # Support orders
            daide_order.append("SUP")
            daide_order.append(daidefy_suborder(dipnet_order_tokens[2]))
            if len(dipnet_order_tokens) == 4 and dipnet_order_tokens[3] != "H":
                daide_order.append("MTO")
                daide_order.append(dipnet_order_tokens[3].split()[-1])
            elif len(dipnet_order_tokens) > 4:
                raise Exception(f"error from utils.dipnet_to_daide_parsing: order {dipnet_order_tokens} is UNEXPECTED. Update code to handle this case!!!")
        elif dipnet_order_tokens[1] == "H":
            # Hold orders
            daide_order.append("HLD")
        elif dipnet_order_tokens[1] == "C":
            # Convoy orders
            daide_order.append("CVY")
            daide_order.append(daidefy_suborder(dipnet_order_tokens[2]))
            daide_order.append("CTO")
            daide_order.append(dipnet_order_tokens[3].split()[-1])
        elif len(dipnet_order_tokens) >= 3 and dipnet_order_tokens[2] == "VIA":
            # VIA/CTO orders
            daide_order.append("CTO")
            daide_order.append(dipnet_order_tokens[1].split()[-1])
            daide_order.append("VIA")
            if dipnet_order_tokens[0] + dipnet_order_tokens[1] in convoy_map:
                daide_order.append(f"({' '.join(convoy_map[dipnet_order_tokens[0] + dipnet_order_tokens[1]])})")
            else:
                print(f"unexpected situation at utils.dipnet_to_daide_parsing. Found order {dipnet_order_tokens} which doesn't have convoying fleet in its own set of orders")
        else:
            # Move orders
            daide_order.append("MTO")
            daide_order.append(dipnet_order_tokens[1].split()[-1])
            if len(dipnet_order_tokens) > 2:
                raise Exception(f"error from utils.dipnet_to_daide_parsing: order {dipnet_order_tokens} is UNEXPECTED. Update code to handle this case!!!")
        daide_orders.append(" ".join(daide_order))

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
        "(FRA AMY PAR) SUP (FRA AMY MAR) MTO BUR" --> "(FRA AMY PAR)", "SUP", "(FRA AMY MAR)", "MTO", "BUR"

        :param daide_style_order_str: DAIDE style string
        :return: list of strings containing components of the order which makes it easy to convert to dipnet-style order
        """
        open_brack = False
        stack = ""
        grouped_order = []
        for char in daide_style_order_str:
            if (not(open_brack) and char == ' ') or char == ')':
                if stack:
                    grouped_order.append(stack)
                    stack = ""
                    open_brack = False
            elif char == '(':
                open_brack = True
            else:
                stack += char
        if stack:
            grouped_order.append(stack)
        return grouped_order
    daide_style_order_groups = split_into_groups(daide_style_order_str)

    def dipnetify_suborder(suborder: str) -> str:
        """
        Translates DAIDE style units to dipnet style units

        :param suborder: DAIDE-style suborder to be encoded
        :return: dipnet suborder
        """
        suborder_tokens = suborder.split()
        try:
            ans = suborder_tokens[1][0] + " " + suborder_tokens[2]
        except Exception:
            raise Exception(f"Failed for suborder: {suborder_tokens}")
        return ans, suborder_tokens[0]

    dipnet_order = []

    # Dipnetify source unit
    suborder, unit_power = dipnetify_suborder(daide_style_order_groups[0])
    dipnet_order.append(suborder)
    if daide_style_order_groups[1] == "SUP":
        # Support order
        dipnet_order.append("S")
        dipnet_order.append(dipnetify_suborder(daide_style_order_groups[2])[0])
        if len(daide_style_order_groups) == 5 and daide_style_order_groups[3] == "MTO":
            dipnet_order.append("-")
            dipnet_order.append(daide_style_order_groups[4])
        elif len(daide_style_order_groups) > 5:
            raise Exception(f"error from utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!")
    elif daide_style_order_groups[1] == "HLD":
        # Hold order
        dipnet_order.append("H")
    elif daide_style_order_groups[1] == "CTO":
        # CTO order
        dipnet_order.append("-")
        dipnet_order.append(daide_style_order_groups[2])
        dipnet_order.append("VIA")
    elif daide_style_order_groups[1] == "CVY":
        # Convoy order
        dipnet_order.append("C")
        dipnet_order.append(dipnetify_suborder(daide_style_order_groups[2])[0])
        dipnet_order.append("-")
        dipnet_order.append(daide_style_order_groups[4])
    elif daide_style_order_groups[1] == "MTO":
        # Move orders
        dipnet_order.append("-")
        dipnet_order.append(daide_style_order_groups[2])
        if len(daide_style_order_groups) > 3:
            raise Exception(f"error from utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!")
    else:
        raise Exception(f"error from utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!")

    return " ".join(dipnet_order), unit_power

def parse_proposal_messages(
        rcvd_messages: List[Tuple[int, Message]],
        game: Game, 
        power_name: str
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]]]:
        """
        From received messages, extract the proposals (categorize as valid and invalid), shared orders and other orders. Use specified game state and power_name to check for validity of moves

        :param rcvd_messages: list of messages received from other players
        :param game: Game state
        :param power_name: power name against which the validity of moves need to be checked
        :return: dictionary of valid proposals, invalid proposals, shared orders (orders that the other power said it would execute), other orders (orders that the other power shared as gossip)
        """
        # Extract messages containing PRP string
        order_msgs = [msg for msg in rcvd_messages.values() if "PRP" in msg.message]

        # Generate a dictionary of sender to list of orders (dipnet-style) for this sender
        proposals = {}
        for order_msg in order_msgs:
            try:
                if "AND" in order_msg.message: # works when AND is present in this format: XDO () AND XDO () AND XDO()
                    daide_style_orders = [order_1 for order in (parse_PRP(order_msg.message)).split("AND") for order_1 in parse_orr_xdo(order.strip())]
                    proposals[order_msg.sender] = [daide_to_dipnet_parsing(order) for order in daide_style_orders]
                else: # works for cases where ORR is present in PRP or nothing is present: ORR ( (XDO()) (XDO()))
                    proposals[order_msg.sender] = [daide_to_dipnet_parsing(order) for order in parse_orr_xdo(parse_PRP(order_msg.message))]
            except Exception:
                raise Exception(f"Exception raised for {order_msg.message}")
        
        invalid_proposals = defaultdict(list)
        valid_proposals = defaultdict(list)
        shared_orders = defaultdict(list)
        other_orders = defaultdict(list)
        # Generate set of possible orders for the given power
        orderable_locs = game.get_orderable_locations(power_name)
        all_possible_orders = game.get_all_possible_orders()
        possible_orders = set([ord for ord_key in all_possible_orders for ord in all_possible_orders[ord_key] if ord_key in orderable_locs])

        # For the set of proposed moves from each sender, check if the specified orders would be allowed. If not, mark them as invalid.
        for sender in proposals:
            for order, unit_power_name in proposals[sender]:
                if unit_power_name == power_name[:3]: # These are supposed to be proposal messages to me
                    if order in possible_orders: # These would be valid proposals to me
                        valid_proposals[sender].append(order)
                    else: # These would be invalid proposals
                        invalid_proposals[sender].append(order)
                elif unit_power_name == sender[:3]: # These are supposed to be conditional orders that the sender is going to execute
                    shared_orders[sender].append(order)
                else:
                    other_orders[sender].append(order)

        if other_orders:
            print("Found other orders while extracting proposal messages:")
            print([msg.message for msg in order_msgs])
            print("Other orders found:")
            print(other_orders)
        
        return valid_proposals, invalid_proposals, shared_orders, other_orders