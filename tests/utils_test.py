from typing import Dict, List

from diplomacy import Game, Message
import pytest

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

    DIPNET_TO_DAIDE_PARSING_TEST_CASES = [
        (["A PAR H"], ["(FRA AMY PAR) HLD"], False),
        (["F STP/SC H"], ["(RUS FLT (STP SCS)) HLD"], False),
        ([("A PAR H", "ENG")], ["(ENG AMY PAR) HLD"], True),
        (["A PAR - MAR"], ["(FRA AMY PAR) MTO MAR"], False),
        (["A PAR R MAR"], ["(FRA AMY PAR) MTO MAR"], False),
        (["F STP/SC - BOT"], ["(RUS FLT (STP SCS)) MTO GOB"], False),
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

    @pytest.mark.parametrize(
        "test_input,expected,unit_power_tuples_included",
        DIPNET_TO_DAIDE_PARSING_TEST_CASES,
    )
    def test_dipnet_to_daide_parsing(
        self,
        test_input: List[str],
        expected: List[str],
        unit_power_tuples_included: bool,
    ):
        game_tc = Game()
        game_tc.set_units("TURKEY", ["F BLA"])

        assert (
            dipnet_to_daide_parsing(
                test_input,
                game_tc,
                unit_power_tuples_included=unit_power_tuples_included,
            )
            == expected
        ), (
            dipnet_to_daide_parsing(
                test_input,
                game_tc,
                unit_power_tuples_included=unit_power_tuples_included,
            ),
            expected,
        )
        comparison_tc_op = (
            test_input[0].replace(" R ", " - ")
            if type(test_input[0]) == str
            else test_input[0][0].replace(" R ", " - ")
        )
        assert daide_to_dipnet_parsing(expected[0])[0] == comparison_tc_op, (
            daide_to_dipnet_parsing(expected[0]),
            comparison_tc_op,
        )

    DIPNET_TO_DAIDE_PARSING_CONVOY_TEST_CASES = [
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

    @pytest.mark.parametrize(
        "test_input,expected", DIPNET_TO_DAIDE_PARSING_CONVOY_TEST_CASES
    )
    def test_dipnet_to_daide_parsing_convoys(
        self, test_input: List[str], expected: List[str]
    ):
        game_tc = Game()
        game_tc.set_units("ITALY", ["A TUN", "F ION", "F EAS", "F AEG"])

        assert dipnet_to_daide_parsing(test_input, game_tc) == expected, (
            dipnet_to_daide_parsing(test_input, game_tc),
            expected,
        )
        for tc_ip_ord, tc_op_ord in zip(test_input, expected):
            assert daide_to_dipnet_parsing(tc_op_ord)[0] == tc_ip_ord.replace(
                " R ", " - "
            ), (daide_to_dipnet_parsing(tc_op_ord), tc_ip_ord.replace(" R ", " - "))

    PARSE_PROPOSAL_MESSAGES_TEST_CASES = [
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
                "peace_proposals": {},
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
                    "GERMANY": [("GERMANY", "ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)")],
                    "ENGLAND": [("GERMANY", "ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)")],
                    "ITALY": [("GERMANY", "ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)")],
                    "AUSTRIA": [("AUSTRIA", "ALY (AUS RUS) VSS (FRA ENG ITA TUR GER)")],
                },
                "peace_proposals": {},
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
                "peace_proposals": {},
            },
        ],
        [
            "TURKEY",
            {
                "RUSSIA": "PRP(XDO((TUR FLT ANK) MTO BLA) AND XDO((RUS AMY SEV) MTO RUM) AND (XDO((ENG AMY LVP) HLD)) AND (ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)) AND (ABC ((RUS AMY WAR) MTO PRU) )  AND (PCE (TUR RUS) ))"
            },
            {
                "valid_proposals": {"RUSSIA": ["F ANK - BLA"]},
                "invalid_proposals": {},
                "shared_orders": {"RUSSIA": ["A SEV - RUM"]},
                "other_orders": {"RUSSIA": ["A LVP H", "ABC ((RUS AMY WAR) MTO PRU)"]},
                "alliance_proposals": {
                    "RUSSIA": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                    "ENGLAND": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                    "ITALY": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                },
                "peace_proposals": {
                    "RUSSIA": [("RUSSIA", "PCE (TUR RUS)")],
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
                "peace_proposals": {},
            },
        ],
    ]

    @pytest.mark.parametrize(
        "power_name,test_input,expected", PARSE_PROPOSAL_MESSAGES_TEST_CASES
    )
    def test_parse_proposal_messages(
        self,
        power_name: str,
        test_input: Dict[str, str],
        expected: Dict[str, Dict[str, List[str]]],
    ):
        # Tests for parse_proposal_messages
        game_GTP = Game()
        for sender in test_input:
            msg_obj = Message(
                sender=sender,
                recipient=power_name,
                message=test_input[sender],
                phase=game_GTP.get_current_phase(),
            )
            game_GTP.add_message(message=msg_obj)
        msgs = game_GTP.filter_messages(
            messages=game_GTP.messages, game_role=power_name
        ).items()
        parsed_orders_dict = parse_proposal_messages(msgs, game_GTP, power_name)

        assert set(parsed_orders_dict.keys()) == set(expected.keys())
        for pod_key in parsed_orders_dict:
            assert set(parsed_orders_dict[pod_key].keys()) == set(
                expected[pod_key].keys()
            ), (
                pod_key,
                set(parsed_orders_dict[pod_key].keys()),
                set(expected[pod_key].keys()),
            )

            for key in parsed_orders_dict[pod_key]:
                assert set(parsed_orders_dict[pod_key][key]) == set(
                    expected[pod_key][key]
                ), (
                    pod_key,
                    key,
                    set(parsed_orders_dict[pod_key][key]),
                    set(expected[pod_key][key]),
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

    PARSE_ARRANGEMENT_TEST_CASES = [
        ["XDO (F BLK - CON)", ["F BLK - CON"], True],
        ["XDO (F BLK - CON)", ["F BLK - CON"], True],
        ["XDO(F BLK - CON)", ["F BLK - CON"], True],
        [
            "ORR (XDO(F BLK - CON))(XDO(A RUM - BUD))(XDO(F BLK - BUD))",
            ["F BLK - CON", "A RUM - BUD", "F BLK - BUD"],
            True,
        ],
        [
            "ORR (XDO (F BLK - CON)) (XDO (A RUM - BUD))",
            ["F BLK - CON", "A RUM - BUD"],
            True,
        ],
        ["XDO (F BLA - CON)", [("XDO", "F BLA - CON")], False],
        ["XDO (F BLA - CON)", [("XDO", "F BLA - CON")], False],
        ["XDO(F BLA - CON)", [("XDO", "F BLA - CON")], False],
        [
            "ALY (GER RUS) VSS (FRA ENG ITA TUR AUS)",
            [("ALY", "ALY (GER RUS) VSS (FRA ENG ITA TUR AUS)")],
            False,
        ],
        [
            "ORR (XDO(F BLA - CON))(XDO(A RUM - BUD))(XDO(F BLA - BUD))",
            [("XDO", "F BLA - CON"), ("XDO", "A RUM - BUD"), ("XDO", "F BLA - BUD")],
            False,
        ],
        [
            "ORR  (XDO (F BLA - CON)) (XDO (A RUM - BUD))",
            [("XDO", "F BLA - CON"), ("XDO", "A RUM - BUD")],
            False,
        ],
        [
            "ORR (XDO (F BLA - CON)) (ALY (GER RUS TUR) VSS (FRA ENG ITA AUS))",
            [
                ("XDO", "F BLA - CON"),
                ("ALY", "ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)"),
            ],
            False,
        ],
        [
            "ORR (XDO ((RUS FLT BLA) MTO CON)) (ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)) (ABC (F BLA - CON))",
            [
                ("XDO", "(RUS FLT BLA) MTO CON"),
                ("ALY", "ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)"),
                ("ABC", "ABC (F BLA - CON)"),
            ],
            False,
        ],
    ]

    @pytest.mark.parametrize(
        "test_input,expected,xdo_only", PARSE_ARRANGEMENT_TEST_CASES
    )
    def test_parse_arrangement(
        self, test_input: str, expected: List[str], xdo_only: bool
    ):
        assert (
            parse_arrangement(test_input, xdo_only=xdo_only) == expected
        ), parse_arrangement(test_input, xdo_only=xdo_only)

    def test_smart_select_support_proposals(self):
        test_input = {
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
        }
        expected = {
            "A BOH": [("A BOH", "A BUD - GAL", "A BOH S A BUD - GAL")],
            "A VIE": [("A VIE", "A BUD - GAL", "A VIE S A BUD - GAL")],
            "A SIL": [("A SIL", "A BUD - GAL", "A SIL S A BUD - GAL")],
            "A SER": [
                ("A SER", "F BUL/EC - RUM", "A SER S F BUL/EC - RUM"),
                ("A SER", "F GRE H", "A SER F GRE H"),
            ],
        }

        assert smart_select_support_proposals(test_input) == expected

    GET_ORDER_TOKENS_TEST_CASES = [
        ["A PAR S A MAR - BUR", ["A PAR", "S", "A MAR", "- BUR"]],
        ["A MAR - BUR", ["A MAR", "- BUR"]],
        ["A MAR R BUR", ["A MAR", "- BUR"]],
        ["A MAR H", ["A MAR", "H"]],
        ["F BUL/EC - RUM", ["F BUL/EC", "- RUM"]],
        ["F RUM - BUL/EC", ["F RUM", "- BUL/EC"]],
    ]

    @pytest.mark.parametrize("test_input,expected", GET_ORDER_TOKENS_TEST_CASES)
    def test_get_order_tokens(self, test_input: str, expected: List[str]):
        assert get_order_tokens(test_input) == expected
