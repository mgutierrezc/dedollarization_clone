from otree.api import Currency as c, currency_range
from .models import Constants

def bot_attempted_trade(bot_item, partner_item):
    """
    (Bots Only) Determines if bot should trade or not

    input: Bot item (String), partner item (String)
    output: trade attempted (Boolean)
    """
    current_items = [bot_item, partner_item]
    
    if Constants.trade_good in current_items and Constants.blue in current_items:
        return True
    else:
        return False
