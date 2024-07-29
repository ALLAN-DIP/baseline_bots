"""Test functions from the `parsing_utils` and `utils` modules."""

from typing import List

from diplomacy import Game
import pytest

from chiron_utils.parsing_utils import daide_to_dipnet_parsing, dipnet_to_daide_parsing
from chiron_utils.utils import get_order_tokens, parse_daide


class TestUtils:
    """Class to contain tests."""

    DIPNET_TO_DAIDE_PARSING_TEST_CASES = (
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
    )

    @pytest.mark.parametrize(
        ("test_input", "expected", "unit_power_tuples_included"),
        DIPNET_TO_DAIDE_PARSING_TEST_CASES,
    )
    def test_dipnet_to_daide_parsing(
        self,
        test_input: List[str],
        expected: List[str],
        *,
        unit_power_tuples_included: bool,
    ) -> None:
        """Test `parsing_utils.dipnet_to_daide_parsing()`.

        Args:
            test_input: List of DipNet orders to convert.
            expected: List of DAIDE orders expected as output.
            unit_power_tuples_included: Whether the unit power will also be included in the input.
        """
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
        assert dipnet_order is not None
        assert dipnet_order[0] == comparison_tc_op, (dipnet_order, comparison_tc_op)

    DIPNET_TO_DAIDE_PARSING_CONVOY_TEST_CASES = (
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
    )

    @pytest.mark.parametrize(("test_input", "expected"), DIPNET_TO_DAIDE_PARSING_CONVOY_TEST_CASES)
    def test_dipnet_to_daide_parsing_convoys(
        self, test_input: List[str], expected: List[str]
    ) -> None:
        """Test convoy logic in `parsing_utils.dipnet_to_daide_parsing()`.

        Args:
            test_input: List of DipNet orders to convert.
            expected: List of DAIDE orders expected as output.
        """
        game_tc = Game()
        game_tc.set_units("ITALY", ["A TUN", "F ION", "F EAS", "F AEG"])

        assert [str(c) for c in dipnet_to_daide_parsing(test_input, game_tc)] == expected, (
            [str(c) for c in dipnet_to_daide_parsing(test_input, game_tc)],
            expected,
        )
        for tc_ip_ord, tc_op_ord in zip(test_input, expected):
            dipnet_order = daide_to_dipnet_parsing(parse_daide(tc_op_ord))
            assert dipnet_order is not None
            assert dipnet_order[0] == tc_ip_ord.replace(" R ", " - "), (
                dipnet_order,
                tc_ip_ord.replace(" R ", " - "),
            )

    GET_ORDER_TOKENS_TEST_CASES = (
        ["A PAR S A MAR - BUR", ["A PAR", "S", "A MAR", "- BUR"]],
        ["A MAR - BUR", ["A MAR", "- BUR"]],
        ["A MAR R BUR", ["A MAR", "- BUR"]],
        ["A MAR H", ["A MAR", "H"]],
        ["F BUL/EC - RUM", ["F BUL/EC", "- RUM"]],
        ["F RUM - BUL/EC", ["F RUM", "- BUL/EC"]],
    )

    @pytest.mark.parametrize(("test_input", "expected"), GET_ORDER_TOKENS_TEST_CASES)
    def test_get_order_tokens(self, test_input: str, expected: List[str]) -> None:
        """Test `utils.get_order_tokens()`.

        Args:
            test_input: DipNet order.
            expected: List of tokens from DipNet order.
        """
        assert get_order_tokens(test_input) == expected
