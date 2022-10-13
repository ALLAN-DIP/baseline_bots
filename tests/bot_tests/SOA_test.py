"""unit tests for smart order accepter bot"""
from gameplay_framework import GamePlay
from diplomacy import Game, Message
from tornado import gen
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop
from baseline_bots.bots.smart_order_accepter_bot import SmartOrderAccepterBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot_AsyncBot
from baseline_bots.bots.baseline_bot import BaselineBot, BaselineMsgRoundBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_best_orders,
    get_other_powers,
    parse_alliance_proposal,
    parse_arrangement,
    parse_PRP,
    get_order_tokens
)

from baseline_bots.parsing_utils import (
    dipnet_to_daide_parsing,
    daide_to_dipnet_parsing,
    parse_proposal_messages
)

class TestSOABot():
    def test(self):
        # start_io_loop(self.test_play)
        # start_io_loop(self.test_stance)
        start_io_loop(self.test_parse_proposals)
        self.test_get_best_orders()
        self.test_gen_messages()

    @gen.coroutine
    def test_play(self):
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        game_play = GamePlay(game, [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), soa_bot], 3, True)
        msgs, done = yield game_play.step()
        game_play = GamePlay(game, [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), soa_bot], 3, True)
        game_play.play()
        print('finish test_play')
        stop_io_loop()

    @gen.coroutine
    def test_stance(self):
        # score-based
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        bot_instances = [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), RandomProposerBot_AsyncBot('GERMANY', game), soa_bot]
        game_play = GamePlay(game, bot_instances, 3, True)
        game_play.game.set_centers('AUSTRIA', ['VIE','TRI','BUD'], reset=True)
        game_play.game.set_centers('ENGLAND', ['LON'], reset=True)
        game_play.game.set_centers('GERMANY', ['MUN', 'KIE', 'BER','BEL'])
        game_play.game.set_centers(soa_bot.power_name, ['PAR','BRE', 'MAR'])
        msgs, done = yield game_play.step()
        soa_bot_stance = soa_bot.stance.get_stance()[soa_bot.power_name]
        print(game_play.game.get_centers())
        print('expected stance ENGLAND: 1, GERMANY: -1, AUTRIA:0')
        print('soa stance', soa_bot_stance)
        assert soa_bot_stance['ENGLAND'] == 1, "Positive stance error"
        assert soa_bot_stance['GERMANY'] == -1, "Negative stance error"
        assert soa_bot_stance['AUSTRIA'] == 0 , "Neutral stance error"

        print('finish test_stance')
        stop_io_loop()

        # to do: add action-based stance test

    @gen.coroutine
    def test_parse_proposals(self):
        # proposal messages -> proposal dict {power_name: a list of proposal orders}
        # valid moves and power units must belong to SOA
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        baseline1 = RandomProposerBot_AsyncBot('AUSTRIA', game)
        baseline2 = RandomProposerBot_AsyncBot('ENGLAND', game)
        bot_instances = [baseline1, baseline2, soa_bot]   
        game_play = GamePlay(game, bot_instances, 3, True)
        rcvd_messages = game_play.game.filter_messages(messages=game_play.game.messages, game_role='AUSTRIA')
        bl1_msg = yield baseline1.gen_messages(rcvd_messages)
        rcvd_messages = game_play.game.filter_messages(messages=game_play.game.messages, game_role='ENGLAND')
        bl2_msg = yield baseline2.gen_messages(rcvd_messages)

        for msg in bl1_msg:
            msg_obj1 = Message(
                                sender=baseline1.power_name,
                                recipient=msg['recipient'],
                                message=msg['message'],
                                phase=game_play.game.get_current_phase(),
                            )
            game_play.game.add_message(message=msg_obj1)

        for msg in bl2_msg:
            msg_obj2 = Message(
                                sender=baseline2.power_name,
                                recipient=msg['recipient'],
                                message=msg['message'],
                                phase=game_play.game.get_current_phase(),
                            )
            game_play.game.add_message(message=msg_obj2)

        rcvd_messages = game_play.game.filter_messages(messages=game_play.game.messages, game_role=soa_bot.power_name)
        parsed_messages_dict = parse_proposal_messages(rcvd_messages, game_play.game, soa_bot.power_name)
        valid_proposal_orders = parsed_messages_dict['valid_proposals']

        # print('parsed_messages_dict ', parsed_messages_dict)
        possible_orders = game_play.game.get_all_possible_orders()

        soa_power_units = game_play.game.powers[soa_bot.power_name].units[:]
        
        for power, orders in valid_proposal_orders.items():
            for order in orders:
                order_token = get_order_tokens(order)
                unit_order = order_token[0]
                unit_loc = unit_order.split()[1]
                assert unit_order in soa_power_units, "unit in " + order + " does not belong to SOA's power (" + soa_bot.power_name + ")"
                assert order in possible_orders[unit_loc], order + " is not possible in this current phase of a game for SOA's power (" + soa_bot.power_name + ")"
        print('finish test_parse_proposal')
        stop_io_loop()

    @gen.coroutine
    def test_get_best_orders(self):
        # proposal -> gen state value check if SOA select the best proposal 
        
        #run test for n times
        n=100
        orders = yield self.brain.get_orders(self.game, self.power_name)
        for i in range(n):
            game = Game()
            soa_bot = SmartOrderAccepterBot('FRANCE', game)
            soa_bot.rollout_length = 10
            baseline1 = RandomProposerBot_AsyncBot('AUSTRIA', game)
            baseline2 = RandomProposerBot_AsyncBot('ENGLAND', game)
            bot_instances = [baseline1, baseline2, soa_bot]   

            game_play = GamePlay(game, bot_instances, 3, True)
            bl1_msg = baseline1.gen_messages()
            bl2_msg = baseline2.gen_messages()

            for msg in bl1_msg:
                msg_obj1 = Message(
                                    sender=baseline1.power_name,
                                    recipient=msg['recipient'],
                                    message=msg['message'],
                                    phase=game_play.game.get_current_phase(),
                                )
                game_play.game.add_message(message=msg_obj1)

            for msg in bl2_msg:
                msg_obj2 = Message(
                                    sender=baseline2.power_name,
                                    recipient=msg['recipient'],
                                    message=msg['message'],
                                    phase=game_play.game.get_current_phase(),
                                )
                game_play.game.add_message(message=msg_obj2)

            rcvd_messages = game_play.game.filter_messages(messages=game_play.game.messages, game_role=soa_bot.power_name)
            parsed_messages_dict = parse_proposal_messages(rcvd_messages, game_play.game, soa_bot.power_name)
            valid_proposal_orders = parsed_messages_dict['valid_proposals']
            valid_proposal_orders[soa_bot.power_name] = orders

            state_value = {power_name: -10000 for power_name in game_play.game.powers}

            for power_name, orders in prp_orders:
                sim_game = game_play.game.__deepcopy__(None)
                sim_game.set_orders(power_name=soa_bot.power_name, orders=orders)
                
                for other_power in game_play.game.powers:
                    power_orders = yield soa_bot.brain.get_orders(sim_game, other_power)
                    sim_game.set_orders(power_name=other_power, orders=power_orders)

                sim_game.progress()
                
                state_value[power_name] = yield get_state_value(soa_bot, sim_game, soa_bot.power_name)

            best_proposer, best_orders = get_best_orders(prp_orders, shared_order)
            max_sv = max(state_value.values())
            max_sv_power = [power_name for power_name in state_value if state_value[power_name] == max_sv]
            assert best_proposer in max_sv_power
        print('finish test_best_prop_order')

    @gen.coroutine    
    def gen_pos_stance_messages(self):
        # gen for only allies 
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        bot_instances = [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), RandomProposerBot_AsyncBot('GERMANY', game), soa_bot]
        game_play = GamePlay(game, bot_instances, 3, True)
        game_play.game.set_centers('AUSTRIA', ['VIE','TRI','BUD'], reset=True)
        game_play.game.set_centers('ENGLAND', ['LON'])
        game_play.game.set_centers('GERMANY', ['MUN', 'KIE', 'BER','BEL'])
        game_play.game.set_centers(soa_bot.power_name, ['PAR','BRE', 'MAR'])
        msgs, done = game_play.step()
        msgs_data = soa_bot.gen_messages()
        ally = 'ENGLAND'
        sending_to_ally = False
        for msg in msgs_data:
            assert msg['recipient'] != 'AUSTRIA' and msg['recipient'] != 'GERMANY', 'SOA bot is sending FCT orders to non-ally powers (AUSTRIA, GERMANY)'

            if msg['recipient'] =='ENGLAND':
                sending_to_ally=True
        assert sending_to_ally, 'SOA bot is not sending FCT orders to ally power (ENGLAND)'
        print('test pos_stance_msg')

if __name__ == "__main__":
    soa_test=TestSOABot()
    soa_test.test()