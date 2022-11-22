import random
from ssl import _ASN1Object
from typing import Tuple

from baseline_bots.randomize_order import (
    ADJACENCY,
    random_list_orders,
    randomize_order,
    string_to_tuple,
    tuple_to_string,
)


class TestRandomizeDipnet:
    def test(self):

        # The following three tests check that build, disband and remove commands do not get changed when input into the order randomizer.

        ord = [(("FRA", "AMY", "PAR"), "BLD")]
        assert ord == random_list_orders(ord)

        ord = [(("FRA", "AMY", "PAR"), "DSB")]
        assert ord == random_list_orders(ord)

        ord = [(("FRA", "AMY", "PAR"), "REM")]
        assert ord == random_list_orders(ord)

        # The following three tests check that when orders that contain movements, holds, convoys and other moves get
        # input into the order randomizer, they come out differnent.

        orders = [
            (("FRA", "FLT", "NTH"), "CVY", ("FRA", "AMY", "HOL"), "CTO", "NWY"),
            (("FRA", "AMY", "HOL"), "CTO", "NWY", "VIA", ("NTH")),
            (("FRA", "AMY", "BER"), "HLD"),
        ]
        assert random_list_orders(orders) != orders

        orders = [
            (("FRA", "AMY", "PIC"), "MTO", "PAR"),
            (("FRA", "AMY", "BUR"), "HLD"),
            (("FRA", "AMY", "BER"), "HLD"),
        ]
        assert random_list_orders(orders) != orders

        orders = [
            (("FRA", "AMY", "PIC"), "MTO", "PAR"),
            (("FRA", "AMY", "BUR"), "SUP", ("FRA", "AMY", "PIC"), "MTO", "PAR"),
            (("FRA", "AMY", "BER"), "HLD"),
        ]
        assert random_list_orders(orders) != orders

        # These following two tests ensure that the valid values are being returned when calling random_list_orders with a seed.

        orders = [
            (("FRA", "FLT", "NTH"), "CVY", ("FRA", "AMY", "HOL"), "CTO", "NWY"),
            (("FRA", "AMY", "HOL"), "CTO", "NWY", "VIA", ("NTH")),
        ]
        random.seed(1)
        assert random_list_orders(orders) == [
            (("FRA", "FLT", "NTH"), "CVY", ("FRA", "AMY", "HOL"), "CTO", "EDI"),
            (("FRA", "AMY", "HOL"), "CTO", "NWY", "VIA", ("NTH",)),
        ]

        orders = [
            (("FRA", "FLT", "NTH"), "CVY", ("FRA", "AMY", "HOL"), "CTO", "NWY"),
            (("FRA", "AMY", "HOL"), "CTO", "NWY", "VIA", ("NTH")),
        ]
        random.seed(15)
        assert random_list_orders(orders) == [
            (("FRA", "FLT", "NTH"), "CVY", ("FRA", "AMY", "HOL"), "CTO", "EDI"),
            (("FRA", "AMY", "HOL"), "CTO", "DEN", "VIA", ("NTH",)),
        ]

        # This tests the ability for string_to_tuple to convert this string representing
        # a "convoy to" order properly

        tup = string_to_tuple("((FRA AMY BUR) CTO BAR VIA (NTH NEA))")
        assert (
            tup
            and isinstance(tup, Tuple)
            and tup == (("FRA", "AMY", "BUR"), "CTO", "BAR", "VIA", ("NTH", "NEA"))
        )

        # The same goes for string_to_tuple
        tup_string = tuple_to_string(
            (("FRA", "AMY", "BUR"), "CTO", "BAR", "VIA", ("NTH", "NEA"))
        )
        assert tup_string and isinstance(tup_string, str)
        assert tup_string == "(FRA AMY BUR) CTO BAR VIA (NTH NEA) "

        # This tests the function randomize_joiner which makes sure that the orders ouput are different than the orders input
        test_string = "AND ((FRA AMY BUR) MTO BEL) ((FRA AMY PIC) CTO FIN VIA (NTH SKA DEN BAL BOT))"
        assert test_string != randomize_order(test_string)

        # These following tests test the validity of orders that the randomizer can generate
        assert valid_MTO((("FRA", "AMY", "HOL"), "MTO", "BEL"))
        assert valid_SUP(
            (("FRA", "AMY", "BUR"), "SUP", ("FRA", "AMY", "PIC"), "MTO", "PAR")
        )
        assert valid_CVY(
            (("FRA", "FLT", "NTH"), "CVY", ("FRA", "AMY", "PIC"), "CTO", "NWY")
        )
        assert valid_CTO(
            (
                ("FRA", "AMY", "PIC"),
                "CTO",
                "FIN",
                "VIA",
                ("NTH", "SKA", "DEN", "BAL", "BOT"),
            )
        )
        assert valid_RTO((("FRA", "AMY", "BUR"), "RTO", "PIC"))
        assert valid_BLD((("FRA", "AMY", "BUR"), "BLD"))
        assert valid_REM((("FRA", "AMY", "BUR"), "REM"))
        assert valid_DSB((("FRA", "AMY", "BUR"), "DSB"))
        assert valid_WVE(("FRA", "WVE"))


countries = {"FRA", "ENG", "GER", "ITA", "TUR", "RUS", "AUS"}
utypes = {"AMY", "FLT"}  # unit types


def valid_order_structure(order: Tuple) -> bool:
    valid_order_tags = {
        "MTO",
        "RTO",
        "CTO",
        "HLD",
        "CVY",
        "BLD",
        "DSB",
        "SUP",
        "WVE",
        "REM",
    }
    assert order[1] in valid_order_tags


def valid_unit(unit: Tuple) -> bool:
    types = isinstance(unit, Tuple) and len(unit) == 3
    vals = (
        isinstance(unit[0], str)
        and unit[0] in countries
        and isinstance(unit[1], str)
        and unit[1] in utypes
        and isinstance(unit[2], str)
        and unit[2] in ADJACENCY
    )
    return types and vals


def valid_MTO(order: Tuple) -> bool:
    return (
        order
        and valid_unit(order[0])
        and order[2]
        and isinstance(order[2], str)
        and order[2] in ADJACENCY
    )


def valid_SUP(order: Tuple) -> bool:
    valid_sup = (
        order[0]
        and isinstance(order[0], Tuple)
        and order[1]
        and isinstance(order[1], str)
        and order[2]
        and isinstance(order[2], Tuple)
    )
    valid_u1 = valid_unit(order[0])
    valid_u2 = valid_unit(order[2])
    if len(order) == 5:
        valid_ord = (
            order[3] and order[3] == "MTO" and order[4] and order[4] in ADJACENCY
        )
        return valid_ord and valid_sup and valid_u1 and valid_u2
    else:
        return len(order) == 3 and valid_sup and valid_u1 and valid_u2


def valid_CVY(order: Tuple) -> bool:
    return (
        valid_unit(order[0])
        and valid_unit(order[2])
        and len(order) == 5
        and order[3] == "CTO"
        and order[4] in ADJACENCY
    )


def valid_CTO(order: Tuple) -> bool:
    return (
        valid_unit(order[0])
        and len(order) == 5
        and order[2] in ADJACENCY
        and order[3] == "VIA"
        and isinstance(order[4], Tuple)
    )


def valid_RTO(order: Tuple) -> bool:
    return len(order) == 3 and valid_unit(order[0]) and order[1] == "RTO"


def valid_DSB(order: Tuple) -> bool:
    return len(order) == 2 and valid_unit(order[0]) and order[1] == "DSB"


def valid_BLD(order: Tuple) -> bool:
    return len(order) == 2 and valid_unit(order[0]) and order[1] == "BLD"


def valid_REM(order: Tuple) -> bool:
    return len(order) == 2 and valid_unit(order[0]) and order[1] == "REM"


def valid_WVE(order: Tuple) -> bool:
    return len(order) == 2 and order[0] in countries and order[1] == "WVE"
