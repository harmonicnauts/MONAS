from dash import Dash, html, dcc, callback, Output, Input, dash_table
import dash_core_components as dcc
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from callbacks import *

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"  # js lib used for colors

colorbar = dl.Colorbar(id = 'map-colorbar',colorscale=temp_colorscale, width=20, height=150, min=temp_min, max=temp_max, unit='°C')


BMKG_LOGO = "https://cdn.bmkg.go.id/Web/Logo-BMKG-new.png"

unique_dates = data_table_lokasi['Date'].unique()
baselayers = [dl.BaseLayer(dl.LayerGroup(), name=date, checked=(index == 0)) for index, date in enumerate(unique_dates)]

# Begin
app = Dash(__name__, external_scripts=[chroma],  external_stylesheets=external_stylesheets, prevent_initial_callbacks=True)

app.title = 'MONAS Dashboard' 

app.layout = html.Div([
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                [dbc.Row(
                    [
                        dbc.Col(html.Img(src=BMKG_LOGO, height="55px")),
                        dbc.Col(dbc.NavbarBrand(className="ms-2")),
                        
                    ],
                    align="center",
                    className="g-0 d-flex flex-column align-items-center justify m-2",
                ),
                html.H1(children=app.title),
                ],
                href="#",
                style={
                    "textDecoration": "none",
                    "display" : "flex",
                    "align-content": "center",
                    "justify-content" : "center",
                    "flex-direction" : "row",
                    },
            ),
        ]
    ),

    # dcc.Dropdown(id='model-list',
    #             options=[
    #                 {'label': i, 'value': i} for i in files
    #             ],
    #             multi=True
    # ),

    html.Div([ # Wrap the map and header in a div for layout
        html.Div([
            html.Div([
                dcc.RangeSlider(
                    id='graph-metric',
                    min=0,
                    max=40,
                    value=[0,0],
                    step=None,
                    vertical=False,
                    disabled=True,
                ),
                # html.H1(children="TEST", id="test_h1"),
                dl.Map(
                    [
                        dl.TileLayer(), 
                        dl.ScaleControl(position="bottomleft"),
                        dl.FullScreenControl(),
                        dl.LayersControl(
                            baselayers  ,
                            id='baselayer-layers-control',
                            collapsed=False
                        ),
                        upt,
                        colorbar,
                    ],
                    center=[-2.058210136999589, 116.78386542384145],
                    markerZoomAnimation = True,
                    id = 'dash-leaflet-map',
                    style={
                        'height': '80vh', 
                        'width' : '1000px',
                        'margin' : '4px',
                        }
                    ),
            ]),
            html.Div([# Div for map, metric, and graph
                dcc.Tabs(
                    id="graph-tabs",
                    value='temp-tab',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                    children=[
                        dcc.Tab(
                            label='Temperature',
                            id='temp-tab',
                            disabled=True,
                            value='temp-tab',
                            className='custom-tab',
                            selected_className='custom-tab--selected'
                        ),
                        dcc.Tab(
                            label='Humidity',
                            id='humid-tab',
                            disabled=True,
                            value='humid-tab',
                            className='custom-tab',
                            selected_className='custom-tab--selected'
                        ),
                        dcc.Tab(
                            label='Precipitation',
                            id='prec-tab',
                            disabled=True,
                            value='prec-tab',
                            className='custom-tab',
                            selected_className='custom-tab--selected'
                        ),
                ]),
                dcc.Loading(
                    dcc.Graph(
                        id='graph_per_loc',
                        figure={
                            'layout' : {
                                "xaxis": {
                                "visible": False
                                },
                                "yaxis": {
                                    "visible": False
                                },
                                "annotations": [
                                    {
                                        "text": "Click on one of the Station in the map to view graph.",
                                        "xref": "paper",
                                        "yref": "paper",
                                        "showarrow": False,
                                        "font": {
                                            "size": 28
                                        }
                                    }
                                ]
                            }
                        },
                        style={
                        'height': '80vh',
                        }
                    ),
                )], 
                style={
                    'display': 'grid', 
                    'grid-column': 'auto auto',
                    'grid-auto-flow': 'row'
                }
            )],
        style={
                'display': 'grid', 
                'grid-column': 'auto auto',
                'grid-auto-flow': 'column'
        }),
        # html.Div([# Div for other details such as comparison graph, data tables, and other metrics 
        #     dash_table.DataTable(
        #         data=data_table_lokasi.to_dict('records'), 
        #         page_size=10)       
        #     ], 
        #     style= {
        #         'display': 'grid', 
        #         'margin' : '10px',
        #         'grid-column': 'auto auto',
        #         'grid-auto-flow': 'row'
        #     }
        # ),
    ])
])
  