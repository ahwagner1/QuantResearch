import pandas as pd


'''
Gonna use this for common functions that I'm too lazy to rewrite accorss the various projects
'''

def import_sierra_data(data_path: str = None):
    '''
    Import csv data, specifically from Sierra Charts
    Sierra sometimes likes to add leading whitespace to columns so this function will strip every column and return the clean dataframe
    '''
    
    df = pd.read_csv(data_path)
    df.columns = [col.strip() for col in df.columns]

    return df


