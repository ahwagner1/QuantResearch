import pandas as pd
from pandas import MultiIndex
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import yahoo_fin.stock_info as si
from pandas.tseries.offsets import MonthEnd, BDay

import sys
import os
sys.path.append('/home/ahwagner/repos/QuantResearch/')
import commons
from dot_env import load_dotenv

load_dotenv('./keys.env')
API_KEY = os.getenv(tk_api_key)

# Function that determines entry date for LONG position N trading days before month end
def is_entry_day(date, trading_days: int = 5):
    current_month_end = pd.Timestamp(date.year, date.month, 1) + MonthEnd(1)
    
    # Find date that is N trading days before month end
    entry_date = current_month_end - BDay(trading_days)
    
    # Check if current date is the entry date
    return date.date() == entry_date.date()

# Function that determines exit date for LONG position and entry for SHORT position
# N trading days after month start
def is_exit_day(date, trading_days: int = 3):
    # First day of current month
    current_month_start = pd.Timestamp(date.year, date.month, 1)
    
    # Find date that is N trading days after month start
    exit_date = current_month_start + BDay(trading_days)
    
    # Check if current date is the exit date
    return date.date() == exit_date.date()

# Function to determine exit date for SHORT position
def is_short_exit_day(date, trading_days: int = 8):
    # First day of current month
    current_month_start = pd.Timestamp(date.year, date.month, 1)
    
    # Find date that is N trading days after month start (when to exit short)
    short_exit_date = current_month_start + BDay(trading_days)
    
    # Check if current date is the short exit date
    return date.date() == short_exit_date.date()

def calc_metrics(data, title):
    ann_factor = 252  # Trading days in a year
    ann_return = data.mean() * ann_factor
    ann_vol = data.std() * np.sqrt(ann_factor)
    sharpe_ratio = ann_return / ann_vol if ann_vol != 0 else 0
 
    print(f'\n\n\n########{title}##########')
    print(f"Strategy Performance Metrics:")
    print(f"Annualized Return: {ann_return:.4f}")
    print(f"Annualized Volatility: {ann_vol:.4f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"Final Portfolio Value (starting with $1): ${(1 + data.iloc[-1]):.2f}")

# mainly used for the stat arb project right now, other things need tweaking before they can use this
def get_data(tickers, start_date, end_date, columns):
    tk = commons.FinanceToolkitHelpers(
        tickers=tickers,
        column_filters=columns,
        api_key=API_KEY,
        start_date=start_date,
        end_date=end_date,
        period='daily',
    )

    hist_data = tk.get_data()
    
    return hist_data    

def stat_arb(tickers, start, end, columns):
    ticker_data = get_data(tickers, start, end, columns)

    returns = ticker_data['Return']
    
    # compute signal space
    signal = -(
        returns.rolling(2).sum().subtract(
            returns.rolling(2).sum.mean(axis=1),
            axis=0,
        )
    )

    signal_space = (
        signal.divide(
            signal.abs().sum(axis=1),
            axis=0,
        )
    )


def main():
    # Getting and preprocessing data
    data = yf.download('TLT', start="2007-07-31", end="2025-04-14")
    data.index = pd.to_datetime(data.index)
    data['returns'] = data['Close'].pct_change()
    
    # getting spy data to compare to strat
    spy_data = yf.download('SPY', start="2007-07-31", end="2025-04-14")
    spy_data.index = pd.to_datetime(spy_data.index)
    spy_data['returns'] = spy_data['Close'].pct_change()

    # Define params for entry and exit days and create signals
    trading_days_before_month_end = 7
    trading_days_after_month_start = 1
    trading_days_short_exit = 8  # When to exit the short position
    transaction_cost = 0.0006  # 6 basis point per trade

    # Generate entry and exit signals
    data['entry_signal'] = data.index.map(lambda date: is_entry_day(date, trading_days_before_month_end))
    data['exit_signal'] = data.index.map(lambda date: is_exit_day(date, trading_days_after_month_start))
    data['short_exit_signal'] = data.index.map(lambda date: is_short_exit_day(date, trading_days_short_exit))

    # Initialize position column
    data['position'] = 0
    current_position = 0  # 0 = no position, 1 = long, -1 = short

    # Generate positions
    for i in range(len(data)):
        if data['entry_signal'].iloc[i]:
            # Enter long position at N trading days before month end
            data.loc[data.index[i], 'position'] = 1
            current_position = 1
        elif data['exit_signal'].iloc[i]:
            # Switch to short position at N trading days after month start
            data.loc[data.index[i], 'position'] = -1
            current_position = -1
        elif data['short_exit_signal'].iloc[i] and current_position == -1:
            # Exit short position after specified trading days
            data.loc[data.index[i], 'position'] = 0
            current_position = 0
        else:
            # Maintain current position
            data.loc[data.index[i], 'position'] = current_position

    # Calculate strategy returns
    data['strategy_returns'] = data['position'] * data['returns']
    
    # Account for transaction costs
    data['trades'] = data['position'].diff().abs()
    data['transaction_costs'] = data['trades'] * transaction_cost
    data['strategy_returns_net'] = data['strategy_returns'] - data['transaction_costs']

    # Calculate cumulative returns
    data['cumulative_returns'] = (1 + data['returns']).cumprod() - 1
    data['spy_cumulative_returns'] = (1 + spy_data['returns']).cumprod() - 1
    data['strategy_cumulative'] = (1 + data['strategy_returns']).cumprod() - 1
    data['strategy_cumulative_net'] = (1 + data['strategy_returns_net']).cumprod() - 1
    data['portfolio_returns'] = (0.5 * data['strategy_returns_net'] + 0.5 * spy_data['returns'])
    data['portfolio_returns_cum'] = (1 + data['portfolio_returns']).cumprod() - 1

    data.to_csv('./tlt-strat-ls.csv')

    # Calculate performance metrics
    total_days = len(data)
    in_market_days = data['position'].sum()
    pct_in_market = in_market_days / total_days


    # Print results
    calc_metrics(data['strategy_returns_net'], 'bonds strat')
    calc_metrics(data['portfolio_returns'], 'combined strat')

    # Plot results
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['spy_cumulative_returns'], label='Buy and Hold', color='blueviolet', linestyle='dotted', linewidth=1)
    plt.plot(data.index, data['strategy_cumulative_net'], label='Long-Short Month End Strategy', color='red', linestyle='dotted', linewidth=1)
    plt.plot(data.index, data['portfolio_returns_cum'], label='50/50 portfolio', color='dodgerblue', linewidth=3)
    plt.title('Bond Long-Short Month End Strategy vs Buy and Hold')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
