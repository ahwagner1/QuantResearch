import socket
import json
import time
import datetime
import random
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('market_data_client')

class MarketDataClient:
    def __init__(self, server_host='127.0.0.1', server_port=5555):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        
    def connect(self):
        """ Connect to the market data server """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            logger.info(f"Connected to server at {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """ Disconnect from the server """
        if self.socket:
            self.socket.close()
            self.socket = None
            self.connected = False
            logger.info("Disconnected from server")
    
    def send_tick_data(self, contract_id, symbol, price, timestamp=None, expiry_date=None, 
                      num_trades=0, bid_volume=0, ask_volume=0):
        """ Send tick data to the server """
        if not self.connected:
            if not self.connect():
                return False
        
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        message = {
            'type': 'raw_data',
            'contract_id': contract_id,
            'symbol': symbol,
            'price': price,
            'timestamp': timestamp,
            'num_trades': num_trades,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume
        }
        
        if expiry_date:
            message['expiry_date'] = expiry_date
        
        return self._send_message(message)
    
    def send_continuous_data(self, symbol, price, active_contract_id, timestamp=None, 
                            volume=0, num_trades=0, bid_volume=0, ask_volume=0, rollover_flag=False):
        """ Send continuous contract data to the server """
        if not self.connected:
            if not self.connect():
                return False
        
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        message = {
            'type': 'continuous_data',
            'symbol': symbol,
            'price': price,
            'timestamp': timestamp,
            'volume': volume,
            'num_trades': num_trades,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'active_contract_id': active_contract_id,
            'rollover_flag': rollover_flag
        }
        
        return self._send_message(message)
    
    def _send_message(self, message):
        """ Encode and send a message to the server """
        try:
            json_data = json.dumps(message) + "\n"
            self.socket.sendall(json_data.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.connected = False
            return False

# example usage
if __name__ == "__main__":
    client = MarketDataClient()
    
    # sample data for testing
    symbols = ["ES", "NQ", "CL", "GC", "ZB"]
    contracts = {
        "ES": ["ESH24", "ESM24", "ESU24", "ESZ24"],
        "NQ": ["NQH24", "NQM24", "NQU24", "NQZ24"],
        "CL": ["CLJ24", "CLK24", "CLM24", "CLN24"],
        "GC": ["GCJ24", "GCM24", "GCQ24", "GCV24"],
        "ZB": ["ZBH24", "ZBM24", "ZBU24", "ZBZ24"]
    }
    
    try:
        for _ in range(100):
            for symbol in symbols:
                symbol_contracts = contracts[symbol]
                
                active_contract = symbol_contracts[0]
                
                base_price = 100.0 if symbol == "ES" else 50.0
                
                for contract in symbol_contracts:
                    contract_idx = symbol_contracts.index(contract)
                    price = base_price + contract_idx + random.random()
                    
                    client.send_tick_data(
                        contract_id=contract,
                        symbol=symbol,
                        price=price,
                        expiry_date="2024-06-21",
                        num_trades=random.randint(1, 100),
                        bid_volume=random.randint(10, 1000),
                        ask_volume=random.randint(10, 1000)
                    )
                
                client.send_continuous_data(
                    symbol=symbol,
                    price=base_price + random.random(),
                    active_contract_id=active_contract,
                    volume=random.randint(100, 10000),
                    num_trades=random.randint(10, 500),
                    bid_volume=random.randint(50, 5000),
                    ask_volume=random.randint(50, 5000)
                )
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Client shutting down")
    finally:
        client.disconnect()