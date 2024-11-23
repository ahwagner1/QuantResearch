import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

spy = yf.Ticker('SPY')
data = spy.history(period='10y', interval='1d')

# see all the columns yf will grab for us
#[print(col) for col in data.columns]

data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
#print(data.head())

# data preprocessing
data.dropna(inplace=True)
data['Percent Change'] = ((data['Close'] / data['Open']) - 1) * 100
data['Next day returns'] = data['Percent Change'].shift(-1)
data['5d returns'] = data['Percent Change'].rolling(window=5, min_periods=1).sum().shift(-5)
data['30d returns'] = data['Percent Change'].rolling(window=30, min_periods=1).sum().shift(-30)
data['60d returns'] = data['Percent Change'].rolling(window=60, min_periods=1).sum().shift(-60)
data['90d returns'] = data['Percent Change'].rolling(window=90, min_periods=1).sum().shift(-90)

# see the distribution of open to close returns
counts, bins = np.histogram(data['Percent Change'])
#plt.stairs(counts, bins, fill=True)
#plt.show()

# show the correlation between previous day being up/down and the following days returns
plt.scatter(data['Percent Change'], data['Next day returns'])
#plt.show()

fig, axs = plt.subplots(2, 2)

# Create the regression plot function to avoid repetition
def create_return_regression(x, y, ax, title):
    # Remove any NaN values just for the regression
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    # Only perform polyfit if we have valid data
    if len(x_clean) > 0 and len(y_clean) > 0:
        m, b = np.polyfit(x_clean, y_clean, 1)
        ax.scatter(x_clean, y_clean, alpha=0.5)
        ax.plot(x_clean, m*x_clean + b, color='red')
        ax.set_title(f'{title} (slope: {m:.2f})')
    else:
        ax.set_title(f'{title} (insufficient data)')

# Create the plots
create_return_regression(data['Percent Change'], data['5d returns'], axs[0,0], '5d returns')
create_return_regression(data['Percent Change'], data['30d returns'], axs[1,0], '30d returns')
create_return_regression(data['Percent Change'], data['60d returns'], axs[0,1], '60d returns')
create_return_regression(data['Percent Change'], data['90d returns'], axs[1,1], '90d returns')

# Adjust layout
plt.tight_layout()

# filtered plots for days that had more than a 2% drop
fig, axs = plt.subplots(2, 2)
filtered_data = data.loc[data['Percent Change'] <= -2]

create_return_regression(filtered_data['Percent Change'], filtered_data['5d returns'], axs[0,0], '5d returns')
create_return_regression(filtered_data['Percent Change'], filtered_data['30d returns'], axs[1,0], '30d returns')
create_return_regression(filtered_data['Percent Change'], filtered_data['60d returns'], axs[0,1], '60d returns')
create_return_regression(filtered_data['Percent Change'], filtered_data['90d returns'], axs[1,1], '90d returns')

plt.show()