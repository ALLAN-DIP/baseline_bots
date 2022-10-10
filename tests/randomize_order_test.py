from baseline_bots.randomize_order import random_list_orders, string_to_tuple, tuple_to_string, randomize_order
from typing import Tuple
import random
class TestRandomizeDipnet:
    def test(self):

        # The following three tests check that build, disband and remove commands do not get changed when input into the order randomizer.

        ord =  [(('FRA', "AMY", 'PAR'), 'BLD')]
        assert ord == random_list_orders(ord)

        ord =  [(('FRA', "AMY", 'PAR'), 'DSB')]
        assert ord == random_list_orders(ord)

        ord =  [(('FRA', "AMY", 'PAR'), 'REM')]
        assert ord == random_list_orders(ord)

        # The following three tests check that when orders that contain movements, holds, convoys and other moves get
        # input into the order randomizer, they come out differnent.

        orders = [(("FRA", "FLT", "NTH"), "CVY", ('FRA', 'AMY', 'HOL'), 'CTO', "NWY"), (("FRA", "AMY", "HOL"), "CTO", 'NWY',"VIA", ('NTH')), (("FRA", "AMY", "BER"), "HLD")]
        assert(random_list_orders(orders) != orders)    

        orders = [(("FRA", "AMY", "PIC"), "MTO", "PAR"), (("FRA", "AMY", "BUR"), "HLD"), (("FRA", "AMY", "BER"), "HLD")]
        assert random_list_orders(orders) != orders

        orders = [(("FRA", "AMY", "PIC"), "MTO", "PAR"), (("FRA", "AMY", "BUR"), "SUP", ('FRA', 'AMY', "PIC"),"MTO", "PAR"), (("FRA", "AMY", "BER"), "HLD")]
        assert random_list_orders(orders) != orders

        # These following two tests ensure that the valid values are being returned when calling random_list_orders with a seed.

        orders = [(("FRA", "FLT", "NTH"), "CVY", ('FRA', 'AMY', 'HOL'), 'CTO', "NWY"), (("FRA", "AMY", "HOL"), "CTO", 'NWY',"VIA", ('NTH'))]
        random.seed(1)
        assert random_list_orders(orders) == [(('FRA', 'FLT', 'NTH'), 'MTO', 'DEN'), (('FRA', 'AMY', 'HOL'), 'MTO', 'NTH')]

        orders = [(("FRA", "FLT", "NTH"), "CVY", ('FRA', 'AMY', 'HOL'), 'CTO', "NWY"), (("FRA", "AMY", "HOL"), "CTO", 'NWY',"VIA", ('NTH'))]
        random.seed(15)
        assert random_list_orders(orders) ==[(('FRA', 'FLT', 'NTH'), 'HLD'), (('FRA', 'AMY', 'HOL'), 'MTO', 'BEL')]
        
        # This tests the ability for string_to_tuple to convert this string representing
        # a "convoy to" order properly

        tup = string_to_tuple("((FRA AMY BUR) CTO BAR VIA (NTH NEA))")
        assert tup and isinstance(tup, Tuple) and tup == (('FRA', 'AMY', 'BUR'), 'CTO', 'BAR', 'VIA', ('NTH', 'NEA'))

        # The same goes for string_to_tuple
        tup_string = tuple_to_string((('FRA', 'AMY', 'BUR'), 'CTO', 'BAR', 'VIA', ('NTH', 'NEA')))
        assert tup_string and isinstance(tup_string, str) 
        assert tup_string == "(FRA AMY BUR) CTO BAR VIA (NTH NEA) "

        # This tests the function randomize_joiner which makes sure that the orders ouput are different than the orders input
        test_string = "AND ((FRA AMY BUR) MTO BEL) ((FRA AMY PIC) CTO FIN VIA (NTH SKA DEN BAL BOT))"
        assert test_string != randomize_order(test_string)
