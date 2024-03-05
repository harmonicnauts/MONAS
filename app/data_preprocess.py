import pandas as pd
import json
import dash_leaflet.express as dlx
import dash_leaflet as dl
import geopandas
from utility_scripts import *
from geojson_scripts import *


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

# Load ML Models
prec_model_path = './models/Temp_xgb_tuned_RMSE_1_441.model'
prec_columns_to_drop = ['clmix.kg.kg.', 'hcloud...', 'wamix.kg.kg.', 'prec_nwp', 'mcloud...', 'lcloud...']
prec_pred = predict_model(prec_model_path, prec_columns_to_drop, ina_nwp_input_filtered)

# Predict temperature
temp_model_path = './models/Temp_xgb_tuned_RMSE_1_441.model'
temp_columns_to_drop = ['lcloud...', 'mcloud...', 'hcloud...', 'clmix.kg.kg.', 'wamix.kg.kg.', 'prec_nwp']
temp_pred = predict_model(temp_model_path, temp_columns_to_drop, ina_nwp_input_filtered)

# Predict humidity
humid_model_path = './models/xgbregressor_humidity.model'
humid_columns_to_drop = ['prec_nwp', 'mcloud...', 'wamix.kg.kg.', 'clmix.kg.kg.', 'lcloud...', 'hcloud...']
humid_pred = predict_model(humid_model_path, humid_columns_to_drop, ina_nwp_input_filtered)



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

# Min and Max temp for point colors
temp_min = 0
temp_max = 38

humid_min = 0
humid_max = 100

prec_min = 0
prec_max = 60


# Example usage with 'lokasi' as the merging column
data_table_lokasi_temp = create_data_table(df_wmoid, df_pred_temp, 'temp', merge_column='lokasi')
data_table_lokasi_humid = create_data_table(df_wmoid, df_pred_humid, 'humidity', merge_column='lokasi')
data_table_lokasi_prec = create_data_table(df_wmoid, df_pred_prec, 'precipitation', merge_column='lokasi')

# Merge the dataframes
data_table_lokasi = data_table_lokasi_temp.merge(data_table_lokasi_humid.drop(columns=['Nama UPT', 'day']), on=['lokasi', 'Date'], how='left').merge(data_table_lokasi_prec.drop(columns=['Nama UPT', 'day']), on=['lokasi', 'Date'], how='left')
print('data_table_lokasi')
print(data_table_lokasi)
print(data_table_lokasi.columns)

# Make geopandas geometry for coordinates
geometry = geopandas.points_from_xy(df_map.LON, df_map.LAT)
upt_gpd = geopandas.GeoDataFrame(df_map, geometry=geometry)
upt_gpd_merged = pd.merge(upt_gpd, data_table_lokasi[data_table_lokasi.drop(columns=['Nama UPT']).columns], on='lokasi')
upt_gpd_merged = upt_gpd_merged.reset_index(drop=True)
print('geojson_outside_callback\n', upt_gpd_merged)

geojson = json.loads(upt_gpd_merged.to_json())
geobuf = dlx.geojson_to_geobuf(geojson)
upt = dl.GeoJSON(
    data=geobuf,
    id='geojson',
    format='geobuf',
    zoomToBounds=True,  # when true, zooms to bounds when data changes
    pointToLayer=point_to_layer,  # how to draw points
    onEachFeature=on_each_feature,  # add (custom) tooltip
    hideout=dict(
        colorProp='mean_temp', 
        circleOptions=dict(
            fillOpacity=1, 
            stroke=False, 
            radius=5),
            min=temp_min, 
            max=temp_max, 
            colorscale=temp_colorscale
            )
)