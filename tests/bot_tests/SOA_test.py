"""unit tests for smart order accepter bot"""
from gameplay_framework import GamePlayAsync
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
    get_order_tokens,
    get_state_value
)

from baseline_bots.parsing_utils import (
    dipnet_to_daide_parsing,
    daide_to_dipnet_parsing,
    parse_proposal_messages
)

class TestSOABot():
    def test(self):
        start_io_loop(self.test_play)
        # start_io_loop(self.test_score_stance)
        # start_io_loop(self.test_action_stance)
        # start_io_loop(self.test_auxilary_functions)
        # start_io_loop(self.test_parse_proposals)
        # start_io_loop(self.test_get_best_orders)
        # start_io_loop(self.test_gen_pos_stance_messages)
        # start_io_loop(self.test_ally_move_filter)
    
    @gen.coroutine
    def test_auxilary_functions(self):
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        RESPOND_TO_INV_ORDERS_TC = [
            [
                {
                    "RUSSIA": [("A PRU - LVN", "TUR"), (("A PRU - MOS", "RUS"))],
                    "AUSTRIA": [("A PRU - LVN", "ENG")]
                },
                [
                    {"recipient": "RUSSIA", "message": "HUH (PRP (ORR (XDO ((TUR AMY PRU) MTO LVN)) (XDO ((RUS AMY PRU) MTO MOS))))"},
                    {"recipient": "AUSTRIA", "message": "HUH (PRP (XDO ((ENG AMY PRU) MTO LVN)))"}
                ]
            ]
        ]

        for tc_ip, tc_op in RESPOND_TO_INV_ORDERS_TC:
            msg_data = MessagesData()
            soa_bot.respond_to_invalid_orders(tc_ip, msg_data)
            assert msg_data.messages == tc_op

        RESPOND_TO_ALLIANCES_TC = [
            [
                {
                    "RUSSIA": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                    "ENGLAND": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                    "ITALY": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                },
                [
                    {"recipient": "RUSSIA", "message": "YES (ALY (TUR RUS ENG ITA) VSS (FRA GER AUS))"}
                ]
            ]
        ]

        for tc_ip, tc_op in RESPOND_TO_ALLIANCES_TC:
            msg_data = MessagesData()
            soa_bot.alliances = tc_ip
            soa_bot.respond_to_alliance_messages(msg_data)
            assert msg_data.messages == tc_op
        
        stop_io_loop()

    @gen.coroutine
    def test_play(self):
        game = Game()
        soa_bot1 = SmartOrderAccepterBot('FRANCE', game)
        soa_bot2 = SmartOrderAccepterBot('RUSSIA', game)
        game_play = GamePlayAsync(game, [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), soa_bot1, soa_bot2, RandomProposerBot_AsyncBot('GERMANY', game), RandomProposerBot_AsyncBot('ITALY', game), RandomProposerBot_AsyncBot('TURKEY', game)], 3, True)
        msgs, done = yield game_play.step()
        game_play = GamePlayAsync(game, [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), soa_bot1, soa_bot2, RandomProposerBot_AsyncBot('GERMANY', game), RandomProposerBot_AsyncBot('ITALY', game), RandomProposerBot_AsyncBot('TURKEY', game)], 3, True)
        while not game_play.game.is_game_done:
            msgs, done = yield game_play.step()
        print('finish test_play')
        stop_io_loop()

    @gen.coroutine
    def test_score_stance(self):
        # score-based
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        bot_instances = [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), RandomProposerBot_AsyncBot('GERMANY', game), soa_bot]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
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

    @gen.coroutine
    def test_action_stance(self):
        # score-based
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        bot_instances = [RandomProposerBot_AsyncBot('ENGLAND', game), RandomProposerBot_AsyncBot('GERMANY', game), soa_bot]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
        game_play.game.set_orders('FRANCE', ['A MAR H', 'A PAR H', 'F BRE - PIC'])
        game_play.game.set_orders('ENGLAND', ['A LVP - WAL', 'F EDI - NTH', 'F LON - ENG'])
        game_play.game.set_orders('GERMANY', ['A BER - MUN', 'A MUN - BUR', 'F KIE - HOL'])
        game_play.game.process()
        game_play.game.set_orders('FRANCE', ['A MAR - BUR', 'A PAR - BRE', 'F PIC H'])
        game_play.game.set_orders('ENGLAND', ['A WAL - BEL VIA', 'F ENG C A WAL - BEL', 'F NTH - HEL'])
        game_play.game.set_orders('GERMANY', ['A BUR - MAR', 'A MUN - RUH', 'F HOL H'])
        game_play.game.process()
        game_play.game.set_orders('ENGLAND', ['A LON B'])
        game_play.game.set_orders('GERMANY', ['A MUN B'])
        game_play.game.process()
        game_play.game.set_orders('FRANCE', ['A BRE H', 'A MAR - GAS', 'F PIC H'])
        game_play.game.set_orders('ENGLAND', ['A BEL S F PIC', 'F ENG S A BRE', 'F HEL - HOL'])
        game_play.game.set_orders('GERMANY', ['A BUR - PAR', 'A RUH - BUR', 'F HOL H'])
        game_play.game.process()
        game_play.game.set_orders('FRANCE', ['A BRE - PAR', 'A GAS - BUR', 'F PIC - BEL'])
        game_play.game.set_orders('ENGLAND', ['A BEL - HOL', 'F ENG S F PIC - BEL', 'F HEL S A BEL - HOL'])
        game_play.game.set_orders('GERMANY', ['A BUR S A PAR - PIC', 'A PAR - PIC', 'F HOL H'])
        game_play.game.process()
        soa_bot_stance = soa_bot.stance.get_stance()[soa_bot.power_name]
        print(soa_bot_stance)

        print('expected stance ENGLAND >0, GERMANY<0')
        print('soa stance', soa_bot_stance)
        assert soa_bot_stance['ENGLAND'] >0.0  , "Positive stance error"
        assert soa_bot_stance['GERMANY'] <0.0, "Negative stance error"

        print('finish test_stance')
        stop_io_loop()

    @gen.coroutine
    def test_ally_move_filter(self):
        # assume that stance is correct using score-based
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        soa_bot.ally_threshold = 1.0
        bot_instances = [RandomProposerBot_AsyncBot('ENGLAND', game), RandomProposerBot_AsyncBot('GERMANY', game), soa_bot]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
        game_play.game.set_centers('ENGLAND', ['LON'], reset=True)
        game_play.game.set_centers('GERMANY', ['MUN', 'KIE', 'BER','BEL'])
        game_play.game.set_centers(soa_bot.power_name, ['PAR','BRE', 'MAR'])
        game_play.game.set_orders('FRANCE', ['A MAR - BUR', 'A PAR - PIC', 'F BRE H'])
        game_play.game.set_orders('ENGLAND', ['A LVP - WAL', 'F EDI - NTH', 'F LON - ENG'])
        game_play.game.process()
        orders = ['F BRE - ENG', 'A PIC - BEL', 'A BUR - PIC']
        orders_data = OrdersData()
        orders_data.add_orders(orders)
        soa_bot.orders = orders_data

        print("aggressive order: ", orders)
        soa_bot_stance = soa_bot.stance.get_stance()[soa_bot.power_name]
        print('soa stance', {k: v for k,v in soa_bot_stance.items() if v >= soa_bot.ally_threshold})
        yield soa_bot.replace_aggressive_order_to_allies()
        print("remove non-aggressive", soa_bot.orders.get_list_of_orders())

        print('finish test ally move filter')
        stop_io_loop()

    @gen.coroutine
    def test_parse_proposals(self):
        # proposal messages -> proposal dict {power_name: a list of proposal orders}
        # valid moves and power units must belong to SOA
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        baseline1 = RandomProposerBot_AsyncBot('AUSTRIA', game)
        baseline2 = RandomProposerBot_AsyncBot('ENGLAND', game)
        bot_instances = [baseline1, baseline2, soa_bot]   
        game_play = GamePlayAsync(game, bot_instances, 3, True)
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

        rcvd_messages = game.filter_messages(messages=game_play.game.messages, game_role=soa_bot.power_name)
        rcvd_messages = list(rcvd_messages.items())
        rcvd_messages.sort()
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
        n=10

        for i in range(n):
            game = Game()
            soa_bot = SmartOrderAccepterBot('FRANCE', game)
            soa_bot.rollout_length = 7
            baseline1 = RandomProposerBot_AsyncBot('AUSTRIA', game)
            baseline2 = RandomProposerBot_AsyncBot('ENGLAND', game)
            bot_instances = [baseline1, baseline2, soa_bot]   

            rcvd_messages = game.filter_messages(messages=game.messages, game_role='AUSTRIA')
            bl1_msg = yield baseline1.gen_messages(rcvd_messages)
            rcvd_messages = game.filter_messages(messages=game.messages, game_role='ENGLAND')
            bl2_msg = yield baseline2.gen_messages(rcvd_messages)

            for msg in bl1_msg:
                msg_obj1 = Message(
                                    sender=baseline1.power_name,
                                    recipient=msg['recipient'],
                                    message=msg['message'],
                                    phase=game.get_current_phase(),
                                )
                game.add_message(message=msg_obj1)

            for msg in bl2_msg:
                msg_obj2 = Message(
                                    sender=baseline2.power_name,
                                    recipient=msg['recipient'],
                                    message=msg['message'],
                                    phase=game.get_current_phase(),
                                )
                game.add_message(message=msg_obj2)

            rcvd_messages = game.filter_messages(messages=game.messages, game_role=soa_bot.power_name)
            rcvd_messages = list(rcvd_messages.items())
            rcvd_messages.sort()
            parsed_messages_dict = parse_proposal_messages(rcvd_messages, game, soa_bot.power_name)
            valid_proposal_orders = parsed_messages_dict['valid_proposals']
            shared_orders = parsed_messages_dict['shared_orders']
            orders = yield soa_bot.brain.get_orders(game, soa_bot.power_name)
            valid_proposal_orders[soa_bot.power_name] = orders

            state_value = {power_name: -10000 for power_name in game.powers}

            for power_name, orders in valid_proposal_orders.items():
                sim_game = game.__deepcopy__(None)
                sim_game.set_orders(power_name=soa_bot.power_name, orders=orders)
                
                for other_power in game.powers:
                    power_orders = yield soa_bot.brain.get_orders(sim_game, other_power)
                    sim_game.set_orders(power_name=other_power, orders=power_orders)

                sim_game.process()
                
                state_value[power_name] = yield get_state_value(soa_bot, sim_game, soa_bot.power_name)
            
            print('state value from power proposals',state_value)

            best_proposer, best_orders = yield get_best_orders(soa_bot, valid_proposal_orders, shared_orders)
            max_sv = max(state_value.values())
            max_sv_power = [power_name for power_name in state_value if state_value[power_name] == max_sv]
            print('expect to have '+ best_proposer +' in max_state_value_powers: ', max_sv_power)
            
            assert best_proposer in max_sv_power, "best proposer did not return the maximum state value"

        print('finish test_best_prop_order')
        stop_io_loop()

    @gen.coroutine    
    def test_gen_pos_stance_messages(self):
        # gen for only allies 
        game = Game()
        soa_bot = SmartOrderAccepterBot('FRANCE', game)
        bot_instances = [RandomProposerBot_AsyncBot('AUSTRIA', game), RandomProposerBot_AsyncBot('ENGLAND', game), RandomProposerBot_AsyncBot('GERMANY', game), soa_bot]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
        game_play.game.set_centers('AUSTRIA', ['VIE','TRI','BUD'], reset=True)
        game_play.game.set_centers('ENGLAND', ['LON'], reset=True)
        game_play.game.set_centers('GERMANY', ['MUN', 'KIE', 'BER','BEL'])
        game_play.game.set_centers(soa_bot.power_name, ['PAR','BRE', 'MAR'])
        rcvd_messages = game.filter_messages(messages=game_play.game.messages, game_role=soa_bot.power_name)
        rcvd_messages = list(rcvd_messages.items())
        rcvd_messages.sort()
        ret_data = yield soa_bot(rcvd_messages)
        soa_bot_stance = soa_bot.stance.get_stance()[soa_bot.power_name]
        print(game_play.game.get_centers())
        print('expected stance ENGLAND: 1, GERMANY: -1, AUTRIA:0')
        print('soa stance', soa_bot_stance)
        print(ret_data['messages'])
        ally = 'ENGLAND'
        sending_to_ally = False
        for msg in ret_data['messages']:
            assert msg['recipient'] != 'AUSTRIA' and msg['recipient'] != 'GERMANY', 'SOA bot is sending FCT orders to non-ally powers (AUSTRIA, GERMANY)'

            if msg['recipient'] =='ENGLAND':
                sending_to_ally=True
        assert sending_to_ally, 'SOA bot is not sending FCT orders to ally power (ENGLAND)'
        print('test pos_stance_msg')
        stop_io_loop()


if __name__ == "__main__":
    soa_test=TestSOABot()
    soa_test.test()
