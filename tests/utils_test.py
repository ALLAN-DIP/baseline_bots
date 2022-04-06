import sys
sys.path.append("..")

from utils import OrdersData




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

