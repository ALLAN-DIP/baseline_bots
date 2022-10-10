from baseline_bots.utils import OrdersData, sort_messages_by_most_recent, parse_FCT, parse_PRP, parse_orr_xdo
from baseline_bots.parsing_utils import dipnet_to_daide_parsing, daide_to_dipnet_parsing, parse_proposal_messages
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
            (["A PAR H"], ["(FRA AMY PAR) HLD"]),
            (["A PAR - MAR"], ["(FRA AMY PAR) MTO MAR"]),
            (["A PAR R MAR"], ["(FRA AMY PAR) MTO MAR"]),
            (["A BUD S F TRI"], ["(AUS AMY BUD) SUP (AUS FLT TRI)"]),
            (["A PAR S A MAR - BUR"], ["(FRA AMY PAR) SUP (FRA AMY MAR) MTO BUR"]),
        ]

        for tc_ip, tc_op in PARSING_TEST_CASES:
            assert dipnet_to_daide_parsing(tc_ip, Game()) == tc_op, dipnet_to_daide_parsing(tc_ip, Game())
            assert daide_to_dipnet_parsing(tc_op[0])[0] == tc_ip[0].replace(" R ", " - "), daide_to_dipnet_parsing(tc_op[0])
            print(tc_ip, " --> ", tc_op)
        
        # Tests for convoy orders
        PARSING_CVY_TEST_CASES = [
            (["A TUN - SYR VIA", "F ION C A TUN - SYR", "F EAS C A TUN - SYR"], ["(ITA AMY TUN) CTO SYR VIA (ION EAS)", "(ITA FLT ION) CVY (ITA AMY TUN) CTO SYR", "(ITA FLT EAS) CVY (ITA AMY TUN) CTO SYR"])
        ]

        game_tc = Game()
        game_tc.set_units("ITALY", ["A TUN", "F ION", "F EAS"])

        for tc_ip, tc_op in PARSING_CVY_TEST_CASES:
            assert dipnet_to_daide_parsing(tc_ip, game_tc) == tc_op, dipnet_to_daide_parsing(tc_ip, game_tc)
            print(tc_ip, " --> ", tc_op)
            for tc_ip_ord, tc_op_ord in zip(tc_ip, tc_op):
                assert daide_to_dipnet_parsing(tc_op_ord)[0] == tc_ip_ord.replace(" R ", " - "), daide_to_dipnet_parsing(tc_op_ord)
        

        # Tests for parse_proposal_messages
        PARSE_PROPOSALS_TC = [
            [
                "RUSSIA",
                {
                    "GERMANY": "PRP (ORR (XDO ((RUS AMY WAR) MTO PRU)) (XDO ((RUS FLT SEV) MTO RUM)) (XDO ((RUS AMY PRU) MTO LVN)))",
                    "AUSTRIA": "PRP (XDO ((RUS AMY MOS) SUP (RUS FLT STP/SC) MTO LVN)))",
                    "ENGLAND": "PRP (XDO ((RUS AMY PRU) MTO LVN)))"
                }, 
                [
                    {
                        "GERMANY": ["A WAR - PRU", "F SEV - RUM"],
                        "AUSTRIA": ["A MOS S F STP/SC - LVN"]
                    },
                    {
                        "GERMANY": ["A PRU - LVN"],
                        "ENGLAND": ["A PRU - LVN"]
                    },
                    {},
                    {}
                ]
            ],
            [
                "TURKEY",
                {
                    "RUSSIA": "PRP(XDO((TUR FLT ANK) MTO BLA) AND XDO((RUS AMY SEV) MTO RUM) AND (XDO((ENG AMY LVP) HLD)))"
                }, 
                [
                    {
                        "RUSSIA": ["F ANK - BLA"]
                    },
                    {},
                    {
                        "RUSSIA": ["A SEV - RUM"]
                    },
                    {
                        "RUSSIA": ["A LVP H"]
                    }
                ]
            ]
        ]
        game_GTP = Game()
        for power_name, tc_ip, tc_op in PARSE_PROPOSALS_TC:
            for sender in tc_ip:
                msg_obj = Message(
                    sender=sender,
                    recipient=power_name,
                    message=tc_ip[sender],
                    phase=game_GTP.get_current_phase(),
                )
                game_GTP.add_message(message=msg_obj)
            valid_proposals, invalid_proposals, shared_orders, other_orders = parse_proposal_messages(game_GTP.filter_messages(messages=game_GTP.messages, game_role=power_name), game_GTP, power_name)
            # print(valid_proposals)
            # print(invalid_proposals)
            # print(shared_orders)
            # print(other_orders)

            assert set(valid_proposals.keys()) == set(tc_op[0].keys()), (set(valid_proposals.keys()), set(tc_op[0].keys()))
            assert set(invalid_proposals.keys()) == set(tc_op[1].keys()), (set(invalid_proposals.keys()), set(tc_op[1].keys()))
            assert set(shared_orders.keys()) == set(tc_op[2].keys()), (set(shared_orders.keys()), set(tc_op[2].keys()))
            assert set(other_orders.keys()) == set(tc_op[3].keys()), (set(other_orders.keys()), set(tc_op[3].keys()))
            
            for key in valid_proposals:
                assert set(valid_proposals[key]) == set(tc_op[0][key])
            
            for key in invalid_proposals:
                assert set(invalid_proposals[key]) == set(tc_op[1][key])

            for key in shared_orders:
                assert set(shared_orders[key]) == set(tc_op[2][key])
            
            for key in other_orders:
                assert set(other_orders[key]) == set(tc_op[3][key])

        # Tests for orders extraction
        FCT_TCS = [
            [
                "FCT (XDO (F BLK - CON))", 
                "XDO (F BLK - CON)"
            ],
            [
                "FCT(XDO (F BLK - CON))", 
                "XDO (F BLK - CON)"
            ]
        ]
        for tc_ip, tc_op in FCT_TCS:
            assert parse_FCT(tc_ip) == tc_op, parse_FCT(tc_ip)
            
        PRP_TCS = [
            [
                "PRP (XDO (F BLK - CON))", 
                "XDO (F BLK - CON)"
            ],
            [
                "PRP(XDO (F BLK - CON))", 
                "XDO (F BLK - CON)"
            ]
        ]
        for tc_ip, tc_op in PRP_TCS:
            assert parse_PRP(tc_ip) == tc_op, parse_PRP(tc_ip)

        XDO_ORR_TCS = [
            [
                "XDO (F BLK - CON)",
                ["F BLK - CON"]
            ], 
            [
                "XDO (F BLK - CON)",
                ["F BLK - CON"]
            ],
            [
                "XDO(F BLK - CON)",
                ["F BLK - CON"]
            ],
            [
                "ORR((XDO(F BLK - CON))(XDO(A RUM - BUD))(XDO(F BLK - BUD)))",
                ["F BLK - CON", "A RUM - BUD", "F BLK - BUD"]
            ],
            [
                "ORR ( (XDO (F BLK - CON)) (XDO (A RUM - BUD)))",
                ["F BLK - CON", "A RUM - BUD"]
            ]
        ]
        
        for tc_ip, tc_op in XDO_ORR_TCS:
            assert parse_orr_xdo(tc_ip) == tc_op, parse_orr_xdo(tc_ip)