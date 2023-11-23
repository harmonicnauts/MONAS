# Import the libraries
import json
from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import pandas as pd
import dash_leaflet as dl
import geopandas
import dash_leaflet.express as dlx
import dash_bootstrap_components as dbc
from dash_extensions.javascript import assign
from xgboost import XGBRegressor
import pickle



# Load script 
colorscale = ['red', 'yellow', 'green', 'blue', 'purple']  # rainbow
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"  # js lib used for colors



# Load xgb
model_xgb = XGBRegressor()



# Load dataframes
df_temp = pd.read_csv('../../Data/data_fix_temp.txt') # Temp Dataframe
df_wmoid = pd.read_excel('../../Data/daftar_wmoid.xlsx') # UPT Dataframe
df_wmoid = df_wmoid.rename(columns={'WMOID': 'lokasi'})
df_wmoid = df_wmoid[['lokasi', 'Nama UPT']]

# Load ML Models
# etr = pickle.load(open('weather_extra_trees_regressor.pkl', 'rb'))
model_xgb.load_model('xgb_tuned.json')



# Make merged dataframe for mapping
df_map = df_wmoid.merge(df_temp, on='lokasi')
df_map = df_map[['lokasi', 'Nama UPT', 'LON', 'LAT']].drop_duplicates()



# Min and Max temp for point colors
vmin = 0
vmax = 100

BMKG_LOGO = "https://cdn.bmkg.go.id/Web/Logo-BMKG-new.png"



# Function for adding some properties to all the points in Leaflet Map
on_each_feature = assign(
    """function(feature, layer, context){
        if(feature.properties.lokasi){
            layer.bindTooltip(`${feature['properties']['Nama UPT']} \nKode:${feature['properties']['lokasi']} \n Koord : (${feature['properties']['LAT']},${feature['properties']['LON']})`)
        }
    }
    """)



# Function for assignng circlemarkers to each point
point_to_layer = assign(
    """
    function(feature, latlng, context){
        //console.log(context.hideout);
        //const {min, max, colorscale, circleOptions, colorProp} = context.hideout;
        //const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
        //circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop
        return L.circleMarker(latlng);  // render a simple circle marker
    }
    """)



# Make geopandas geometry for coordinates
geometry = geopandas.points_from_xy(df_map.LON, df_map.LAT)
upt_gpd = geopandas.GeoDataFrame(df_map, geometry=geometry)
upt_gpd = upt_gpd.reset_index(drop=True)

geojson = json.loads(upt_gpd.to_json())
geobuf = dlx.geojson_to_geobuf(geojson)
upt = dl.GeoJSON(
    data=geobuf,
    id='geojson',
    format='geobuf',
    onEachFeature=on_each_feature,  # add (custom) tooltip
    pointToLayer=point_to_layer,
    hideout=dict(colorProp='t_obs', 
                 circleOptions=dict(fillOpacity=1, 
                                    stroke=False, 
                                    radius=2,
                                    ),
                                    min=vmin, 
                                    max=vmax
                                    )
)



# Sort the data by Date
df_temp_sorted = df_temp.set_index('Date')
df_temp_sorted = df_temp_sorted.sort_index()



# Make dataframe for showing min, max, avg temperature
grouped = df_temp_sorted.groupby('lokasi')['t_obs'].agg(['max', 'mean', 'min']).round(1)
df_wmoid_merged = df_wmoid.merge(grouped, left_on='lokasi', right_index=True)
df_wmoid_merged = df_wmoid_merged.rename(columns={'mean': 'average', 'max': 'max', 'min': 'min'})



# Begin
app = Dash(__name__)

app.layout = html.Div([
    html.Div([  # Wrap the map and header in a div for layout
        
        dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=BMKG_LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("BMKG", className="ms-2")),
                        html.H1(children='MONAS Dashboard')
                    ],
                    align="center",
                    className="g-0",
                ),
                href="https://plotly.com",
                style={
                    "textDecoration": "none",
                    "display" : "flex",
                    "align-content": "center",
                    "justify-content" : "center",
                    "flex-direction" : "row"
                    },
            ),
        ]
    ),
        html.Div([ # Div for temperature metrics

        html.Div([
            html.H2(children='Min Temp', 
                    style={'textAlign': 'center'}),
            html.H3(id='min-temp', 
                    children='0',
                    style={'textAlign': 'center'}),
        ]),

        html.Div([
            html.H2(children='Avg Temp', 
                style={'textAlign': 'center'}),
            html.H3(id='avg-temp', 
                    children='0',
                    style={'textAlign': 'center'}),
        ]),

        html.Div([
            html.H2(children='Max Temp', 
                style={'textAlign': 'center'}),
            html.H3(id='max-temp', 
                    children='0',
                    style={'textAlign': 'center'}),
        ]),
        ], 
        style={
            'display' : 'grid',
            'grid-column': 'auto auto',
            'grid-auto-flow': 'column'

        }),
        html.Div([ # Div for map, metric, and graph
        
        dl.Map(
            [dl.TileLayer(), 
            upt ,
            ],
            center=[-2.058210136999589, 116.78386542384145],
            zoom=5,
            markerZoomAnimation = True,
            style={
                'height': '40vh', 
                'width' : '40vw'},
        ),
        # html.Div(id="graph-per-loc"),
        dcc.Graph(id='graph_per_loc'),
        ], 
        style={
            'display': 'grid', 
            'grid-column': 'auto auto',
            'grid-auto-flow': 'column'
        }),
        html.Div([# Div for other details such as comparison graph, data tables, and other metrics 
            dcc.Dropdown(
                    options=[{'label': loc, 
                            'value': loc} for loc in df_temp['lokasi'].unique()],
                    value=[96001],
                    id='dropdown-selection',
                    multi=True,
                ),
            html.Div([ 
                dcc.Graph(id='graph-content', 
                style={
                    'display': 'flex', 
                    'align-items': 'center',
                    'justify-content': 'center',
                    'width': '100vh',
                }),
                dash_table.DataTable(
                    data=df_wmoid_merged.to_dict('records'), 
                    page_size=10),
            ], style={
                'display': 'grid', 
                'grid-column': 'auto auto',
                'grid-auto-flow': 'column'
                })        
            ], style= {
                'display': 'grid', 
                'grid-column': 'auto auto',
                'grid-auto-flow': 'row'
            }),
    
    ], 
    style={
        'display': 'grid', 
        'grid-column': 'auto auto',
        'grid-auto-flow': 'row'
        }
        ),  # Display elements side by side
])



# Callback function for changing line graph based on 'lokasi'.
@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    lokasi_length = len(value)
    dff = df_temp_sorted[df_temp_sorted['lokasi'].isin(value)][['t_obs', 'lokasi']]
    print(value)
    print(df_temp_sorted)
    print(dff)
    print(df_wmoid_merged)
    return px.line(dff.tail(lokasi_length * 17), y='t_obs', title='Temperature Observations over Time', color='lokasi', markers=True, line_shape='spline')



# Callback function for changing 
@callback(
        Output("min-temp", "children"),
        Output("avg-temp", "children"),
        Output("max-temp", "children"),
        Output("graph_per_loc", "figure"), 
        Input("geojson", "clickData"),
        prevent_initial_call=True
        )
def upt_click(feature):
    print(feature)    
    if feature is not None:
        wmoid_lokasi = df_wmoid_merged['lokasi']
        prop_lokasi = feature['properties']['lokasi']
        nama_upt = df_wmoid_merged[wmoid_lokasi == prop_lokasi]['Nama UPT'].values[0]

        features_to_display = ['t_obs', 'lokasi']

        dff_one_loc = df_temp_sorted[df_temp_sorted['lokasi'] == prop_lokasi][features_to_display]
        
        figure = px.line(dff_one_loc.tail(17), y='t_obs', title=f'Temperatures in UPT {nama_upt}', color='lokasi', markers=True, line_shape='spline')

        min_temp = df_wmoid_merged[wmoid_lokasi == prop_lokasi]['min']
        avg_temp = df_wmoid_merged[wmoid_lokasi == prop_lokasi]['average']
        max_temp = df_wmoid_merged[wmoid_lokasi == prop_lokasi]['max']

        return min_temp, avg_temp, max_temp, figure
    else:
        figure =  px.line(dff_one_loc.tail(17), y='t_obs', title=f'Temperatures in UPT x', color='lokasi', markers=True, line_shape='spline')
        dff_one_loc = df_temp_sorted[df_temp_sorted['lokasi'] == 96001][['t_obs', 'lokasi']]
        return figure



if __name__ == '__main__':
    app.run_server(debug=True)
