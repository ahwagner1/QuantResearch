import sys
sys.path.append('/home/ahwagner/repos/QuantResearch/') # have to do this until I actually structure things correctly
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import commons
import os
from dotenv import load_dotenv

load_dotenv('./keys_and_secrets.env')
API_KEY = os.getenv('tk_api_key')

'''
test file for now
DO NOT COMMIT WITH API KEY DUMBASS
'''
class SimpleStatArb():
    """
    https://x.com/systematicls/status/1802666506125558115
    Ripped the code from this guy. Will implement something more advanced in the future
    This is meant simply to checkout stat arb strats using the assests mean returns
    """

    def __init__(self, data):
        self.data = data # returns data
        self.signal_space = None
        self.returns = None
    
    def compute_simple_signal(self, rolling_period: int = 2):
        """
        Non complex signal calculation
        Price to mean sorta idea
        """
        
        signal = -(
            self.data.rolling(rolling_period).sum().subtract(
                self.data.rolling(rolling_period).sum().mean(axis=1),
                axis=0
            )
        )

        self.signal_space = (
            signal.divide(
                signal.abs().sum(axis=1),
                axis=0
            )
        )
    
    def plot_cumulative_returns(self, shift_amount: int = 2):
        self.signal_space.shift(shift_amount).multiply(self.data).sum(axis=1).cumsum().plot(grid=True, figsize=(14,6))
        plt.title('Signal Space Cumulative Returns')
        plt.ylabel('Cumulative Returns')
        plt.show()

    def show_stats(self):
        daily_returns = self.signal_space.shift(2).multiply(self.data).sum(axis=1)
        ann_returns = (1 + daily_returns.mean()) ** 252 -1
        ann_volatility = daily_returns.std() * np.sqrt(252)
        sharpe = ann_returns / ann_volatility
        daily_turnover = self.signal_space.diff().abs().sum(axis=1).mean()

        print(f'Annualized Returns: {ann_returns * 100:.2f}%')
        print(f'Annualized Volatility: {ann_volatility * 100:.2f}%')
        print(f'Sharpe: {sharpe:.2f}')
        print(f'Daily Turnover: {daily_turnover * 100:.2f}%')


tickers = ['JPM', 'BAC', 'C', 'MS', 'GS']
start_date = '2010-01-01'
cols = ['Close', 'Adj Close', 'Volume', 'Return']

tk = commons.FinanceToolkitHelpers(
    tickers=tickers,
    column_filter=cols,
    api_key=API_KEY,
    start_date=start_date,
    end_date=None,
    period='daily'
)

hist_data = tk.get_data()
banks_rets = hist_data['Return']

statarb = SimpleStatArb(banks_rets)
statarb.compute_simple_signal(2)
statarb.plot_cumulative_returns(2)
statarb.show_stats()

'''
banks_rets_signal = -(
    banks_rets.rolling(2).sum().subtract(
        banks_rets.rolling(2).sum().mean(axis=1), 
        axis=0
    )
)

banks_rets_signal = (
    banks_rets_signal.divide(
        banks_rets_signal.abs().sum(axis=1),
        axis=0
    )
)

banks_rets_signal.plot(grid=True, figsize=(14, 6))
plt.title('Banks 2D Returns Space Signal')
plt.ylabel('Signal')
plt.show()

daily_returns = banks_rets_signal.shift(2).multiply(banks_rets).sum(axis=1)
ann_returns = (1 + daily_returns.mean()) ** 252 -1
ann_volatility = daily_returns.std() * np.sqrt(252)
sharpe = ann_returns / ann_volatility
daily_turnover = banks_rets_signal.diff().abs().sum(axis=1).mean()

print(f'Annualized Returns: {ann_returns:.2f}')
print(f'Annualized Volatility: {ann_volatility:.2f}')
print(f'Sharpe: {sharpe:.2f}')
print(f'Daily Turnover: {daily_turnover * 100:.2f}%')

daily_returns.cumsum().plot(grid=True, figsize=(14, 6))
plt.title('Banks 2D Returns Space Signal Cumulative Returns')
plt.ylabel('Cumulative Returns')
plt.show()


# autocorr example
banks = hist_data['Volume'] * hist_data['Adj Close']
banks_autocorr = banks.rolling(20).apply(lambda x: x.autocorr())
banks_autocorr_signal = -(
    banks_autocorr.subtract(
        banks_autocorr.mean(axis=1),
        axis=0
    )
)
banks_autocorr_signal = (
    banks_autocorr_signal.divide(
        banks_autocorr_signal.abs().sum(axis=1), 
        axis=0
    )
)

banks_autocorr_signal.plot(grid=True, figsize=(14, 6))
plt.title('Banks 20D AutoCorr Space Signal')
plt.ylabel('Signal')
plt.show()

banks_autocorr_signal.shift(2).multiply(banks_rets).sum(axis=1).cumsum().plot(grid=True, figsize=(14, 6))
plt.title('Banks 20D AutoCorr Space Signal Cumulative Returns')
plt.ylabel('Cumulative Returns')
plt.show()

daily_returns = banks_autocorr_signal.shift(2).multiply(banks_rets).sum(axis=1)
ann_returns = (1 + daily_returns.mean()) ** 252 -1
ann_volatility = daily_returns.std() * np.sqrt(252)
sharpe = ann_returns / ann_volatility
daily_turnover = banks_autocorr_signal.diff().abs().sum(axis=1).mean()

print(f'Annualized Returns: {ann_returns:.2f}')
print(f'Annualized Volatility: {ann_volatility:.2f}')
print(f'Sharpe: {sharpe:.2f}')
print(f'Daily Turnover: {daily_turnover * 100:.2f}%')

'''