from baseline_bots.utils import OrdersData, sort_messages_by_most_recent, dipnet_to_daide_parsing, daide_to_dipnet_parsing
from diplomacy import Game, Message

class TestUtils:
    def test(self):
        EXAMPLE_ORDER = 'A VIE S A BUD - GAL'
        EXAMPLE_ORDER_2 = 'A VIE H'

        orders_data = OrdersData()

        # test regular add
        orders_data.add_order(EXAMPLE_ORDER)
        assert orders_data.get_list_of_orders() == ['A VIE S A BUD - GAL']

        # test guarded add
        orders_data.add_order(EXAMPLE_ORDER_2, overwrite=False)
        assert orders_data.get_list_of_orders() == ['A VIE S A BUD - GAL']

        orders_data.add_order(EXAMPLE_ORDER_2, overwrite=True)
        assert orders_data.get_list_of_orders() == ['A VIE H']


        # test sort_messages_by_most_recent
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

        # Tests for utils.dipnet_to_daide_parsing
        PARSING_TEST_CASES = [
            ("A PAR H", "(FRA AMY PAR) HLD"),
            ("A PAR - MAR", "(FRA AMY PAR) MTO MAR"),
            ("A PAR R MAR", "(FRA AMY PAR) MTO MAR"),
            ("A BUD S F TRI", "(AUS AMY BUD) SUP (AUS FLT TRI)"),
            ("A PAR S A MAR - BUR", "(FRA AMY PAR) SUP (FRA AMY MAR) MTO BUR"),
        ]

        for tc_ip, tc_op in PARSING_TEST_CASES:
            print(tc_ip + " --> " + tc_op)
            assert dipnet_to_daide_parsing(tc_ip) == tc_op
            assert daide_to_dipnet_parsing(tc_op) == tc_ip.replace(" R ", " - "), daide_to_dipnet_parsing(tc_op)