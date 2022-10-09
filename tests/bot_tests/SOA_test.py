"""unit tests for smart order accepter bot"""
from gameplay_framework import GamePlay
from diplomacy import Game

from baseline_bots.bots.smart_order_accepter_bot import SmartOrderAccepterBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot
from baseline_bots.bots.baseline_bot import BaselineBot, BaselineMsgRoundBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_state_value,
    get_best_orders,
    get_other_powers,
    parse_orr_xdo,
    parse_PRP,
    dipnet_to_daide_parsing,
    daide_to_dipnet_parsing
)

class TestSOABot():
    def test(self):
        self.test_play()
        self.test_stance()
        self.test_get_proposals()
        self.test_get_best_orders()
        self.test_gen_messages()

    def test_play(self):
        game = Game()
        game_play = GamePlay(game, [RandomProposerBot('AUSTRIA', game), RandomProposerBot('ENGLAND', game), SmartOrderAccepterBot('FRANCE', game)], 3, True)
        msgs, done = game_play.step()
        game_play = GamePlay(game, [RandomProposerBot('AUSTRIA', game), RandomProposerBot('ENGLAND', game), SmartOrderAccepterBot('FRANCE', game)], 3, True)
        game_play.play()

    def test_stance(self):
        # score-based
        SOA_bot = SmartOrderAccepterBot
        game = Game()
        bot_instances = [RandomProposerBot('AUSTRIA', game), RandomProposerBot('ENGLAND', game), SmartOrderAccepterBot('FRANCE', game), RandomProposerBot('GERMANY', game)]
        game_play = GamePlay(game, bot_instances, 3, True)
        game_play.game.set_centers('AUSTRIA', ['VIE','TRI','BUD'], reset=True)
        game_play.game.set_centers('ENGLAND', ['LON'])
        game_play.game.set_centers('GERMANY', ['MUN', 'KIE', 'BER','BEL'])
        game_play.game.set_centers(SOA_bot.power, ['PAR','BRE', 'MAR'])
        msgs, done = game_play.step()
        SOA_bot_stance = SOA_bot.stance.get_stance()[SOA_bot.power]
        assert SOA_bot_stance['ENGLAND'] == 1, "Positive stance error"
        assert SOA_bot_stance['GERMANY'] == -1, "Negative stance error"
        assert SOA_bot_stance['AUSTRIA'] == 0 , "Neutral stance error"

        # to do: add action-based stance test

    def test_get_proposals(self):
        # proposal messages -> proposal dict {power_name: a list of proposal orders}
        # valid moves and power units must belong to SOA
        game = Game()
        SOA_bot = SmartOrderAccepterBot('FRANCE', game)
        baseline1 = RandomProposerBot('AUSTRIA', game)
        baseline2 = RandomProposerBot('ENGLAND', game)
        bot_instances = [baseline1, baseline2, SOA_bot]   
        game_play = GamePlay(game, bot_instances, 3, True)
        bl1_msg = baseline1.gen_messages().messages
        bl2_msg = baseline2.gen_messages().messages

        msg_obj1 = Message(
                            sender=baseline1.power_name,
                            recipient=bl1_msg['recipient'],
                            message=bl1_msg['message'],
                            phase=game_play.game.get_current_phase(),
                        )


        msg_obj2 = Message(
                            sender=baseline2.power_name,
                            recipient=bl2_msg['recipient'],
                            message=bl2_msg['message'],
                            phase=game_play.game.get_current_phase(),
                        )
        game_play.game.add_message(message=msg_obj1)
        game_play.game.add_message(message=msg_obj2)

        rcvd_messages = game_play.game.filter_messages(messages=game_play.game.messages, game_role=SOA_bot.power_name)
        prp_orders = SOA_bot.get_proposals(rcvd_messages)
        possible_orders = game_play.game.get_all_possible_orders()

        SOA_power_units = game_play.game.powers[SOA_bot.power_name].units[:]
        
        for power, orders in prp_orders.items():
            for order in orders:
                order_token = get_order_tokens(order)
                unit_order = order_token[0]
                assert unit_order in SOA_power_units, "unit in " + order + " does not belong to SOA's power (" + SOA_bot.power_name + ")"
                assert order in possible_orders[unit_order], order + " is not possible in this current phase of a game for SOA's power (" + SOA_bot.power_name + ")"


    def test_get_best_orders(self):
        # proposal -> gen state value check if SOA select the best proposal 
        
        #run test for n times
        n=100
        orders = yield self.brain.get_orders(self.game, self.power_name)
        for i in range(n):
            game = Game()
            SOA_bot = SmartOrderAccepterBot('FRANCE', game)
            SOA_bot.rollout_length = 10
            baseline1 = RandomProposerBot('AUSTRIA', game)
            baseline2 = RandomProposerBot('ENGLAND', game)
            bot_instances = [baseline1, baseline2, SOA_bot]   

            game_play = GamePlay(game, bot_instances, 3, True)
            bl1_msg = baseline1.gen_messages().messages
            bl2_msg = baseline2.gen_messages().messages

            msg_obj1 = Message(
                                sender=baseline1.power_name,
                                recipient=bl1_msg['recipient'],
                                message=bl1_msg['message'],
                                phase=game_play.game.get_current_phase(),
                            )


            msg_obj2 = Message(
                                sender=baseline2.power_name,
                                recipient=bl2_msg['recipient'],
                                message=bl2_msg['message'],
                                phase=game_play.game.get_current_phase(),
                            )
            game_play.game.add_message(message=msg_obj1)
            game_play.game.add_message(message=msg_obj2)
            rcvd_messages = game_play.game.filter_messages(messages=game_play.game.messages, game_role=SOA_bot.power_name)
            prp_orders = SOA_bot.get_proposals(rcvd_messages)
            prp_orders[SOA_bot.power_name] = orders

            state_value = {power_name: -10000 for power_name in game_play.game.powers}

            for power_name, orders in prp_orders:
                sim_game = game_play.game.__deepcopy__(None)
                sim_game.set_orders(power_name=SOA_bot.power_name, orders=orders)
                
                for other_power in game_play.game.powers:
                    power_orders = yield SOA_bot.brain.get_orders(sim_game, other_power)
                    sim_game.set_orders(power_name=other_power, orders=power_orders)

                sim_game.progress()
                
                state_value[power_name] = yield get_state_value(SOA_bot, sim_game, SOA_bot.power_name)

            best_proposer, best_orders = get_best_orders(prp_orders, shared_order)
            max_sv = max(state_value.values())
            max_sv_power = [power_name for power_name in state_value if state_value[power_name] == max_sv]
            assert best_proposer in max_sv_power


    def gen_pos_stance_messages(self):
        # gen for only allies 
        game = Game()
        bot_instances = [RandomProposerBot('AUSTRIA', game), RandomProposerBot('ENGLAND', game), SmartOrderAccepterBot('FRANCE', game), RandomProposerBot('GERMANY', game)]
        game_play = GamePlay(game, bot_instances, 3, True)
        game_play.game.set_centers('AUSTRIA', ['VIE','TRI','BUD'], reset=True)
        game_play.game.set_centers('ENGLAND', ['LON'])
        game_play.game.set_centers('GERMANY', ['MUN', 'KIE', 'BER','BEL'])
        game_play.game.set_centers(SOA_bot.power, ['PAR','BRE', 'MAR'])
        msgs, done = game_play.step()
        msgs_data = SOA_bot.gen_messages()
        ally = 'ENGLAND'
        sending_to_ally = False
        for msg in msgs_data:
            assert msg['recipient'] != 'AUSTRIA' and msg['recipient'] != 'GERMANY', 'SOA bot is sending FCT orders to non-ally powers (AUSTRIA, GERMANY)'

            if msg['recipient'] =='ENGLAND':
                sending_to_ally=True
        assert sending_to_ally, 'SOA bot is not sending FCT orders to ally power (ENGLAND)'
