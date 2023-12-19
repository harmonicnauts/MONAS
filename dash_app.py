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
# import joblib
import os

# List of models
pathway = './models'

files = [f for f in os.listdir(pathway)]



# Load dataframes
df_wmoid = pd.read_excel('./Data/daftar_wmoid.xlsx') # UPT Dataframe
ina_nwp_input = pd.read_csv('./Data/MONAS-input_nwp_compile.csv') # Feature to predict from INA-NWP
df_wmoid = df_wmoid.rename(columns={'WMOID': 'lokasi'}) # WMOID dataframe preproceses
df_wmoid = df_wmoid[['lokasi', 'Nama UPT']]



# Make merged dataframe for mapping
df_map = df_wmoid.merge(ina_nwp_input, on='lokasi')
df_map = df_map[['lokasi', 'Nama UPT', 'LON', 'LAT']].drop_duplicates()



# INA-NWP input preprocess
ina_nwp_input_filtered = ina_nwp_input.drop(columns=['Date', 'LAT', 'LON'])  
ina_nwp_input_filtered = ina_nwp_input_filtered.rename(
    columns={
        'suhu2m(degC)' : 'suhu2m.degC.',
        'dew2m(degC)' : 'dew2m.degC.',
        'rh2m(%)' : 'rh2m...',
        'wspeed(m/s)' : 'wspeed.m.s.',
        'wdir(deg)' : 'wdir.deg.',
        'lcloud(%)' : 'lcloud...',
        'mcloud(%)' : 'mcloud...' ,
        'hcloud(%)' : 'hcloud...',
        'surpre(Pa)' : 'surpre.Pa.' ,
        'clmix(kg/kg)' : 'clmix.kg.kg.' ,
        'wamix(kg/kg)' : 'wamix.kg.kg.' ,
        'outlr(W/m2)' : 'outlr.W.m2.' ,
        'pblh(m)' : 'pblh.m.',
        'lifcl(m)' : 'lifcl.m.' ,
        'cape(j/kg)' : 'cape.j.kg.' ,
        'mdbz' : 'mdbz' ,
        't950(degC)' : 't950.degC.' ,
        'rh950(%)' : 'rh950...',
        'ws950(m/s)' : 'ws950.m.s.' ,
        'wd950(deg)' : 'wd950.deg.' ,
        't800(degC)' : 't800.degC.' ,
        'rh800(%)' : 'rh800...' ,
        'ws800(m/s)' : 'ws800.m.s.',
        'wd800(deg)' : 'wd800.deg.' ,
        't500(degC)' : 't500.degC.' ,
        'rh500(%)' : 'rh500...' ,
        'ws500(m/s)' : 'ws500.m.s.' ,
        'wd500(deg)' : 'wd500.deg.',
})


def predict_xgb(model_path, columns_to_drop, input_df):
    model = XGBRegressor()
    model.load_model(model_path)
    input_data = input_df.drop(columns=columns_to_drop)
    predictions = model.predict(input_data)
    return predictions


# Function for adding some properties to all the points in Leaflet Map
on_each_feature = assign(
    """function(feature, layer, context){
        if(feature.properties.lokasi){
            var tooltipContent = `
            <div 
                style='
                border: 1px solid black;
                border-radius: 5px;
                font-size: 15px;
                padding : 3px;'
                >
                <img style = 'width : 20px' src="https://cdn.bmkg.go.id/Web/Logo-BMKG-new.png"/>
                <strong>${feature['properties']['Nama UPT']}</strong><br>
                <p>Kode: ${feature['properties']['lokasi']}</p>
                <p>Koord: (${feature['properties']['LAT']}, ${feature['properties']['LON']})</p>
                <p>Temperature : <span style = 'color: red'; >${feature['properties']['average temp']}</span> C</p>
                <p>Relative Humidity : <span style = 'color: blue'; >${feature['properties']['average humidity']}</span>%</p>
                <p>Precipitation : <span style = 'color: purple';>${feature['properties']['average precipitation']}</span>mm.</p>
            </div>
                `;
            layer.bindTooltip(tooltipContent, { sticky: true });
        }
    }
    """)



# Function for assignng circlemarkers to each point
point_to_layer = assign(
    """
    function(feature, latlng, context){
        const {min, max, colorscale, circleOptions, colorProp} = context.hideout;
        const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
        circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop
        return L.circleMarker(latlng, circleOptions);  // render a simple circle marker
    }
    """)

def create_data_table(df_wmoid, df_pred, col_name, merge_column='lokasi'):
    grouped_data = df_pred.groupby(merge_column)['prediction'].agg(['max', 'mean', 'min']).astype('float64').round(1)
    data_table_lokasi = df_wmoid.merge(grouped_data, left_on=merge_column, right_index=True)
    
    column_mapping = {
        'mean': f'average {col_name}',
        'max': f'max {col_name}',
        'min': f'min {col_name}'
    }
    
    data_table_lokasi = data_table_lokasi.rename(columns=column_mapping)
    
    return data_table_lokasi


def plot_graph(df_graph, upt_name, nwp_output, graph_type):
    if graph_type in ['Temperature', 'Humidity'] : 
        figure = px.line(
                df_graph, 
                x='Date', 
                y='prediction', 
                title=f'{graph_type} in UPT {upt_name} (UTF)', 
                markers=True, 
                line_shape='spline'
                )
        
        figure.add_scatter(
                x=df_graph['Date'], 
                y=df_graph[nwp_output], 
                mode='lines', 
                name=f'Output {graph_type} 2m INA-NWP',
                line_shape='spline'
                )
        
        figure.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                )
            )
        
        return figure
    elif graph_type in ['Precipitation']:
        figure = px.bar(
                df_graph, 
                x='Date', 
                y=['prediction', 'prec_nwp'], 
                title=f'{graph_type} in UPT {upt_name} (UTF)', 
                )
        return figure



def get_datatable(wmoid_lokasi, prop_lokasi, column):
    return data_table_lokasi[wmoid_lokasi == prop_lokasi][column].iloc[0]



# Callback function for changing 
@callback(
        Output("graph-metric", "value"), # RangeSlider value
        Output("graph-metric", "min"), # RangeSlider minimum value
        Output("graph-metric", "max"), # RangeSlider maximum value
        Output("graph_per_loc", "figure"), # Graph Figure

        Output("geojson", "hideout"), # Hideout property for dash leaflet GeoJSON'

        Output("map-colorbar", "colorscale"), # colorbar's colorscale
        Output("map-colorbar", "min"), # colorbar's minimum value
        Output("map-colorbar", "max"), # colorbar's maximum value
        Output("map-colorbar", "unit"), # colorbar's unit

        Output("low-temp", "children"), #
        Output("avg-temp", "children"),
        Output("high-temp", "children"),

        Input ("geojson", "clickData"), # Marker OnClick Event
        Input ("graph-tabs", "value"), # Value of currently selected tab
        prevent_initial_call=True
        )
def upt_click(feature, tabs_value):
    print(feature)    
    if feature is not None:
        wmoid_lokasi = data_table_lokasi['lokasi']
        prop_lokasi = feature['properties']['lokasi']
        nama_upt = data_table_lokasi[wmoid_lokasi == prop_lokasi]['Nama UPT'].values[0]

        # Column to display on plots
        temp_features_to_display = ['Date', 'suhu2m.degC.', 'prediction', 'lokasi']
        humid_features_to_display = ['Date', 'rh2m...', 'prediction', 'lokasi']
        prec_features_to_display = ['Date', 'prec_nwp', 'prediction', 'lokasi']

        # Sliced Dataframe filtered to only one location
        dff_one_loc_temp = df_pred_temp[df_pred_temp['lokasi'] == prop_lokasi][temp_features_to_display]
        dff_one_loc_humidity = df_pred_humid[df_pred_humid['lokasi'] == prop_lokasi][humid_features_to_display]
        dff_one_loc_prec = df_pred_prec[df_pred_prec['lokasi'] == prop_lokasi][prec_features_to_display]
        

        print('graph_mode', tabs_value)


        if tabs_value == 'temp-tab':
            # Plotly Express Figure for  Temperature
            type = 'Temperature'
            figure = plot_graph(dff_one_loc_temp, nama_upt, 'suhu2m.degC.', type)

            # Min - Max Value for Inactive Temperature Slider
            min = get_datatable(wmoid_lokasi, prop_lokasi, 'min temp')
            avg = get_datatable(wmoid_lokasi, prop_lokasi, 'average temp')
            max = get_datatable(wmoid_lokasi, prop_lokasi, 'max temp')

            unit = '°C'

            # Hideout dict
            color_prop = 'average temp'
            min_abs = temp_min
            max_abs = temp_max
            colorscale = temp_colorscale



        elif tabs_value == 'humid-tab':
            # Plotly Express Figure for  Humidity
            type = 'Humidity'
            figure = plot_graph(dff_one_loc_humidity, nama_upt, 'rh2m...', type)
            
            # Min - Max Value for Inactive Humidity Slider
            min = get_datatable(wmoid_lokasi, prop_lokasi, 'min humidity')
            avg = get_datatable(wmoid_lokasi, prop_lokasi, 'average humidity')
            max = get_datatable(wmoid_lokasi, prop_lokasi, 'max humidity')

            unit = '%'

            # Hideout dict
            color_prop = 'average humidity'
            min_abs = humid_min
            max_abs = humid_max
            colorscale = humid_colorscale
            
        
        elif tabs_value == 'prec-tab':
            # Plotly Express Figure for Precipitation
            type = 'Precipitation'
            figure = plot_graph(dff_one_loc_prec, nama_upt, 'prec_nwp', type)

            unit = 'mm'
            
            # Min - Max Value for Inactive Precipitation Slider
            min = get_datatable(wmoid_lokasi, prop_lokasi, 'min precipitation')
            avg = get_datatable(wmoid_lokasi, prop_lokasi, 'average precipitation')
            max = get_datatable(wmoid_lokasi, prop_lokasi, 'max precipitation')
            

            # Hideout dict
            color_prop = 'average precipitation'
            min_abs = prec_min
            max_abs = prec_max
            colorscale = prec_colorscale

        # Combining the value to one array
        slider_value = [min, max]
        hideout = dict(
                colorProp = color_prop,
                circleOptions=dict(
                    fillOpacity=1, 
                    stroke=False, 
                    radius=5
                    ),   
                min = min_abs,
                max = max_abs,
                colorscale = colorscale
            )

        return (slider_value, min_abs, max_abs, figure, 
                hideout, 
                colorscale, min_abs, max_abs, unit,
                min, avg, max
                )


def generate_output_df(variable_name, original_df, filtered_df, prediction_array):
    df_pred = pd.concat([original_df['Date'], filtered_df[['lokasi', variable_name]], pd.Series(prediction_array, index=filtered_df.index)], axis=1)
    df_pred.columns = ['Date', 'lokasi', variable_name, 'prediction']
    df_pred = df_pred.dropna()
    return df_pred


# Load ML Models
with open('./models/huber_regressor_bad.pkl','rb') as f:
    prec_model = pickle.load(f)

# Predict temperature
temp_model_path = './models/Temp_xgb_tuned_RMSE_1_441.json'
temp_columns_to_drop = ['lcloud...', 'mcloud...', 'hcloud...', 'clmix.kg.kg.', 'wamix.kg.kg.', 'prec_nwp']
temp_pred = predict_xgb(temp_model_path, temp_columns_to_drop, ina_nwp_input_filtered)

# Predict humidity
humid_model_path = './models/xgbregressor_humidity.json'
humid_columns_to_drop = ['prec_nwp', 'mcloud...', 'wamix.kg.kg.', 'clmix.kg.kg.', 'lcloud...', 'hcloud...']
humid_pred = predict_xgb(humid_model_path, humid_columns_to_drop, ina_nwp_input_filtered)

# Predict precipitation
prec_pred = prec_model.predict(ina_nwp_input_filtered[[
    'lokasi', 'suhu2m.degC.', 'dew2m.degC.', 'rh2m...', 'wspeed.m.s.',
    'wdir.deg.', 'lcloud...', 'mcloud...', 'hcloud...', 'surpre.Pa.',
    'clmix.kg.kg.', 'wamix.kg.kg.', 'outlr.W.m2.', 'pblh.m.', 'lifcl.m.',
    'cape.j.kg.', 'mdbz', 't950.degC.', 'rh950...', 'ws950.m.s.',
    'wd950.deg.', 't800.degC.', 'rh800...', 'ws800.m.s.', 'wd800.deg.',
    't500.degC.', 'rh500...', 'ws500.m.s.', 'wd500.deg.', 'ELEV',
    'prec_nwp'
]])


# OUTPUT temperature
df_pred_temp = generate_output_df('suhu2m.degC.', ina_nwp_input, ina_nwp_input_filtered, temp_pred)

# OUTPUT humidity
df_pred_humid = generate_output_df('rh2m...', ina_nwp_input, ina_nwp_input_filtered, humid_pred)

# OUTPUT precipitation
df_pred_prec = generate_output_df('prec_nwp', ina_nwp_input, ina_nwp_input_filtered, prec_pred)


# Load script 
temp_colorscale = [
    'rgb(0, 10, 112)',
    'rgb(0, 82, 190)', 
    'rgb(51, 153, 255)', 
    'rgb(153, 235, 255)', 
    'rgb(204, 255, 255)',
    'rgb(255, 255, 204)',
    'rgb(255, 225, 132)',
    'rgb(255, 158, 20)',
    'rgb(245, 25, 25)',
    'rgb(165, 0, 0)',
    'rgb(50, 0, 0)'
    ]

humid_colorscale = [
    'rgb(204, 102, 0)',
    'rgb(255, 128, 0)', 
    'rgb(255, 193, 51)', 
    'rgb(255, 255, 102)', 
    'rgb(255, 255, 255)',
    'rgb(153, 255, 255)',
    'rgb(102, 178, 255)',
    'rgb(10, 102, 204)',
    'rgb(10, 76, 153)',
    'rgb(10, 51, 102)',
    ]

prec_colorscale=[
    'rgb(6, 62, 114)',
    'rgb(34, 112, 192)',
    'rgb(57, 196, 234)',
    'rgb(0, 255, 193)',
    'rgb(0, 224, 71)',
    'rgb(250, 255, 66)',
    'rgb(255, 173, 13)',
    'rgb(255, 108, 0)',
    'rgb(179, 58, 0)',
    'rgb(252, 38, 42)',
    'rgb(226, 0, 34)',
    'rgb(255, 0, 203)',
    'rgb(201, 0, 154)',
    'rgb(121, 0, 123)',
]
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"  # js lib used for colors



# Min and Max temp for point colors
temp_min = 0
temp_max = 38

humid_min = 0
humid_max = 100

prec_min = 0
prec_max = 60

colorbar = dl.Colorbar(id = 'map-colorbar',colorscale=temp_colorscale, width=20, height=150, min=temp_min, max=temp_max, unit='°C')
# humid_colorbar = dl.Colorbar(colorscale=humid_colorscale, width=20, height=150, min=humid_min, max=humid_max, unit='%')

BMKG_LOGO = "https://cdn.bmkg.go.id/Web/Logo-BMKG-new.png"


# Example usage with 'lokasi' as the merging column
data_table_lokasi_temp = create_data_table(df_wmoid, df_pred_temp, 'temp', merge_column='lokasi')
data_table_lokasi_humid = create_data_table(df_wmoid, df_pred_humid, 'humidity', merge_column='lokasi')
data_table_lokasi_prec = create_data_table(df_wmoid, df_pred_prec, 'precipitation', merge_column='lokasi')

# Merge the dataframes
data_table_lokasi = data_table_lokasi_temp.merge(data_table_lokasi_humid, on='lokasi').merge(data_table_lokasi_prec, on='lokasi')
print('data_table_lokasi')
print(data_table_lokasi)


# Make geopandas geometry for coordinates
geometry = geopandas.points_from_xy(df_map.LON, df_map.LAT)
upt_gpd = geopandas.GeoDataFrame(df_map, geometry=geometry)
upt_gpd = pd.merge(upt_gpd, data_table_lokasi[['lokasi', 'average temp', 'average humidity', 'average precipitation']], on='lokasi')
upt_gpd = upt_gpd.reset_index(drop=True)

geojson = json.loads(upt_gpd.to_json())
geobuf = dlx.geojson_to_geobuf(geojson)
upt = dl.GeoJSON(
    data=geobuf,
    id='geojson',
    format='geobuf',
    zoomToBounds=True,  # when true, zooms to bounds when data changes
    pointToLayer=point_to_layer,  # how to draw points
    onEachFeature=on_each_feature,  # add (custom) tooltip
    hideout=dict(
        colorProp='average temp', 
        circleOptions=dict(
            fillOpacity=1, 
            stroke=False, 
            radius=5),
            min=temp_min, 
            max=temp_max, 
            colorscale=temp_colorscale
            )
)
print('upt_gpd\n', upt_gpd)



# Sort the data by Date
# ina_nwp_input_sorted = ina_nwp_input_filtered.copy()
# ina_nwp_input_sorted = ina_nwp_input_sorted.sort_values(by='Date')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


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
                html.H1(children='MONAS Dashboard'),
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

    html.Div([
        html.Div([  # Wrap the map and header in a div for layout
            dl.Map(
                [
                    dl.TileLayer(), 
                    dl.ScaleControl(position="bottomleft"),
                    dl.FullScreenControl(),
                    upt,
                    colorbar,
                ],
                center=[-2.058210136999589, 116.78386542384145],
                markerZoomAnimation = True,
                id = 'dash-leaflet-map',
                style={
                    'height': '90vh', 
                    'width' : '50vw'
                    }
                ),
            html.Div([
                html.Div([
                    html.Div([ # Div for map, metric, and graph
                        html.Div([
                            dcc.Tabs(
                                id="graph-tabs",
                                value='temp-tab',
                                parent_className='custom-tabs',
                                className='custom-tabs-container',
                                children=[
                                    dcc.Tab(
                                        label='Temperature',
                                        value='temp-tab',
                                        className='custom-tab',
                                        selected_className='custom-tab--selected'
                                    ),
                                    dcc.Tab(
                                        label='Humidity',
                                        value='humid-tab',
                                        className='custom-tab',
                                        selected_className='custom-tab--selected'
                                    ),
                                    dcc.Tab(
                                        label='Precipitation',
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
                                    } 
                                ),
                            ),
                            dcc.RangeSlider(
                                id='graph-metric',
                                min=0,
                                max=40,
                                value=[0,0],
                                step=None,
                                vertical=False,
                                disabled=True,
                            ),

                            html.Div([
                                html.Div([
                                    html.Label("Lowest Value", style={"font-weight": "bold"}),
                                    html.Div(id='low-temp', style={"font-size": "20px"}, children='0')
                                ], style={'width': '33%', 'display': 'inline-block'}),
                                html.Div([
                                    html.Label("Average Value", style={"font-weight": "bold"}),
                                    html.Div(id='avg-temp', style={"font-size": "20px"}, children='0')
                                ], style={'width': '33%', 'display': 'inline-block'}),
                                html.Div([
                                    html.Label("Highest Value", style={"font-weight": "bold"}),
                                    html.Div(id='high-temp', style={"font-size": "20px"}, children='0')
                                ], style={'width': '33%', 'display': 'inline-block'}),
                            ]),

                            
                        ]),
                    ], 
                    style={
                        'display': 'grid', 
                        'grid-column': 'auto auto',
                        'grid-auto-flow': 'column'
                    }),
                ], 
                style={
                    'display': 'grid', 
                    'grid-column': 'auto auto',
                    'grid-auto-flow': 'row'
                    }
                ),  # Display elements side by side
            ]),
        ], 
        style={
            'display' : 'grid',
            'grid-column': 'auto auto',
            'grid-auto-flow': 'column'
            }),
        html.Div([# Div for other details such as comparison graph, data tables, and other metrics 
                dash_table.DataTable(
                    data=data_table_lokasi.to_dict('records'), 
                    page_size=10)       
                ], 
                style= {
                    'display': 'grid', 
                    'grid-column': 'auto auto',
                    'grid-auto-flow': 'row'
                }
                ),
    ])
])



if __name__ == '__main__':
    # app.run_server(host= '0.0.0.0',debug=False)
    app.run_server(host= '127.0.0.1',debug=True)
