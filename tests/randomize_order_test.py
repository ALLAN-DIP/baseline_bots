import random

from baseline_bots.randomize_order import random_list_orders
from baseline_bots.utils import parse_daide


class TestRandomizeDipnet:
    def test(self):
        # The following three tests check that build, disband and remove commands do not get changed when input into the order randomizer.

        orders = [parse_daide("(FRA AMY PAR) BLD")]
        assert orders == random_list_orders(orders)

        orders = [parse_daide("(FRA AMY PAR) DSB")]
        assert orders == random_list_orders(orders)

        orders = [parse_daide("(FRA AMY PAR) REM")]
        assert orders == random_list_orders(orders)

        # The following three tests check that when orders that contain movements, holds, convoys and other moves get
        # input into the order randomizer, they come out different.

        orders = [
            parse_daide("(FRA FLT NTH) CVY (FRA AMY HOL) CTO NWY"),
            parse_daide("(FRA AMY HOL) CTO NWY VIA (NTH)"),
            parse_daide("(FRA AMY BER) HLD"),
        ]
        assert random_list_orders(orders) != orders

        orders = [
            parse_daide("(FRA AMY PIC) MTO PAR"),
            parse_daide("(FRA AMY BUR) HLD"),
            parse_daide("(FRA AMY BER) HLD"),
        ]
        assert random_list_orders(orders) != orders

        orders = [
            parse_daide("(FRA AMY PIC) MTO PAR"),
            parse_daide("(FRA AMY BUR) SUP (FRA AMY PIC) MTO PAR"),
            parse_daide("(FRA AMY BER) HLD"),
        ]
        assert random_list_orders(orders) != orders

        # These following two tests ensure that the valid values are being returned when calling random_list_orders with a seed.

        orders = [
            parse_daide("(FRA FLT NTH) CVY (FRA AMY HOL) CTO NWY"),
            parse_daide("(FRA AMY HOL) CTO NWY VIA (NTH)"),
        ]
        random.seed(1)
        assert random_list_orders(orders) == [
            parse_daide("(FRA FLT NTH) CVY (FRA AMY HOL) CTO EDI"),
            parse_daide("(FRA AMY HOL) CTO NWY VIA (NTH)"),
        ]
        random.seed(15)
        assert random_list_orders(orders) == [
            parse_daide("(FRA FLT NTH) CVY (FRA AMY HOL) CTO EDI"),
            parse_daide("(FRA AMY HOL) CTO DEN VIA (NTH)"),
        ]
