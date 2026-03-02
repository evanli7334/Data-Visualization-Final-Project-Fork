import streamlit as st
import altair as alt
from utils.data_utils import get_all_data

st.markdown("""
    <style>
    /* Target the main container */
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Optional: Center your headers and subheaders for a cleaner look */
    h1, h2, h3 {
        text-align: center;
    }
    
    /* Center the chart container itself */
    .stVegaLiteChart {
        display: flex;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)


def render_story_page():
    pax_by_country, pax_by_airport, full_airport_map, new_data = get_all_data()

    ### Scatterplot ### 
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    #create years selection and country selection
    Years = sorted(pax_by_country['Year'].unique().tolist())
    Years_Options = [None] + Years 
    Years_Labels = ['All'] + [str(y) for y in Years]

    country_list = sorted(pax_by_country['Country Name'].unique())

    dropdown_country = alt.binding_select(
        options=country_list, 
        labels=country_list,
        name='Country Name: ')

    min_year = int(pax_by_country['Year'].min())
    max_year = int(pax_by_country['Year'].max())

    selection_year = alt.selection_point(
        fields=['Year'],
        value=min_year,
        bind=alt.binding_range(
            min=min_year, 
            max=max_year, 
            step=1, 
            name='Select Year: ', debounce=500),
        name='year_selection')

    country_selection = alt.selection_point(
        name='country_selection',   
        bind=dropdown_country,
        fields=['Country Name'],
        empty=False,
        toggle=False, on = 'click')

    #Create initial top bar chart showing year selected
    years_bar_chart = alt.Chart(pax_by_country).mark_bar().add_params(selection_year).encode(
            x=alt.X('Year:O', 
                    title="Year"),
            y=alt.Y('sum(PASSENGERS):Q', title="Total Passengers Flown To/From The US"),
            opacity=alt.condition(selection_year,
                alt.value(1.0),   
                alt.value(0.3)),
            tooltip=['Year:O', alt.Tooltip('sum(PASSENGERS):Q', title='Sum of Passengers', format=',.0f')]
            ).properties(#width=1000, 
                         height=200, 
                         title=alt.Title('US International Air Traffic: Annual Passenger Volume to/from the United States', fontSize = 20, anchor = 'middle'))

    top_10_countries = pax_by_country.groupby('Country Name')['PASSENGERS'].sum().nlargest(10).index.tolist()

    #Create scatterplot for selecting country 
    country_change_chart = alt.Chart(pax_by_country).transform_filter(alt.FieldOneOfPredicate(field='Country Name', oneOf=top_10_countries)
    ).mark_line(point=True).encode(
        x=alt.X('Year:O', title= 'Year'),
        y=alt.Y('sum(PASSENGERS):Q', title= 'Total Passengers Flown To/From The US'),
        color=alt.Color('Country Name:N', title="Country",
                        scale=alt.Scale(scheme='category10')),
        opacity=alt.condition(country_selection, alt.value(1.0), alt.value(0.6)),
        tooltip=[
            alt.Tooltip('Country Name:N'),
            alt.Tooltip('Year:O'),
            alt.Tooltip('sum(PASSENGERS):Q', title='Total Passengers', format=',.0f')]).add_params(
        country_selection).properties(#width
                                      height=400,
        title=alt.TitleParams(
            text="Annual Passenger Trends: Top 10 Countries",
            fontSize=20, anchor = 'middle'))

    scatterplot_title = alt.Chart(full_airport_map).mark_text(
        fontSize=20,           
        align='center',
    ).encode(
        text=alt.Text('label:N') 
    ).transform_calculate(
        year_txt="isValid(year_selection.Year) ? year_selection.Year : 'All Years'",
        label="'US-International Travel: ' + datum.year_txt + ' Average Country Distance vs. Passengers Flown'"
    ).properties(
        #width=1000,
        height=40 
    ).add_params(selection_year)

    scatterplot = alt.Chart(pax_by_country).mark_circle(size = 100).encode(
        x = alt.X('mean(AVG_DISTANCE_FLOWN):Q', 
                        title='Average Flown Distance To US (Miles)'),
        color = alt.Color('Continent:N', title = 'Continent', scale=alt.Scale(scheme='category10'), 
        legend=alt.Legend(
            orient='right', 
            symbolSize=100, 
            titleFontSize=14, 
            labelFontSize=12)),
        y=alt.Y('sum(PASSENGERS):Q', 
                     title='Total Passengers Flown To/From The US', axis=alt.Axis(tickCount=5, grid=True, minExtent=40),
                        scale=alt.Scale(type='log', domain=[10, 100000000], clamp=True)),
        opacity=alt.condition(
            country_selection,
            alt.value(1.0),   
            alt.value(0.8)),
        stroke=alt.condition(country_selection, alt.value('black'), alt.value('transparent')),
        detail=['Country Name:N','Continent:N'],
        tooltip =[alt.Tooltip('Country Name:N', title='Country Name'),
                  alt.Tooltip('mean(AVG_DISTANCE_FLOWN):Q', title='Average Flown Distance To US (Miles)', format=',.0f'),
                  alt.Tooltip('sum(PASSENGERS):Q', title='Total Passengers Flown', format=',.0f')]
                ).add_params(country_selection).transform_filter("(year_selection.Year == null) || (datum.Year == year_selection.Year)"
                                                                ).properties(#width=1000,
                    height=500)

    #Create income chart
    base_income = alt.Chart(pax_by_country).encode(
        x=alt.X('Year:O', title="Year")
    ).add_params(country_selection).transform_filter(country_selection)

    income_line = base_income.mark_line(color='#5276A7', point=True).encode(
        y=alt.Y('mean(GDP_Per_Capita):Q', 
                title='Income (GDP Per Capita)', 
                axis=alt.Axis(titleColor='#5276A7')),
        tooltip=[
            alt.Tooltip('Year:O'),
            alt.Tooltip('Country Name:N'),
            alt.Tooltip('mean(GDP_Per_Capita):Q', 
                        title='GDP Per Capita', 
                        format='$,.0f'),
            alt.Tooltip('sum(PASSENGERS):Q', 
                        title='Total Passengers', 
                        format=',.0f')])

    passenger_line = base_income.mark_line(color='#F18536', point=True).encode(
        y=alt.Y('sum(PASSENGERS):Q', 
                title='Total Passengers Flown To/From The US', 
                axis=alt.Axis(titleColor='#F18536')),
        tooltip=[
            alt.Tooltip('Year:O'),
            alt.Tooltip('Country Name:N'),
            alt.Tooltip('mean(GDP_Per_Capita):Q', 
                        title='GDP Per Capita', 
                        format='$,.0f'),
            alt.Tooltip('sum(PASSENGERS):Q', 
                        title='Total Passengers', 
                        format=',.0f')])

    income_chart = alt.layer(
        income_line,
        passenger_line
    ).resolve_scale(
        y='independent').encode(
        x=alt.X(
            'Year:O',
            title="Year",
            axis=alt.Axis(labelAngle=0, tickCount=10))
    ).properties(
        width=800,
        height=400,
        title=alt.TitleParams(
        text=alt.ExprRef(
            "country_selection['Country Name'] ? "
            "country_selection['Country Name'] + ' GDP Per Capita vs. Passenger Volume' : "
            "''"), fontSize=20, anchor='middle'))

    bar_plots_title = alt.Chart(full_airport_map).mark_text(
        fontSize=20,           
        align='center',
    ).encode(
        text=alt.Text('label:N') 
    ).transform_calculate(
        label="(isValid(year_selection.Year) && country_selection['Country Name']) ? "
              "country_selection['Country Name'] + ' ' + year_selection.Year + ' Summary Statistics' : ''").properties(
        width=800,
        height=50 
    ).add_params(
        selection_year, 
        country_selection)

    #create top airlines and top routes bar charts
    top_airlines_bar_chart = alt.Chart(pax_by_country).transform_filter(
        country_selection                    
    ).transform_filter(
        "isValid(year_selection.Year) && datum.Year == year_selection.Year"
    ).transform_fold(
        ['TOP_1_CARRIER_NAME', 'TOP_2_CARRIER_NAME', 'TOP_3_CARRIER_NAME', 'TOP_4_CARRIER_NAME', 'TOP_5_CARRIER_NAME'],
        as_=['rank_name', 'carrier_name']
    ).transform_fold(
        ['TOP_1_CARRIER_NAME_PAX', 'TOP_2_CARRIER_NAME_PAX', 'TOP_3_CARRIER_NAME_PAX', 'TOP_4_CARRIER_NAME_PAX', 'TOP_5_CARRIER_NAME_PAX'],
        as_=['rank_pax', 'passenger_count']
    ).transform_filter(
       (alt.expr.substring(alt.datum.rank_name, 4, 5) == alt.expr.substring(alt.datum.rank_pax, 4, 5)) &
        (alt.datum.carrier_name != None) & (alt.datum.carrier_name != '')).mark_bar().encode(
        x=alt.X('carrier_name:N', title='Carrier', 
            sort='-y',
        axis=alt.Axis(
            labelAngle=-45)),
        y=alt.Y('passenger_count:Q', title='Passengers'),
        color=alt.Color('carrier_name:N', legend=None),
        tooltip=[
            alt.Tooltip('carrier_name:N', title='Carrier'),
            alt.Tooltip('passenger_count:Q', title='Passengers', format=',.0f')]
    ).properties(
        width=350,
        height=450,
        title=alt.TitleParams(
            text="Top 5 Carriers",
            anchor='middle'
        ))

    top_routes_bar_chart = alt.Chart(pax_by_country).transform_filter(
        country_selection                    
    ).transform_filter(
        "isValid(year_selection.Year) && datum.Year == year_selection.Year"
    ).transform_fold(
        ['TOP_1_NONDIRECTIONAL_MARKET', 'TOP_2_NONDIRECTIONAL_MARKET', 'TOP_3_NONDIRECTIONAL_MARKET', 'TOP_4_NONDIRECTIONAL_MARKET', 'TOP_5_NONDIRECTIONAL_MARKET'],
        as_=['rank_name', 'route_name']
    ).transform_fold(
        ['TOP_1_NONDIRECTIONAL_MARKET_PAX', 'TOP_2_NONDIRECTIONAL_MARKET_PAX', 'TOP_3_NONDIRECTIONAL_MARKET_PAX', 'TOP_4_NONDIRECTIONAL_MARKET_PAX', 'TOP_5_NONDIRECTIONAL_MARKET_PAX'],
        as_=['rank_pax', 'passenger_count']
    ).transform_filter(
       (alt.expr.substring(alt.datum.rank_name, 4, 5) == alt.expr.substring(alt.datum.rank_pax, 4, 5)) &
        (alt.datum.route_name != None) & (alt.datum.route_name != '')).mark_bar().encode(
        x=alt.X('route_name:N', title='Nondirectional Route', 
            sort='-y',
        axis=alt.Axis(
            labelAngle=-45)),
        y=alt.Y('passenger_count:Q', title='Passengers'),
        color=alt.Color('route_name:N', legend=None),
        tooltip=[
            alt.Tooltip('route_name:N', title='Nondirectional Route'),
            alt.Tooltip('passenger_count:Q', title='Passengers', format=',.0f')]
    ).properties(
        width=350,
        height=450,
        title=alt.TitleParams(
            text="Top 5 Nondirectional Nonstop Routes",
            anchor='middle'
        ))

    #create spacer so that bar chart labels become visible
    spacer = alt.Chart().mark_rect(
        color='white',           
        opacity=0             
    ).encode(
    ).properties(
        width=400,
        height=120)

    #display
    chart = (years_bar_chart & 
     country_change_chart & 
     scatterplot_title &
     scatterplot & 
     income_chart & 
     bar_plots_title &
     (top_airlines_bar_chart | top_routes_bar_chart) & 
     spacer).resolve_scale(
        color='independent')
    
    st.altair_chart(chart, use_container_width=True)

render_story_page()