import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join

if len(sys.argv) != 2:
    print('USAGE: python examine_covid_data.py <path to data directory>')
    quit()
    
data_dir = sys.argv[1]
data_files = []

for f in listdir(data_dir):
    file_path = join(data_dir, f)
    if (isfile(file_path) and f.endswith('.csv')):
        data_files.append(file_path)

dfs = [ pd.read_csv(f) for f in data_files ]
main_df = pd.concat(dfs).drop_duplicates()

sums_by_country = main_df[['Country_Region', 'Confirmed', 'Deaths', 'Recovered', 'Active']].groupby('Country_Region').sum()
sums_by_state = main_df[['Province_State', 'Country_Region', 'Confirmed', 'Deaths', 'Recovered', 'Active']].groupby(['Province_State', 'Country_Region']).sum()
sums_by_city = main_df[['Combined_Key', 'Confirmed', 'Deaths', 'Recovered', 'Active']].groupby('Combined_Key').sum()

print('--------------------------------------------------------------------------------')
print('Sums by Country')
print('--------------------------------------------------------------------------------')
print('')
print(sums_by_country)
print('')

print('--------------------------------------------------------------------------------')
print('Sums by State/Province')
print('--------------------------------------------------------------------------------')
print('')
print(sums_by_state)
print('')

print('--------------------------------------------------------------------------------')
print('Sums by City')
print('--------------------------------------------------------------------------------')
print('')
print(sums_by_city)
print('')


