import requests, json
from TTUtilities import TT_OrderCreations
from TTConfig import TTConfig
import datetime
import sys

'''
Library to connect to TastyTrade via REST api for autotrading purposes
TODO
Add some documentation like a readme or at least comments, this is a bt hard to follow
'''

class TTApi:
    session_token: str = None
    remember_token: str = None
    streamer_token: str = None
    streamer_uri: str = None
    streamer_websocket_uri: str = None
    streamer_level: str = None
    tt_uri: str = None
    wss_uri: str = None
    headers: dict = {}
    user_data: dict = {}
    use_prod: bool = False
    use_mfa: bool = False
    stop_body: dict = None

    def __init__(self, tt_config: TTConfig = TTConfig()) -> None:
        self.headers['Authorization'] = ""
        self.headers["Content-Type"] = "application/json"
        self.headers["Accept"] = "application/json"
        self.tt_config = tt_config

        if self.tt_config.use_prod:
            self.tt_uri = self.tt_config.prod_uri
            self.tt_wss = self.tt_config.prod_wss
        else:
            self.tt_uri = self.tt_config.cert_uri
            self.tt_wss = self.tt_config.prod_wss

    def _post(self, endpoints: str = None, body : dict = {}, headers : dict = None):
        if headers is None:
            headers = self.headers

        response = requests.post(self.tt_uri + endpoints, data=json.dumps(body), headers = headers)
        if response.status_code == 201:
            return response.json()
        print(f"Error {response.status_code}")
        print(f"Endpoint: {endpoints}")
        print(f"Body: {body}")
        print(f"Headers: {headers}")
        print(f"Response: {response.text}")
        return None
    
    def _get(self, endpoint: str = None, body: dict = {}, headers: dict = None, params: dict = {}):
        if headers is None:
            headers = self.headers
        
        response = requests.get(self.tt_uri + endpoint, data = json.dumps(body), headers = headers, params = params)
        if response.status_code == 200:
            return response.json()
        print(f"Error {response.status_code}")
        print(f"Endpoint: {endpoint}")
        print(f"Body: {body}")
        print(f"Headers: {headers}")
        print(f"Response: {response.text}")
        return None


    def _put(self, endpoint: str = None, body: dict = {}, headers: dict = None):
        '''
        pretty much only used for canceling/replacing orders. Will use thise for managing stop loss
        '''
        if headers is None:
            headers = self.headers
        
        response = requests.put(self.tt_uri + endpoint, data = json.dumps(body), headers = headers)
        if response.status_code == 204:
            return response.json()
        print(f"Error {response.status_code}")
        print(f"Endpoint: {endpoint}")
        print(f"Body: {body}")
        print(f"Headers: {headers}")
        print(f"Response: {response.text}")
        return None
    
    def _delete(self, endpoint: str = None, body: dict = {}, headers: dict = None):
        if headers is None:
            headers = self.headers
        
        response = requests.delete(self.tt_uri + endpoint, data=json.dumps(body), headers=headers)
        if response.status_code == 204:
            return response.json()
        print(f"Error {response.status_code}")
        print(f"Endpoint: {endpoint}")
        print(f"Body: {body}")
        print(f"Headers: {headers}")
        print(f"Response: {response.text}")
        return None

    def create_session(self):
        body = {
            'login' : self.tt_config.username,
            'password' : self.tt_config.password,
            'remember-me' : True,
        }

        if self.tt_config.use_mfa is True:
            mfa = input('MFA: ')
            self.headers['X-Tastyworks=OTP'] = mfa

        response = requests.post(self.tt_uri + '/sessions', data=json.dumps(body), headers=self.headers)
        response = response.json()
        self.headers['Authorization'] = response['data']['session-token']
        self.remember_token = response['data']['remember-token']


    def end_session(self):
        self._delete('/sessions')
        return True
    
    def fetch_accounts(self):
        response = self._get('/customers/me/accounts')

        if response is None:
            return False
        
        self.user_data["accounts"] = []
        for account in response["data"]["items"]:
            self.user_data["accounts"].append(account["account"])

        return True
    
    def fetch_positions(self, account: str = ""):
        if account == "":
            return False
        
        response = self._get(f'/accounts/{account}/positions')

        if response is None:
            return False
        
        if 'account_positions' not in self.user_data:
            self.user_data['account_positions'] = []
        
        for position in response['data']['items']:
            self.user_data['account_positions'].append(position['symbol'].split()[0])
        
        return True
    
    def submit_order(self, order: TT_OrderCreations = None):
        if order is None:
            return False
        
        # submit the entry order, and then submit the exit order only if the entry order is placed successfully
        entry_order, exit_order = order.build_orders()
        self.stop_body = exit_order
        
        ##print(self.user_data)
        ##sys.exit(1)

        response = self._post(
            f"/accounts/{self.user_data['accounts'][0]['account-number']}/orders/dry-run",
            body = entry_order
        )
        
        response2 = None
        if response is not None:
            response2 = self._post(
                f"/accounts/{self.user_data['accounts'][0]['account-number']}/orders/dry-run",
                body = exit_order
            )
        
        if response2 is not None:
            return response2['data']['order']['id']
        
    def manage_stop(self, stop_id: int = None, new_price: float = None):
        '''
        manage the stop every minute
        '''

        if stop_id is None or new_price is None:
            print("id or price is missing")
            return False
        
        body = self.stop_body
        body['stop-trigger'] = new_price

        response = self._put(
            f"/accounts/{self.user_data['accounts'][0]['account-number']}/orders/{stop_id}",
            body = body,
        )

        if response is not None:
            return True
    
    def kill(self):
        '''
        will be used for canceling and closing all trades at once
        '''
        
'''
TTApi class handles the connections to TastyTrade, and all order handling
autotrading logic can be split to other files, below was just texting to see if it worked
gonna keep examples in so I don't forget how to use this
'''

ORDER_ACTIONS = {
    'BTO' : 'Buy to Open',
    'BTC' : 'Buy to Close',
    'STO' : 'Sell to Open',
    'STC' : 'Sell to Close',
}
'''
configs = TTConfig(path = "/TTAutoTrading", filename = "tt.ini")
connection = TTApi(configs)
connection.create_session()
res = connection.fetch_accounts()

order = TT_OrderCreations(
    'Day',
    'SPY',
    2,
    ORDER_ACTIONS['BTO'],
    450.05,
    ORDER_ACTIONS['STC'],    
)

stop_order_id = connection.submit_order(order)
if stop_order_id is None:
    print("THINGS BROKEN, FIX ASAP")
    raise ValueError("BROIKEN")'''
