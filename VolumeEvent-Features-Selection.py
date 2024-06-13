import pandas as pd
import matplotlib.pyplot as plt
from commons import SierraChartsDataHelpers, MachineLearningLabeling
import time

path = 'Data/250_VOL.txt'
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
for index, element in enumerate(labels):
    if element != labels2[index]:
        false_spots.append(index)
        all_true = False
print(all_true)

for idx in false_spots:
    print(f'My functiuon label: {labels[idx]}')
    print(f'Numpy function label: {labels2[idx]}')
    print(f'Index: {idx}')
    print(f'Closing Prices:\n{df['Last'].iloc[idx:idx+6]}')
    print('--')

