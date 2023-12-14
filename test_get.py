import requests
import json

# Set up the API URL and file
api_url = 'http://127.0.0.1:5000/predict'  # Adjust the URL based on your API
file_path = './Data/MONAS-input_nwp_compile.csv'  # Adjust the file path

# Create a dictionary to store the file in the 'file' key
files = {'input': ('MONAS-input_nwp_compile.csv', open(file_path, 'rb'))}

# Send the POST request to the API
response = requests.post(api_url, files=files)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the JSON response into a list
    predictions_json = json.loads(response.text)
    
    # Extract the predictions from the JSON into a Python list
    # predictions_list = [entry['prediction'] for entry in predictions_json]

    # Print or use the predictions list as needed
    # print("Predictions:", predictions_json)
    print('Humidity', predictions_json['humidity'])

else:
  print(f"Error: {response.status_code}, {response.text}")