"""
Some quickly built utils mostly for DAIDE stuff
It would be preferrable to use a real DAIDE parser in prod
"""

__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

# from diplomacy_research.models.state_space import get_order_tokens
import re
from collections import defaultdict
from typing import Dict, List, Tuple

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
        return msg[msg.find("(") + 1:-1]
    except Exception:
        raise Exception(f"Cant parse FCT msg {msg}")


def parse_PRP(msg) -> str:
    """Detaches PRP from main arrangement"""
    if "PRP" not in msg:
        raise ParseError("This is not an PRP message")
    try:
        return msg[msg.find("(") + 1:-1]
    except Exception:
        raise Exception(f"Cant parse PRP msg {msg}")


def parse_orr_xdo(msg: str) -> List[str]:
    """
    Attempts to parse a specific message configuration
    """
    # parse may fail
    if "VSS" in msg:
        raise ParseError("This looks an ally message")
    try:
        if "ORR" in msg:
            msg = msg[msg.find("(") + 1:-1]
        # else:
        #     # remove else since it is a bug to 'XDO (order)'
        #     msg = msg[1:-1]

        # split the message at )( points
        parts = re.split(r"\)\s*\(", msg)

        def extract_suborder_indices(part: str) -> str:
            """
            Finds the start and end indices of suborder in an XDO message
            For instance, 
            "XDO (F BLK - CON)" returns (4, 16)
            "XDO(F BLK - CON)" returns (3, 15)
            "XDO ((RUS AMY WAR) MTO PRU)" returns (4, 26)

            :param part: part of the message representing an arrangement for 1 unit
            :return: the actual order after excluding XDO
            """
            start_in = part.find("(", part.find("XDO"))
            parenthesis_cnt = 0
            for i in range(start_in, len(part)):
                if part[i] == '(':
                    parenthesis_cnt += 1
                elif part[i] == ')':
                    parenthesis_cnt -= 1
                if parenthesis_cnt == 0:
                    return start_in, i
            return start_in, -1
        
        ans = []
        for part in parts:
            start, end = extract_suborder_indices(part)
            ans.append(part[start+1:end])
        return ans

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