import pandas as pd
import matplotlib.pyplot as plt
from commons import import_sierra_data

path = 'Data/250_VOL.txt'
df = import_sierra_data(path)

print(df)

