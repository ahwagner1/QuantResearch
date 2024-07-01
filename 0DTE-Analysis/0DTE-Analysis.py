import sys
sys.path.append('/home/ahwagner/repos/QuantResearch/') # have to do this until I actually structure things correctly
from commons import SPXOptions
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from datetime import time as datetime_time # giving alias since there is a naming conflict with below time module
import yfinance as yf
import numpy as np
import pandas as pd
import random
import pytz
import os
import time

'''
Using this to analyse SPX options greeks on price
Mainly interested in Net Delta and Net Gamma over the course of a day

TODO
Setup function to hit CBOE rest api in intervals of 5/10 mins and grab relevant options data
Store Data (Strike, IV, Gamma, Delta, Maybe Vega/Vanna/Vomma/Charm)
Plot the data overtime to see if obvious 
'''

def create_and_save_plot(option_codes, net_gamma, net_delta, spot) -> None:
    '''
    Create and save the historgam plots as time goes on to analyze at later times
    Plots saved as html
    '''

    # extracting the strikes from the options codes
    strikes = [float(s[12:16]) for s in option_codes]

    # padding
    y_min = min(strikes)
    y_max = max(strikes)
    y_range = [y_min - (y_max - y_min) * 0.1, y_max + (y_max - y_min) * 0.1]

    fig = make_subplots(rows = 1, cols = 2, subplot_titles = ('Net Gamma by Strike', 'Net Delta by Strike'))

    fig.add_trace(
        go.Bar(x = net_gamma, y = strikes, name = 'Net Gamma', orientation = 'h'),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(x = net_delta, y = strikes, name = 'Net Delta', orientation = 'h'),
        row=1, 
        col=2,
    )

    fig.update_layout(
        title_text=f'Options Greeks (Spot: {spot})',
        height=1250,
        width=2000,
    )

    # spot prices
    fig.add_hline(y = spot, line_dash = 'dash', line_color = 'red', row = 1, col = 1)
    fig.add_hline(y = spot, line_dash = 'dash', line_color = 'red', row = 1, col = 2)

    # update x and y axes
    fig.update_xaxes(title_text = 'Net Gamma', row=1, col=1)
    fig.update_xaxes(title_text = 'Net Delta', row=1, col=2)
    fig.update_yaxes(title_text = 'Strike Price', row=1, col=1, range = y_range)
    fig.update_yaxes(title_text = 'Strike Price', row=1, col=2, range = y_range)

    # create the folder to save the plot
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'plots/options_greeks_{timestamp}.html'
    fig.write_html(filename)

def create_eod_chart(spot_prices, total_gammas, total_deltas):
    # create the EOD chart to see price v ganna/delta

    fig = make_subplots(rows = 2, cols = 1, subplot_titles = ('Splot Price vs Total Gamma', 'Spot Price vs Total Delta'))

    # spot v gamma
    fig.add_trace(
        go.Scatter(x = list(range(len(spot_prices))), y = spot_prices, name = 'Spot Price', line = dict(color = 'blue')),
        row = 1,
        col = 1,
    )

    fig.add_trace(
        go.Scatter(x = list(range(len(total_gammas))), y = total_gammas, name = 'Summed Gamma', line = dict(color = 'blue')),
        row = 1,
        col = 1,
    )

    # spot v delta
    fig.add_trace(
        go.Scatter(x = list(range(len(spot_prices))), y = spot_prices, name = 'Spot Price', line = dict(color = 'blue')),
        row = 2,
        col = 1,
    )

    fig.add_trace(
        go.Scatter(x = list(range(len(total_deltas))), y = total_gammas, name = 'Summed Delta', line = dict(color = 'blue')),
        row = 2,
        col = 1,
    )

    fig.update_layout(
        title_text = 'Spot Price vs Total Gamma and Delta',
        height = 1000,
        width = 1000,
        yaxis=dict(title = 'Spot Price', side = 'left', showgrid = True),
        yaxis2=dict(title='Total Gamma', side='right', overlaying='y', showgrid=True),
        yaxis3=dict(title = 'Spot Price', side = 'left', showgrid = True),
        yaxis4=dict(title='Total Delta', side='right', overlaying='y3', showgrid=True),
    )

    # create 'eod_charts' folder 
    if not os.path.exists('eod_charts'):
        os.makedirs('eod_charts')

    # Save the plot
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f'eod_charts/spot_gamma_delta_chart_{timestamp}.html'
    fig.write_html(filename)


def get_data(spot):
    # getting options greeks at different intervals

    # god I love python, so beautiful
    date = ''.join(str(datetime.date(datetime.now())).split('-'))[2:]
    strikes = SPXOptions.get_options_codes_range(spot, date)
    filtered_options = SPXOptions.get_spx_options(strikes) # list of options dictionaries
    
    # calc interesting metrics
    # a bit ugly but I need to differentiate between calls and puts, the 10th letter in the option code is always 'C' or 'P'
    # https://doc.tradingflow.com/product-docs/concepts/delta-exposure-dex
    gamma_calls = [option['open_interest'] * option['gamma'] * 100 * spot**2 * 0.01 for option in filtered_options if option['option'][10] == 'C']
    gamma_puts = [option['open_interest'] * option['gamma'] * -100 * spot**2 * 0.01 for option in filtered_options if option['option'][10] == 'P']

    delta_calls = [option['open_interest'] * option['delta'] * 100 for option in filtered_options if option['option'][10] == 'C']
    delta_puts = [option['open_interest'] * option['delta'] * 100 for option in filtered_options if option['option'][10] == 'P']

    # need to store these in a sequential file or data structure to analyse EOD to see if any predictive power
    net_gamma_by_strike = [call_gamma + put_gamma for call_gamma, put_gamma in zip(gamma_calls, gamma_puts)]
    net_delta_by_strike = [call_delta + put_delta for call_delta, put_delta in zip(delta_calls, delta_puts)]

    total_gamma = sum(net_gamma_by_strike)
    total_delta = sum(net_delta_by_strike)

    return strikes, net_gamma_by_strike, net_delta_by_strike, total_gamma, total_delta

def is_market_open():
    
    market_open = datetime_time(5, 30)
    market_close = datetime_time(12, 0),

    akst = pytz.timezone('US/Alaska')
    current_time = datetime.now(akst).time()

    # check if weekend, although I probably will never run this on the weekend
    is_weekday = datetime.now(akst).weekday() < 5

    # fun boolean logic
    return is_weekday and market_open <= current_time < market_close

def main():
    # perpetual loop that polls CBOE Rest endpoint at semi random times
    # data gets stored in file for later visualization
    base_interval = 900 #
    random_range = 10 # +- 10 seconds for polling, can't have cboe getting wise on me

    spot_prices = []
    total_gammas = []
    total_deltas = []
    while True:
        if not is_market_open():
            print('Market closed, exiting')
            break

        spx = yf.Ticker('^SPX')
        spx_prices = spx.history(interval = '5m')
        spot = spx_prices['Close'][-3] # need to delay 15 mins since cboe only provides delayed quotes

        strikes, net_gamma, net_delta, total_gamma, total_delta = get_data(spot)

        create_and_save_plot(strikes, net_gamma, net_delta, spot)
        total_gammas.append(total_gamma)
        total_deltas.append(total_delta)
        spot_prices.append(spot)
        
        random_delay = random.randint(-random_range, random_range)
        delay = base_interval + random_delay
        time.sleep(delay)
    
    create_eod_chart(spot_prices, total_gammas, total_deltas)

if __name__ == '__main__':
    main()