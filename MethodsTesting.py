import pandas as pd
import matplotlib.pyplot as plt
from commons import SierraChartsDataHelpers, MachineLearningLabeling, SPXOptions
import time
import json

'''
Testing file for new function to ensure they are accurate and performing as desired
'''

#spx_chain = SPXOptions.get_spx_options()
#if spx_chain is None:
#    print('Failed to get options data')

#with open("data.json", "w") as file:
#    json.dump(spx_chain, file, indent = 4)

options_codes = SPXOptions.get_options_codes_range(5426.2, '240618')
filtered_odtes = SPXOptions.get_spx_options(options_codes)
print(filtered_odtes)
