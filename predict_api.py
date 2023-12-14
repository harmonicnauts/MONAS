# Import necessary libraries
from flask import Flask, request, jsonify
import pandas as pd
import joblib  # Assuming you used joblib to save your model
import pickle
from xgboost import XGBRegressor
import json

# Create a Flask app
app = Flask(__name__)

# Load the pre-trained model
temp_model = XGBRegressor()
# temp_model = joblib.load('./models/Temp_xgb_tuned_RMSE_1_44.joblib')  # Replace with your actual model filename
temp_model.load_model('./models/Temp_xgb_tuned_R2_77.json')  # Replace with your actual model filename


humid_model = XGBRegressor()
humid_model.load_model('./models/humid_xgb_tuned_noShuffle.json')

with open('./models/huber_regressor_bad.pkl','rb') as f:
    prec_model = pickle.load(f)

# Define an endpoint for making predictions
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Check if the request contains a file
        if 'input' not in request.files:
            print(request.files)
            return jsonify({'error': 'No file part'}), 400

        file = request.files['input']

        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Assuming the file is a CSV, read it into a DataFrame
        input_df = pd.read_csv(file)

        # INA-NWP input preprocess
        ina_nwp_input_filtered = input_df.drop(columns=['Date', 'LAT', 'LON'])  
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

        # Make predictions using the loaded model
        temp_pred = temp_model.predict(ina_nwp_input_filtered.drop(columns=['lokasi', 'lcloud...','mcloud...', 'hcloud...', 'clmix.kg.kg.', 'wamix.kg.kg.', 'prec_nwp']))
        humid_pred = humid_model.predict(ina_nwp_input_filtered.drop(columns=['prec_nwp']))
        prec_pred = prec_model.predict(ina_nwp_input_filtered[[
            'lokasi', 'suhu2m.degC.', 'dew2m.degC.', 'rh2m...', 'wspeed.m.s.',
            'wdir.deg.', 'lcloud...', 'mcloud...', 'hcloud...', 'surpre.Pa.',
            'clmix.kg.kg.', 'wamix.kg.kg.', 'outlr.W.m2.', 'pblh.m.', 'lifcl.m.',
            'cape.j.kg.', 'mdbz', 't950.degC.', 'rh950...', 'ws950.m.s.',
            'wd950.deg.', 't800.degC.', 'rh800...', 'ws800.m.s.', 'wd800.deg.',
            't500.degC.', 'rh500...', 'ws500.m.s.', 'wd500.deg.', 'ELEV',
            'prec_nwp'
        ]])

        # Create a DataFrame with the predictions

        #OUTPUT TEMP
        df_pred_temp = pd.concat([input_df['Date'], ina_nwp_input_filtered[['lokasi', 'suhu2m.degC.']], pd.Series(temp_pred, index = ina_nwp_input_filtered.index)], axis=1)
        df_pred_temp.columns = ['Date','lokasi', 'suhu2m.degC.', 'prediction']
        df_pred_temp = df_pred_temp.dropna()



        #OUTPUT HUMIDITY
        df_pred_humid = pd.concat([input_df['Date'], ina_nwp_input_filtered[['lokasi', 'rh2m...']], pd.Series(humid_pred, index = ina_nwp_input_filtered.index)], axis=1)
        df_pred_humid.columns = ['Date','lokasi', 'rh2m...', 'prediction']
        df_pred_humid = df_pred_humid.dropna()

        #OUTPUT Precipitation
        df_pred_prec = pd.concat([input_df['Date'], ina_nwp_input_filtered[['lokasi', 'prec_nwp']], pd.Series(prec_pred, index = ina_nwp_input_filtered.index)], axis=1)
        df_pred_prec.columns = ['Date','lokasi', 'prec_nwp', 'prediction']
        df_pred_prec = df_pred_prec.dropna()

        combined_data = {
            'temperature': json.loads(df_pred_temp.to_json(orient='records')),
            'humidity': json.loads(df_pred_humid.to_json(orient='records')),
            'precipitation': json.loads(df_pred_prec.to_json(orient='records'))
        }

        # Convert the DataFrame to JSON and return
        return (
            jsonify(combined_data)
            )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)