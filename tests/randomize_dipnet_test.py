from baseline_bots.randomize_dipnet import random_orders, string_to_tuple
from typing import Tuple
class TestUtils:
    def test(self):

        # The following three tests check that build, disband and remove commands do not get changed when input into the order randomizer.

        ord =  [(('FRA', "AMY", 'PAR'), 'BLD')]
        assert ord == random_orders(ord)

        ord =  [(('FRA', "AMY", 'PAR'), 'DSB')]
        assert ord == random_orders(ord)

        ord =  [(('FRA', "AMY", 'PAR'), 'REM')]
        assert ord == random_orders(ord)

        # The following three tests check that when orders that contain movements, holds, convoys and other moves get
        # input into the order randomizer, they come out differnent

        orders = [(("FRA", "FLT", "NTH"), "CVY", ('FRA', 'AMY', 'HOL'), 'CTO', "NWY"), (("FRA", "AMY", "HOL"), "CTO", 'NWY',"VIA", ('NTH')), (("FRA", "AMY", "BER"), "HLD")]
        assert(random_orders(orders) != orders)    

        orders = [(("FRA", "AMY", "PIC"), "MTO", "PAR"), (("FRA", "AMY", "BUR"), "HLD"), (("FRA", "AMY", "BER"), "HLD")]
        assert random_orders(orders) != orders

        orders = [(("FRA", "AMY", "PIC"), "MTO", "PAR"), (("FRA", "AMY", "BUR"), "SUP", ('FRA', 'AMY', "PIC"),"MTO", "PAR"), (("FRA", "AMY", "BER"), "HLD")]
        assert random_orders(orders) != orders

        # This tests the ability for string_to_tuple to convert this string representing
        # a "convoy to" order properly

        tup = string_to_tuple("((FRA AMY BUR) CTO BAR VIA (NTH NEA))")
        assert tup and isinstance(tup, Tuple) and tup == (('FRA', 'AMY', 'BUR'), 'CTO', 'BAR', 'VIA', ('NTH', 'NEA'))


