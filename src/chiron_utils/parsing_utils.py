"""Utilities for converting between DipNet and DAIDE syntax."""

import asyncio
from collections import defaultdict
from typing import Any, List, Mapping, Optional, Sequence, Tuple, Union

from daidepp import CVY, HLD, MTO, SUP, Command, Location, MoveByCVY, Unit
from diplomacy import Game

from chiron_utils.utils import DEBUG_MODE, get_order_tokens, return_logger

logger = return_logger(__name__)

dipnet2daide_loc = {
    "BOT": "GOB",
    "ENG": "ECH",
    "LYO": "GOL",
}
daide2dipnet_loc = {v: k for k, v in dipnet2daide_loc.items()}


def daidefy_location(prov: str) -> Location:
    """Converts DipNet-style location to DAIDE-style location.

    E.g.
    BUL/EC --> BUL ECS
    STP/SC --> STP SCS
    ENG    --> ECH
    PAR    --> PAR

    Args:
        prov: DipNet-style province notation.

    Returns:
        DAIDE-style order.
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
    """Converts DipNet-style unit to DAIDE-style unit.

    E.g. (for initial game state)
    A BUD --> AUS AMY BUD
    F TRI --> AUS FLT TRI
    A PAR --> FRA AMY PAR
    A MAR --> FRA AMY MAR

    Args:
        dipnet_unit: DipNet-style unit notation.
        unit_game_mapping: Mapping from DipNet-style units to powers.

    Returns:
        DAIDE-style unit.
    """
    power = unit_game_mapping[dipnet_unit]

    if dipnet_unit.startswith("A"):
        unit_type = "AMY"
    elif dipnet_unit.startswith("F"):
        unit_type = "FLT"
    else:
        raise ValueError(f"Cannot extract unit type from DipNet-style unit {dipnet_unit!r}")

    location = daidefy_location(dipnet_unit.split()[-1])

    unit = Unit(power, unit_type, location)
    return unit


def dipnet_to_daide_parsing(
    dipnet_style_order_strs: Sequence[Union[str, Tuple[str, str]]],
    game: Game,
    *,
    unit_power_tuples_included: bool = False,
) -> List[Command]:
    """Convert set of DipNet-style orders to DAIDE-style orders.

    Needs game instance to determine the powers owning the units.

    More details here: https://docs.google.com/document/d/16RODa6KDX7vNNooBdciI4NqSVN31lToto3MLTNcEHk0/edit?usp=sharing

    Args:
        dipnet_style_order_strs: DipNet-style list of orders to be converted to DAIDE.
            Either in format {"RUSSIA": ["A SEV - RUM"]} or {"RUSSIA": [("A SEV - RUM", "RUS")]}.
        game: Game instance.
        unit_power_tuples_included: Whether the unit power will also be included in
            `dipnet_style_order_strs` along with the orders like this: ("A SEV - RUM", "RUS").

    Returns:
        List of DAIDE-style orders.
    """
    convoy_map = defaultdict(list)
    dipnet_style_order_strs_tokens: List[Any] = [None for _ in range(len(dipnet_style_order_strs))]

    # Convert strings to order tokens and store a dictionary mapping of armies to be convoyed and fleets helping to convoy
    for i in range(len(dipnet_style_order_strs)):  # pylint: disable=consider-using-enumerate
        if not unit_power_tuples_included:
            dipnet_style_order_strs_tokens[i] = get_order_tokens(dipnet_style_order_strs[i])  # type: ignore[arg-type]
            if dipnet_style_order_strs_tokens[i][1] == "C":
                convoy_map[
                    dipnet_style_order_strs_tokens[i][2] + dipnet_style_order_strs_tokens[i][3]
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
        except Exception as ex:
            logger.exception(
                "ALLAN: error from %s.%s()\n\tOrder with error: %r\n\tSet of orders: %s",
                __name__,
                dipnet_to_daide_parsing.__name__,
                " ".join(dipnet_order_tokens),
                dipnet_style_order_strs,
            )
            if DEBUG_MODE:
                raise ex
            continue
    return daide_orders


def dipnetify_location(loc: Location) -> str:
    """Converts DipNet-style location to DAIDE-style location.

    E.g.
    BUL ECS --> BUL/EC
    STP SCS --> STP/SC
    ECH     --> ENG
    PAR     --> PAR

    Args:
        loc: DAIDE-style location.

    Returns:
        DipNet-style province notation.
    """
    prov = daide2dipnet_loc.get(loc.province, loc.province)
    if loc.coast is not None:
        prov += "/" + loc.coast[:-1]
    return prov


def dipnetify_unit(unit: Unit) -> str:
    """Converts DAIDE-style unit to DipNet-style unit.

    Args:
        unit: DAIDE-style unit.

    Returns:
        DipNet-style unit notation.
    """
    unit_type = unit.unit_type[0]
    location = dipnetify_location(unit.location)
    return f"{unit_type} {location}"


def daide_to_dipnet_parsing(daide_order: Command) -> Optional[Tuple[str, str]]:
    """Convert single DAIDE-style order to DipNet-style order.

    More details here: https://docs.google.com/document/d/16RODa6KDX7vNNooBdciI4NqSVN31lToto3MLTNcEHk0/edit?usp=sharing

    Args:
        daide_order: DAIDE-style order to be converted to DipNet style.

    Returns:
        DipNet-style order string and unit's power name.
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
    except Exception as ex:
        logger.exception(
            "ALLAN: error from %s.%s\n\tCould not convert DAIDE command %r to DipNet format",
            __name__,
            daide_to_dipnet_parsing.__name__,
            str(daide_order),
        )
        if DEBUG_MODE:
            raise ex
        return None
