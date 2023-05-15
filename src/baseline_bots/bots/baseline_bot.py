"""Abstract base classes for baseline bots"""


from abc import ABC, abstractmethod
from typing import List

from diplomacy import Game, Message
from diplomacy.client.network_game import NetworkGame

from baseline_bots.utils import MessagesData, OrdersData, is_valid_daide_message


class BaselineBot(ABC):
    """Abstract Base Class for baselines bots"""

    power_name: str
    game: Game

    def __init__(self, power_name: str, game: Game) -> None:
        self.power_name = power_name
        self.game = game

    @property
    def display_name(self) -> str:
        """Display name consisting of power name and bot type."""
        return f"{self.power_name} ({self.__class__.__name__})"

    def read_messages(self) -> List[Message]:
        """Retrieves all valid messages for the current phase sent to the bot.
        :return: List of messages.
        """
        messages = self.game.filter_messages(
            messages=self.game.messages, game_role=self.power_name
        )
        received_messages = sorted(
            msg for msg in messages.values() if msg.sender != self.power_name
        )
        for msg_obj in received_messages:
            print(f"{self.display_name} received message: {msg_obj}")
        valid_messages = []
        for msg in received_messages:
            if is_valid_daide_message(msg.message):
                valid_messages.append(msg)
            else:
                print(
                    f"!! {self.display_name} received a message with invalid DAIDE syntax: {msg.message!r}"
                )
        return valid_messages

    async def send_message(
        self, recipient: str, message: str, msg_data: MessagesData
    ) -> None:
        """Send message asynchronously to the server

        :param recipient: The name of the recipient power
        :param message: Message to be sent
        :param msg_data: MessagesData object containing set of all sent messages
        """
        if not is_valid_daide_message(message):
            print(
                f"!! {self.display_name} attempted to send a message with invalid DAIDE syntax: {message!r}"
            )
            return

        msg_obj = Message(
            sender=self.power_name,
            recipient=recipient,
            message=message,
            phase=self.game.get_current_phase(),
        )
        message_already_exists = msg_data.add_message(
            msg_obj.recipient, msg_obj.message, allow_duplicates=False
        )
        if message_already_exists:
            return

        print(f"{self.display_name} sent message: {msg_obj}")

        # Messages should not be sent in local games, only stored
        if isinstance(self.game, NetworkGame):
            await self.game.send_game_message(message=msg_obj)
        else:
            self.game.add_message(message=msg_obj)

    async def send_messages(self, msg_data: MessagesData) -> None:
        """Send messages asynchronously to the server

        :param msg_data: MessagesData object containing messages to send
        """
        for msg in msg_data.messages:
            # A new `MessagesData` instance is used because we don't want
            # to add duplicate messages to the passed-in instance
            await self.send_message(msg["recipient"], msg["message"], MessagesData())

    @abstractmethod
    def __call__(self) -> OrdersData:
        """
        :return: dict containing messages and orders
        """
        raise NotImplementedError()


class BaselineMsgRoundBot(BaselineBot, ABC):
    """
    Abstract Base Class for bots which execute
    multiple rounds of communication before setting
    orders
    """

    total_msg_rounds: int
    cur_msg_round: int
    orders: OrdersData

    def __init__(self, power_name: str, game: Game, total_msg_rounds: int = 3) -> None:
        """
        :param num_msg_rounds: the number of communication rounds the bot
        will go through
        """
        super().__init__(power_name, game)
        self.total_msg_rounds = total_msg_rounds
        self.orders = OrdersData()

    def gen_orders(self) -> OrdersData:
        """finalizes moves"""
        return self.orders

    def phase_init(self) -> None:
        """reset information after each order round complete"""
        # the current message round, which is reset after each order round
        self.curr_msg_round = 1
        # reset selected orders
        self.orders = OrdersData()

    def are_msg_rounds_done(self) -> bool:
        return self.curr_msg_round == self.total_msg_rounds + 1
