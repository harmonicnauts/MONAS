import pandas as pd
import plotly.express as px
import joblib

def predict_model(model_path, columns_to_drop, input_df):
    model = joblib.load(model_path)
    input_data = input_df.drop(columns=columns_to_drop)
    predictions = model.predict(input_data)
    return predictions


def create_data_table(df_wmoid, df_pred, col_name, merge_column='lokasi'):
    df_pred['Date'] = pd.to_datetime(df_pred['Date'])
    df_pred['day'] = df_pred['Date'].dt.day

    # Group by 'day' and calculate the averages
    df_pred_avg = df_pred.groupby(['lokasi', 'day']).agg({
        'prediction': ['max', 'mean', 'min']
    }).astype('float64').round(1).reset_index()

    # Rename columns
    df_pred_avg.columns = ['lokasi', 'day', f'max_{col_name}', f'mean_{col_name}', f'min_{col_name}']

    # Convert 'Date' to a string format without timezone
    df_pred_avg['Date'] = df_pred_avg['day'].apply(lambda x: f'2023-10-{x:02d}')

    # Rearrange columns
    df_pred_avg = df_pred_avg[['lokasi', 'day', 'Date', f'max_{col_name}', f'mean_{col_name}', f'min_{col_name}']]

    # Merge with df_wmoid
    data_table_lokasi = pd.merge(df_wmoid, df_pred_avg, how='inner', on=merge_column)

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

def get_datatable(data_table_lokasi, wmoid_lokasi, prop_lokasi, column):
    return data_table_lokasi[wmoid_lokasi == prop_lokasi][column].iloc[0]


def generate_output_df(variable_name, original_df, filtered_df, prediction_array):
    df_pred = pd.concat([original_df['Date'], filtered_df[['lokasi', variable_name]], pd.Series(prediction_array, index=filtered_df.index)], axis=1)
    df_pred.columns = ['Date', 'lokasi', variable_name, 'prediction']
    df_pred = df_pred.dropna()
    return df_pred