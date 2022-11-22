from diplomacy import Game, Message

from baseline_bots.parsing_utils import (
    daide_to_dipnet_parsing,
    dipnet_to_daide_parsing,
    parse_proposal_messages,
)
from baseline_bots.utils import (
    OrdersData,
    get_order_tokens,
    parse_arrangement,
    parse_FCT,
    parse_PRP,
    smart_select_support_proposals,
    sort_messages_by_most_recent,
)


class TestUtils:
    def test_get_list_of_orders(self):
        EXAMPLE_ORDER = "A VIE S A BUD - GAL"
        EXAMPLE_ORDER_2 = "A VIE H"

        orders_data = OrdersData()

        # test regular add
        orders_data.add_order(EXAMPLE_ORDER)
        assert orders_data.get_list_of_orders() == ["A VIE S A BUD - GAL"]

        # test guarded add
        orders_data.add_order(EXAMPLE_ORDER_2, overwrite=False)
        assert orders_data.get_list_of_orders() == ["A VIE S A BUD - GAL"]

        orders_data.add_order(EXAMPLE_ORDER_2, overwrite=True)
        assert orders_data.get_list_of_orders() == ["A VIE H"]

    def test_sort_messages_by_most_recent(self):
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

    def test_dipnet_to_daide_parsing(self):
        # Tests for utils.dipnet_to_daide_parsing
        PARSING_TEST_CASES = [
            (["A PAR H"], ["(FRA AMY PAR) HLD"], False),
            (["F STP/SC H"], ["(RUS FLT (STP SCS)) HLD"], False),
            ([("A PAR H", "ENG")], ["(ENG AMY PAR) HLD"], True),
            (["A PAR - MAR"], ["(FRA AMY PAR) MTO MAR"], False),
            (["A PAR R MAR"], ["(FRA AMY PAR) MTO MAR"], False),
            (["F STP/SC - BOT"], ["(RUS FLT (STP SCS)) MTO BOT"], False),
            (["A CON - BUL"], ["(TUR AMY CON) MTO BUL"], False),
            (["F BLA - BUL/EC"], ["(TUR FLT BLA) MTO (BUL ECS)"], False),
            (["A BUD S F TRI"], ["(AUS AMY BUD) SUP (AUS FLT TRI)"], False),
            (
                ["A PAR S A MAR - BUR"],
                ["(FRA AMY PAR) SUP (FRA AMY MAR) MTO BUR"],
                False,
            ),
            (
                ["A MOS S F STP/SC - LVN"],
                ["(RUS AMY MOS) SUP (RUS FLT (STP SCS)) MTO LVN"],
                False,
            ),
            (
                ["A SMY S A CON - BUL"],
                ["(TUR AMY SMY) SUP (TUR AMY CON) MTO BUL"],
                False,
            ),
            (
                ["A CON S F BLA - BUL/EC"],
                ["(TUR AMY CON) SUP (TUR FLT BLA) MTO (BUL ECS)"],
                False,
            ),
        ]

        game_tc = Game()
        game_tc.set_units("TURKEY", ["F BLA"])

        for tc_ip, tc_op, unit_power_tuples_included in PARSING_TEST_CASES:
            assert (
                dipnet_to_daide_parsing(
                    tc_ip,
                    game_tc,
                    unit_power_tuples_included=unit_power_tuples_included,
                )
                == tc_op
            ), (
                dipnet_to_daide_parsing(
                    tc_ip,
                    game_tc,
                    unit_power_tuples_included=unit_power_tuples_included,
                ),
                tc_op,
            )
            comparison_tc_op = (
                tc_ip[0].replace(" R ", " - ")
                if type(tc_ip[0]) == str
                else tc_ip[0][0].replace(" R ", " - ")
            )
            assert daide_to_dipnet_parsing(tc_op[0])[0] == comparison_tc_op, (
                daide_to_dipnet_parsing(tc_op[0]),
                comparison_tc_op,
            )

    def test_dipnet_to_daide_parsing_convoys(self):
        # Tests for convoy orders
        PARSING_CVY_TEST_CASES = [
            (
                ["A TUN - SYR VIA", "F ION C A TUN - SYR", "F EAS C A TUN - SYR"],
                [
                    "(ITA AMY TUN) CTO SYR VIA (ION EAS)",
                    "(ITA FLT ION) CVY (ITA AMY TUN) CTO SYR",
                    "(ITA FLT EAS) CVY (ITA AMY TUN) CTO SYR",
                ],
            ),
            (
                ["A TUN - BUL VIA", "F ION C A TUN - BUL", "F AEG C A TUN - BUL"],
                [
                    "(ITA AMY TUN) CTO BUL VIA (ION AEG)",
                    "(ITA FLT ION) CVY (ITA AMY TUN) CTO BUL",
                    "(ITA FLT AEG) CVY (ITA AMY TUN) CTO BUL",
                ],
            ),
        ]

        game_tc = Game()
        game_tc.set_units("ITALY", ["A TUN", "F ION", "F EAS", "F AEG"])

        for tc_ip, tc_op in PARSING_CVY_TEST_CASES:
            assert dipnet_to_daide_parsing(tc_ip, game_tc) == tc_op, (
                dipnet_to_daide_parsing(tc_ip, game_tc),
                tc_op,
            )
            for tc_ip_ord, tc_op_ord in zip(tc_ip, tc_op):
                assert daide_to_dipnet_parsing(tc_op_ord)[0] == tc_ip_ord.replace(
                    " R ", " - "
                ), (daide_to_dipnet_parsing(tc_op_ord), tc_ip_ord.replace(" R ", " - "))

    def test_parse_proposal_messages(self):
        # Tests for parse_proposal_messages
        PARSE_PROPOSALS_TC = [
            [
                "RUSSIA",
                {
                    "GERMANY": "PRP (ORR (XDO ((RUS AMY WAR) MTO PRU)) (XDO ((RUS FLT SEV) MTO RUM)) (XDO ((RUS AMY PRU) MTO LVN)))",
                    "AUSTRIA": "PRP (XDO ((RUS AMY MOS) SUP (RUS FLT STP/SC) MTO LVN)))",
                    "ENGLAND": "PRP (XDO ((RUS AMY PRU) MTO LVN)))",
                },
                {
                    "valid_proposals": {
                        "GERMANY": ["A WAR - PRU", "F SEV - RUM"],
                        "AUSTRIA": ["A MOS S F STP/SC - LVN"],
                    },
                    "invalid_proposals": {
                        "GERMANY": [("A PRU - LVN", "RUS")],
                        "ENGLAND": [("A PRU - LVN", "RUS")],
                    },
                    "shared_orders": {},
                    "other_orders": {},
                    "alliance_proposals": {},
                },
            ],
            [
                "RUSSIA",
                {
                    "GERMANY": "PRP (ORR (XDO ((RUS AMY WAR) MTO PRU)) (ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)) (ABC ((RUS AMY WAR) MTO PRU)))",
                    "AUSTRIA": "PRP (ALY (AUS RUS) VSS (FRA ENG ITA TUR GER))",
                },
                {
                    "valid_proposals": {"GERMANY": ["A WAR - PRU"]},
                    "invalid_proposals": {},
                    "shared_orders": {},
                    "other_orders": {"GERMANY": ["ABC ((RUS AMY WAR) MTO PRU)"]},
                    "alliance_proposals": {
                        "GERMANY": [
                            ("GERMANY", "ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)")
                        ],
                        "ENGLAND": [
                            ("GERMANY", "ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)")
                        ],
                        "ITALY": [
                            ("GERMANY", "ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)")
                        ],
                        "AUSTRIA": [
                            ("AUSTRIA", "ALY (AUS RUS) VSS (FRA ENG ITA TUR GER)")
                        ],
                    },
                },
            ],
            [
                "TURKEY",
                {
                    "RUSSIA": "PRP(XDO((TUR FLT ANK) MTO BLA) AND XDO((RUS AMY SEV) MTO RUM) AND (XDO((ENG AMY LVP) HLD)))"
                },
                {
                    "valid_proposals": {"RUSSIA": ["F ANK - BLA"]},
                    "invalid_proposals": {},
                    "shared_orders": {"RUSSIA": ["A SEV - RUM"]},
                    "other_orders": {"RUSSIA": ["A LVP H"]},
                    "alliance_proposals": {},
                },
            ],
            [
                "TURKEY",
                {
                    "RUSSIA": "PRP(XDO((TUR FLT ANK) MTO BLA) AND XDO((RUS AMY SEV) MTO RUM) AND (XDO((ENG AMY LVP) HLD)) AND (ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)) AND (ABC ((RUS AMY WAR) MTO PRU) ) )"
                },
                {
                    "valid_proposals": {"RUSSIA": ["F ANK - BLA"]},
                    "invalid_proposals": {},
                    "shared_orders": {"RUSSIA": ["A SEV - RUM"]},
                    "other_orders": {
                        "RUSSIA": ["A LVP H", "ABC ((RUS AMY WAR) MTO PRU)"]
                    },
                    "alliance_proposals": {
                        "RUSSIA": [
                            ("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")
                        ],
                        "ENGLAND": [
                            ("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")
                        ],
                        "ITALY": [
                            ("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")
                        ],
                    },
                },
            ],
            [
                "ENGLAND",
                {
                    "FRANCE": "PRP(AND(XDO((ENG AMY LVP) MTO WAL))(XDO((ENG FLT EDI) MTO NTH))(XDO((ENG FLT LON) MTO ENG)))"
                },
                {
                    "valid_proposals": {
                        "FRANCE": ["A LVP - WAL", "F EDI - NTH", "F LON - ENG"]
                    },
                    "invalid_proposals": {},
                    "shared_orders": {},
                    "other_orders": {},
                    "alliance_proposals": {},
                },
            ],
        ]
        for power_name, tc_ip, tc_op in PARSE_PROPOSALS_TC:
            game_GTP = Game()
            for sender in tc_ip:
                msg_obj = Message(
                    sender=sender,
                    recipient=power_name,
                    message=tc_ip[sender],
                    phase=game_GTP.get_current_phase(),
                )
                game_GTP.add_message(message=msg_obj)
            msgs = (
                game_GTP.filter_messages(
                    messages=game_GTP.messages, game_role=power_name
                )
            ).items()
            parsed_orders_dict = parse_proposal_messages(msgs, game_GTP, power_name)
            # print(tc_ip)
            # print(parsed_orders_dict)

            assert set(parsed_orders_dict.keys()) == set(tc_op.keys())
            for pod_key in parsed_orders_dict:
                assert set(parsed_orders_dict[pod_key].keys()) == set(
                    tc_op[pod_key].keys()
                ), (
                    pod_key,
                    set(parsed_orders_dict[pod_key].keys()),
                    set(tc_op[pod_key].keys()),
                )

                for key in parsed_orders_dict[pod_key]:
                    assert set(parsed_orders_dict[pod_key][key]) == set(
                        tc_op[pod_key][key]
                    ), (
                        pod_key,
                        key,
                        set(parsed_orders_dict[pod_key][key]),
                        set(tc_op[pod_key][key]),
                    )

    def test_parse_FCT(self):
        # Tests for orders extraction
        FCT_TCS = [
            ["FCT (XDO (F BLK - CON))", "XDO (F BLK - CON)"],
            ["FCT(XDO (F BLK - CON))", "XDO (F BLK - CON)"],
        ]
        for tc_ip, tc_op in FCT_TCS:
            assert parse_FCT(tc_ip) == tc_op, parse_FCT(tc_ip)

    def test_parse_PRP(self):
        PRP_TCS = [
            ["PRP (XDO (F BLK - CON))", "XDO (F BLK - CON)"],
            ["PRP(XDO (F BLK - CON))", "XDO (F BLK - CON)"],
        ]
        for tc_ip, tc_op in PRP_TCS:
            assert parse_PRP(tc_ip) == tc_op, parse_PRP(tc_ip)

    def test_parse_arrangement(self):
        ORR_TCS = [
            ["XDO (F BLK - CON)", ["F BLK - CON"]],
            ["XDO (F BLK - CON)", ["F BLK - CON"]],
            ["XDO(F BLK - CON)", ["F BLK - CON"]],
            [
                "ORR (XDO(F BLK - CON))(XDO(A RUM - BUD))(XDO(F BLK - BUD))",
                ["F BLK - CON", "A RUM - BUD", "F BLK - BUD"],
            ],
            [
                "ORR (XDO (F BLK - CON)) (XDO (A RUM - BUD))",
                ["F BLK - CON", "A RUM - BUD"],
            ],
        ]

        for tc_ip, tc_op in ORR_TCS:
            assert parse_arrangement(tc_ip, xdo_only=True) == tc_op, parse_arrangement(
                tc_ip, xdo_only=True
            )

        ORR_XDO_ALY_TCS = [
            ["XDO (F BLA - CON)", [("XDO", "F BLA - CON")]],
            ["XDO (F BLA - CON)", [("XDO", "F BLA - CON")]],
            ["XDO(F BLA - CON)", [("XDO", "F BLA - CON")]],
            [
                "ALY (GER RUS) VSS (FRA ENG ITA TUR AUS)",
                [("ALY", "ALY (GER RUS) VSS (FRA ENG ITA TUR AUS)")],
            ],
            [
                "ORR (XDO(F BLA - CON))(XDO(A RUM - BUD))(XDO(F BLA - BUD))",
                [
                    ("XDO", "F BLA - CON"),
                    ("XDO", "A RUM - BUD"),
                    ("XDO", "F BLA - BUD"),
                ],
            ],
            [
                "ORR  (XDO (F BLA - CON)) (XDO (A RUM - BUD))",
                [("XDO", "F BLA - CON"), ("XDO", "A RUM - BUD")],
            ],
            [
                "ORR (XDO (F BLA - CON)) (ALY (GER RUS TUR) VSS (FRA ENG ITA AUS))",
                [
                    ("XDO", "F BLA - CON"),
                    ("ALY", "ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)"),
                ],
            ],
            [
                "ORR (XDO ((RUS FLT BLA) MTO CON)) (ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)) (ABC (F BLA - CON))",
                [
                    ("XDO", "(RUS FLT BLA) MTO CON"),
                    ("ALY", "ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)"),
                    ("ABC", "ABC (F BLA - CON)"),
                ],
            ],
        ]

        for tc_ip, tc_op in ORR_XDO_ALY_TCS:
            assert parse_arrangement(tc_ip, xdo_only=False) == tc_op, (
                parse_arrangement(tc_ip, xdo_only=False),
                tc_op,
            )

    def test_smart_select_support_proposals(self):
        SMART_SELECT_SUPPORT_PROPOSALS = [
            [
                {
                    "A BOH": [
                        ("A BOH", "A BUD - GAL", "A BOH S A BUD - GAL"),
                        ("A BOH", "A BER - MUN", "A BOH S A BER - MUN"),
                        ("A BOH", "A MUN - TYR", "A BOH S A MUN - TYR"),
                    ],
                    "A VIE": [
                        ("A VIE", "A BUD - GAL", "A VIE S A BUD - GAL"),
                        ("A VIE", "A MUN - TYR", "A VIE S A MUN - TYR"),
                    ],
                    "A SIL": [("A SIL", "A BUD - GAL", "A SIL S A BUD - GAL")],
                    "A SER": [
                        ("A SER", "F BUL/EC - RUM", "A SER S F BUL/EC - RUM"),
                        ("A SER", "F GRE H", "A SER F GRE H"),
                    ],
                },
                {
                    "A BOH": [("A BOH", "A BUD - GAL", "A BOH S A BUD - GAL")],
                    "A VIE": [("A VIE", "A BUD - GAL", "A VIE S A BUD - GAL")],
                    "A SIL": [("A SIL", "A BUD - GAL", "A SIL S A BUD - GAL")],
                    "A SER": [
                        ("A SER", "F BUL/EC - RUM", "A SER S F BUL/EC - RUM"),
                        ("A SER", "F GRE H", "A SER F GRE H"),
                    ],
                },
            ]
        ]

        for tc_ip, tc_op in SMART_SELECT_SUPPORT_PROPOSALS:
            assert smart_select_support_proposals(tc_ip) == tc_op

    def test_get_order_tokens(self):
        GET_ORDER_TOKENS_TCS = [
            ["A PAR S A MAR - BUR", ["A PAR", "S", "A MAR", "- BUR"]],
            ["A MAR - BUR", ["A MAR", "- BUR"]],
            ["A MAR R BUR", ["A MAR", "- BUR"]],
            ["A MAR H", ["A MAR", "H"]],
            ["F BUL/EC - RUM", ["F BUL/EC", "- RUM"]],
            ["F RUM - BUL/EC", ["F RUM", "- BUL/EC"]],
        ]

        for tc_ip, tc_op in GET_ORDER_TOKENS_TCS:
            assert get_order_tokens(tc_ip) == tc_op
