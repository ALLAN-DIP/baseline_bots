"""Abstract base classes for baseline bots"""


from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
import random
from typing import ClassVar, List, Optional, Sequence

from diplomacy import Game, Message
from diplomacy.client.network_game import NetworkGame
from diplomacy.utils import strings

from baseline_bots.utils import (
    LIMITED_MESSAGE_GRAMMAR,
    USE_LIMITED_DAIDE,
    MessagesData,
    is_valid_daide_message,
    return_logger,
)

logger = return_logger(__name__)


@dataclass
class BaselineBot(ABC):
    """Abstract Base Class for baselines bots"""

    player_type: ClassVar[str] = strings.PRESS_BOT
    power_name: str
    game: Game
    num_message_rounds: Optional[int] = None
    # communication_stage_length: int = 300  # 5 minutes
    communication_stage_length: int = 30  # in seconds

    @property
    def display_name(self) -> str:
        """Display name consisting of power name and bot type."""
        return f"{self.power_name} ({self.__class__.__name__})"

    async def wait_for_comm_stage(self) -> None:
        """Wait for all other press bots to be ready.

        The bot marks itself as ready and then polls the other press bots until they are all ready.
        Once they all, the bot can start communicating.
        """
        # Comm status should not be sent in local games, only set
        if isinstance(self.game, NetworkGame):
            await self.game.set_comm_status(
                power_name=self.power_name, comm_status=strings.READY
            )
        else:
            self.game.set_comm_status(
                power_name=self.power_name, comm_status=strings.READY
            )

        while not all(
            power.comm_status == strings.READY
            for power in self.game.powers.values()
            if power.player_type == strings.PRESS_BOT and not power.is_eliminated()
        ):
            await asyncio.sleep(1)

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
            logger.info(f"{self.display_name} received message: {msg_obj}")
        valid_messages = []
        for msg in received_messages:
            if is_valid_daide_message(msg.message):
                valid_messages.append(msg)
            else:
                logger.warning(
                    f"{self.display_name} received a message with invalid DAIDE syntax: {msg.message!r}"
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
            logger.warning(
                f"{self.display_name} attempted to send a message with invalid DAIDE syntax: {message!r}"
            )
            return

        if USE_LIMITED_DAIDE and not is_valid_daide_message(
            message, LIMITED_MESSAGE_GRAMMAR
        ):
            logger.warning(
                f"{self.display_name} attempted a message outside of the limited DAIDE syntax: {message!r}"
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

        logger.info(f"{self.display_name} sent message: {msg_obj}")

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

    async def send_intent_log(self, log_msg: str) -> None:
        """Send intent log asynchronously to the server

        :param log_msg: Log message to be sent
        """
        logger.info(f"Intent log: {log_msg!r}")
        # Intent logging should not be sent in local games
        if not isinstance(self.game, NetworkGame):
            return
        log_data = self.game.new_log_data(body=log_msg)
        await self.game.send_log_data(log=log_data)

    async def send_orders(self, orders: Sequence[str], wait: bool = False) -> None:
        """Send orders asynchronously to the server

        :param orders: Orders to be sent
        """
        logger.info(f"Sent orders: {orders}")

        # Orders should not be sent in local games, only stored
        if isinstance(self.game, NetworkGame):
            await self.game.set_orders(
                power_name=self.power_name, orders=orders, wait=wait
            )
        else:
            self.game.set_orders(power_name=self.power_name, orders=orders)

    @abstractmethod
    async def gen_orders(self) -> List[str]:
        """
        :return: dict containing messages and orders
        """
        raise NotImplementedError()

    @abstractmethod
    async def do_messaging_round(
        self,
        orders: Sequence[str],
        msgs_data: MessagesData,
    ) -> List[str]:
        """
        :return: dict containing messages and orders
        """
        raise NotImplementedError()

    async def __call__(self) -> List[str]:
        """
        :return: dict containing messages and orders
        """
        orders = await self.gen_orders()

        # Skip communications unless in the movement phase
        if not self.game.get_current_phase().endswith("M"):
            return orders

        await self.send_intent_log(f"Initial orders (before communication): {orders}")

        await self.wait_for_comm_stage()

        if self.num_message_rounds:
            msgs_data = MessagesData()

            for _ in range(self.num_message_rounds):
                # sleep for a random amount of time before retrieving new messages for the power
                await asyncio.sleep(random.uniform(0.5, 1.5))
                orders = await self.do_messaging_round(orders, msgs_data)
        else:

            async def run_messaging_loop() -> None:
                nonlocal orders

                msgs = MessagesData()

                while True:
                    # sleep for a random amount of time before retrieving new messages for the power
                    await asyncio.sleep(random.uniform(0.5, 1.5))

                    orders = await self.do_messaging_round(orders, msgs)

            try:
                # Set aside 10s for cancellation
                wait_time = self.communication_stage_length - 10
                await asyncio.wait_for(run_messaging_loop(), timeout=wait_time)
            except asyncio.TimeoutError:
                logger.info("Exiting communication phase because out of time")

        return orders
