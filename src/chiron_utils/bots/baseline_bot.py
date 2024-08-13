"""Abstract base classes for bots."""


from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
import os
import random
from typing import ClassVar, List, Optional, Sequence

from diplomacy import Game, Message
from diplomacy.client.network_game import NetworkGame
from diplomacy.utils import strings

from chiron_utils.utils import return_logger

logger = return_logger(__name__)

DEFAULT_COMM_STAGE_LENGTH = 300  # 5 minutes in seconds
COMM_STAGE_LENGTH = int(os.environ.get("COMM_STAGE_LENGTH", DEFAULT_COMM_STAGE_LENGTH))


@dataclass
class BaselineBot(ABC):
    """Abstract base class for bots."""

    player_type: ClassVar[str] = strings.PRESS_BOT
    bot_type: ClassVar[str]
    power_name: str
    game: Game
    num_message_rounds: Optional[int] = None
    communication_stage_length: int = COMM_STAGE_LENGTH  # in seconds

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
            await self.game.set_comm_status(power_name=self.power_name, comm_status=strings.READY)
        else:
            self.game.set_comm_status(power_name=self.power_name, comm_status=strings.READY)

        while not all(
            power.comm_status == strings.READY
            for power in self.game.powers.values()
            if power.player_type == strings.PRESS_BOT and not power.is_eliminated()
        ):
            await asyncio.sleep(1)

    def read_messages(self) -> List[Message]:
        """Retrieves all valid messages for the current phase sent to the bot.

        Returns:
            List of messages.
        """
        messages = self.game.filter_messages(messages=self.game.messages, game_role=self.power_name)
        received_messages = sorted(
            msg for msg in messages.values() if msg.sender != self.power_name
        )
        for msg_obj in received_messages:
            logger.info("%s received message: %s", self.display_name, msg_obj)
        return received_messages

    async def send_message(
        self,
        recipient: str,
        message: str,
        *,
        sender: Optional[str] = None,
        msg_type: Optional[str] = None,
    ) -> None:
        """Send message to the server.

        Args:
            recipient: The name of the power receiving the message.
            message: Text of message to be sent.
            sender: The name of the power sending the message.
            msg_type: Type of message (e.g., `"suggested_message"`, `"suggested_move"`)
        """
        msg_obj = Message(
            sender=sender or self.power_name,
            recipient=recipient,
            message=message,
            phase=self.game.get_current_phase(),
            type=msg_type,
        )
        logger.info("%s sent message: %s", self.display_name, msg_obj)

        # Messages should not be sent in local games, only stored
        if isinstance(self.game, NetworkGame):
            await self.game.send_game_message(message=msg_obj)
        else:
            self.game.add_message(message=msg_obj)

    async def suggest_orders(self, orders: List[str]) -> None:
        """Send suggested orders for power to the server.

        Args:
            orders: Orders to suggest.
        """
        await self.send_message(
            "GLOBAL",
            f"{self.power_name} Cicero suggests move: {', '.join(orders)}",
            sender="omniscient_type",
            msg_type="suggested_move",
        )

    async def suggest_message(self, recipient: str, message: str) -> None:
        """Send suggested messages for power to the server.

        Args:
            recipient: The name of the power that would receive the recommended message.
            message: Text of the recommended message.
        """
        await self.send_message(
            "GLOBAL",
            f"{self.power_name} Cicero suggests a message to {recipient}: {message}",
            sender="omniscient_type",
            msg_type="suggested_message",
        )

    async def send_intent_log(self, log_msg: str) -> None:
        """Send intent log to the server.

        Args:
            log_msg: Text of message to store in intent log.
        """
        logger.info("Intent log: %r", (log_msg))
        # Intent logging should not be sent in local games
        if not isinstance(self.game, NetworkGame):
            return
        log_data = self.game.new_log_data(body=log_msg)
        await self.game.send_log_data(log=log_data)

    async def send_orders(self, orders: Sequence[str], *, wait: bool = False) -> None:
        """Send orders to the server.

        Args:
            orders: Orders to send.
            wait: Whether the server should be told to wait for further orders.
        """
        logger.info("Sent orders: %s", orders)

        # Orders should not be sent in local games, only stored
        if isinstance(self.game, NetworkGame):
            # pylint: disable=unexpected-keyword-arg
            await self.game.set_orders(power_name=self.power_name, orders=orders, wait=wait)
        else:
            self.game.set_orders(power_name=self.power_name, orders=orders)

    async def start_phase(self) -> None:
        """Execute actions at the start of the phase."""
        return

    @abstractmethod
    async def gen_orders(self) -> List[str]:
        """Generate orders for a turn.

        Returns:
            List of orders to carry out.
        """
        raise NotImplementedError

    @abstractmethod
    async def do_messaging_round(self, orders: Sequence[str]) -> List[str]:
        """Carry out one round of messaging, along with related tasks.

        Returns:
            List of orders to carry out.
        """
        raise NotImplementedError

    async def end_phase(self) -> None:
        """Execute actions at the end of the phase."""
        return

    async def __call__(self) -> List[str]:
        """Carry out one phase of the game.

        Returns:
            List of orders to carry out.
        """
        await self.start_phase()

        orders = await self.gen_orders()

        # Skip communications unless in the movement phase
        if not self.game.get_current_phase().endswith("M"):
            return orders

        if self.bot_type == "player":
            await self.send_intent_log(f"Initial orders (before communication): {orders}")

        await self.wait_for_comm_stage()

        if self.num_message_rounds:
            for _ in range(self.num_message_rounds):
                # sleep for a random amount of time before retrieving new messages for the power
                await asyncio.sleep(random.uniform(0.5, 1.5))
                orders = await self.do_messaging_round(orders)
        else:

            async def run_messaging_loop() -> None:
                nonlocal orders

                while True:
                    # sleep for a random amount of time before retrieving new messages for the power
                    await asyncio.sleep(random.uniform(0.5, 1.5))

                    orders = await self.do_messaging_round(orders)

            try:
                # Set aside 10s for cancellation
                wait_time = self.communication_stage_length - 10
                await asyncio.wait_for(run_messaging_loop(), timeout=wait_time)
            except asyncio.TimeoutError:
                logger.info("Exiting communication phase because out of time")

        await self.end_phase()

        return orders
