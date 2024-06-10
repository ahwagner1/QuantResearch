import pandas as pd
from datetime import time
import numpy as np

'''
Gonna use this for common functions that I'm too lazy to rewrite accross various projects
'''

def import_sierra_data(data_path: str = None):
    '''
    Import csv data, specifically from Sierra Charts
    Sierra sometimes likes to add leading whitespace to columns so this function will strip every column and return the clean dataframe

    This will also create a datetime index
    '''
    
    df = pd.read_csv(data_path)
    df.columns = [col.strip() for col in df.columns]

    df['TimeStamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df.set_index('TimeStamp', inplace = True)
    df.drop(['Date', 'Time'], axis = 1, inplace = True)

    return df

def resample_data(data: pd.DataFrame, bin_size: str, features_and_methods: dict):
    '''
    This function will resample data to specified bin sizes, check pandas documentation for bin_size (syntax)?
    Pretty sure the index needs to be datetime var 
    features_and_methods is a dict that specifies how to aggregate each feature
        - ex: 'Some_Ratio' : 'mean'
    '''
    
    resampled_data = data.resample(bin_size).agg(features_and_methods)
    return resampled_data

#TODO: REWRITE TO ACCEPT VARIABLE UPPER AND LOWER THRESHOLD AMOUNTS INSTEAD OF FIXED 1:1
def rth_threshold_barrier_classifying(data: pd.DataFrame, lookahead: int, threshold: float, zero_or_sign: str = 'zero', eod_timestamp: time = time(11,44,00)):
    '''
    As the name suggests this function will iterate through RTH price data and determine the sign of direction based on close to close price, lookahead bars in the future
    If the lookahead is past the end of the current day, the EOD of price will be used

    Since theres a 99% chance I use this with sierra data, the closing price columns name is assumed to be 'Last'
    If the closing price column is NOT 'Last', change it

    data >> pandas dataframe with closing price data, AND some form of datetime/timestamp data as the index
    lookahead >> number of events forward to place the vertical barrier
    threshold >> number of points price needs to exceed before vertical barrier
    zero_or_sign >> string that determines how to classify the data when it hits the vertical barrier
                    'zero' assigns 0 to the label
                    'sign' assigns the directional sign (-1, 1) 

    '''
    
    if (zero_or_sign not in ['zero', 'sign']):
        raise ValueError('Invalid option, optios are [\'zero\', \'sign\']')
    
    closing_prices = data['Last'].values
    timestamps = data.index
    num_samples = len(closing_prices)
    y = np.empty(shape=(num_samples))

    for i in range(num_samples):
        # bounds checking
        future_idx = min(i + lookahead, num_samples - 1)
        
        # compare dates to determine if EOD or not
        curr_date = timestamps[i].date()
        future_date = timestamps[future_idx].date()

        if curr_date == future_date:
            y[i] = closing_prices[future_idx] - closing_prices[i]
        else:
            last_rth_timestamp = timestamps[(timestamps.date == curr_date) & (timestamps.time == eod_timestamp)]

            if not last_rth_timestamp.empty:
                last_rth_idx = timestamps.get_loc(last_rth_timestamp[0])
                y[i] = closing_prices[last_rth_idx] - closing_prices[i]
            else:
                y[i] = 0 # in case of edge case
        
    if zero_or_sign == 'zero':
        # vertcal barriers result in 0 label (meaning no change in price)
        # 1 means price >= upper barrier, -1 means price <= lower barrier

        y = [1 if num >= threshold else -1 if num <= -threshold else 0 for num in y]
    else:
        # signed labeling based on direction once vertical barrier hits

        y = [1 if num > 0 else -1 if num < 0 else 0 for num in y]
    
    return y

def rth_triple_barrier_method(data: pd.DataFrame, ):
    '''
    Triple barrier method, as proposed by MLDP

    This functions differs from the one before in that it will iterate to check which threshold gets hit first
    The above function just looks at where price is at the future index and disregards the path it took to get there
    '''
