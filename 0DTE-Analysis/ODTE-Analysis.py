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
    strikes = SPXOptions.get_options_codes_range(spot)
    filtered_options = SPXOptions.get_spx_options(strikes)

    # might add function to SPXOptions class to grab the relevant greeks from the filtered options




# perpetual loop that polls CBOE Rest endpoint at semi random times
# data gets stored in file for later visualization
base_interval = 300 # 300 seconds
random_range = 10 # +- 10 seconds for polling, can't have cboe getting wise on me
while True:
    # create function to grab the data
    get_data()
    
    random_delay = random.randint(-random_range, random_range)
    delay = base_interval + random_delay

    time.sleep(delay)