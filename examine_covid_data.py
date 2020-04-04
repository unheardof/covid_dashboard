import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from os import listdir, makedirs
from os.path import isfile, join, exists
import pycountry
import re
from urllib.request import urlopen
import json

HTML_FILE_DIRECTORY = './html_graph_files/'

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

state_name_cache = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
    'American Samoa': 'AS',
    'Guam': 'GU',
    'Northern Mariana Islands': 'MP',
    'Puerto Rico': 'PR',
    'Virgin Islands': 'VI',
    'Grand Princess': None,
    'Diamond Princess': None,
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

def fix_fips(s):
    # In the time-series data, FIPS are stored as '1001.0' formatted strings instead of 01001
    fips = s.split('.')[0]
    while (len(fips) < 5):
        fips = '0' + fips

    return fips

def save_fig(fig, title, html_file_name):
    if not exists(HTML_FILE_DIRECTORY):
        makedirs(HTML_FILE_DIRECTORY)
    
    fig.update_layout(title_text=title)
    fig.write_html(join(HTML_FILE_DIRECTORY, html_file_name), auto_open=True)
        
def latest_date_column_name(df):
    dates = [ x for x in df.columns if re.match('([0-9]{1,2}\/){2}[0-9]{2}', x) ]
    dates.sort(reverse=True)
    return dates[0]

def create_and_save_global_graph(root_dir, input_file_name, graph_title, output_filename):
    df = pd.read_csv(join(root_dir, 'csse_covid_19_time_series', input_file_name))
    df['CountryCode'] = df['Country/Region'].apply(lambda x: country_code(str(x)))
    latest_date_column = latest_date_column_name(df)

    fig = px.choropleth(df,
                        locations='CountryCode',
                        color=np.log10(df[latest_date_column]),
                        hover_name=latest_date_column, # column to add to hover information
                        color_continuous_scale="Inferno")

    # Anything between the <extra></extra> tags will appear in a second box on the right part of the hovertext
    # See https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html -> hovertemplate for details
    df['text'] = '<b>' + df['CountryCode'].astype(str) + '</b><br>' + \
                 df[latest_date_column].astype(str) + '<br><extra></extra>'
    
    fig = go.Figure(
        data=go.Choropleth(
            locations=df['CountryCode'],
            z=np.log10(df[latest_date_column]),
            #locationmode='USA-states',
            colorscale='Inferno',
            autocolorscale=True,
            hovertemplate=df['text'],
            hoverinfo=['none'],
            marker_line_color='white', # line markers between states
            showscale=False,
        )
    )

    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular'
        ),
        coloraxis_showscale=False, # Hide the color-scale bar
    )
    
    save_fig(fig, graph_title, output_filename)

def create_and_save_us_graph(root_dir, input_file_name, graph_title, output_filename):
    df = pd.read_csv(join(root_dir, 'csse_covid_19_time_series', input_file_name), dtype={ 'FIPS': 'string' })
    df['StateCode'] = df['Province_State'].apply(lambda x: state_name_cache[x])
    latest_date_column = latest_date_column_name(df)
    sums_by_state = df[['StateCode', latest_date_column]].groupby('StateCode').sum()

    sums_by_state['StateCode'] = sums_by_state.index
    df2 = pd.DataFrame(sums_by_state)

    # Anything between the <extra></extra> tags will appear in a second box on the right part of the hovertext
    # See https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html -> hovertemplate for details
    df2['text'] = '<b>' + df2['StateCode'].astype(str) + '</b><br>' + \
                  df2[latest_date_column].astype(str) + '<br><extra></extra>'
        
    # fig = px.choropleth(df2,
    #                     locations='StateCode',
    #                     locationmode="USA-states",
    #                     color=np.log10(df2[latest_date_column]),
    #                     scope="usa",
    #                     hover_name=latest_date_column, # column to add to hover information
    #                     color_continuous_scale="Inferno")

    fig = go.Figure(
        data=go.Choropleth(
            locations=df2['StateCode'],
            z=np.log10(df2[latest_date_column]),
            locationmode='USA-states',
            colorscale='Inferno',
            autocolorscale=True,
            hovertemplate=df2['text'],
            marker_line_color='white', # line markers between states
            showscale=False,
        )
    )
    
    fig.update_layout(
        geo_scope='usa', # limit map scope to USA
        margin={"r":0,"t":0,"l":0,"b":0},
    )

    save_fig(fig, graph_title, output_filename)

def create_and_save_us_counties_graph(root_dir, input_file_name, graph_title, output_filename):
    df = pd.read_csv(join(root_dir, 'csse_covid_19_time_series', input_file_name), dtype={ 'FIPS': 'string' })
    df['StateCode'] = df['Province_State'].apply(lambda x: state_name_cache[x])
    latest_date_column = latest_date_column_name(df)

    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    
    # TODO: Fill in missing FIPS with 0

    # TODO: Cleanup
    df = df[df.iso2 == 'US'][df.FIPS.notnull()]
    df['FIPS'] = df['FIPS'].apply(lambda x: fix_fips(x))
    # df_with_fips['Confirmed'] = df_with_fips['Confirmed'].fillna(value=0)

    # Anything between the <extra></extra> tags will appear in a second box on the right part of the hovertext
    # See https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html -> hovertemplate for details
    df['text'] = '<b>' + df['Admin2'].astype(str) + ', ' + df['StateCode'] + '</b><br>' + \
                 df[latest_date_column].astype(str) + '<extra></extra>'

    # fig = go.Figure(
    #     data=go.Choropleth(
    #         geojson=counties,
    #         locations=df['FIPS'],
    #         z=np.log10(df[latest_date_column]),
    #         locationmode='USA-states',
    #         colorscale='Inferno',
    #         autocolorscale=True,
    #         hovertemplate=df['text'],
    #         marker_line_color='white', # line markers between states
    #         showscale=False,
    #     )
    # )
    
    # fig.update_layout(
    #     geo_scope='usa', # limit map scope to USA
    #     margin={"r":0,"t":0,"l":0,"b":0},
    # )
    
    fig = px.choropleth(
        df,
        geojson=counties,
        locations='FIPS',
        color=np.log10(df[latest_date_column]),
        #hover_data=[latest_date_column],
        #hover_data=['text'],
        hover_data=[],
        #hovertemplate='text',
        #hover_name=latest_date_column,
        #hover_name='text',
        hover_name=None,
        color_continuous_scale="Inferno",
        scope="usa",
        labels={ 'text': '' },
    )

    fig.update_traces(hovertemplate=df['text']) # TODO: Try text= next
    
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_showscale=False
    )
    
    save_fig(fig, graph_title, output_filename)
    
###
### Start of Execution
###
        
if len(sys.argv) != 2:
    print('USAGE: python examine_covid_data.py <path to data directory>')
    quit()
    
root_dir = sys.argv[1]

print('Creating graph of confirmed cases globally...')
create_and_save_global_graph(root_dir, 'time_series_covid19_confirmed_global.csv', 'Confirmed COVID-19 Cases Globally', 'covid_confirmed_global.html')
print('Done!')

print('Creating graph of deaths globally...')
create_and_save_global_graph(root_dir, 'time_series_covid19_deaths_global.csv', 'COVID-19 Deaths Globally', 'covid_deaths_global.html')
print('Done!')

print('Creating graph of recovered cases globally...')
create_and_save_global_graph(root_dir, 'time_series_covid19_recovered_global.csv', 'Recovered COVID-19 Cases Globally', 'covid_recovered_global.html')
print('Done!')

print('Creating graph of confirmed cases in the US...')
create_and_save_us_graph(root_dir, 'time_series_covid19_confirmed_US.csv', 'Confirmed COVID-19 Cases U.S.', 'covid_confirmed_us.html')
print('Done!')

print('Creating graph of deaths in the US...')
create_and_save_us_graph(root_dir, 'time_series_covid19_deaths_US.csv', 'COVID-19 Deaths U.S.', 'covid_deaths_us.html')
print('Done!')

print('Creating graph of confirmed cases in the US by county...')
create_and_save_us_counties_graph(root_dir, 'time_series_covid19_confirmed_US.csv', 'Confirmed COVID-19 Cases U.S.', 'covid_confirmed_us_counties.html')
print('Done!')

print('Creating graph of deaths in the US by county...')
create_and_save_us_counties_graph(root_dir, 'time_series_covid19_deaths_US.csv', 'COVID-19 Deaths U.S.', 'covid_deaths_us_counties.html')
print('Done!')
