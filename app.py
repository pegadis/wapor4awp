import json
import io
import urllib.parse
import pandas as pd
import plotly.express as px
import xlsxwriter
from gevent import pywsgi

from dash import html

import dash
import dash_bootstrap_components as dbc

from dash import dcc

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

with open("awp_map_new.json", "r") as f:
    countries = json.load(f)

df = pd.read_csv("awp_csv_new.csv", dtype={"country_name": str})

# Build your components

#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX, "https://codepen.io/chriddyp/pen/bWLwgP.css"])

app = dash.Dash(__name__, server=pywsgi.WSGIServer(('0.0.0.0', 8056)), external_stylesheets=[dbc.themes.LUX, "https://codepen.io/chriddyp/pen/bWLwgP.css"])
server = app.server

mytitle = dcc.Markdown(children='#Awp')
map_graph = dcc.Graph(id='map-graph', figure={})
line_chart = dcc.Graph(id='line-chart', figure={})

download_button = html.A('Download Data', id='download-button', download='line_chart_data.xlsx', href='', target='_blank')
dropdown = dcc.Dropdown(
    id='dropdown',
    options=[{'label': 'Awp', 'value': 'Awp'},
             {'label': 'PCP', 'value': 'PCP'},
             {'label': 'PE', 'value': 'PE'},
             {'label': 'AETI', 'value': 'AETI'}],

    value='Awp',  # initial value displayed when page first loads
    clearable=False
)

# Customize your own Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src=app.get_asset_url('logo.png'), height="70px"), width=2),
        dbc.Col(html.H2('WaPOR4AWP: Agricultural Water Use Efficiency'), width=8),
    ], justify='center', align='center', className='header'),
    dbc.Row([
        dbc.Col([map_graph], width=9),
        dbc.Col([line_chart, download_button], width=3)
    ], align='center', className='content'),
    
    dbc.Row([
        dbc.Col([dropdown], width=6)
    ], justify='center', align='center', className='footer'),
    
    dbc.Row([ 
        dbc.Col(html.Img(src=app.get_asset_url('logo.png'), height="70px"), width=2),
        dbc.Col(html.H2(''), width=8),
    ], justify='center', align='center', className='header'),
    
    dbc.Row([    
        dbc.Col(html.P('Westvest 7, 2611 AX Delft'), width=8, style={'text-align': 'right'}),
        dbc.Col(html.P('Phone: +3115 215 1715'), width=2, style={'text-align': 'left'}),       
    ], justify='around', align='right', className='footer'),
], fluid=True)


@app.callback(
    [Output('map-graph', 'figure'), Output('line-chart', 'figure'), Output("download-button", "href")],
    [Input('map-graph', 'clickData'), Input('dropdown', 'value'), Input('download-button', 'n_clicks')],
    [State('line-chart', 'figure')]
)
def update_graph(click_data, dropdown_value, download_clicks, line_chart_figure):
    column_names = ['Awp', 'PCP', 'PE', 'AETI']
    filtered_df = df.copy()
    href = ""
    if click_data is not None:
        selected_iso = click_data['points'][0]['location']
        filtered_df = df[df['ISO-3'] == selected_iso]
    if dropdown_value is not None:
        color_column = dropdown_value
    else:
        color_column = column_names[0]
    map_fig = px.choropleth(data_frame=df, geojson=countries, locations='ISO-3',
                            featureidkey='properties.ISO-3',
                            locationmode="ISO-3",
                            color_continuous_scale="Darkmint",
                            scope="world",
                            height=600,
                            color=color_column,
                            animation_frame='year',
                            hover_data={'country_name':True})
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
    
    


# Run app
if __name__ == '__main__':
    app.run_server(debug=True, port=8056)