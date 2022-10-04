"""
Some quickly built utils mostly for DAIDE stuff
It would be preferrable to use a real DAIDE parser in prod
"""

__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

# from diplomacy_research.models.state_space import get_order_tokens
import re
from collections import defaultdict
from typing import List

from DAIDE.utils.exceptions import ParseError
from diplomacy import Game, Message
from tornado import gen


def get_order_tokens(order):
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
        if word not in ["A", "F", "-"]:
            order_tokens += [" ".join(buffer)]
            buffer = []
    return order_tokens


def AND(arrangements: List[str]) -> str:
    """
    ANDs together an array of arrangements
    """

    if len(arrangements) < 2:
        raise Exception("Need at least 2 items to AND")

    return "AND" + "".join([f" ({a})" for a in arrangements])


def ORR(arrangements: List[str]) -> str:
    """
    ORRs together an array of arrangements
    """

    if len(arrangements) < 2:
        return "".join([f"({a})" for a in arrangements])
        # raise Exception("Need at least 2 items to ORR")

    return "ORR" + "".join([f" ({a})" for a in arrangements])


def XDO(orders: List[str]) -> List[str]:
    """
    Adds XDO to each order in array
    """
    return [f"XDO ({order})" for order in orders]


def get_other_powers(powers: List[str], game: Game):
    """
    :return: powers in the game other than those listed
    in the powers parameter
    """
    return set(game.get_map_power_names()) - set(powers)


def ALY(powers: List[str], game: Game) -> str:
    """
    Forms an alliance proposal string

    :param powers: an array of powers to be allied
    """
    others = get_other_powers(powers, game)
    return "ALY (" + " ".join(powers) + ") VSS (" + " ".join(others) + ")"


def YES(string) -> str:
    """Forms YES message"""
    return f"YES ({string})"


def REJ(string) -> str:
    """Forms REJ message"""
    return f"REJ ({string})"


def FCT(string) -> str:
    """Forms FCT message"""
    return f"FCT ({string})"


def parse_FCT(msg) -> str:
    """Detaches FCT from main arrangement"""
    if "FCT" not in msg:
        raise ParseError("This is not an FCT message")
    try:
        return msg[5:-1]
    except Exception:
        raise ParseError(f"Cant parse FCT msg {msg}")


def parse_PRP(msg) -> str:
    """Detaches PRP from main arrangement"""
    if "PRP" not in msg:
        raise ParseError("This is not an PRP message")
    try:
        return msg[5:-1]
    except Exception:
        raise ParseError(f"Cant parse PRP msg {msg}")


def parse_orr_xdo(msg: str) -> List[str]:
    """
    Attempts to parse a specific message configuration
    """
    # parse may fail
    if "VSS" in msg:
        raise ParseError("This looks an ally message")
    try:
        if "ORR" in msg:
            msg = msg[5:-1]
        # else:
        #     # remove else since it is a bug to 'XDO (order)'
        #     msg = msg[1:-1]
        parts = msg.split(") (")

        return [part[5:-1] for part in parts]
    except Exception:
        raise ParseError("Cant parse ORR XDO msg")


def parse_alliance_proposal(msg: str, recipient: str) -> List[str]:
    """
    Parses an alliance proposal
    E.g. (assuming the receiving country is RUSSIA)
    "ALY (GERMANY RUSSIA) VSS (FRANCE ENGLAND ITALY TURKEY AUSTRIA)" -> [GERMANY]
    :param recipient: the power which has received the alliance proposal
    :return: list of allies in the proposal
    """
    groups = re.findall(r"\(([a-zA-Z\s]*)\)", msg)

    if len(groups) != 2:
        # raise ParseError("Found more than 2 groups")
        allies = []

    # get proposed allies
    allies = groups[0].split(" ")

    if recipient not in allies:
        # raise ParseError("Recipient not in allies")
        allies = []
        return allies

    allies.remove(recipient)

    if allies:
        return allies
    else:
        raise ParseError("A minimum of 2 powers are needed for an alliance")


def is_order_aggressive(order: str, sender: str, game: Game) -> bool:
    """
    Checks if this is an agressive order
    :param order: A string order, e.g. "A BUD S F TRI"
    NOTE: Adapted directly from Joy's code
    """
    order_token = get_order_tokens(order)
    # print(order_token)
    if order_token[0][0] == "A" or order_token[0][0] == "F":
        # get location - add order_token[0] ('A' or 'F') at front to check if it collides with other powers' units
        order_unit = order_token[0][0] + order_token[1][1:]
        # check if loc has some units of other powers on
        for power in game.powers:
            if sender != power:
                if order_unit in game.powers[power].units:
                    return True
    return False


def get_non_aggressive_orders(orders: List[str], sender: str, game: Game) -> List[str]:
    """
    :return: all non aggressive orders in orders
    """
    return [order for order in orders if not is_order_aggressive(order, sender, game)]


def is_move_order(order):
    order_tokens = get_order_tokens(order)
    if len(order_tokens) == 2 and order_tokens[1][0] == "-":
        return True
    else:
        return False


def is_support_order(order):
    order_tokens = get_order_tokens(order)
    if 3 <= len(order_tokens) <= 4 and order_tokens[1] == "S":
        return True
    else:
        return False


def is_cross_support(order, power, game):
    if not is_support_order(order):
        return False
    order_tokens = get_order_tokens(order)
    for power2 in game.powers:
        if power != power2 and order_tokens[2] in game.powers[power2].units:
            return True
        else:
            return False


def is_convoyed_order(order):
    order_tokens = get_order_tokens(order)
    if len(order_tokens) == 3 and order_tokens[-1] == "VIA":
        return True
    else:
        return False


def get_province_from_order(order):
    order_tokens = get_order_tokens(order)
    parts = order_tokens[0].split()
    if len(parts) >= 2:
        return parts[1]
    else:
        return order_tokens[0]

def dipnet_to_daide_parsing(dipnet_style_order_strs: List[str], game: Game) -> List[str]:
    """
    Convert dipnet style single order to DAIDE style order. Needs game instance to determine the powers owning the units

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
            raise f"error from utils.dipnet_to_daide_parsing: unit {dipnet_suborder} not present in unit_game_mapping"
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
                raise f"error from utils.dipnet_to_daide_parsing: order {dipnet_order_tokens} is UNEXPECTED. Update code to handle this case!!!"
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
                raise f"error from utils.dipnet_to_daide_parsing: order {dipnet_order_tokens} is UNEXPECTED. Update code to handle this case!!!"
        daide_orders.append(" ".join(daide_order))

    return daide_orders


def daide_to_dipnet_parsing(daide_style_order_str: str) -> str:
    """
    Convert DAIDE style single order to dipnet style order

    :param daide_style_order_str: DAIDE style string to be converted to dipnet style
    :return: dipnet style order string
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
        return suborder_tokens[1][0] + " " + suborder_tokens[2]

    dipnet_order = []

    # Dipnetify source unit
    dipnet_order.append(dipnetify_suborder(daide_style_order_groups[0]))
    if daide_style_order_groups[1] == "SUP":
        # Support order
        dipnet_order.append("S")
        dipnet_order.append(dipnetify_suborder(daide_style_order_groups[2]))
        if len(daide_style_order_groups) == 5 and daide_style_order_groups[3] == "MTO":
            dipnet_order.append("-")
            dipnet_order.append(daide_style_order_groups[4])
        elif len(daide_style_order_groups) > 5:
            raise f"error from utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!"
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
        dipnet_order.append(dipnetify_suborder(daide_style_order_groups[2]))
        dipnet_order.append("-")
        dipnet_order.append(daide_style_order_groups[4])
    elif daide_style_order_groups[1] == "MTO":
        # Move orders
        dipnet_order.append("-")
        dipnet_order.append(daide_style_order_groups[2])
        if len(daide_style_order_groups) > 3:
            raise f"error from utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!"
    else:
        raise f"error from utils.daide_to_dipnet_parsing: order {daide_style_order_groups} is UNEXPECTED. Update code to handle this case!!!"

    return " ".join(dipnet_order)
    
class MessagesData:
    def __init__(self):
        self.messages = []

    def add_message(self, recipient: str, message: str):
        self.messages.append({"recipient": recipient, "message": message})

    def __iter__(self):
        return iter(self.messages)


class OrdersData:
    def __init__(self):
        self.orders = defaultdict(str)

    def add_order(self, order, overwrite=True):
        """
        Adds single order

        :param overwrite: whether or not to overwrite an order
        """

        province = get_province_from_order(order)

        if overwrite:
            self.orders[province] = order
        else:
            if province not in self.orders:
                self.orders[province] = order

    def add_orders(self, orders, overwrite=True):
        """
        Adds multiple orders

        :param overwrite: whether or not to overwrite orders
        """
        for order in orders:
            self.add_order(order, overwrite)

    def get_list_of_orders(self):
        return list(self.orders.values())

    def __iter__(self):
        return iter(self.orders)

    def empty(self):
        return len(self.orders) > 0


def sort_messages_by_most_recent(messages: List[Message]):
    messages.sort(key=lambda msg: msg.time_sent)
    return messages


@gen.coroutine
def get_state_value(bot, game, power_name):
    # rollout the game --- orders in rollout are from dipnet
    # state value
    for i in range(bot.rollout_length):
        # print('rollout: ', i)
        for power in game.powers:
            orders = yield bot.brain.get_orders(game, power)
            # print(power + ': ')
            # print(orders)
            game.set_orders(
                power_name=power,
                orders=orders[: min(bot.rollout_n_order, len(orders))],
            )
        game.process()
    return len(game.get_centers(power_name))


@gen.coroutine
def get_best_orders(bot, proposal_order: dict, shared_order: dict):
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
    state_value = {power: -10000 for power in bot.game.powers}

    # get state value for each proposal
    for proposer, unit_orders in proposal_order.items():

        # if there is a proposal from this power
        if unit_orders:
            proposed = True

            # simulate game by copying the current one
            simulated_game = bot.game.__deepcopy__(None)

            # censor aggressive orders
            unit_orders = get_non_aggressive_orders(
                unit_orders, bot.power_name, bot.game
            )

            # set orders as a proposal order
            simulated_game.set_orders(power_name=bot.power_name, orders=unit_orders)

            # consider shared orders in a simulated game
            for other_power, power_orders in shared_order.items():

                # if they are not sharing any info about their orders then assume that they are DipNet-based
                if not power_orders:
                    power_orders = yield bot.brain.get_orders(game, other_power)
                simulated_game.set_orders(power_name=other_power, orders=power_orders)

            # process current turn
            simulated_game.process()

            # rollout and get state value
            state_value[proposer] = yield get_state_value(
                bot, simulated_game, bot.power_name
            )

    # get power name that gives the max state value
    best_proposer = max(state_value, key=state_value.get)

    return best_proposer, proposal_order[best_proposer]


if __name__ == "__main__":
    game = Game()
    powers = list(game.powers)
    power_0 = powers[0]
    power_1 = powers[1]
    msg_obj1 = Message(
        sender=power_0,
        recipient=power_1,
        message="HELLO",
        phase=game.get_current_phase(),
    )
    game.add_message(message=msg_obj1)
    msg_obj2 = Message(
        sender=power_1,
        recipient=power_0,
        message="GOODBYE",
        phase=game.get_current_phase(),
    )
    game.add_message(message=msg_obj2)
    msgs = [msg_obj2, msg_obj1]

    assert sort_messages_by_most_recent(msgs)[0].message == "HELLO"

    # if __name__ == "__main__":
    # from diplomacy import Game
    # # game instance
    # game = Game()
    # print(AND(["GO HOME", "BAD MONKEY"]))
    # # print(AND(["GO HOME"]))
    # print(XDO(["Move back", "Move"]))
    msg = ORR(XDO(["Move back", "Move"]))
    print(parse_orr_xdo(msg))
    # # print(ALY(["p1", "p2"]))
    # # print(ALY(["GERMANY", "RUSSIA"], game))
    # # print(parse_alliance_proposal("ALY (GERMANY RUSSIA) VSS (FRANCE ENGLAND ITALY TURKEY AUSTRIA)", "RUSSIA"))
    # print(is_order_aggressive("A CON BUL", "TURKEY", game))