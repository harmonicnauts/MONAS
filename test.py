# Import necessary libraries
from flask import Flask, request, jsonify
import pandas as pd
import joblib  # Assuming you used joblib to save your model
from xgboost import XGBRegressor

# Create a Flask app
app = Flask(__name__)

# Load the pre-trained model
model = XGBRegressor()
model.load_model('./models/Temp_xgb_tuned_R2_77.json')  # Replace with your actual model filename

# Define an endpoint for making predictions
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get input data from the request
        # data = request.get_json()

        # Assuming the input data is a list of features, you need to convert it to a DataFrame
        input_df = pd.read_csv('./Data/MONAS-input_nwp_compile.csv')

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
        predictions = model.predict(ina_nwp_input_filtered.drop(columns=['lokasi', 'lcloud...','mcloud...', 'hcloud...', 'clmix.kg.kg.', 'wamix.kg.kg.', 'prec_nwp']))

        # Create a DataFrame with the predictions
        result_df = pd.DataFrame({'Prediction': predictions})

        print (result_df.to_json(orient='records'))

        # Convert the DataFrame to JSON and return
        return result_df.to_json(orient='records')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)