import pandas as pd
import altair as alt
import numpy as np
import matplotlib.pyplot as plt
from vega_datasets import data
import streamlit as st

@st.cache_data
def get_all_data():
    ##### 2025 DATA ENDS IN OCTOBER years = range(1990, 2026)
    files = [f"T100-{year}.csv" for year in years]
    df_list = [pd.read_csv(file) for file in files]
    T100_full = pd.concat(df_list, axis=0, ignore_index=True)
    print(T100_full.shape)
    T100_full.head() # Create a new column NON_US_COUNTRY
    T100_full['NON_US_COUNTRY'] = np.where(
        T100_full['ORIGIN_COUNTRY_NAME'] != 'United States', 
        T100_full['ORIGIN_COUNTRY_NAME'], 
        T100_full['DEST_COUNTRY_NAME'])

    # Create new column NON_US_AIRPORT
    T100_full['NON_US_AIRPORT'] = np.where(
        T100_full['ORIGIN_COUNTRY_NAME'] != 'United States', 
        T100_full['ORIGIN'], 
        T100_full['DEST'])

    # Create a new column US_AIRPORT
    T100_full['US_AIRPORT'] = np.where(
        T100_full['ORIGIN_COUNTRY_NAME'] == 'United States', 
        T100_full['ORIGIN'], 
        T100_full['DEST'])

    # Create a new column US_CITY_NAME
    T100_full['US_CITY_NAME'] = np.where(
        T100_full['ORIGIN_COUNTRY_NAME'] == 'United States', 
        T100_full['ORIGIN_CITY_NAME'], 
        T100_full['DEST_CITY_NAME'])

    # Create a new column US_CITY_NAME
    T100_full['NON_US_CITY_NAME'] = np.where(
        T100_full['ORIGIN_COUNTRY_NAME'] == 'United States', 
        T100_full['DEST_CITY_NAME'], 
        T100_full['ORIGIN_CITY_NAME'])

    #Create NONDIRECTIONAL_MARKET variable - combines US Airport with Foreign Airport, US Airport 
    T100_full['NONDIRECTIONAL_MARKET'] = T100_full['US_AIRPORT'] + T100_full['NON_US_AIRPORT']

    #Create DIRECTIONAL_MARKET variable - combines US Airport with Foreign Airport, US Airport 
    T100_full['DIRECTIONAL_MARKET'] = T100_full['ORIGIN'] + T100_full['DEST']

    #Create Aicraft Types Variable
    Aircraft_Types = pd.read_csv("Aircraft Types.csv")
    T100_full['AIRCRAFT_TYPE']= T100_full['AIRCRAFT_TYPE'].astype(int)
    Aircraft_Types['Code'] = Aircraft_Types['Code'].astype(int)

    df_merged = pd.merge(
        T100_full, 
        Aircraft_Types[['Code', 'Description']], 
        left_on='AIRCRAFT_TYPE', 
        right_on='Code', 
        how='left')

    T100_full['Description'] = df_merged['Description']
    T100_full = T100_full.rename(columns={'Description': 'AIRCRAFT_NAME'})

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.expand_frame_repr', False) ## Import Continent Dataset ##
    continents = pd.read_csv('Countries-Continents.csv')
    continents.head() ### Import Income Dataset ###
    income_import = pd.read_csv('GDP_Per_Capita.csv')
    id_vars = ['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code']
    income = income_import.melt(id_vars=id_vars, var_name='Year', value_name='GDP_Per_Capita')

    income['Year'] = pd.to_numeric(income['Year'])
    income = income.dropna(subset=['GDP_Per_Capita'])

    income = income.sort_values(['Country Name', 'Year'])
    income = income.drop(columns=['Indicator Name', 'Indicator Code'])

    print(income.head()) ### Lookup By Year ###
    pd.set_option('display.max_rows', 500)
    filtered_data = T100_full[
         (T100_full['DEPARTURES_PERFORMED'] >= 5) 
        & (T100_full['CLASS'] == 'F') 
        & (T100_full['YEAR'] < 2025)
    ].copy()

    ## Calculate Average Distance Over All Years For Each Country ## 
    filtered_distance_analysis_data = filtered_data.copy()
    filtered_distance_analysis_data['PASSENGER_MILES'] = filtered_distance_analysis_data['PASSENGERS'] * filtered_distance_analysis_data['DISTANCE']
    avg_distance_analysis = filtered_distance_analysis_data.groupby(['NON_US_COUNTRY']).agg({
        'PASSENGERS': 'sum',
        'PASSENGER_MILES': 'sum'}).reset_index()

    avg_distance_analysis['AVG_DISTANCE_FLOWN'] = avg_distance_analysis['PASSENGER_MILES'] / avg_distance_analysis['PASSENGERS']
    avg_distance_analysis = avg_distance_analysis.sort_values(by='AVG_DISTANCE_FLOWN', ascending=False)
    avg_distance_analysis = avg_distance_analysis.drop(columns=['PASSENGERS','PASSENGER_MILES'])

    pax_by_country = filtered_data.groupby(['YEAR', 'NON_US_COUNTRY']).agg({
        'PASSENGERS': 'sum',
        'SEATS': 'sum',
        'DEPARTURES_PERFORMED': 'sum',
    }).reset_index()

    #create columns that show the top n carriers, foreign airports, US airports, and flights for each country-year
    variables_top_by_index = ['CARRIER_NAME', 'NON_US_AIRPORT', 'US_AIRPORT', 'NONDIRECTIONAL_MARKET']

    for var in variables_top_by_index:
        totals = filtered_data.groupby(['YEAR', 'NON_US_COUNTRY', var])['PASSENGERS'].sum().reset_index()
        
        top_5 = (totals.sort_values(['YEAR', 'NON_US_COUNTRY', 'PASSENGERS'], ascending=[True, True, False])
                 .groupby(['YEAR', 'NON_US_COUNTRY'])
                 .head(5))
        top_5['rank'] = top_5.groupby(['YEAR', 'NON_US_COUNTRY']).cumcount() + 1
        top_5_pivoted = top_5.pivot(index=['YEAR', 'NON_US_COUNTRY'], 
                                    columns='rank', 
                                    values=[var, 'PASSENGERS'])
        top_5_pivoted.columns = [
            f'TOP_{col[1]}_{var}{"_PAX" if col[0] == "PASSENGERS" else ""}' 
            for col in top_5_pivoted.columns.values
        ]
        top_5_pivoted = top_5_pivoted.reset_index()
        
        pax_by_country = pax_by_country.merge(
            top_5_pivoted, 
            on=['YEAR', 'NON_US_COUNTRY'], 
            how='left')
        
    ## Merge Datasets 
    pax_by_country = pd.merge(
        pax_by_country, 
        avg_distance_analysis, 
        on = 'NON_US_COUNTRY', 
        how='inner')

    pax_by_country = pd.merge(
        income, 
        pax_by_country, 
        left_on=['Country Name', 'Year'], 
        right_on=['NON_US_COUNTRY', 'YEAR'], 
        how='inner')

    pax_by_country = pd.merge(
        continents, 
        pax_by_country, 
        left_on=['Country'], 
        right_on=['NON_US_COUNTRY'], 
        how='inner')

    cols_to_drop = ['NON_US_COUNTRY', 'Country']
    pax_by_country = pax_by_country.drop(columns=[c for c in cols_to_drop if c in pax_by_country.columns])

    for i in range(1, 6):
        col = f'TOP_{i}_NONDIRECTIONAL_MARKET'
        if col in pax_by_country.columns:
            pax_by_country[col] = pax_by_country[col].str.replace(r'([A-Z]{3})([A-Z]{3})', r'\1 - \2', regex=True)
            
    pax_by_country = pax_by_country.sort_values(by='PASSENGERS', ascending=True)
    pax_by_country = pax_by_country.sort_values(by='YEAR', ascending=False)

    pax_by_country ### Lookup By Year ###
    ## Calculate Average Distance Over All Years For Each Country #
    filtered_distance_analysis_data = filtered_data.copy()
    filtered_distance_analysis_data['PASSENGER_MILES'] = filtered_distance_analysis_data['PASSENGERS'] * filtered_distance_analysis_data['DISTANCE']
    avg_distance_analysis = filtered_distance_analysis_data.groupby(['US_AIRPORT']).agg({
        'PASSENGERS': 'sum',
        'PASSENGER_MILES': 'sum'}).reset_index()

    avg_distance_analysis['AVG_DISTANCE_FLOWN'] = avg_distance_analysis['PASSENGER_MILES'] / avg_distance_analysis['PASSENGERS']
    avg_distance_analysis = avg_distance_analysis.sort_values(by='AVG_DISTANCE_FLOWN', ascending=False)
    avg_distance_analysis = avg_distance_analysis.drop(columns=['PASSENGERS','PASSENGER_MILES'])

    pax_by_airport = filtered_data.groupby(['YEAR', 'US_AIRPORT', 'NON_US_COUNTRY','CARRIER_NAME','NON_US_AIRPORT','US_CITY_NAME','NON_US_CITY_NAME']).agg({
        'PASSENGERS': 'sum',
        'SEATS': 'sum',
        'DEPARTURES_PERFORMED': 'sum',
        'DISTANCE': 'mean'
    }).reset_index()

    pax_by_airport = pd.merge(
        continents, 
        pax_by_airport, 
        left_on=['Country'], 
        right_on=['NON_US_COUNTRY'], 
        how='inner')

    us_airport_map = pd.read_json("united-states-international-airports.geojson")

    # Final Map Logic
    us_airport_map['type'] = us_airport_map.features.apply(lambda x: x['type'])
    us_airport_map['geometry'] = us_airport_map.features.apply(lambda x: x['geometry'])
    us_airport_map['code'] = us_airport_map.features.apply(lambda x: x['properties']['code'])

    manual_airports = [
        {"code": "HNL", "name": "Honolulu", "lon": -157.9254, "lat": 21.3187},
        {"code": "ANC", "name": "Anchorage", "lon": -149.9906, "lat": 61.1769},
        {"code": "OGG", "name": "Kahului", "lon": -156.4361, "lat": 20.8946},
        {"code": "KOA", "name": "Kona", "lon": -156.0456, "lat": 19.7388},
        {"code": "ITO", "name": "Hilo", "lon": -155.0485, "lat": 19.7214},
        {"code": "LIH", "name": "Lihue", "lon": -159.3390, "lat": 21.9760},
        {"code": "FAI", "name": "Fairbanks", "lon": -147.8564, "lat": 64.8151},
        {"code": "AUS", "name": "Austin", "lon": -97.6664, "lat": 30.1945},
        {"code": "PVD", "name": "Providence", "lon": -71.4282, "lat": 41.7240}]

    new_data = pd.DataFrame(manual_airports)
    new_data['geometry'] = new_data.apply(lambda x: {'type': 'Point', 'coordinates': [x['lon'], x['lat']]}, axis=1)
    
    return pax_by_country, pax_by_airport, us_airport_map, new_data