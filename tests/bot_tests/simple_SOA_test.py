"""unit tests for smart order accepter bot"""
from diplomacy import Game, Message
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop
from tornado import gen, testing
from tornado.testing import AsyncTestCase

from baseline_bots.bots.baseline_bot import BaselineBot, BaselineMsgRoundBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot_AsyncBot
from baseline_bots.bots.smart_order_accepter_bot import SmartOrderAccepterBot
from baseline_bots.parsing_utils import (
    daide_to_dipnet_parsing,
    dipnet_to_daide_parsing,
    parse_proposal_messages,
)
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_best_orders,
    get_order_tokens,
    get_other_powers,
    get_state_value,
    parse_alliance_proposal,
    parse_arrangement,
    parse_PRP,
)


class TestSimpleSOABot(AsyncTestCase):
    @testing.gen_test
    def test_play(self):
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True)
        messages = MessagesData().add_message("FRANCE", "A PAR - BUR")
        soa_bot.send_message("FRANCE", messages)
