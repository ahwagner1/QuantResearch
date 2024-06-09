import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('/home/ahwagner/repos/QuantResearch/Data/250_VOL.txt')
df.columns = [col.strip() for col in df.columns]

print(df)