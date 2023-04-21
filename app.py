import json
import io
import os
import urllib.parse
import pandas as pd
import plotly.express as px
import xlsxwriter
import flask
from flask import Flask
import dash
from dash import Dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html

from dash.dependencies import ClientsideFunction
import shapely.geometry
from shapely.geometry import Polygon
from shapely.geometry import shape
import numpy as np



from gevent import pywsgi




with open("awp_map_new.json", "r") as f:
    countries = json.load(f)

df = pd.read_csv("awp_csv_new.csv", dtype={"country_name": str})
#print(df.dtypes)

# Copy 'country_name' to 'Country' variable
df['Country'] = df['country_name']

with open("overlay_borders.json", "r") as f:
    overlay_borders = json.load(f)

multilines = [shape(line["geometry"]) for line in overlay_borders["features"]]




# Build your components
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX, "https://codepen.io/chriddyp/pen/bWLwgP.css", "/assets/custom.css"])


app.title = "WaPOR4Awp: Agricultural Water Productivity Dashboard"

mytitle = dcc.Markdown(children='')
map_graph = dcc.Graph(id='map-graph', figure={}, style={'height': '100%', 'width': '100%'})

line_chart = dcc.Graph(id='line-chart', figure={}, style={'height': '100%', 'width': '100%'})

download_button = html.A('Download Data', id='download-button', download='line_chart_data.xlsx', href='', target='_blank')
dropdown = dcc.Dropdown(
    id='dropdown',
    options=[{'label': 'Agricultural water productivity (Awp) [USD/m3]', 'value': 'Awp', 'title': 'Agricultural water productivity of irrigated cropland'},
             {'label': 'Change in agricultural water productivity (cAwp) [%]', 'value': 'cAwp', 'title': 'Year-to-year percentage change in agricultural water productivity'},
             {'label': 'Trend in agricultural water productivity (tAwp) [%]', 'value': 'tAwp', 'title': 'Percentage change in agricultural water productivity against baseline 2015'},               
             {'label': 'Total water consumed by irrigated cropland (Vetb) [Mm3/year]', 'value': 'VEtb', 'title': 'Total water consumed by irrigated cropland'},
             {'label': 'Gross value added by irrigated cropland (GVAa) [USD/year]', 'value': 'GVAa', 'title': 'Gross value added by irrigated cropland'},
             {'label': 'Area of irrigated crop land (Airr) [km2]', 'value': 'Airr', 'title': 'Area of irrigated crop land'}],

    value='tAwp',  # initial value displayed when page first loads
    clearable=False
)

# Define the layout
app.layout = dbc.Container([
    
    # Header
    dbc.Row([
        dbc.Col(html.Img(src=app.get_asset_url('header.png'), height="40px", width="100%")),
    ], justify='center', align='center', className='header'),

    dbc.Row([
        dbc.Col(html.Img(src=app.get_asset_url('logo.png'), height="70px"), width=4),
        dbc.Col(html.H2('WaPOR4Awp - Agricultural Water Productivity', style={'text-transform': 'none'}), width=8),
    ], justify='left', align='left', className='header'),


    # Main content
    dbc.Row([
        dbc.Col(dropdown, width=8, className='text-center'),  
        dbc.Col(html.P(['WaPOR4Awp computes and visualizes agricultural water productivity data for countries in Africa and the Near-East using ',
                html.A('WaPOR data', href='https://wapor.apps.fao.org/catalog/WAPOR_2/1', target='_blank'),
                ' ',
                html.P(['and methods for computing the values displayed in the dashboard are explained ',
                    html.A('HERE', href='/assets/WaPOR4Awp_methodology.pdf', target='_blank')]),
            ]), width=4, className='address-text'),    

           
                  
        ], justify='center', align='center', className='footer'),



    dbc.Row([
        #dbc.Row(html.Br(), className='empty_row'),
        dbc.Col(map_graph, width=8, className='text-center'), 
        
        dbc.Col(line_chart, width=4, className='text-center'),
        
        dbc.Row(html.Br(), className='empty_row'),
        
        dbc.Row([            
            dbc.Col(" ", width=8, className='text-center'),            
            dbc.Col(download_button, width=4, className='text-center'),
            dbc.Row(html.Br(), className='empty_row'),
        ]),
    dbc.Row([   
            dbc.Col(" ", width=8, className='text-center'), 
            dbc.Col(html.P(['WaPOR4Awp supports the monitoring of ',
                html.A('SDG indicator 6.4.1', href='https://www.fao.org/3/cb8768en/cb8768en.pdf', target='_blank'),
                ' - Change in Water Use Efficiency (CWUE). It offers an alternative approach to estimate water use efficiency in the form of water productivity. ',
                #html.Br(),
                html.A('Read more on SDG 6.4.1 methodology', href='https://www.fao.org/documents/card/en/c/cb8768en', target='_blank'),
               ]), width=4, className='address-text'),
            
        ]),
        dbc.Row(html.Br(), className='empty_row'),
        #dbc.Row(html.Br(), className='empty_row'),
             
    ]),   


    # Introduction text
    dbc.Row([
        dbc.Row(html.Br(), className='empty_row') for i in range(5)], align='left', className='intro_p'),
        dbc.Col(html.P(''), width=1, className='empty_space'),


    # Contact us footer
    dbc.Row([
        dbc.Col(html.A('Contact Us', href='mailto:wateraccounting_project@un-ihe.org'), width=12, className='address-text'),
    ], align='right', className='main-content2'),

    # Footer
    dbc.Row([
        dbc.Col(html.Img(src=app.get_asset_url('footer.png'), height="50px", width="100%")),
    ], justify='center', align='center', className='header'),

], fluid=True)#fluid=True, style={'backgroundColor': '#AAD3df'})





# Define the Mapbox access token
mapbox_access_token = "your_mapbox_access_token"


#Find the index of the frame corresponding to 2021 

year_index = df[df['year'] == 2021].index[0]
#year_index = df['year'].values.tolist().index(2021)


# Define the callback functions
@app.callback(
    [Output('map-graph', 'figure'), Output('line-chart', 'figure'), Output("download-button", "href")],
    [Input('map-graph', 'clickData'), Input('dropdown', 'value'), Input('map-graph', 'relayoutData'), Input('download-button', 'n_clicks')],
    [State('line-chart', 'figure'), State('map-graph', 'figure')]
)
def update_graph(click_data, dropdown_value, relayout_data, download_clicks, line_chart_figure, map_figure_state):


    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'].split('.')[0]

       
    if triggered == 'map-graph' and 'relayoutData' in triggered:
        if "dragmode" in relayout_data or "xaxis.range[0]" in relayout_data or "yaxis.range[0]" in relayout_data:
            raise PreventUpdate
            
    column_names = ['Awp', 'cAwp', 'tAwp', 'VEtb', 'GVAa', 'Airr']
    units = {'Awp': 'USD/m³', 'cAwp': '%', 'tAwp': '%', 'VEtb': 'm³', 'GVAa': 'USD', 'Airr': 'km²'}
    filtered_df = df.copy()

    color_column = dropdown_value  # Set the initial column for the color
    colorbar_title = f"{dropdown_value} ({units[dropdown_value]})"
    
    href = ""
    
 
    
    
    if click_data is not None:
        # Check if the 'location' key is present in the click_data dictionary
        if "location" not in click_data["points"][0]:
            raise PreventUpdate
        selected_iso = click_data['points'][0]['location']
        filtered_df = df[df['ISO-3'] == selected_iso]
       
    if dropdown_value is not None:
        color_column = dropdown_value
    else:
        color_column = column_names[0]
    map_fig = px.choropleth_mapbox(data_frame=df, geojson=countries, locations='ISO-3',
                                   featureidkey='properties.ISO-3',
                                   color_continuous_scale="GnBu", 
                                   height=680, 
                                   width=None,
                                   color=color_column,
                                   animation_frame='year',
                                   animation_group='year',
                                   hover_data={'Country': True, dropdown_value: ':.2f', 'year': False, 'ISO-3': False},
                                   mapbox_style="open-street-map",
                                   center={"lat": 2.7832, "lon": 26.5085},
                                   zoom=2.0,
                                   )

    # Add the multilinestring borders as a new trace
    border_lats, border_lons = [], []
    # Iterate through each MultiLineString
    for multiline in multilines:
        # Iterate through each LineString in the MultiLineString
        for linestring in multiline.geoms:
            # Extract the coordinates for each point in the LineString
            line_coords = list(linestring.coords)
            # Add a Scattermapbox trace for each LineString
            map_fig.add_trace(
                go.Scattermapbox(
                    lat=[coord[1] for coord in line_coords],
                    lon=[coord[0] for coord in line_coords],
                    mode='lines',
                    line=dict(width=0.5, color='red'),
                    showlegend=False,
                    hoverinfo='none'
                )
            )

    
    border_trace = go.Scattermapbox(
        lat=border_lats,
        lon=border_lons,
        mode="lines",
        line=dict(width=0.5, color="red"),
        showlegend=False,
        hoverinfo="none"
    )
    
    map_fig.add_trace(border_trace)



    # if relayout_data and 'mapbox.zoom' in relayout_data:
        # current_zoom = relayout_data['mapbox.zoom']
    # else:
        # current_zoom = 2.0

    # map_fig.update_layout(
        # mapbox_zoom=current_zoom,
        # mapbox_center={"lat": 2.7832, "lon": 26.5085},
        # updatemenus=[
            # dict(
                # type="buttons",
                # buttons=[
                    # dict(
                        # label="Zoom In",
                        # method="relayout",
                        # args=[{"mapbox.zoom": current_zoom + 1}],
                    # ),
                    # dict(
                        # label="Zoom Out",
                        # method="relayout",
                        # args=[{"mapbox.zoom": current_zoom - 1}],
                    # ),
                # ],
                # direction="left",
                # pad={"r": 10, "t": 10},
                # showactive=True,
                # x=0.1,
                # xanchor="left",
                # y=1,
                # yanchor="top",
            # ),
        # ],
    # )

    #Add the units to the color bar
    map_fig.update_layout(coloraxis_colorbar_title=colorbar_title)    
    
    map_fig.update_layout(autosize=True, margin=dict(l=30, r=30, t=30, b=30))
    


    if relayout_data and 'mapbox.zoom' in relayout_data:
        current_zoom = relayout_data['mapbox.zoom']
    else:
        current_zoom = 2.0

    map_fig.update_layout(
        mapbox_zoom=current_zoom,
        mapbox_center={"lat": 2.7832, "lon": 26.5085},
    )

    



    #map_fig.layout.updatemenus[0].buttons[0].args[0]['frame'] = {'duration': 1080}
    map_fig.update(frames=None)

    map_fig.layout.sliders[0].active = year_index


    # Update map color based on the active slider index
    current_frame = map_fig.frames[year_index]
    for trace, z_data in zip(map_fig.data, [current_frame.data[0]['z']]):
        trace.update(z=z_data)


    
    # Update frames to None after setting the active slider index
    map_fig.update(frames=None)



    if click_data is not None:
        line_data = filtered_df.melt(id_vars=['year', 'country_name', 'ISO-3'], value_vars=column_names,
                                     var_name='variable', value_name='value')
        line_fig = px.line(line_data, x='year', y='value', color='variable', line_group='country_name',
                           labels={"variable": click_data['points'][0]['customdata'][0]},
                           template="simple_white",
                           )
        for trace in line_fig.data:
            trace.update(mode='lines+markers')
            # Set trace visibility based on the selected dropdown value
            trace.visible = 'legendonly' if trace.legendgroup != color_column else True

        # Apply custom tickformat for different columns
        for column in column_names:
            if column == 'Awp':
                line_fig.update_yaxes(tickformat=".1e", exponentformat='e', selector=dict(variable=column))
            elif column in ['VEtb', 'GVAa', 'Airr']:
                line_fig.update_yaxes(tickformat=",.0f", selector=dict(variable=column))
            else:
                line_fig.update_yaxes(tickformat=",.2f", selector=dict(variable=column))

        line_fig.update_layout(autosize=True, margin=dict(l=50, r=50, t=50, b=50))
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
        href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8,' + urllib.parse.quote(
            output.getvalue())

    return [map_fig, line_fig, href or None]





# Run app
if __name__ == '__main__':
    app.run_server(debug=True, port=8056)
