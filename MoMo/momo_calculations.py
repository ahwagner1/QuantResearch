import pandas as pd
import numpy as np

# also would be nice to incorporate a relative strength measurement into this
# like highest momo plus relative strength to marker to find the absolute strongest stocks

def sort_momo(df):
    df['slope_diff'] = (df['30d_slope'] - df['90d_slope']).abs()

    winners = df[(df['30d_slope'] > df['60d_slope']) & (df['60d_slope'] > df['90d_slope'])]
    winners_sorted = winners.sort_values('slope_diff', ascending=False)

    losers = df[(df['30d_slope'] < df['60d_slope']) & (df['60d_slope'] < df['90d_slope'])]
    losers_sorted = losers.sort_values('slope_diff', ascending=False)

    return winners_sorted, losers_sorted

def main():
    df = pd.read_csv('nasdaq_linear_regression_results.csv', header = 0, names = ['Ticker', '30d_slope', '60d_slope', '90d_slope'])
    print(df)
    w, l = sort_momo(df)

    print(f'Top 10 Winners:\n{w.head(10)}\n')
    print(f'Top 10 Losers:\n{l.head(10)}')

if __name__ == '__main__':
    main()