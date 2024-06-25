import sys
sys.path.append('/home/ahwagner/repos/QuantResearch/') # have to do this until I actually structure things correctly
from commons import SPXOptions
import numpy as np
import pandas as pd
import plotly.express as px
import random
import datetime
import time

'''
Using this to analyse SPX options greeks on price
Mainly interested in Net Delta and Net Gamma over the course of a day

TODO
Setup function to hit CBOE rest api in intervals of 5/10 mins and grab relevant options data
Store Data (Strike, IV, Gamma, Delta, Maybe Vega/Vanna/Vomma/Charm)
Plot the data overtime to see if obvious 
'''

def get_data(spot):

    # god I love python, so beautiful
    date = ''.join(str(datetime.date.today()).split('-'))[2:]
    strikes = SPXOptions.get_options_codes_range(spot, date)
    filtered_options = SPXOptions.get_spx_options(strikes) # list of options dictionaries
    
    # calc interesting metrics
    # a bit ugly but I need to differentiate between calls and puts, the 10th letter in the option code is always 'C' or 'P'
    # https://doc.tradingflow.com/product-docs/concepts/delta-exposure-dex
    gamma_calls = [option['open_interest'] * option['gamma'] * 100 for option in filtered_options if option['option'][10] == 'C']
    gamma_puts = [option['open_interest'] * option['gamma'] * -100 for option in filtered_options if option['option'][10] == 'P']

    delta_calls = [option['open_interest'] * option['delta'] * 100 for option in filtered_options if option['option'][10] == 'C']
    delta_puts = [option['open_interest'] * option['delta'] * 100 for option in filtered_options if option['option'][10] == 'P']

    # need to store these in a sequential file or data structure to analyse EOD to see if any predictive power
    net_gamma = gamma_calls + gamma_puts
    net_delta = delta_calls + delta_puts

# perpetual loop that polls CBOE Rest endpoint at semi random times
# data gets stored in file for later visualization
base_interval = 300 # 300 seconds
random_range = 10 # +- 10 seconds for polling, can't have cboe getting wise on me
while True:
    # create function to grab the data
    spot = 5447.87
    get_data(spot)
    
    random_delay = random.randint(-random_range, random_range)
    delay = base_interval + random_delay
    break
    time.sleep(delay)