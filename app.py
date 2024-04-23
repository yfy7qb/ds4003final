# Import libraries
import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash,dash_table, dcc, html, Input, Output, callback
import plotly as py
import geopandas as gpd
import dash_bootstrap_components as dbc

# Import main data
df = pd.read_csv('data.csv')

# Import second data
dfff = pd.read_csv('reppercent.csv')

# Import district shapes
shpfile = gpd.read_file('districts114.shp')
shapes = shpfile[shpfile['STATENAME'] == 'Georgia'].drop(columns = ['ID', 'STARTCONG', 'ENDCONG', 'DISTRICTSI', 'COUNTY', 'PAGE', 'LAW', 'NOTE', 'BESTDEC', 'FINALNOTE', 'RNOTE', 'LASTCHANGE', 'FROMCOUNTY']).reset_index(drop = True)

# Make some data adjustments
dfffpres = pd.DataFrame(columns = ['district', 'year', 'reppercent'])

for j in [2016, 2020]:
    reppercentvalue = float(dfff[dfff['year'] == j][dfff['district'] == 0]['reppercent'][15*(j - 2016)/4])
    for i in range(0, 15):
        x = {'district': i, 'year': j, 'reppercent': reppercentvalue}
        dfffpres = pd.concat([dfffpres, pd.DataFrame([x])], ignore_index = True)

        # Add in stylesheet
#stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
stylesheet = dbc.themes.BOOTSTRAP

# Set up app and sever
app = Dash(__name__, external_stylesheets= ['https://codepen.io/chriddyp/pen/bWLwgP.css'])
server = app.server

# Set app layout
app.layout = html.Div([
    
    html.Hr(),

    # Adding title
    html.Div(html.H1(
        children = 'Georgia Election Results: 2016 and 2020',
        style = {'display': 'flex', 'justifyContent': 'center'}
        )),

    html.Hr(),

    # Adding description
    html.Div(html.P(children =
        'This interactive dashboard, when fully functional, will allow for comparisons between 2016 and 2020 election data, and House and Presidential results, in the state of Georgia.'
        )),

    html.Hr(),

    # Adding Radio Items for Year
    html.Div(dcc.RadioItems(
            id = 'yearradio',
            options = [2016, 2020],
            value =  2016,
            inline = False,
            className="four columns",
            style = {
                'display': 'flex',
                'justifyContent': 'center'
                }
            )),

    # Adding Dropdown for District
    html.Div(dcc.Dropdown(
            id = 'districtdd',
            options = df['district'].unique(),
            value =  'statewide',
            multi = False,
            className="four columns"
            )),

    # Adding Radio Items for Race
    html.Div(dcc.RadioItems(
            id = 'preshouseradio',
            options=[
                {'label': 'President', 'value': 'pres'},
                {'label': 'House', 'value': 'house'}],
            value =  'house',
            inline = True,
            className="four columns",
            style = {'display': 'flex', 'justifyContent': 'center'}
            )),

    # Add space
    html.Hr(),

    # Adding graphs

    html.Div(dcc.Graph(
        id = 'geo',
        className = 'eight columns')),

    html.Div(dcc.Graph(
        id = 'pie',
        className = 'four columns')),

    html.Hr(),

    html.Div(dcc.Graph(
        id = 'votingtypechart',
        className = 'six columns')),
    
    html.Div(dcc.Graph(
        id = 'linechart',
        className = 'six columns')),
    
    ]
    )

# Define chained callback
@app.callback(
    Output('districtdd', 'options'),
    Input('preshouseradio', 'value'))
def set_district_options(preshouseradio):
    # Generate options for the subcategory dropdown
    if preshouseradio == 'pres':
        return [{'label': 'President', 'value': 0}]
    else:
        return [{'label': 'District {}'.format(str(i)), 'value': i} for i in range(1, 15)]

@callback(
    Output('districtdd', 'value'),
    Input('districtdd', 'options'))
def set_district_value(available_options):
    return available_options[0]['value']


# Define callback function for graphs
@callback(
    Output('geo', 'figure'),
    Output('pie', 'figure'),
    Output('votingtypechart', 'figure'),
    Output('linechart', 'figure'),
    Input('yearradio', 'value'),
    Input('districtdd', 'value'),
    Input('preshouseradio', 'value')
)

# Define update function
def update_graph(yearradio, districtdd, preshouseradio):

    # Filter for data in given year, race, district
    dff = df[df['year'] == yearradio][df['race'] == preshouseradio][df['district'] == districtdd]

    # Map of election districts, colored by vote proportions
    fig4 = px.choropleth_mapbox( #
                            dfff[dfff['year'] == yearradio][dfff['district'] != 0] if preshouseradio == 'house' else dfffpres[dfff['year'] == yearradio],
                            shapes,
                            color = 'reppercent',
                            locations = dfff['district'][dfff['year'] == yearradio][dfff['district'] != 0] - 1 if preshouseradio == 'house' else dfffpres['district'][dfffpres['year'] == yearradio],
                            color_continuous_scale = 'RdBu_r',
                            range_color = (0, 1) if preshouseradio == 'house' else (0.45, 0.55),
                            mapbox_style = "carto-positron",
                            title = 'All House Results in {}'.format(yearradio) if preshouseradio == 'house' else 'Presidential Results in {}'.format(yearradio),
                            zoom = 6.3,
                            center = {"lat": 32.662, "lon": -83.438},
                            opacity = 0.9,
                            height = 850,
                            labels = {'reppercent': 'Percentage of Republican Votes'}
                          )

    # Histogram of different vote types (mail, early, etc.)
    fig1 = px.histogram( 
            dff[dff['mode'] != 'provisional'], # Filtered dataframe, no provisional votes
             x="party", # by party
             y="votes",
             color="party",
             facet_col="mode", # seperate by mode of voting
             histfunc = 'sum', # sum of votecount
             title = 'Results in District {} in {} by Voting Type'.format(districtdd, yearradio) if preshouseradio == 'house' else 'Results in Presidential Election in {} by Voting Type'.format(yearradio),
             color_discrete_map = {"republican": "#E81B23", "democratic": "#0015BC", 'libertarian': '#FFD100'}, # matching colors
             category_orders= {'mode': ['election day', 'mail', 'early'], 'party': ['republican', 'democratic']},
             height = 600,
             labels={
                "party": "Party",
                "votes": "Vote Total",
                "mode": 'Voting Type'
                 }
             )

    fig1.update_layout(showlegend = False)
    
    # Pie chart of results
    fig2 = px.pie( 
        dff,
        values = 'votes',
        names = 'party',
        title = 'Results in District {} in {}'.format(districtdd, yearradio) if preshouseradio == 'house' else 'Results in Presidential Election in {}'.format(yearradio),
        color = 'party',
        color_discrete_map = {"republican": "#E81B23", "democratic": "#0015BC", 'libertarian': '#FFD100'}, # matching colors
        height = 850,
        labels={
                "republican": "Republican Candidate",
                "democratic": "Democratic Candidate",
                "libertarian": 'Libertarian Candidate'
                 }
    )

    # Line chart
    fig3 = px.line(
        dfff[dfff['district'] == districtdd],
        x = 'year',
        y = 'reppercent',
        title = 'Results in District {} Over Time'.format(districtdd) if preshouseradio == 'house' else 'Results in Presidential Election Over Time',
        height = 600,
        labels={
                "year": "Year",
                "reppercent": "Percentage of Republican Votes (decimal)"
                 }
        )

    fig3.update_layout(
        xaxis=dict(
            showline=False,
            showgrid=False,
            showticklabels=False,
            range = [2016, 2020]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=True,
            range = [0, 1]
        )
    )

    return fig4, fig2, fig1, fig3

# Run app
if __name__ == '__main__':
    app.run_server(debug = True, port = 8049, jupyter_mode = 'tab')