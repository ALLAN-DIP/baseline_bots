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
    parse_daide,
)


class TestUtils:
    def test_get_list_of_orders(self) -> None:
        EXAMPLE_ORDER = "A VIE S A BUD - GAL"
        EXAMPLE_ORDER_2 = "A VIE H"

        orders_data = OrdersData()

        # test initial add
        orders_data.add_order(EXAMPLE_ORDER)
        assert list(orders_data) == ["A VIE S A BUD - GAL"]

        # test overwrite add
        orders_data.add_order(EXAMPLE_ORDER_2)
        assert list(orders_data) == ["A VIE H"]

    DIPNET_TO_DAIDE_PARSING_TEST_CASES = [
        (["A PAR H"], ["( FRA AMY PAR ) HLD"], False),
        (["F STP/SC H"], ["( RUS FLT (STP SCS) ) HLD"], False),
        ([("A PAR H", "ENG")], ["( ENG AMY PAR ) HLD"], True),
        (["A PAR - MAR"], ["( FRA AMY PAR ) MTO MAR"], False),
        (["A PAR R MAR"], ["( FRA AMY PAR ) MTO MAR"], False),
        (["F STP/SC - BOT"], ["( RUS FLT (STP SCS) ) MTO GOB"], False),
        (["A CON - BUL"], ["( TUR AMY CON ) MTO BUL"], False),
        (["F BLA - BUL/EC"], ["( TUR FLT BLA ) MTO (BUL ECS)"], False),
        (["A BUD S F TRI"], ["( AUS AMY BUD ) SUP ( AUS FLT TRI )"], False),
        (
            ["A PAR S A MAR - BUR"],
            ["( FRA AMY PAR ) SUP ( FRA AMY MAR ) MTO BUR"],
            False,
        ),
        (
            ["A MOS S F STP/SC - LVN"],
            ["( RUS AMY MOS ) SUP ( RUS FLT (STP SCS) ) MTO LVN"],
            False,
        ),
        (
            ["A SMY S A CON - BUL"],
            ["( TUR AMY SMY ) SUP ( TUR AMY CON ) MTO BUL"],
            False,
        ),
        (
            ["A CON S F BLA - BUL/EC"],
            ["( TUR AMY CON ) SUP ( TUR FLT BLA ) MTO BUL"],
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
    ) -> None:
        game_tc = Game()
        game_tc.set_units("TURKEY", ["F BLA"])

        assert [
            str(c)
            for c in dipnet_to_daide_parsing(
                test_input,
                game_tc,
                unit_power_tuples_included=unit_power_tuples_included,
            )
        ] == expected, (
            [
                str(c)
                for c in dipnet_to_daide_parsing(
                    test_input,
                    game_tc,
                    unit_power_tuples_included=unit_power_tuples_included,
                )
            ],
            expected,
        )
        comparison_tc_op = (
            test_input[0].replace(" R ", " - ")
            if isinstance(test_input[0], str)
            else test_input[0][0].replace(" R ", " - ")
        )
        # Remove coast for target destination in support orders
        if " S " in comparison_tc_op and comparison_tc_op[-3:] in {
            "/NC",
            "/SC",
            "/EC",
            "/WC",
        }:
            comparison_tc_op = comparison_tc_op.rsplit("/", maxsplit=1)[0]
        dipnet_order = daide_to_dipnet_parsing(parse_daide(expected[0]))
        assert dipnet_order is not None and dipnet_order[0] == comparison_tc_op, (
            dipnet_order,
            comparison_tc_op,
        )

    DIPNET_TO_DAIDE_PARSING_CONVOY_TEST_CASES = [
        (
            ["A TUN - SYR VIA", "F ION C A TUN - SYR", "F EAS C A TUN - SYR"],
            [
                "( ITA AMY TUN ) CTO SYR VIA ( ION EAS )",
                "( ITA FLT ION ) CVY ( ITA AMY TUN ) CTO SYR",
                "( ITA FLT EAS ) CVY ( ITA AMY TUN ) CTO SYR",
            ],
        ),
        (
            ["A TUN - BUL VIA", "F ION C A TUN - BUL", "F AEG C A TUN - BUL"],
            [
                "( ITA AMY TUN ) CTO BUL VIA ( ION AEG )",
                "( ITA FLT ION ) CVY ( ITA AMY TUN ) CTO BUL",
                "( ITA FLT AEG ) CVY ( ITA AMY TUN ) CTO BUL",
            ],
        ),
    ]

    @pytest.mark.parametrize("test_input,expected", DIPNET_TO_DAIDE_PARSING_CONVOY_TEST_CASES)
    def test_dipnet_to_daide_parsing_convoys(
        self, test_input: List[str], expected: List[str]
    ) -> None:
        game_tc = Game()
        game_tc.set_units("ITALY", ["A TUN", "F ION", "F EAS", "F AEG"])

        assert [str(c) for c in dipnet_to_daide_parsing(test_input, game_tc)] == expected, (
            [str(c) for c in dipnet_to_daide_parsing(test_input, game_tc)],
            expected,
        )
        for tc_ip_ord, tc_op_ord in zip(test_input, expected):
            dipnet_order = daide_to_dipnet_parsing(parse_daide(tc_op_ord))
            assert dipnet_order is not None and dipnet_order[0] == tc_ip_ord.replace(
                " R ", " - "
            ), (
                dipnet_order,
                tc_ip_ord.replace(" R ", " - "),
            )

    PARSE_PROPOSAL_MESSAGES_TEST_CASES = [
        [
            "RUSSIA",
            {
                "GERMANY": "PRP (ORR (XDO ((RUS AMY WAR) MTO PRU)) (XDO ((RUS FLT SEV) MTO RUM)) (XDO ((RUS AMY PRU) MTO LVN)))",
                "AUSTRIA": "PRP (XDO ((RUS AMY MOS) SUP (RUS FLT (STP SCS)) MTO LVN))",
                "ENGLAND": "PRP (XDO ((RUS AMY PRU) MTO LVN))",
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
                "GERMANY": "PRP (ORR (XDO ((RUS AMY WAR) MTO PRU)) (ALY (GER RUS ENG ITA) VSS (FRA TUR AUS)))",
                "AUSTRIA": "PRP (ALY (AUS RUS) VSS (FRA ENG ITA TUR GER))",
            },
            {
                "valid_proposals": {"GERMANY": ["A WAR - PRU"]},
                "invalid_proposals": {},
                "shared_orders": {},
                "other_orders": {},
                "alliance_proposals": {
                    "GERMANY": [("GERMANY", "ALY ( ENG GER ITA RUS ) VSS ( AUS FRA TUR )")],
                    "ENGLAND": [("GERMANY", "ALY ( ENG GER ITA RUS ) VSS ( AUS FRA TUR )")],
                    "ITALY": [("GERMANY", "ALY ( ENG GER ITA RUS ) VSS ( AUS FRA TUR )")],
                    "AUSTRIA": [("AUSTRIA", "ALY ( AUS RUS ) VSS ( ENG FRA GER ITA TUR )")],
                },
                "peace_proposals": {},
            },
        ],
        [
            "TURKEY",
            {
                "RUSSIA": "PRP(AND (XDO((TUR FLT ANK) MTO BLA)) (XDO((RUS AMY SEV) MTO RUM)) (XDO((ENG AMY LVP) HLD)))"
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
                "RUSSIA": "PRP(AND (XDO((TUR FLT ANK) MTO BLA)) (XDO((RUS AMY SEV) MTO RUM)) "
                "(XDO((ENG AMY LVP) HLD)) (ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)) (PCE (TUR RUS) ))"
            },
            {
                "valid_proposals": {"RUSSIA": ["F ANK - BLA"]},
                "invalid_proposals": {},
                "shared_orders": {"RUSSIA": ["A SEV - RUM"]},
                "other_orders": {"RUSSIA": ["A LVP H"]},
                "alliance_proposals": {
                    "RUSSIA": [("RUSSIA", "ALY ( ENG ITA RUS TUR ) VSS ( AUS FRA GER )")],
                    "ENGLAND": [("RUSSIA", "ALY ( ENG ITA RUS TUR ) VSS ( AUS FRA GER )")],
                    "ITALY": [("RUSSIA", "ALY ( ENG ITA RUS TUR ) VSS ( AUS FRA GER )")],
                },
                "peace_proposals": {
                    "RUSSIA": [("RUSSIA", "PCE ( RUS TUR )")],
                },
            },
        ],
        [
            "ENGLAND",
            {
                "FRANCE": "PRP(AND(XDO((ENG AMY LVP) MTO WAL))(XDO((ENG FLT EDI) MTO NTH))(XDO((ENG FLT LON) MTO ECH)))"
            },
            {
                "valid_proposals": {"FRANCE": ["A LVP - WAL", "F EDI - NTH", "F LON - ENG"]},
                "invalid_proposals": {},
                "shared_orders": {},
                "other_orders": {},
                "alliance_proposals": {},
                "peace_proposals": {},
            },
        ],
    ]

    @pytest.mark.parametrize("power_name,test_input,expected", PARSE_PROPOSAL_MESSAGES_TEST_CASES)
    def test_parse_proposal_messages(
        self,
        power_name: str,
        test_input: Dict[str, str],
        expected: Dict[str, Dict[str, List[str]]],
    ) -> None:
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
        msgs = game_GTP.filter_messages(messages=game_GTP.messages, game_role=power_name).values()
        parsed_orders_dict = parse_proposal_messages(msgs, game_GTP, power_name)

        assert set(parsed_orders_dict.keys()) == set(expected.keys())
        for pod_key, pod_value in parsed_orders_dict.items():
            assert set(pod_value.keys()) == set(expected[pod_key].keys()), (
                pod_key,
                set(pod_value.keys()),
                set(expected[pod_key].keys()),
            )

            for key in parsed_orders_dict[pod_key]:
                assert set(pod_value[key]) == set(expected[pod_key][key]), (
                    pod_key,
                    key,
                    set(pod_value[key]),
                    set(expected[pod_key][key]),
                )

    PARSE_ARRANGEMENT_TEST_CASES = [
        ["PRP (XDO ((RUS FLT BLA) MTO CON))", ["XDO ( ( RUS FLT BLA ) MTO CON )"]],
        [
            "PRP (ORR (XDO(( RUS FLT BLA ) MTO CON))(XDO(( RUS AMY RUM ) MTO BUD))(XDO(( RUS FLT BLA ) MTO BUD)))",
            [
                "XDO ( ( RUS AMY RUM ) MTO BUD )",
                "XDO ( ( RUS FLT BLA ) MTO BUD )",
                "XDO ( ( RUS FLT BLA ) MTO CON )",
            ],
        ],
        [
            "PRP (ORR (XDO(( RUS FLT BLA ) MTO CON))(XDO(( RUS AMY RUM ) MTO BUD)))",
            ["XDO ( ( RUS AMY RUM ) MTO BUD )", "XDO ( ( RUS FLT BLA ) MTO CON )"],
        ],
        [
            "PRP(ALY (GER RUS) VSS (FRA ENG ITA TUR AUS))",
            ["ALY ( GER RUS ) VSS ( AUS ENG FRA ITA TUR )"],
        ],
        [
            "PRP(ORR (XDO (( RUS FLT BLA ) MTO CON)) (ALY (GER RUS TUR) VSS (FRA ENG ITA AUS)))",
            [
                "ALY ( GER RUS TUR ) VSS ( AUS ENG FRA ITA )",
                "XDO ( ( RUS FLT BLA ) MTO CON )",
            ],
        ],
    ]

    @pytest.mark.parametrize("test_input,expected", PARSE_ARRANGEMENT_TEST_CASES)
    def test_parse_arrangement(self, test_input: str, expected: List[str]) -> None:
        assert parse_arrangement(test_input) == expected, (
            parse_arrangement(test_input),
            expected,
        )

    GET_ORDER_TOKENS_TEST_CASES = [
        ["A PAR S A MAR - BUR", ["A PAR", "S", "A MAR", "- BUR"]],
        ["A MAR - BUR", ["A MAR", "- BUR"]],
        ["A MAR R BUR", ["A MAR", "- BUR"]],
        ["A MAR H", ["A MAR", "H"]],
        ["F BUL/EC - RUM", ["F BUL/EC", "- RUM"]],
        ["F RUM - BUL/EC", ["F RUM", "- BUL/EC"]],
    ]

    @pytest.mark.parametrize("test_input,expected", GET_ORDER_TOKENS_TEST_CASES)
    def test_get_order_tokens(self, test_input: str, expected: List[str]) -> None:
        assert get_order_tokens(test_input) == expected
