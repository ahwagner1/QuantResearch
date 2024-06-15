import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np

vix1d = yf.Ticker('^VIX1D')
vix1d = vix1d.history(period='1y', interval='1d')
print(vix1d)

spx = yf.Ticker('^SPX')
spx = spx.history(period='1y', interval='1d')
spx['% Change'] = abs((spx['Close'].shift(1) / spx['Close']) - 1) * 100
print(spx)

m, b = np.polyfit(vix1d['Close'].iloc[1:], spx['% Change'].iloc[1:], 1)
print(f'Linear Regression Line: y = {m:.5f}x + {b}')

plt.figure(figsize=(10,6))
plt.scatter(vix1d['Close'].iloc[1:], spx['% Change'].iloc[1:])
plt.plot(vix1d['Close'].iloc[1:], m * vix1d['Close'].iloc[1:] + b, color = 'red')
plt.show()