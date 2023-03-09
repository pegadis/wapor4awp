import json
import io
import urllib.parse
import pandas as pd
import plotly.express as px
import xlsxwriter
from gevent import pywsgi
import flask
from flask import Flask
from dash import html
import dash
from dash import Dash
import dash_bootstrap_components as dbc

from dash import dcc

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

with open("awp_map_new.json", "r") as f:
    countries = json.load(f)

df = pd.read_csv("awp_csv_new.csv", dtype={"country_name": str})

# Build your components
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX, "https://codepen.io/chriddyp/pen/bWLwgP.css"])
#server = Flask(__name__)
#app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.LUX, "https://codepen.io/chriddyp/pen/bWLwgP.css"])

mytitle = dcc.Markdown(children='#Awp')
map_graph = dcc.Graph(id='map-graph', figure={})
line_chart = dcc.Graph(id='line-chart', figure={})

download_button = html.A('Download Data', id='download-button', download='line_chart_data.xlsx', href='', target='_blank')
dropdown = dcc.Dropdown(
    id='dropdown',
    options=[{'label': 'Awp', 'value': 'Awp'},
             {'label': 'cAwp', 'value': 'cAwp'},
             {'label': 'tAwp', 'value': 'tAwp'},
             {'label': 'PCP', 'value': 'PCP'},
             {'label': 'PE', 'value': 'PE'},
             {'label': 'AETI', 'value': 'AETI'}],

    value='Awp',  # initial value displayed when page first loads
    clearable=False
)

# Customize your own Layout
app.layout = dbc.Container([

    dbc.Row([html.Img(src=app.get_asset_url('header.png'), height="50px"),
            ], justify='left', align='left', className='header'),
    dbc.Row([
         dbc.Col(html.Img(src=app.get_asset_url('logo.png'), height="50px"), width=2),         
         #dbc.Col(html.H2('WaPOR4Awp - Agricultural Water Productivity', style={'text-transform': 'none'}), width=8),
            ], justify='left', align='left', className='header'),        
            
    
    dbc.Row([
        dbc.Col(html.P(''), width=1, className='empty_space'),
        dbc.Col(html.P('WaPOR4Awp is a dashboard that computes and visualizes agricultural water productivity data for various countries in Africa and the Near-East. It supports the monitoring of SDG indicator 6.4.1 - Change in Water Use Efficiency (CWUE) using remote sensing data. The dashboard offers an alternative approach to estimate water productivity using the FAO WaPOR database.'), width=16, className='address-text'),
    ], align='left', className='intro_p'),
    
    dbc.Row([
        
        dbc.Col([

            dbc.Row([
                dbc.Col([map_graph], width=9),
                dbc.Col([line_chart, download_button], width=3)
            ], align='left', className='content'),

            dbc.Row([
                dbc.Col([dropdown], width=6)
            ], justify='center', align='center', className='footer'),            
            
        ], width=18)
    ], align='left', className='main-content'),
    
   
    dbc.Row([
        dbc.Col(html.A('Contact Us', href='mailto:wateraccounting_project@un-ihe.org'), width=0.1, className='address-text'),
    ], align='right', className='main-content2'),

    dbc.Row([html.Img(src=app.get_asset_url('footer.png'), height="70px"),
            ], justify='left', align='left', className='header'),
], fluid=True)

# Define the Mapbox access token
mapbox_access_token = "your_mapbox_access_token"
@app.callback(
    [Output('map-graph', 'figure'), Output('line-chart', 'figure'), Output("download-button", "href")],
    [Input('map-graph', 'clickData'), Input('dropdown', 'value'), Input('download-button', 'n_clicks')],
    [State('line-chart', 'figure')]
)
def update_graph(click_data, dropdown_value, download_clicks, line_chart_figure):
    column_names = ['Awp', 'cAwp','tAwp','PCP', 'PE', 'AETI']
    filtered_df = df.copy()
    href = ""
    if click_data is not None:
        selected_iso = click_data['points'][0]['location']
        filtered_df = df[df['ISO-3'] == selected_iso]
    if dropdown_value is not None:
        color_column = dropdown_value
    else:
        color_column = column_names[0]
    map_fig = px.choropleth_mapbox(data_frame=df, geojson=countries, locations='ISO-3',
                                featureidkey='properties.ISO-3',
                                color_continuous_scale="Darkmint",                            
                                height=600,
                                width=1200,
                                color=color_column,
                                animation_frame='year',
                                hover_data={'country_name':True},
                                mapbox_style="open-street-map",
                                center={"lat": 2.7832, "lon": 26.5085},
                                zoom=1.5,
                                )
    map_fig.update_layout(legend=dict(
        yanchor="bottom",
        y=1.0,
        xanchor="left",
        x=0.01
    ))


    if click_data is not None:
        line_fig = px.scatter(filtered_df, x='year', y=column_names, color='country_name',
                           color_discrete_sequence=px.colors.qualitative.Plotly,
                           labels={"variable": click_data['points'][0]['customdata'][0], "value": "Value", "year": "Year", "country_name": "Country"},
                           template="simple_white",
                           )
        line_fig.add_traces(px.line(filtered_df, x='year', y=column_names, line_group='country_name',
                                 color_discrete_sequence=px.colors.qualitative.Plotly,
                                 labels={"variable": click_data['points'][0]['customdata'][0], "value": "Value", "year": "Year", "country_name": "Country"},
                                 ).data)
    else:
        line_fig = line_chart_figure     
        


    # Check if Download Data button was clicked and filtered_df is not empty
    if download_clicks and not filtered_df.empty:
        # Generate downloadable Excel file
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        filtered_df.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.save()
        output.seek(0)
        href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8,' + urllib.parse.quote(output.getvalue())

    return [map_fig, line_fig, href or None]



	
	
if __name__ == '__main__':
    app.run_server(debug=True, port=8056)