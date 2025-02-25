"""
This file contains all of the functions for connecting to the database and all that
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('./keys_and_secrets.py')
SQL_USERNAME = os.getenv('sql_username')
SQL_PASSWORD = os.getenv('sql_password')
SQL_DB_NAME  = os.get_env('sql_name')

class DatabaseUtility:

    @classmethod
    def create_db(cls, db_name, user, password, host='localhost', port='5432') -> None:
        """
        This function creates a database if one does not already exists
        """
        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host=host,
            port=port,
        )

        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        cur = conn.cursor()

        try:
            cur.execute("SELECT 1 from pg_catalog.pg_database where datname = %s", (db_name,))
            exists = cur.fetchone()

            if not exists:
                cur.execute(f"CREATE DATABASE {db_name}")
                print(f"Database '{db_name}' created successfully")
            else:
                (f"Database '{db_name}' already exists")
        except Exception as e:
            print(f"Erorr:\n{e}")
        finally:
            cur.close()
            conn.close()
    
    @classmethod
    def create_tables(db_name, user, password, host='localhost', port='5432'):
        """
        This function creates tables for storing commodity data that we parsed from .scid files provided by SC
        """

        conn_string = f"dbname={db_name} user={user} password={password} host={host} port={port}"

        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        try:
            # create main table for data
            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw_contracts (
                        id SERIAL PRIMARY KEY,
                        contract_id VARCHAR(50) NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        expiry_date DATE,
                        datetime TIMESTAMP WITH TIME ZONE NOT NULL,
                        price DECIMAL(12, 6),
                        num_trades INTEGER,
                        bid_volume INTEGER,
                        ask_volume INTEGER,
                        UNIQUE(contract_id, datetime)
            );        
            """)
            
            # create index for faster queries
            cur.execute("""
                        CREATE INDEX IF NOT EXISTS ids_raw_contract_datetime
                        ON raw_contracts(contract_id, datetime);
            """)

            # create continuous contract table for easier backtesting
            cur.execute("""
            CREATE TABLE IF NOT EXISTS continuous_contracts (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                datetime TIMESTAMP WITH TIME ZONE NOT NULL,
                price DECIMAL(12, 6),
                volume INTEGER,
                num_trades INTEGER,
                bid_volume INTEGER,
                ask_volume INTEGER,
                active_contract_id VARCHAR(50) NOT NULL,
                rollover_flag BOOLEAN DEFAULT FALSE,
                UNIQUE(symbol, datetime)
            );
            """)

            # index for continuous contracts
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_continuous_datetime 
                ON continuous_contracts(symbol, datetime);
            """)

            # TODO
            # could add tables to track the files used and processing times

            conn.commit()
            print("Tables created successfully")
        except Exception as e:
            conn.rollback()
            print(f"Error creating tables:\n{e}")
        finally:
            cur.close()
            conn.close()