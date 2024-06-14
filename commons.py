import pandas as pd
from datetime import time
import numpy as np

'''
Gonna use this for common functions that I'm too lazy to rewrite accross various projects
I'm also too lazy right now to split into seperate files, so formatting them into different classes
'''
class SierraChartsDataHelpers:
    '''
    This class will hold useful functions for working with data from Sierra Charts
    '''
    @classmethod
    def import_sierra_data(cls, data_path: str = None):
        '''
        Import csv data, specifically from Sierra Charts
        Sierra sometimes likes to add leading whitespace to columns so this function will strip every column and return the clean dataframe

        This will also create a datetime index
        '''
        
        df = pd.read_csv(data_path)
        df.columns = [col.strip() for col in df.columns]

        df['TimeStamp'] = pd.to_datetime(df['Date'].astype(str) + df['Time'].astype(str), format='mixed')#format='%Y/%m/%d %H:%M:%S.%f')
        df.set_index('TimeStamp', inplace = True)
        df.drop(['Date', 'Time'], axis = 1, inplace = True)

        return df

    @classmethod
    def resample_data(cls, data: pd.DataFrame, bin_size: str, features_and_methods: dict):
        '''
        This function will resample data to specified bin sizes, check pandas documentation for bin_size (syntax)?
        Pretty sure the index needs to be datetime var 
        features_and_methods is a dict that specifies how to aggregate each feature
            - ex: 'Some_Ratio' : 'mean'
        '''
        
        resampled_data = data.resample(bin_size).agg(features_and_methods)
        return resampled_data


class MachineLearningLabeling:
    '''
    This class will hold useful functions for labeling data
    Use these when you want to work with classification tasks and not regression

    TODO: 
     - add the ability to have variable upper and lower thresholds for both functions
     - create an event only triple barrier method that accepts the indices of events instead of labeling every bar
    '''

    @classmethod
    def rth_threshold_barrier_classifying(cls, data: pd.DataFrame, lookahead: int, threshold: float, zero_or_sign: str = 'zero', eod_timestamp: time = time(11,44,00)):
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
        y = np.empty(shape = (num_samples))

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

    @classmethod
    def triple_barrier_method(cls, data: pd.DataFrame, lookahead: int, threshold: float, zero_or_sign: str = 'zero'):
        '''
        Triple barrier labeling, for every bar

        This functions differs from 'rth_threshold_barrier_classifying()' in that it will iterate to check which threshold gets hit first AND it will work on ETH and RTH
        The 'rth_threshold_barrier_classifying() function just looks at where price is at the future index and disregards the path it took to get there
        '''

        if (zero_or_sign not in ['zero', 'sign']):
            raise ValueError('Invalid option, optios are [\'zero\', \'sign\']')

        closing_prices = data['Last'].values
        num_samples = len(closing_prices)
        y = np.empty(shape = (num_samples))

        for i in range(num_samples):
            # computing barriers
            current_price = closing_prices[i]
            upper_barrier = current_price + threshold
            lower_barrier = current_price - threshold
            vertical_barrier_index = min(i + lookahead, num_samples - 1)

            subset = data.iloc[i+1:vertical_barrier_index+1] # setting to i + 1 to exclude the current price from the subset of data (e.g. if i == 5, we want the subset to be [6-10], so i+1:i+lookahead+1)
            max_price = subset['High'].max()
            min_price = subset['Low'].min()
            #print(f'Current price: {current_price}\nUpper & Lower: {upper_barrier}, {lower_barrier}\nMax and Min: {max_price}, {min_price}')         

            if max_price >= upper_barrier and min_price <= lower_barrier:
                # upper or lower barrier is hit first

                # fix this need to check one or the other, not both at the same time
                max_idx = subset[subset['High'] >= upper_barrier].index[0]
                min_idx = subset[subset['Low'] <= lower_barrier].index[0]

                if max_idx < min_idx:
                    y[i] = 1
                elif min_idx < max_idx:
                    y[i] = -1
                else:
                    # this else branch SHOULD NEVER be executed
                    raise Exception('Somehow both barriers were hit in one bar')
            elif max_price >= upper_barrier:
                y[i] = 1
            elif min_price <= lower_barrier:
                y[i] = -1
            else:
                # vertical barrier gets hit
                if zero_or_sign == 'zero':
                    y[i] = 0
                else:
                    # give directional label
                    label_map = {
                        closing_prices[vertical_barrier_index] > current_price : 1,
                        closing_prices[vertical_barrier_index] < current_price : -1,
                    }
                    y[i] = label_map.get(True, 0)
        
        return y
    
    @classmethod
    def triple_barrier_method_fast(cls, data: pd.DataFrame, lookahead: int, threshold: float, zero_or_sign: str = 'zero'):
        if zero_or_sign not in ['zero', 'sign']:
            raise ValueError('Invalid option, options are [\'zero\', \'sign\']')

        closing_prices = data['Last'].values
        num_samples = len(closing_prices)

        # Compute barriers for all samples at once
        upper_barriers = closing_prices + threshold
        lower_barriers = closing_prices - threshold
        vertical_barrier_indices = np.minimum(np.arange(num_samples) + lookahead, num_samples - 1)

        # Compute max and min prices for each subset using rolling window
        max_prices = data['High'].shift(-1).rolling(window=lookahead, min_periods=1).max().values
        min_prices = data['Low'].shift(-1).rolling(window=lookahead, min_periods=1).min().values

        # Determine which barrier gets hit first
        upper_hit = max_prices >= upper_barriers
        lower_hit = min_prices <= lower_barriers
        vertical_hit = np.logical_not(upper_hit | lower_hit)

        # Assign labels based on which barrier gets hit first
        y = np.where(upper_hit, 1, np.where(lower_hit, -1, np.where(vertical_hit, 0, np.nan)))

        if zero_or_sign == 'sign':
            vertical_labels = np.where(closing_prices > closing_prices[vertical_barrier_indices], -1,
                                np.where(closing_prices < closing_prices[vertical_barrier_indices], 1, 0))
            y[vertical_hit] = vertical_labels[vertical_hit]

        return y