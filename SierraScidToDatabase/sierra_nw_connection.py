import socket
import threading
import json
import datetime
import time
import logging
import os
import sys
from database_util import DatabaseUtility
from queue import Queue
from dotenv import load_dotenv

load_dotenv('./keys_and_secrets.env')
DB_NAME = os.getenv('sql_name')
DB_USER = os.getenv('sql_username')
DB_PW = os.getenv('sql_password')
DB_CREATED = os.getenv('db_created')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('market_data_server')

DB_PARAMS = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PW,
    'host': 'localhost',
    'port': '5432',
}

db_queue = Queue()

# double check the db connection
if DB_CREATED == 'false':
    DatabaseUtility.create_db(DB_NAME, DB_USER, DB_PW)
    DatabaseUtility.create_tables(DB_NAME, DB_USER, DB_PW)
    sys.exit("Attempted to create database and tables, doublecheck...")
db_connection = DatabaseUtility.database_connect(DB_PARAMS['dbname'], DB_PARAMS['user'], DB_PARAMS['password'])

def db_worker() -> None:
    """ Worker that handles database operations from the queue """
    cur = db_connection.cursor()

    while True:
        batch = []
        batch.append(db_queue.get())

        # try to get more items for batch operation
        try:
            while (len(batch) < 100):
                item = db_queue.get_nowait()
                batch.append(item)
        except:
            # queue empty or not enough items
            pass

        # process the batchj
        try:
            for operation, data in batch:
                if operation == "insert_raw":
                    cur.execute("""
                        INSERT INTO raw_contracts 
                        (contract_id, symbol, expiry_date, datetime, price, num_trades, bid_volume, ask_volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (contract_id, datetime) DO UPDATE SET
                        price = EXCLUDED.price,
                        num_trades = EXCLUDED.num_trades,
                        bid_volume = EXCLUDED.bid_volume,
                        ask_volume = EXCLUDED.ask_volume
                    """, data)
                elif operation == "insert_continuous":
                    cur.execute("""
                        INSERT INTO continuous_contracts 
                        (symbol, datetime, price, volume, num_trades, bid_volume, ask_volume, active_contract_id, rollover_flag)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, datetime) DO UPDATE SET
                        price = EXCLUDED.price,
                        volume = EXCLUDED.volume,
                        num_trades = EXCLUDED.num_trades,
                        bid_volume = EXCLUDED.bid_volume,
                        ask_volume = EXCLUDED.ask_volume,
                        active_contract_id = EXCLUDED.active_contract_id,
                        rollover_flag = EXCLUDED.rollover_flag
                    """, data)
            
            db_connection.commit()

            for _ in range(len(batch)):
                db_queue.task_done()

        except Exception as e:
            logger.error(f'Database operation error: {e}')
            db_connection.rollback()

            for item in batch:
                db_queue.put(item)
            
            for _ in range(len(batch)):
                db_queue.task_done()
            
            time.sleep(1)

def handle_client(client_socket, client_address):
    """Handle incoming client connections"""
    logger.info(f"Connection established with {client_address}")
    
    try:
        buffer = b""
        while True:
            try:
                client_socket.settimeout(30)
                data = client_socket.recv(4096)
                
                if not data:
                    logger.info(f"Client {client_address} closed connection (empty data)")
                    break
                
                logger.debug(f"Received {len(data)} bytes from {client_address}")
                    
                buffer += data
                logger.debug(f"Buffer size now: {len(buffer)} bytes")
                
                # process complete messages
                while b"\n" in buffer:
                    msg_bytes, buffer = buffer.split(b"\n", 1)
                    logger.debug(f"Processing message of size {len(msg_bytes)} bytes")
                    
                    try:
                        msg_data = json.loads(msg_bytes.decode('utf-8'))
                        logger.debug(f"JSON parsed successfully: {msg_data.get('type', 'unknown')} message")
                        
                        process_message(msg_data)
                        logger.debug(f"Message processed successfully")
                        
                    except json.JSONDecodeError as je:
                        logger.warning(f"Invalid JSON received from {client_address}: {je}, message: {msg_bytes[:100]}...")
                    except Exception as e:
                        logger.error(f"Error processing message from {client_address}: {e}")
            
            except socket.timeout:
                logger.debug(f"Socket timeout for {client_address}, continuing...")
                continue
            except ConnectionResetError:
                logger.error(f"Connection reset by {client_address}")
                break
            except ConnectionAbortedError:
                logger.error(f"Connection aborted by {client_address}")
                break
    
    except Exception as e:
        logger.error(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        logger.info(f"Connection closed with {client_address}")

def process_message(message):
    """ Process a message and queue it for database insertion """
    msg_type = message.get('type')

    if msg_type == 'raw_data':
        contract_id = message.get('contract_id')
        symbol = message.get('symbol')
        expiry_date = message.get('expiry_date')
        if expiry_date:
            expiry_date = datetime.datetime.fromisoformat(expiry_date).date()
        timestamp = datetime.datetime.fromisoformat(message.get('timestamp'))
        price = message.get('price')
        num_trades = message.get('num_trades', 0)
        bid_volume = message.get('bid_volume', 0)
        ask_volume = message.get('ask_volume', 0)

        db_queue.put((
            "insert_raw",
            (contract_id, symbol, expiry_date, timestamp, price, num_trades, bid_volume, ask_volume)
        ))
    elif msg_type == 'continuous_data':
        symbol = message.get('symbol')
        timestamp = datetime.datetime.fromisoformat(message.get('timestamp'))
        price = message.get('price')
        volume = message.get('volume', 0)
        num_trades = message.get('num_trades', 0)
        bid_volume = message.get('bid_volume', 0)
        ask_volume = message.get('ask_volume', 0)
        active_contract = message.get('active_contract_id')
        rollover = message.get('rollover_flag', False)

        db_queue.put((
            "insert_continuous",
            (symbol, timestamp, price, volume, num_trades, bid_volume, ask_volume, active_contract, rollover)
        ))
    else:
        logger.warning(f'Unknown message type: {msg_type}')

def start_server(host='0.0.0.0', port=5555):
    """ Start the TCP server """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((host, port))
        server.listen(5)
        logger.info(f'Server listening on {host}:{port}')

        db_worker_thread = threading.Thread(target=db_worker, daemon=True)
        db_worker_thread.start()

        while True:
            client_sock, address = server.accept()
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_sock, address),
                daemon=True
            )
            client_handler.start()
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server.close()
            


if __name__ == '__main__':
        
    while True:
        try:
            conn = DatabaseUtility.database_connect(DB_PARAMS['dbname'], DB_PARAMS['user'], DB_PARAMS['password'])
            conn.close()
            break
        except:
            logger.info("Waiting for database connection...")
            time.sleep()
    start_server()
