from baseline_bots.randomize_dipnet import string_to_tuple, tuple_to_string, randomize_joiner
from typing import Tuple

class TestUtils:
    def test(self):
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
        assert test_string != randomize_joiner(test_string)