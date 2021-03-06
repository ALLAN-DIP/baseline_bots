import sys
sys.path.append("..")

from utils import OrdersData, sort_messages_by_most_recent




EXAMPLE_ORDER = 'A VIE S A BUD - GAL'
EXAMPLE_ORDER_2 = 'A VIE H'


orders_data = OrdersData()

# test regular add
orders_data.add_order(EXAMPLE_ORDER)
assert orders_data.get_list_of_orders() == ['A VIE S A BUD - GAL']

# test guarded add
orders_data.add_order(EXAMPLE_ORDER_2, overwrite=False)
assert orders_data.get_list_of_orders() == ['A VIE S A BUD - GAL']

orders_data.add_order(EXAMPLE_ORDER_2, overwrite=True)
assert orders_data.get_list_of_orders() == ['A VIE H']


# test sort_messages_by_most_recent
game = Game()
powers = list(game.powers)
power_0 = powers[0]
power_1 = powers[1]
msg_obj1 = Message(
    sender=power_0,
    recipient=power_1,
    message="HELLO",
    phase=game.get_current_phase(),
)
game.add_message(message=msg_obj1)
msg_obj2 = Message(
    sender=power_1,
    recipient=power_0,
    message="GOODBYE",
    phase=game.get_current_phase(),
)
game.add_message(message=msg_obj2)
msgs = [msg_obj2, msg_obj1]

assert sort_messages_by_most_recent(msgs)[0].message == "HELLO"