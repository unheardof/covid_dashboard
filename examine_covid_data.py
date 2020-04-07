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
from datetime import datetime, timedelta

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

state_names_to_codes = {
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

counties_json = None

def nan_safe_int_cast(value):
    if np.isnan(value.iloc[0]):
        return 0
    else:
        return int(value.iloc[0])

def datetime_to_date_string(date):
    strs = date.strftime('%m/%d/%y').split('/')
    if strs[0].startswith('0'):
        strs[0] = strs[0][1:] # Remove zero-padding from the month field

    if strs[1].startswith('0'):
        strs[1] = strs[1][1:] # Remove zero-padding from the day field

    return '/'.join(strs)
    
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
    
    fig.update_layout(
        title={
            'text': title,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )
    
    fig.write_html(join(HTML_FILE_DIRECTORY, html_file_name), auto_open=True)
        
def latest_date_column_name(df):
    dates = [ x for x in df.columns if re.match('([0-9]{1,2}\/){2}[0-9]{2}', x) ]
    dates.sort(reverse=True)
    return dates[0]

def global_data(root_dir, input_file_name):
    df = pd.read_csv(join(root_dir, 'csse_covid_19_time_series', input_file_name))
    df['CountryCode'] = df['Country/Region'].apply(lambda x: country_code(str(x)))
    latest_date_column = latest_date_column_name(df)
    
    # Add empty rows for any states for which no data has been received
    all_country_codes = [ country.alpha_3 for country in pycountry.countries.__dict__['objects'] ]
    missing_countries = set(all_country_codes) - set(df['CountryCode'].tolist())

    next_index = len(df)
    missing_data_frames = []
    
    for country in missing_countries:
        # using 0.1 instead of zero so that the value will actually show up on the choropleth map
        missing_data_frames.append(pd.DataFrame({ 'CountryCode': country, latest_date_column: 0.1 }, index = [next_index]))
        next_index += 1

    missing_data_frames.append(df)
    df = pd.concat(missing_data_frames)
    
    # Make sure that all values actually get displayed (zero values get ignored by the choropleth generation logic)
    df[latest_date_column] = df[latest_date_column].apply(lambda x: x if x > 0 else 0.1)

    return df

def us_states_data(root_dir, input_file_name):
    df = pd.read_csv(join(root_dir, 'csse_covid_19_time_series', input_file_name), dtype={ 'FIPS': 'string' })
    df['StateCode'] = df['Province_State'].apply(lambda x: state_names_to_codes[x])
    latest_date_column = latest_date_column_name(df)
    
    # TODO: Cleanup
    #sums_by_state = df[['StateCode', latest_date_column]].groupby('StateCode').sum()
    df_summed_by_state = pd.merge(df.groupby('StateCode').sum(), df.loc[:,['Province_State', 'StateCode']], on='StateCode')
    
    #sums_by_state['StateCode'] = sums_by_state.index
    #df_summed_by_state = pd.DataFrame(sums_by_state)

    # Add empty rows for any states for which no data has been received
    missing_states = set(state_names_to_codes.values()) - set(df_summed_by_state['StateCode'].tolist())

    next_index = len(df)
    missing_data_frames = []

    for state in missing_states:
        # using 0.1 instead of zero so that the value will actually show up on the choropleth map
        missing_data_frames.append(pd.DataFrame({ 'StateCode': state, latest_date_column: 0.1 }, index = [next_index]))
        next_index += 1

    missing_data_frames.append(df_summed_by_state)
    df_summed_by_state = pd.concat(missing_data_frames)

    # Make sure that all values actually get displayed (zero values get ignored by the choropleth generation logic)
    df_summed_by_state[latest_date_column] = df_summed_by_state[latest_date_column].apply(lambda x: x if x > 0 else 0.1)

    return df_summed_by_state

def us_counties_as_json():
    global counties_json
    
    if (counties_json == None):
        with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
            counties_json = json.load(response)

    return counties_json
    
def us_counties_data(root_dir, input_file_name, counties):
    df = pd.read_csv(join(root_dir, 'csse_covid_19_time_series', input_file_name), dtype={ 'FIPS': 'string' })
    df = df[df.iso2 == 'US'][df.FIPS.notnull()]
    df['FIPS'] = df['FIPS'].apply(lambda x: fix_fips(x))
    df['StateCode'] = df['Province_State'].apply(lambda x: state_names_to_codes[x])
    
    latest_date_column = latest_date_column_name(df)
    df[latest_date_column] = df[latest_date_column].fillna(value=0)

    # Add empty rows for any FIPS (i.e. counties) for which no data has been received
    us_county_fips = [ x['id'] for x in counties['features'] if x['properties']['LSAD'] == 'County' ]
    missing_fips = list(set(us_county_fips) - set(df['FIPS'].dropna().tolist())) # Need a list for creating the DateFrame object

    # TODO: Cleanup
    next_index = len(df)
    #missing_data_frames = []

    fips_col_values = []
    indices = []

    for fips in missing_fips:
        # using 0.1 instead of zero so that the value will actually show up on the choropleth map
        #missing_data_frames.append(pd.DataFrame({ 'FIPS': fips, latest_date_column: 0.1 }, index = [next_index]))
        indices.append(next_index)
        next_index += 1

    #missing_data_frames.append(df)
    missing_df = pd.DataFrame(
        {
            'FIPS': missing_fips,
            latest_date_column: 0.1
        },
        index = indices
    )
    
    #return pd.concat(missing_data_frames)
    return pd.concat([df, missing_df])

def create_and_save_global_heatmap(root_dir, input_file_name, graph_title, output_filename):
    df = global_data(root_dir, input_file_name)
    latest_date_column = latest_date_column_name(df)
    
    # Anything between the <extra></extra> tags will appear in a second box on the right part of the hovertext
    # See https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html -> hovertemplate for details
    #
    # The <latest_date_column> values are cast to int to remove the decimal portion of the number, and then converted to
    # string to allow it to be added to other strings 
    df['text'] = '<b>' + df['CountryCode'].astype(str) + '</b><br>' + \
                 df[latest_date_column].astype(int).astype(str) + '<br><extra></extra>'

    fig = go.Figure(
        data=go.Choropleth(
            locations=df['CountryCode'],
            z=np.log10(df[latest_date_column]),
            colorscale='Plasma',
            reversescale=False,
            autocolorscale=False,
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
        margin={"r":0,"t":30,"l":0,"b":0},
    )
    
    save_fig(fig, graph_title, output_filename)

def create_and_save_us_heatmap(root_dir, input_file_name, graph_title, output_filename):
    df = us_states_data(root_dir, input_file_name)
    latest_date_column = latest_date_column_name(df)
    
    # Anything between the <extra></extra> tags will appear in a second box on the right part of the hovertext
    # See https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html -> hovertemplate for details
    #
    # The <latest_date_column> values are cast to int to remove the decimal portion of the number, and then converted to
    # string to allow it to be added to other strings 
    df['text'] = '<b>' + df['StateCode'].astype(str) + '</b><br>' + \
                 df[latest_date_column].astype(int).astype(str) + '<br><extra></extra>'
        
    fig = go.Figure(
        data=go.Choropleth(
            locations=df['StateCode'],
            z=np.log10(df[latest_date_column]),
            locationmode='USA-states',
            colorscale='Plasma',
            autocolorscale=False,
            hovertemplate=df['text'],
            marker_line_color='white', # line markers between states
            showscale=False,
        )
    )
    
    fig.update_layout(
        geo_scope='usa', # limit map scope to USA
        margin={"r":0,"t":30,"l":0,"b":0},
    )

    save_fig(fig, graph_title, output_filename)

def create_and_save_us_counties_heatmap(root_dir, input_file_name, graph_title, output_filename):
    counties = us_counties_as_json()
    df = us_counties_data(root_dir, input_file_name, counties)
    latest_date_column = latest_date_column_name(df)

    # Anything between the <extra></extra> tags will appear in a second box on the right part of the hovertext
    # See https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html -> hovertemplate for details
    #
    # The <latest_date_column> values are cast to int to remove the decimal portion of the number, and then converted to
    # string to allow it to be added to other strings
    df['text'] = '<b>' + df['Admin2'].astype(str) + ', ' + df['StateCode'] + '</b><br>' + \
                df[latest_date_column].astype(int).astype(str) + '<extra></extra>'

    # Make sure that all values actually get displayed (zero values get ignored by the choropleth generation logic)
    df[latest_date_column] = df[latest_date_column].apply(lambda x: x if x > 0 else 0.1)
    
    fig = px.choropleth(
        df,
        geojson=counties,
        locations='FIPS',
        color=np.log10(df[latest_date_column]),
        hover_data=[],
        hover_name=None,
        color_continuous_scale="Plasma",
        scope="usa",
        title=graph_title, # TODO: Get this working, and then apply it to states too and move out of save logic
    )

    # Reference: https://plotly.com/python/hover-text-and-formatting/
    fig.update_traces(hovertemplate=df['text'])
    
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_showscale=False,
    )
    
    save_fig(fig, graph_title, output_filename)

def transform_df_for_line_chart(df, location_code_column, location_name_column, start_date = None):
    latest_date_column = latest_date_column_name(df)
    
    all_dates = [ datetime.strptime(x, "%m/%d/%y") for x in df.T.index if re.match('([0-9]{1,2}\/){2}[0-9]{2}', x) ]

    if start_date == None:
        dates = all_dates
    else:
        dates = [ d for d in all_dates if d >= start_date ] # Only look at data from past 30 days; too much data split across all counties other     
    
    dates.sort()
    
    indices = []
    dates_col_values = []
    loc_code_col_values = []
    loc_name_col_values = []
    case_count_col_values = []
    next_index = 0
    
    for location_code in df[location_code_column].drop_duplicates():
        if location_code == None:
            continue

        for date in dates:
            location_name = df[df[location_code_column] == location_code][location_name_column].iloc[0]

            if pd.isnull(location_name):
                location_name = location_code

            dates_col_values.append(date)
            loc_code_col_values.append(location_code)
            loc_name_col_values.append(location_name)
            case_count_col_values.append(nan_safe_int_cast(df[df[location_code_column] == location_code][datetime_to_date_string(date)]))
            indices.append(next_index) 
            next_index += 1

    return pd.DataFrame(
        {
            'Date': dates_col_values,
            location_code_column: loc_code_col_values,
            location_name_column: loc_name_col_values,
            'Cases': case_count_col_values
        },
        index = indices
    )

def create_and_save_global_line_chart(root_dir, input_file_name, graph_title, output_filename):
    df = transform_df_for_line_chart(global_data(root_dir, input_file_name), 'CountryCode', 'Country/Region')
    
    fig = px.line(df,
                  x='Date',
                  y='Cases',
                  color='CountryCode',
                  hover_name='Country/Region')

    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_showscale=False,
    )

    save_fig(fig, graph_title, output_filename)

def create_and_save_us_states_line_chart(root_dir, input_file_name, graph_title, output_filename):
    df = transform_df_for_line_chart(us_states_data(root_dir, input_file_name), 'StateCode', 'Province_State')

    # TODO: Remove color bar / legend
    fig = px.line(df,
                  x='Date',
                  y='Cases',
                  color='StateCode',
                  hover_name='Province_State')

    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_showscale=False,
    )

    save_fig(fig, graph_title, output_filename)

def create_and_save_us_counties_line_chart(root_dir, input_file_name, graph_title, output_filename):
    counties = us_counties_as_json()

    start_date = datetime.now() - timedelta(30)
    df = transform_df_for_line_chart(us_counties_data(root_dir, input_file_name, counties), 'FIPS', 'Admin2', start_date)

    # TODO: Remove
    print('Creating counties line chart now')
    
    # TODO: Fold into transform function
    fig = px.line(df,
                  x='Date',
                  y='Cases',
                  color='FIPS',
                  hover_name='Admin2')

    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_showscale=False,
    )

    save_fig(fig, graph_title, output_filename)

###
### Start of Execution
###
        
if len(sys.argv) != 2:
    print('USAGE: python examine_covid_data.py <path to data directory>')
    quit()
    
root_dir = sys.argv[1]

###
### Generate Line Charts
###

print('Creating line chart of confirmed cases globally...')
create_and_save_global_line_chart(root_dir, 'time_series_covid19_confirmed_global.csv', 'Confirmed COVID-19 Cases Globally', 'covid_confirmed_global_line.html')
print('Done!')

print('Creating line chart of deaths globally...')
create_and_save_global_line_chart(root_dir, 'time_series_covid19_deaths_global.csv', 'COVID-19 Deaths Globally', 'covid_deaths_global_line.html')
print('Done!')

print('Creating line chart of recovered cases globally...')
create_and_save_global_line_chart(root_dir, 'time_series_covid19_recovered_global.csv', 'Recovered COVID-19 Cases Globally', 'covid_recovered_global_line.html')
print('Done!')

print('Creating line chart of confirmed cases in the US...')
create_and_save_us_states_line_chart(root_dir, 'time_series_covid19_confirmed_US.csv', 'Confirmed COVID-19 Cases in U.S. by State', 'covid_confirmed_us_line.html')
print('Done!')

print('Creating line chart of deaths in the US...')
create_and_save_us_states_line_chart(root_dir, 'time_series_covid19_deaths_US.csv', 'COVID-19 Deaths in the U.S. by State', 'covid_deaths_us_line.html')
print('Done!')

# TODO: Use or Remove (need to only do top 10-15 counties
# print('Creating line chart of confirmed cases in the US by county...')
# create_and_save_us_counties_line_chart(root_dir, 'time_series_covid19_confirmed_US.csv', 'Confirmed COVID-19 Cases in U.S. by County', 'covid_confirmed_us_counties_line.html')
# print('Done!')

# print('Creating line chart of deaths in the US by county...')
# create_and_save_us_counties_line_chart(root_dir, 'time_series_covid19_deaths_US.csv', 'COVID-19 Deaths in the U.S. by County', 'covid_deaths_us_counties_line.html')
# print('Done!')

###
### Generate Heat Maps
###

print('Creating graph of confirmed cases globally...')
create_and_save_global_heatmap(root_dir, 'time_series_covid19_confirmed_global.csv', 'Confirmed COVID-19 Cases Globally', 'covid_confirmed_global.html')
print('Done!')

print('Creating graph of deaths globally...')
create_and_save_global_heatmap(root_dir, 'time_series_covid19_deaths_global.csv', 'COVID-19 Deaths Globally', 'covid_deaths_global.html')
print('Done!')

print('Creating graph of recovered cases globally...')
create_and_save_global_heatmap(root_dir, 'time_series_covid19_recovered_global.csv', 'Recovered COVID-19 Cases Globally', 'covid_recovered_global.html')
print('Done!')

print('Creating graph of confirmed cases in the US...')
create_and_save_us_heatmap(root_dir, 'time_series_covid19_confirmed_US.csv', 'Confirmed COVID-19 Cases in U.S. by State', 'covid_confirmed_us.html')
print('Done!')

print('Creating graph of deaths in the US...')
create_and_save_us_heatmap(root_dir, 'time_series_covid19_deaths_US.csv', 'COVID-19 Deaths in U.S. by State', 'covid_deaths_us.html')
print('Done!')

print('Creating graph of confirmed cases in the US by county...')
create_and_save_us_counties_heatmap(root_dir, 'time_series_covid19_confirmed_US.csv', 'Confirmed COVID-19 Cases in U.S. by County', 'covid_confirmed_us_counties.html')
print('Done!')

print('Creating graph of deaths in the US by county...')
create_and_save_us_counties_heatmap(root_dir, 'time_series_covid19_deaths_US.csv', 'COVID-19 Deaths in U.S. by County', 'covid_deaths_us_counties.html')
print('Done!')
