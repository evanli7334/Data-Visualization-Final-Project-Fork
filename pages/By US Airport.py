
import streamlit as st
import altair as alt
import pandas as pd
from vega_datasets import data
from utils.data_utils import get_all_data

def render_airport_page():
    pax_by_country, pax_by_airport, us_airport_map, new_data = get_all_data()

    alt.data_transformers.disable_max_rows()

    title = alt.Chart(us_airport_map).mark_text(
        fontSize=30, fontWeight='bold', align='center', baseline='middle',).encode(
        text=alt.value('US-International Travel: Passenger Trends by US Gateway Airports')
    ).properties(#width=1000, 
                 height=50)

    #Create year and airport selections
    full_airport_map = pd.concat([us_airport_map, new_data], ignore_index=True)

    full_airport_map = full_airport_map.merge(
        pax_by_airport, left_on='code', 
        right_on='US_AIRPORT', how='left'
    ).fillna(0)
    full_airport_map = full_airport_map[full_airport_map['PASSENGERS'] > 0]

    full_airport_map['lon'] = full_airport_map['geometry'].apply(lambda x: x['coordinates'][0])
    full_airport_map['lat'] = full_airport_map['geometry'].apply(lambda x: x['coordinates'][1])

    states = alt.topo_feature(data.us_10m.url, feature='states')

    click_selection = alt.selection_point(
        on='click', fields=['code'], 
        empty=False, nearest=True,
        clear='dblclick')

    Years = sorted(pax_by_airport['YEAR'].unique().tolist())
    Years_Options = [None] + Years 
    Years_Labels = ['All'] + [str(y) for y in Years]

    min_year = int(pax_by_airport['YEAR'].min())
    max_year = int(pax_by_airport['YEAR'].max())

    selection_year = alt.selection_point(
        fields=['YEAR'],
        value=min_year,
        bind=alt.binding_range(
            min=min_year, 
            max=max_year, 
            step=1, 
            name='Select Year: ', 
            debounce=500),
        name='year_selection')

    years_bar_chart = alt.Chart(pax_by_airport).mark_bar().add_params(selection_year).encode(
        x=alt.X('YEAR:O', title="Year"),
        y=alt.Y('sum(PASSENGERS):Q', title="Total Passengers"),
        opacity=alt.condition(
            selection_year, alt.value(1.0), alt.value(0.3)),
        tooltip=[
            alt.Tooltip('YEAR:O', title='Year'), 
            alt.Tooltip('sum(PASSENGERS):Q', title='Total Passengers', format=',.0f')]
        ).properties(
            #width=1000, 
            height=200, 
            title=alt.Title(
                'US International Air Traffic - Annual Passenger Volume', 
                fontSize=20))

    #create map for showing size of airport international destinations and selecting the airport
    background = alt.Chart(states).mark_geoshape(
        fill='lightgray',
        stroke='black',
        strokeWidth=1.5
    ).properties(
        #width=1000,
        height=500,
        title=alt.TitleParams(
            text="US Airports By Annual International Passengers - Volume Map",
            subtitle="Select year through dropdown menu at the bottom. Click an airport to view passenger trends by airport by year, top airlines, and top foreign destinations.",
            fontSize=20,
            subtitleFontSize=14,
            subtitleColor='gray',
            anchor='middle' ))

    max_pax = full_airport_map.groupby(['YEAR', 'code'])['PASSENGERS'].sum().max()

    circles = alt.Chart(full_airport_map
                        ).mark_circle(stroke = 'white', strokeWidth = 1, strokeOpacity =.8).encode(
        longitude='lon:Q', 
        latitude='lat:Q', 
        size=alt.Size('total_pax:Q', 
                      scale=alt.Scale(domain=[0, max_pax],range=[10, 4000]), 
                      title='Total Passengers'),
        opacity=alt.condition(click_selection, alt.value(.9), alt.value(0.4)),
        tooltip=[
            alt.Tooltip('code:N', title='Airport Code'),
            alt.Tooltip('US_CITY_NAME:N', title='City Name'),
            alt.Tooltip('total_pax:Q', title='International Passengers', format=',.0f')]
        ).transform_filter(
            selection_year
        ).transform_aggregate(
            total_pax='sum(PASSENGERS)',
            groupby=['code', 'lon', 'lat', 'US_CITY_NAME'] 
        ).add_params(
            click_selection)

    airport_label_block = alt.Chart(full_airport_map).mark_text(
        fontSize=20, align='center',
    ).encode(
        text=alt.condition(
            click_selection,
            alt.Text('label:N'),
            alt.value("Select an airport"))
    ).transform_calculate(
        label="'Annual International Passenger Volume - ' + datum.code + ' (' + datum.US_CITY_NAME + ')'"
    ).transform_filter(
        click_selection).properties(
        #width=1000, 
        height=30 ).add_params(click_selection)

    line_graph_by_airport = alt.Chart(full_airport_map).mark_line(point=True).encode(
        y=alt.Y('sum(PASSENGERS):Q', title='Sum of International Passengers'),
        x=alt.X('YEAR:O', title='Year'),
        tooltip=[
            alt.Tooltip('YEAR:O', title='Year'),
            alt.Tooltip('US_CITY_NAME:N', title='City Name'),
            alt.Tooltip('sum(PASSENGERS):Q', title='International Passengers', format=',.0f')]
    ).transform_filter(
        click_selection 
    ).properties(
        #width=1000, 
        height=250,
    ).add_params(
        click_selection)

    bar_graph_top_airlines_label_block = alt.Chart(full_airport_map).mark_text(
        fontSize=20,
        align='center'
    ).encode(
        text=alt.condition(
            click_selection,
            alt.Text('label:N'),
            alt.value("Select an airport to view top airlines"))
    ).transform_calculate(
        year_txt="isValid(year_selection.YEAR) ? year_selection.YEAR : 'All Years'",
        label="datum.code + ' (' + datum.US_CITY_NAME + ') - ' + datum.year_txt + ' Summary Statistics'"
    ).transform_filter(
        click_selection
    ).properties(
        #width=1000, 
        height=30 
    ).add_params(click_selection, selection_year)

    #create bar graph showing top airlines for each airport
    unique_airlines = full_airport_map['CARRIER_NAME'].unique().tolist()
    bar_graph_top_airlines = alt.Chart(full_airport_map).mark_bar().encode(
        y=alt.Y('sum_passengers:Q', title='Sum of International Passengers'),
        x=alt.X('CARRIER_NAME:N', title='Airline Name', sort='-y', 
                axis=alt.Axis(labelAngle=-45)),
        color=alt.Color('CARRIER_NAME:N', 
            scale=alt.Scale(
                domain=unique_airlines,
                scheme='category20'), 
            legend=None),
        tooltip=[
            alt.Tooltip('CARRIER_NAME:N', title='Airline Name'),
            alt.Tooltip('sum_passengers:Q', title='Total International Passengers', format=',.0f')]
    ).transform_filter(
        click_selection 
    ).transform_filter(
        selection_year 
    ).transform_aggregate(
        sum_passengers='sum(PASSENGERS)',
        groupby=['CARRIER_NAME']
    ).transform_window(
        rank='rank(sum_passengers)',
        sort=[alt.SortField('sum_passengers', order='descending')]
    ).transform_filter(
        alt.datum.rank <= 5
    ).properties(
        width=350, height=450, 
        title = 'Top 5 Airlines by International Passengers')

    #create bar graph showing top destinations
    unique_cities = full_airport_map['NON_US_CITY_NAME'].unique().tolist()
    bar_graph_top_destinations = alt.Chart(full_airport_map).mark_bar().encode(
        y=alt.Y('sum_passengers:Q', title='Sum of Passengers'),
        x=alt.X('NON_US_CITY_NAME:N', title='Foreign City', sort='-y', 
                axis=alt.Axis(labelAngle=-45)),
        color=alt.Color('NON_US_CITY_NAME:N', 
            scale=alt.Scale(
                domain=unique_cities,  
                scheme='category20'), legend=None),
        tooltip=[
            alt.Tooltip('NON_US_CITY_NAME:N', title='Foreign City Name'),
            alt.Tooltip('NON_US_AIRPORT:N', title='Foreign Airport Code'),
            alt.Tooltip('sum_passengers:Q', title='Total Passengers', format=',.0f')],
    ).transform_filter(
        click_selection 
    ).transform_filter(
        selection_year 
    ).transform_aggregate(
        sum_passengers='sum(PASSENGERS)',
        groupby=['NON_US_CITY_NAME', 'NON_US_AIRPORT']
    ).transform_window(
        rank='rank(sum_passengers)',
        sort=[alt.SortField('sum_passengers', order='descending')]
    ).transform_filter(
        alt.datum.rank <= 5
    ).properties(
        width=350, height=450, 
        title = 'Top 5 Foreign Destinations')

    map_chart = (background + circles).project(type='albersUsa')

    spacer = alt.Chart(pd.DataFrame({'x': [0]})).mark_point(opacity=0).properties(height=50)

    dashboard = (title & 
                 years_bar_chart & 
                 map_chart & 
                 airport_label_block & 
                 line_graph_by_airport & 
                 bar_graph_top_airlines_label_block &
                 (bar_graph_top_airlines | bar_graph_top_destinations) & 
                 spacer).resolve_scale(
        color='independent',
        size='independent')

    st.altair_chart(dashboard, use_container_width=True)

render_airport_page()