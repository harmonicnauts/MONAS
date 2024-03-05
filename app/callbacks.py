from dash import callback, Output, Input
import dash_leaflet.express as dlx
from data_preprocess import *
import json

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

        Output("temp-tab", "disabled"), Output("humid-tab", "disabled"), Output("prec-tab", "disabled"),

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
            min = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'min_temp')
            avg = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'mean_temp')
            max = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'max_temp')

            unit = '°C'

            # Hideout dict
            color_prop = 'mean_temp'
            min_abs = temp_min
            max_abs = temp_max
            colorscale = temp_colorscale



        elif tabs_value == 'humid-tab':
            # Plotly Express Figure for  Humidity
            type = 'Humidity'
            figure = plot_graph(dff_one_loc_humidity, nama_upt, 'rh2m...', type)
            
            # Min - Max Value for Inactive Humidity Slider
            min = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'min_humidity')
            avg = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'mean_humidity')
            max = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'max_humidity')

            unit = '%'

            # Hideout dict
            color_prop = 'mean_humidity'
            min_abs = humid_min
            max_abs = humid_max
            colorscale = humid_colorscale
            
        
        elif tabs_value == 'prec-tab':
            # Plotly Express Figure for Precipitation
            type = 'Precipitation'
            figure = plot_graph(dff_one_loc_prec, nama_upt, 'prec_nwp', type)

            unit = 'mm'
            
            # Min - Max Value for Inactive Precipitation Slider
            min = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'min_precipitation')
            avg = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'mean_precipitation')
            max = get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, 'max_precipitation')
            

            # Hideout dict
            color_prop = 'mean_precipitation'
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
                False, False, False
                )

@callback(
        Output("geojson", "data"),
        Input ("baselayer-layers-control", "baseLayer")
        ) # Marker OnClick Event)
def base_layer_click(base_name):
    geojson_data = pd.merge(upt_gpd, data_table_lokasi[data_table_lokasi.drop(columns=['Nama UPT']).columns], on='lokasi')
    # print('geojson_in_callback\n', geojson_data)
    # print('Selected base name:', base_name)
    # print('Unique dates in data_table_lokasi:', data_table_lokasi['Date'].unique())
    geojson_data = geojson_data[geojson_data['Date'] == base_name]
    geojson_data = geojson_data.reset_index(drop=True)

    geojson_data = json.loads(geojson_data.to_json())
    goejson_data_geobuf = dlx.geojson_to_geobuf(geojson_data)
    return(goejson_data_geobuf)
