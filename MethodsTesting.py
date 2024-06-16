import pandas as pd
import matplotlib.pyplot as plt
from commons import SierraChartsDataHelpers, MachineLearningLabeling, SPXOptions
import time

'''
Testing file for new function to ensure they are accurate and performing as desired
'''

spx_chain = SPXOptions.get_spx_options()
if spx_chain is None:
    print('Failed to get options data')

print(spx_chain) 


'''path = 'Data/250_VOL.txt'
df = SierraChartsDataHelpers.import_sierra_data(path)

df['Uppers'] = df['Last'] + 4.75
df['Lowers'] = df['Last'] - 4.75
print(df.head(10))

start = time.time()
labels = MachineLearningLabeling.triple_barrier_method(df, 5, 4.75, 'sign')
end = time.time()
print(end - start)
print(labels[:10])

start = time.time()
labels2 = MachineLearningLabeling.triple_barrier_method_fast(df, 5, 4.75, 'sign')
end = time.time()
print(end - start)
print(labels2[:10])

print(labels.shape)
print(labels2.shape)
all_true = True
false_spots = []
count = 0
for index, element in enumerate(labels):
    if element != labels2[index]:
        false_spots.append(index)
        all_true = False
        count += 1
print(all_true)
print(count)

for idx in false_spots:
    print(f'My functiuon label: {labels[idx]}')
    print(f'Numpy function label: {labels2[idx]}')
    print(f'Index: {idx}')
    print(f'Closing Prices:\n{df['Last'].iloc[idx:idx+6]}')
    print('--')'''

