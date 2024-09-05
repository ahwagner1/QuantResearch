import sys
sys.path.append('/home/ahwagner/repos/QuantResearch/') # have to do this until I actually structure things correctly
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import commons
import os
import yfinance as yf
from yahoo_fin import stock_info as si
from dotenv import load_dotenv
from sklearn.decomposition import PCA

load_dotenv('./keys_and_secrets.env')
API_KEY = os.getenv('tk_api_key')

# i would love to run PCA on all of them at once but that will probably take too long
# for now I'm just going to stick to spoos tickers and hope I don't run out of memory

def get_and_save_data(tickers):
    start_date = '2020-01-01'
    cols = ['Return']
    tk = commons.FinanceToolkitHelpers(
        tickers=tickers,
        column_filter=cols,
        api_key=API_KEY,
        start_date=start_date,
        end_date=None,
        period='daily'
    )

    hist_data = tk.get_data()
    commons.DataManagement.save_data('saved_data', 'SEMIS', hist_data)

def analyze_pca_variance(data, tickers):
    '''
    see the cumulative variance explained by the number of components
    '''
    pca = PCA()
    pca.fit(data)

    cumulative_variance_ratio = np.cumsum(pca.explained_variance_ratio_)

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(tickers) + 1), cumulative_variance_ratio, 'bo-')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Explained Variance Ratio')
    plt.title('Explained Variance Ratio vs Number of Components')
    plt.grid(True)
    plt.show()

    components_95 = next(i for i, var in enumerate(cumulative_variance_ratio) if var >= 0.95) + 1
    print(f"Number of components needed to explain 95% of variance: {components_95}")

    return cumulative_variance_ratio, components_95

def analyze_pca_components(data, tickers, n):
    pca = PCA(n_components = n)
    pca.fit(data)

    component_weights = pd.DataFrame(
        pca.components_.T,
        columns=[f'PC{i+1}' for i in range(n)],
        index=tickers,
    )

    print("Component Weights:")
    print(component_weights)

    plt.figure(figsize=(12, 8))
    plt.scatter(component_weights['PC1'], component_weights['PC2'])
    
    # annotate
    for i, ticker in enumerate(tickers):
        plt.annotate(ticker, (component_weights['PC1'][i], component_weights['PC2'][i]))

    plt.xlabel('First Principal Component')
    plt.ylabel('Second Principal Component')
    plt.title('Stock Loadings on First Two Principal Components')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return component_weights

def main():
    tickers = ['NVDA', 'TSM', 'AVGO', 'AMD', 'QCOM', 'TXN', 'ARM', 'INTC', 'MU', 'ADI', 'NXPI', 'MRVL', 'STM', 'ON', 'MCHP']
    #get_and_save_data(tickers)

    # this dataframe contains the returns data from 2020 of ~4300 stocks
    data = commons.DataManagement.load_data('./saved_data/SEMIS')
    data.dropna(inplace = True)

    # Assuming 'data' is your DataFrame and 'tickers' is a list of your stock tickers
    cumulative_variance, components_95 = analyze_pca_variance(data, tickers)
    weights = analyze_pca_components(data, tickers, 4)


if __name__ == '__main__':
    main()

