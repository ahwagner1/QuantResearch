import sys
import os
sys.path.append('/home/ahwagner/repos/QuantResearch/')
import commons

import pandas as pd
import numpy as np
import yfinance as yf
from yahoo_fin import stock_info as si
from dotenv import load_dotenv
from get_all_tickers import get_tickers as gt

load_dotenv('./keys_and_secrets.env')
API_KEY = os.getenv('tk_api_key')

def calc_lin_reg(df: pd.DataFrame, periods: list[int] = [30, 60, 90]):
    def linear_regression(y):
        x = np.arange(len(y))
        A = np.vstack([x, np.ones(len(x))]).T
        slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
        return pd.Series({'slope': slope, 'intercept': intercept})

    results = {}
    for ticker in df.columns:
        ticker_results = {}
        for period in periods:
            period_data = df[ticker].iloc[-period:]
            regression_result = linear_regression(period_data)
            ticker_results[f'{period}d_slope'] = regression_result['slope']
        results[ticker] = ticker_results

    final_results = pd.DataFrame(results).T
    final_results = final_results.reindex(columns=[f'{period}d_slope' for period in periods])
    return final_results

def sort_stocks_by_avg_dollar_volume(data):
    # Step 1: Calculate dollar volume for each stock
    tickers = data['Close'].columns
    dollar_volumes = pd.DataFrame(index=data.index)
    
    for ticker in tickers:
        dollar_volumes[ticker] = data['Close'][ticker] * data['Volume'][ticker]
    
    avg_dollar_volumes = dollar_volumes.mean()
    sorted_stocks = avg_dollar_volumes.sort_values(ascending=False)
    
    result_df = pd.DataFrame({
        'Ticker': sorted_stocks.index,
        'Avg Dollar Volume': sorted_stocks.values
    })

    print(result_df.head(25))
    
    result_df['Rank'] = range(1, len(result_df) + 1)
    
    return result_df

def process_ticker_batch(tickers, cols, start_date):
    tk = commons.FinanceToolkitHelpers(
        tickers=tickers,
        column_filter=cols,
        api_key=API_KEY,
        start_date=start_date,
        end_date=None,
        period='daily'
    )
    data = tk.get_data()
    data['Cumulative Return'] = np.log(data['Cumulative Return'])

    dollar_volume_data = sort_stocks_by_avg_dollar_volume(data)
    top_stocks = dollar_volume_data['Ticker'][:250].tolist()

    data = data['Cumulative Return'][top_stocks]

    data = data.dropna(axis=1, how='any')
    
    if not data.empty:
        return calc_lin_reg(data)
    else:
        return pd.DataFrame()


def main():
    
    nasdaq_data = pd.read_csv('nasdaq_stocks.csv')
    nasdaq_data.sort_values('Market Cap', ascending = False, inplace = True)

    tickers = nasdaq_data['Symbol'][:2500].tolist()
    tickers = [str(ticker) for ticker in tickers]
    tickers = [ticker for ticker in tickers if '^' not in ticker] # so fkn ugly
    tickers = [ticker for ticker in tickers if '/' not in ticker]
    
    columns = ['Cumulative Return', 'Close', 'Volume']
    start_date = '2024-01-01'
    results = process_ticker_batch(tickers, columns, start_date)
    
    print(results)

    results.to_csv('nasdaq_linear_regression_results.csv')

if __name__ == '__main__':
    main()