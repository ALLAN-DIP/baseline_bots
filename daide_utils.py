"""
Some quickly built utils mostly for DAIDE stuff
It would be preferrable to use a real DAIDE parser in prod
"""

__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from lib2to3.pgen2.parse import ParseError
from typing import List

from diplomacy import Game
# from diplomacy_research.models.state_space import get_order_tokens
import re

def get_order_tokens(order):
    """ Retrieves the order tokens used in an order
        e.g. 'A PAR - MAR' would return ['A PAR', '-', 'MAR']
        NOTE: Stolen from diplomacy_research
    """
    # We need to keep 'A', 'F', and '-' in a temporary buffer to concatenate them with the next word
    # We replace 'R' orders with '-'
    # Tokenization would be: 'A PAR S A MAR - BUR' --> 'A PAR', 'S', 'A MAR', '- BUR'
    #                        'A PAR R MAR'         --> 'A PAR', '- MAR'
    buffer, order_tokens = [], []
    for word in order.replace(' R ', ' - ').split():
        buffer += [word]
        if word not in ['A', 'F', '-']:
            order_tokens += [' '.join(buffer)]
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
        raise Exception("Need at least 2 items to ORR")

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

def parse_orr_xdo(msg: str) -> List[str]:
    """
    Attempts to parse a specific message configuration
    """
    # parse may fail
    if "VSS" in msg:
        raise ParseError("This looks an ally message")
    try:
        msg = msg[5:-1]
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
    groups = re.findall(r'\(([a-zA-Z\s]*)\)', msg)
    
    if len(groups) != 2:
        raise ParseError("Found more than 2 groups")
    
    # get proposed allies
    allies = groups[0].split(" ")

    if recipient not in allies:
        raise ParseError("Recipient not in allies")
    
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
    if order_token[0] =='A' or order_token[0] =='F':
        #get location - add order_token[0] ('A' or 'F') at front to check if it collides with other powers' units
        order_unit = order_token[0]+' '+order_token[2]
        #check if loc has some units of other powers on
        for power in game.powers:
          if sender != power:
            if order_unit in game.powers[power].units:
              return True 
    return False

def get_non_aggressive_orders(orders: List[str], sender:str, game: Game) -> List[str]:
    """
    :return: all non aggressive orders in orders
    """
    return [order for order in orders if not is_order_aggressive(order, sender, game)]

# def parse_daide_message(msg):
#     """where's ocaml when I need it"""

if __name__ == "__main__":
    from diplomacy import Game
    # game instance
    game = Game()
    print(AND(["GO HOME", "BAD MONKEY"]))
    # print(AND(["GO HOME"]))
    print(XDO(["Move back", "Move"]))
    # msg = ORR(XDO(["Move back", "Move"]))
    # print(parse_orr_xdo(msg))
    # print(ALY(["p1", "p2"]))
    # print(ALY(["GERMANY", "RUSSIA"], game))
    # print(parse_alliance_proposal("ALY (GERMANY RUSSIA) VSS (FRANCE ENGLAND ITALY TURKEY AUSTRIA)", "RUSSIA"))
    print(is_order_aggressive("A CON BUL", "TURKEY", game))