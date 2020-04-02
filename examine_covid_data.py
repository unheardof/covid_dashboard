import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from os import listdir
from os.path import isfile, join
import pycountry
import re
from urllib.request import urlopen
import json

# TODO: Remove
#import pdb; pdb.set_trace()

country_code_cache = {
    'nan': None,
    'Korea, South': 'KOR',
    'Cruise Ship': None,
    'Laos': 'LAO',
    'Diamond Princess': None,
    'West Bank and Gaza': 'PSE', # Including the West Bank as part of Palestine
    'Burma': 'MMR',
    'MS Zaandam': None, # Another cruise ship
}

def scrub_country_name(country_name):
    try:
        scrubbed_name = re.sub('\*', '', country_name)
    except:
        print('Failed to scrub country name for "' + country_name + '"')
        return None

    return scrubbed_name

def country_code(country_name):
    if (country_name in country_code_cache):
        return country_code_cache[country_name]
    elif (country_name.split(' ')[0] == 'Congo'):
        return 'COD'

    scrubbed_name = scrub_country_name(country_name)
    
    try:    
        country_code = pycountry.countries.search_fuzzy(scrubbed_name)[0].alpha_3
        country_code_cache[country_name] = country_code
        
        return country_code
    except:
        print('Failed to get country code for county "' + country_name + '"; scrubbed name: "' + scrubbed_name + '"')
        return None

    
    
###
### Start of Execution
###
        
if len(sys.argv) != 2:
    print('USAGE: python examine_covid_data.py <path to data directory>')
    quit()
    
data_dir = sys.argv[1]
data_files = []

for f in listdir(data_dir):
    file_path = join(data_dir, f)
    if (isfile(file_path) and f.endswith('.csv')):
        data_files.append(file_path)

dfs = [ pd.read_csv(f, dtype={ 'FIPS': 'string' }) for f in data_files ]



main_df = pd.concat(dfs).drop_duplicates()

# TODO: Only take most recent data for each entry

# TODO: Remove
#sums_by_country = main_df[['Country_Region', 'Confirmed', 'Deaths', 'Recovered', 'Active']].groupby('Country_Region').sum()
#sums_by_state = main_df[['Province_State', 'Country_Region', 'Confirmed', 'Deaths', 'Recovered', 'Active']].groupby(['Province_State', 'Country_Region']).sum()
#sums_by_county = main_df[['FIPS', 'Combined_Key', 'Confirmed', 'Deaths', 'Recovered', 'Active']].groupby(['FIPS', 'Combined_Key']).sum()

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

# TODO: Remove
import pdb; pdb.set_trace()

# TODO: Fill in missing FIPS with 0
    
df_with_fips = main_df[main_df.FIPS.notnull()] # FIPS == US county codes
df_with_fips['Confirmed'] = df_with_fips['Confirmed'].fillna(value=0)
df_with_fips['text'] = 'Confirmed: ' + df_with_fips['Confirmed'].astype(str) + '<br>' + \
                       'Active: ' + df_with_fips['Active'].astype(str) + '<br>' + \
                       'Recovered: ' + df_with_fips['Recovered'].astype(str) + '<br>' + \
                       'Deaths: ' + df_with_fips['Deaths'].astype(str)

# counties_fig = go.Figure(
#     data=go.Choropleth(
#         geojson=counties,
#         locations=df_with_fips['FIPS'],
#         z=np.log10(df_with_fips['Confirmed']),
#         #locationmode='USA-states',
#         colorscale='Reds',
#         autocolorscale=True,
#         text=df_with_fips['text'], # hover text
#         marker_line_color='white', # line markers between states
#         colorbar_title="Confirmed COVID Cases"
#     )
# )

counties_fig = px.choropleth(
    df_with_fips,
    geojson=counties,
    locations='FIPS',
    color=np.log10(df_with_fips['Confirmed']),
    hover_data=['Confirmed', 'Active', 'Recovered', 'Deaths'],
    color_continuous_scale="Inferno",
    range_color=(0, 5),
    scope="usa",
)

counties_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
counties_fig.write_html('covid_by_usa_county.html', auto_open=True)


main_df['CountryCode'] = main_df['Country_Region'].apply(lambda x: country_code(str(x)))


country_fig = px.choropleth(main_df,
                            locations="CountryCode",
                            color="Confirmed",
                            hover_name="Deaths", # column to add to hover information
                            color_continuous_scale=px.colors.sequential.Plasma)

# country_fig = go.Figure(data=go.Choropleth(
#     locations = main_df['CountryCode'],
#     z = main_df['Confirmed'],
#     text = main_df['Confirmed'],
#     colorscale = 'Reds',
#     autocolorscale=False,
#     reversescale=False,
#     marker_line_color='white',
#     marker_line_width=0.5,
#     colorbar_title = 'Number of Confirmed Cases',
# ))

country_fig.update_layout(
    title_text='Confirmed COVID-19 Cases',
    geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular'
        )
)

country_fig.write_html('covid_by_country.html', auto_open=True)

# TODO: Do US states also
