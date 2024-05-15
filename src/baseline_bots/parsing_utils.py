"""
Some quickly built parsing utils mostly for DAIDE stuff
"""

import asyncio
from collections import defaultdict
from typing import Dict, List, Mapping, Tuple, Union

from daidepp import (
    ALYVSS,
    CVY,
    HLD,
    MTO,
    PCE,
    PRP,
    SUP,
    XDO,
    Command,
    Location,
    MoveByCVY,
    Unit,
)
from diplomacy import Game, Message

from baseline_bots.utils import (
    DEBUG_MODE,
    get_order_tokens,
    parse_alliance_proposal,
    parse_arrangement,
    parse_daide,
    parse_peace_proposal,
    return_logger,
)

logger = return_logger(__name__)

dipnet2daide_loc = {
    "BOT": "GOB",
    "ENG": "ECH",
    "LYO": "GOL",
}
daide2dipnet_loc = {v: k for k, v in dipnet2daide_loc.items()}


def daidefy_location(prov: str) -> Location:
    """Converts DipNet-style location to DAIDE-style location

    E.g.
    BUL/EC --> BUL ECS
    STP/SC --> STP SCS
    ENG    --> ECH
    PAR    --> PAR

    :param prov: DipNet-style province notation
    :return: DAIDE-style order
    """
    if "/" in prov:
        prov, coast = prov.split("/")
        coast += "S"
    else:
        coast = None
    prov = dipnet2daide_loc.get(prov, prov)
    loc = Location(province=prov, coast=coast)
    return loc


def daidefy_unit(dipnet_unit: str, unit_game_mapping: Mapping[str, str]) -> Unit:
    """Converts DipNet-style unit to DAIDE-style unit

    E.g. (for initial game state)
    A BUD --> AUS AMY BUD
    F TRI --> AUS FLT TRI
    A PAR --> FRA AMY PAR
    A MAR --> FRA AMY MAR

    :param dipnet_unit: DipNet-style unit notation
    :param unit_game_mapping: Mapping from DipNet-style units to powers
    :return: DAIDE-style unit
    """
    power = unit_game_mapping[dipnet_unit]

    if dipnet_unit.startswith("A"):
        unit_type = "AMY"
    elif dipnet_unit.startswith("F"):
        unit_type = "FLT"
    else:
        raise ValueError(
            f"Cannot extract unit type from DipNet-style unit {dipnet_unit!r}"
        )

    location = daidefy_location(dipnet_unit.split()[-1])

    unit = Unit(power, unit_type, location)
    return unit


def dipnet_to_daide_parsing(
    dipnet_style_order_strs: List[Union[str, Tuple[str, str]]],
    game: Game,
    unit_power_tuples_included: bool = False,
) -> List[Command]:
    """Convert set of DipNet-style orders to DAIDE-style orders

    Needs game instance to determine the powers owning the units.

    More details here: https://docs.google.com/document/d/16RODa6KDX7vNNooBdciI4NqSVN31lToto3MLTNcEHk0/edit?usp=sharing

    :param dipnet_style_order_strs: DipNet-style list of orders to be converted to DAIDE.
        Either in format: {"RUSSIA": ["A SEV - RUM"]} or {"RUSSIA": [("A SEV - RUM", "RUS")]}
    :param game: game instance
    :param unit_power_tuples_included: Whether the unit power will also be included in
        dipnet_style_order_strs along with the orders like this: ("A SEV - RUM", "RUS")
    :return: List of DAIDE-style orders
    """

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
            for power, units in game.get_units().items():
                for unit in units:
                    unit_game_mapping[unit] = power[:3]

            # If unit powers are also included in the input, then add the unit - unit power mapping for DAIDE construction
            if unit_power_tuples_included:
                unit_game_mapping[dipnet_order_tokens[0]] = unit_power

            if dipnet_order_tokens[0] not in unit_game_mapping:
                raise ValueError(
                    f"Acting unit {dipnet_order_tokens[0]!r} does not have a corresponding power"
                )
            if (
                len(dipnet_order_tokens) >= 3
                and dipnet_order_tokens[2] != "VIA"
                and dipnet_order_tokens[2] not in unit_game_mapping
            ):
                raise ValueError(
                    f"Target unit {dipnet_order_tokens[2]!r} does not have a corresponding power"
                )

            # Daidefy and add source unit as it is
            acting_unit = daidefy_unit(dipnet_order_tokens[0], unit_game_mapping)

            if dipnet_order_tokens[1] == "S":
                target_unit = daidefy_unit(dipnet_order_tokens[2], unit_game_mapping)

                if len(dipnet_order_tokens) == 4 and dipnet_order_tokens[3] != "H":
                    province_no_coast = daidefy_location(
                        dipnet_order_tokens[3].split()[-1]
                    ).province
                elif len(dipnet_order_tokens) > 4:
                    raise NotImplementedError(
                        f"Cannot process DipNet support order {' '.join(dipnet_order_tokens)!r} "
                        "because it has more than 4 tokens"
                    )
                else:
                    province_no_coast = None

                support_order = SUP(
                    supporting_unit=acting_unit,
                    supported_unit=target_unit,
                    province_no_coast=province_no_coast,
                )
                daide_orders.append(support_order)
            elif dipnet_order_tokens[1] == "H":
                hold_order = HLD(acting_unit)
                daide_orders.append(hold_order)
            elif dipnet_order_tokens[1] == "C":
                target_unit = daidefy_unit(dipnet_order_tokens[2], unit_game_mapping)
                target_prov = daidefy_location(dipnet_order_tokens[3].split()[-1])
                convoy_order = CVY(
                    convoying_unit=acting_unit,
                    convoyed_unit=target_unit,
                    province=target_prov,
                )
                daide_orders.append(convoy_order)
            elif len(dipnet_order_tokens) >= 3 and dipnet_order_tokens[2] == "VIA":
                province = daidefy_location(dipnet_order_tokens[1].split()[-1])
                if dipnet_order_tokens[0] + dipnet_order_tokens[1] in convoy_map:
                    seas = convoy_map[dipnet_order_tokens[0] + dipnet_order_tokens[1]]
                    seas = [daidefy_location(prov).province for prov in seas]
                else:
                    raise ValueError(
                        f"Found unexpected order {' '.join(dipnet_order_tokens)!r} which "
                        "doesn't have convoying fleet in its own set of orders"
                    )
                via_cto_order = MoveByCVY(acting_unit, province, *seas)
                daide_orders.append(via_cto_order)
            else:
                target_location = daidefy_location(dipnet_order_tokens[1].split()[-1])
                move_order = MTO(acting_unit, target_location)
                if len(dipnet_order_tokens) > 2:
                    raise NotImplementedError(
                        f"Cannot process DipNet movement order {' '.join(dipnet_order_tokens)!r} "
                        "because it has more than 2 tokens"
                    )
                daide_orders.append(move_order)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(
                f"ALLAN: error from {__name__}.{dipnet_to_daide_parsing.__name__}()\n"
                f"\tOrder with error: {' '.join(dipnet_order_tokens)!r}\n"
                f"\tSet of orders: {dipnet_style_order_strs}"
            )
            if DEBUG_MODE:
                raise e
            continue
    return daide_orders


def dipnetify_location(loc: Location) -> str:
    """Converts DipNet-style location to DAIDE-style location

    E.g.
    BUL ECS --> BUL/EC
    STP SCS --> STP/SC
    ECH     --> ENG
    PAR     --> PAR

    :param loc: DAIDE-style location
    :return: DipNet-style province notation
    """
    prov = daide2dipnet_loc.get(loc.province, loc.province)
    if loc.coast is not None:
        prov += "/" + loc.coast[:-1]
    return prov


def dipnetify_unit(unit: Unit) -> str:
    """Converts DAIDE-style unit to DipNet-style unit

    :param unit: DAIDE-style unit
    :return: DipNet-style unit notation
    """
    unit_type = unit.unit_type[0]
    location = dipnetify_location(unit.location)
    return f"{unit_type} {location}"


def daide_to_dipnet_parsing(daide_order: Command) -> Tuple[str, str]:
    """Convert single DAIDE-style order to DipNet-style order

    More details here: https://docs.google.com/document/d/16RODa6KDX7vNNooBdciI4NqSVN31lToto3MLTNcEHk0/edit?usp=sharing

    :param daide_order: DAIDE-style order to be converted to DipNet style
    :return: DipNet-style order string and unit's power name
    """

    try:
        # Dipnetify source unit
        acting_unit = dipnetify_unit(daide_order.unit)
        unit_power = daide_order.unit.power
        if isinstance(daide_order, SUP):
            # Support order
            supported_unit = dipnetify_unit(daide_order.supported_unit)
            dipnet_order = f"{acting_unit} S {supported_unit}"
            if daide_order.province_no_coast_location is not None:
                prov = dipnetify_location(daide_order.province_no_coast_location)
                dipnet_order += f" - {prov}"
        elif isinstance(daide_order, HLD):
            # Hold order
            dipnet_order = f"{acting_unit} H"
        elif isinstance(daide_order, MoveByCVY):
            # CTO order
            prov = dipnetify_location(daide_order.province)
            dipnet_order = f"{acting_unit} - {prov} VIA"
        elif isinstance(daide_order, CVY):
            # Convoy order
            convoyed_unit = dipnetify_unit(daide_order.convoyed_unit)
            prov = dipnetify_location(daide_order.province)
            dipnet_order = f"{acting_unit} C {convoyed_unit} - {prov}"
        elif isinstance(daide_order, MTO):
            # Move orders
            prov = dipnetify_location(daide_order.location)
            dipnet_order = f"{acting_unit} - {prov}"
        else:
            raise NotImplementedError(
                f"Conversion for {type(daide_order).__name__} commands has not been implemented yet"
            )

        return dipnet_order, unit_power
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception(
            f"ALLAN: error from {__name__}.{daide_to_dipnet_parsing.__name__}\n"
            f"\tCould not convert DAIDE command {str(daide_order)!r} to DipNet format"
        )
        if DEBUG_MODE:
            raise e
        return None


def parse_proposal_messages(
    rcvd_messages: List[Message], game: Game, power_name: str
) -> Dict[str, Dict[str, List[str]]]:
    """Extracts proposals and orders from received messages

    From each received messages, extract the proposals (categorize as valid and invalid),
    shared orders and other orders. Use specified game state and power_name
    to check for validity of moves

    :param rcvd_messages: list of messages received from other players
    :param game: Game state
    :param power_name: power name against which the validity of moves need to be checked
    :return: dictionary of
        valid proposals,
        invalid proposals,
        shared orders (orders that the other power said it would execute),
        other orders (orders that the other power shared as gossip),
        alliance proposals
        peace proposals
    """
    try:
        # Extract messages containing PRP string
        order_msgs = [
            msg for msg in rcvd_messages if isinstance(parse_daide(msg.message), PRP)
        ]
        logger.info(
            f"Received {len(order_msgs)} PRP messages: "
            f"{[(order_msg.sender, order_msg.message) for order_msg in order_msgs]}"
        )

        # Generate a dictionary of sender to list of DipNet-style orders for this sender
        proposals = defaultdict(list)

        invalid_proposals = defaultdict(list)
        valid_proposals = defaultdict(list)
        shared_orders = defaultdict(list)
        other_orders = defaultdict(list)
        alliance_proposals = defaultdict(list)
        peace_proposals = defaultdict(list)

        for order_msg in order_msgs:
            try:
                daide_style_orders = [
                    parse_daide(order) for order in parse_arrangement(order_msg.message)
                ]
                for order in daide_style_orders:
                    if isinstance(order, XDO):
                        temp_message = daide_to_dipnet_parsing(order.order)
                        if temp_message:
                            proposals[order_msg.sender].append(temp_message)
                    # from RY: I think this parsing is problematic though..
                    # when we YES/REJ a ALY/PCE proposal we should do it as a whole..
                    elif isinstance(order, ALYVSS):
                        for ally in parse_alliance_proposal(order, power_name):
                            alliance_proposals[ally].append(
                                (order_msg.sender, str(order))
                            )
                    elif isinstance(order, PCE):
                        for peace in parse_peace_proposal(order, power_name):
                            peace_proposals[peace].append(
                                (order_msg.sender, str(order))
                            )
                    else:
                        other_orders[order_msg.sender].append(str(order))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception(
                    f"ALLAN: error from {__name__}.{parse_proposal_messages.__name__}()\n"
                    f"\tUnexpected proposal message format: {order_msg.message!r}"
                )
                if DEBUG_MODE:
                    raise e
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

        # For the set of proposed moves from each sender,
        # check if the specified orders would be allowed.
        # If not, mark them as invalid.
        for sender in proposals:
            for order, unit_power_name in proposals[sender]:
                # These are supposed to be proposal messages to me
                if unit_power_name == power_name[:3]:
                    if order in possible_orders:  # These would be valid proposals to me
                        valid_proposals[sender].append(order)
                    else:  # These would be invalid proposals
                        invalid_proposals[sender].append((order, unit_power_name))
                # These are supposed to be conditional orders that the sender is going to execute
                elif unit_power_name == sender[:3]:
                    shared_orders[sender].append(order)
                else:
                    other_orders[sender].append(order)

        if other_orders:
            logger.info(
                "ALLAN: Found other orders while extracting proposal messages: "
                f"{[msg.message for msg in order_msgs]}"
            )
            logger.info(f"ALLAN: Other orders found: {dict(other_orders)}")

        return {
            "valid_proposals": valid_proposals,
            "invalid_proposals": invalid_proposals,
            "shared_orders": shared_orders,
            "other_orders": other_orders,
            "alliance_proposals": alliance_proposals,
            "peace_proposals": peace_proposals,
        }
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception(
            f"ALLAN: error from {__name__}.{parse_proposal_messages.__name__}()\n"
            f"\tReceived messages: {rcvd_messages}"
        )
        if DEBUG_MODE:
            raise e
        return {
            "valid_proposals": {},
            "invalid_proposals": {},
            "shared_orders": {},
            "other_orders": {},
            "alliance_proposals": {},
            "peace_proposals": {},
        }
