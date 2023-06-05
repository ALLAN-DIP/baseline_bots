from typing import List, Set

from daidepp import FCT, XDO
from diplomacy import Game, Message

from baseline_bots.bots.dipnet_bot import DipnetBot
from baseline_bots.parsing_utils import daide_to_dipnet_parsing, dipnet_to_daide_parsing
from baseline_bots.utils import (
    MessagesData,
    get_other_powers,
    optional_ORR,
    parse_arrangement,
    parse_daide,
)


class TransparentBot(DipnetBot):
    """
    Execute orders computed by dipnet
    Send out some of them randomly
    """

    orders_gossiped: Set[str]
    my_orders_informed: bool
    orders: List[str]

    def __init__(self, power_name: str, game: Game, total_msg_rounds: int = 3):
        super().__init__(power_name, game, total_msg_rounds)
        self.orders_gossiped = set()
        self.my_orders_informed = False
        self.orders = []

    def phase_init(self) -> None:
        super().phase_init()
        self.orders_gossiped = set()
        self.my_orders_informed = False

    def parse_messages(self, rcvd_messages: List[Message]) -> List[str]:
        press_msgs = [
            msg for msg in rcvd_messages if isinstance(parse_daide(msg.message), FCT)
        ]
        parsed_orders = []
        for msg in press_msgs:
            parsed_message: FCT = parse_daide(msg.message)
            parsed_orders += parse_arrangement(str(parsed_message.arrangement_qry_not))
        return parsed_orders

    def gen_messages(self, rcvd_messages: List[Message]) -> MessagesData:
        self.my_orders_informed = False
        comms_obj = MessagesData()
        if self.game.get_current_phase()[-1] != "M":
            return comms_obj
        parsed_orders = self.parse_messages(rcvd_messages)
        parsed_orders = [
            list(daide_to_dipnet_parsing(order))[0]
            for order in parsed_orders
            if daide_to_dipnet_parsing(order)
        ]

        # My orders' messages if not already sent
        if not self.my_orders_informed:
            parsed_orders += self.orders
            self.my_orders_informed = True

        final_orders = []
        for order in parsed_orders:
            if order not in self.orders_gossiped:
                final_orders.append(order)
                self.orders_gossiped.add(order)

        for other_power in get_other_powers([self.power_name], self.game):
            if final_orders:
                commands = dipnet_to_daide_parsing(final_orders, self.game)
                orders = [XDO(command) for command in commands]
                msg = FCT(optional_ORR(orders))
                comms_obj.add_message(other_power, str(msg))

        return comms_obj

    async def __call__(self) -> List[str]:
        self.orders = await self.gen_orders()
        rcvd_messages = self.read_messages()
        messages = self.gen_messages(rcvd_messages)
        await self.send_messages(messages)
        return self.orders
