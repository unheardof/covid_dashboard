import sys
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
sums_by_county = main_df[['FIPS', 'Combined_Key', 'Confirmed', 'Deaths', 'Recovered', 'Active']].groupby(['FIPS', 'Combined_Key']).sum()

from urllib import urlopen
import json
#with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
#    counties = json.load(response)

# TODO: cleanup
# counties = json.load(urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'))

# counties_fig = px.choropleth(
#     main_df,
#     geojson=counties,
#     locations='FIPS',
#     color='Confirmed',
#     color_continuous_scale="Viridis",
#     range_color=(0, 12),
#     scope="usa",
#     labels={
#         'Confirmed': 'Confirmed Cases',
#         'Active': 'Active Cases',
#         'Deaths': 'Deaths',
#         'Recovered': 'Recovered'
#     }
# )

# counties_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# counties_fig.write_html('covid_by_usa_county.html', auto_open=True)

# TODO: Get this working
country_fig = go.Figure(data=go.Choropleth(
    locations = main_df['Country_Region'],
    #z = main_df['Confirmed'],
    text = main_df['Confirmed'],
    colorscale = 'Reds',
    autocolorscale=False,
    reversescale=False,
    marker_line_color='white',
    marker_line_width=0.5,
    #colorbar_tickprefix = '$',
    colorbar_title = 'Number of Confirmed Cases',
))

country_fig.update_layout(
    title_text='Confirmed COVID-19 Cases',
    geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular'
        )
)

country_fig.write_html('covid_by_country.html', auto_open=True)

# TODO: Also do counties

# TODO: Auto-upload to S3

# print('--------------------------------------------------------------------------------')
# print('Sums by Country')
# print('--------------------------------------------------------------------------------')
# print('')
# print(sums_by_country)
# print('')

# print('--------------------------------------------------------------------------------')
# print('Sums by State/Province')
# print('--------------------------------------------------------------------------------')
# print('')
# print(sums_by_state)
# print('')

# print('--------------------------------------------------------------------------------')
# print('Sums by County')
# print('--------------------------------------------------------------------------------')
# print('')
# print(sums_by_county)
# print('')


