from DAIDE import ALY, PRP
from diplomacy import Message

from baseline_bots.bots.random_proposer_bot import RandomProposerBot
from baseline_bots.utils import MessagesData, OrdersData, get_other_powers


class RandomAllierProposerBot(RandomProposerBot):
    """
    The first time this bot acts, it sends an alliance message to
    all other bots. Otherwise, it just sends random order proposals to
    other bots.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.alliance_props_sent = False

    def gen_messages(self, rcvd_messages):
        ret_msgs = MessagesData()
        if self.alliance_props_sent:
            # send random action proposals
            return super().gen_messages(rcvd_messages)
        else:
            # send alliance proposals to other bots

            # for all other powers
            for other_power in get_other_powers([self.power_name], self.game):
                allies = [other_power, self.power_name]
                # encode alliance message in daide syntax
                alliance_message = ALY(allies, get_other_powers(allies, self.game))
                # send the other power an ally request
                ret_msgs.add_message(other_power, str(PRP(alliance_message)))

            # dont sent alliance props again
            self.alliance_props_sent = True

        return ret_msgs

    def gen_orders(self):
        return None

    def __call__(self, rcvd_messages):
        messages = self.gen_messages(rcvd_messages)
        return {"messages": messages}
