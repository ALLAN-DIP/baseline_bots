"""
Some functions that generate randomized orders from 
an already existing order / list of orders.
"""

__author__ = "Konstantine Kahadze"
__email__ = "konstantinekahadze@gmail.com"

import re
from typing import Tuple

def tuple_to_string(order: Tuple) -> str:
    '''
    Takes in a tuple representing an order and returns a string
    representing the same order in DAIDE format
    Ex. tuple_to_string((('FRA', 'AMY', 'BUR'), 'MTO', 'PAR'))  -> "(FRA AMY BUR) MTO PAR"
    '''
    for i, sub in enumerate(order):
        if isinstance(sub, Tuple): # if a recursive call is necessary to parse a nested tuple
            if i == 0 or i == 1: # if a comma must be added before the parenthesis
                return ' '.join(str(item) for item in order[:i]) + "(" + tuple_to_string(sub) + ") " + tuple_to_string(order[i+1:])
            else:
                return ' '.join(str(item) for item in order[:i]) + " (" + tuple_to_string(sub) + ") " + tuple_to_string(order[i+1:])
    # otherwise joins the tuple without recursion
    return ' '.join(str(item) for item in order) 

def string_to_tuple(orders: str) -> Tuple:
    '''
    Takes as string representing an order in DAIDE format and 
    returns a tuple representing the same order.
    Ex. -> string_to_tuple( "((FRA AMY BUR) MTO PAR)" ) -> (('FRA', 'AMY', 'BUR'), 'MTO', 'PAR')
    '''
    with_commas = re.sub(r"(.*?[^(])\s+?([^)].*?)", r"\1, \2",  orders) # inserts commas in between tuples and strings
    with_quotes = re.sub(r"([(, ])([A-Z]+)([), ])", r"\1'\2'\3", with_commas) # inserts quotes around strings
    return eval(with_quotes)
 

def randomize_joiner(order: str) -> str:
    '''
    This function only takes in non-nested ANDs or ORRs and returns a randomized version
    of those orders.
    '''
    with_joiner = re.sub(r"[\s+]?(AND|ORR)", r"\1", order)
    joiner = with_joiner[0:3] # extracts the "AND" or "ORR" string
    just_moves = with_joiner[3:] # removes the "AND" or "ORR" with all preceding whitespace
    with_inner_commas = re.sub(r"(.*?[^(])\s+?([^)].*?)", r"\1, \2", just_moves) # adds commas within tuples
    with_outer_commas = re.sub(r"(\(\(.+\)\)|\(.+?WVE\)) ", r"\1,", with_inner_commas) # adds commas between strings and tuples
    with_quotes = re.sub(r"([(, ])([A-Z]+)([), ])", r"\1'\2'\3", with_outer_commas) # adds quotes around strings
    order_list = eval('[' + with_quotes + ']') # turns string into list of tuples
    rand = random_orders(order_list) # randomizing orders
    str_orders = joiner + " "
    for ord in rand:
        str_orders += "(" + (tuple_to_string(ord)) + ") "
    return str_orders

