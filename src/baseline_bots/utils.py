"""
Some quickly built utils mostly for DAIDE stuff
It would be preferable to use a real DAIDE parser in prod
"""


import asyncio
import logging
import os
from typing import List, Optional, Set

from daidepp import (
    AnyDAIDEToken,
    DAIDEGrammar,
    create_daide_grammar,
    daide_visitor,
)
from daidepp.grammar.grammar import MAX_DAIDE_LEVEL
from diplomacy import Game


def return_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """Returns a properly set up logger.

    Args:
        name: Name of logger.
        log_level: Verbosity level of logger.

    Returns:
        An initialized logger.
    """
    # Monkey patch module to show milliseconds
    logging.Formatter.default_msec_format = "%s.%03d"

    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        # Fall back to `WARNING`, the default level of the root logger, if `log_level` is `NOTSET`
        level=log_level or logging.WARNING,
    )
    new_logger = logging.getLogger(name)
    new_logger.setLevel(log_level)
    return new_logger


logger = return_logger(__name__)

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
    logger.info("Enabling debugging mode")
    DEBUG_MODE = True

MESSAGE_GRAMMAR = create_daide_grammar(level=MAX_DAIDE_LEVEL, string_type="message")
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
    except Exception:  # pylint: disable=broad-exception-caught
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
