from enum import Enum
import json

class TT_OrderCreations:
    '''
    This will really only be good for market orders on stocks, in the future I'll update it to be more flexible for other order types
    '''
    
    def __init__(self, tif: str = None, 
                 symbol: str = None, 
                 quantity: int = None, 
                 action: str = None,
                 stop_price: float = None,
                 stop_action: str = None
                 ):
        self.tif = tif
        self.symbol = symbol
        self.quantity = quantity
        self.action = action
        self.legs = []
        self.body = None

        # extra variables for building the stop order
        self.stop_price = stop_price
        self.stop_action = stop_action
        self.stop_legs = []
        self.stop_body = None

    def build_orders(self):
        '''
        DONT NEED TO KNOW DIRECTION. STRUCTURE DOESNT CHANGE FOR L/S, AS LONG AS THE ACTIONS ARE CORRECT, THIS SHOULD BE FINE
        '''

        # open market order
        self.legs.append({
            'instrument-type' : 'Equity',
            'symbol' : self.symbol,
            'quantity' : self.quantity,
            'action' : self.action
        })

        self.body = {
            'time-in-force' : self.tif,
            'order-type' : 'Market',
            'legs' : self.legs
        }
        print(json.dumps(self.body))
        
        # building the associated stop order to go with the market order
        self.stop_legs.append({
            'instrument-type' : 'Equity',
            'symbol' : self.symbol,
            'quantity' : self.quantity,
            'action' : self.stop_action
        })

        self.stop_body = {
            'time-in-force' : self.tif,
            'order-type' : 'Stop',
            'stop-trigger' : self.stop_price,
            'legs' : self.stop_legs
        }
        print(json.dumps(self.stop_body))
        
        return self.body, self.stop_body
