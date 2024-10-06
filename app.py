from flask import Flask, render_template, request, redirect, url_for, flash,jsonify,send_file
from flask_cors import CORS
import io
import pandas as pd
from seismic_processor_mars import process_seismic_data
from seismic_pro_moon import process_seismic_data2
import os
import json

app = Flask(__name__)
CORS(app)
app.secret_key = "moses_the_mass"
output_directory = './output/mars'
output_directory2 = './output/moon'

# Ensure the output directory exists
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

@app.route('/')
def index():
    return render_template('planet_quaker.html')
@app.route('/mars')
def index2():
    return render_template('mars_seismic_data.html')

@app.route('/moon')
def index1():
    return render_template("moon_seismic_data.html")

@app.route('/upload', methods=['POST'])
def upload_file():
   
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        # Read the uploaded CSV file into a pandas DataFrame
        try:
            df = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
            # Process the CSV data (trigger detection, filtering, etc.)
            my_file_name = file.filename
            processed_output = process_seismic_data(df,my_file_name)

            # Save the output to CSV
            output_filepath = os.path.join(output_directory, 'mars_catalog.csv')
            processed_output.to_csv(output_filepath, index=False)
            
            flash(f'File processed and saved to {output_filepath}')
        except Exception as e:
            flash(f'Error processing file: {e}')
            return redirect(request.url)

        return "successful"
    
@app.route('/upload2', methods=['POST'])
def upload_file2():
   
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        # Read the uploaded CSV file into a pandas DataFrame
        try:
            df = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
            # Process the CSV data (trigger detection, filtering, etc.)
            my_file_name = file.filename
            processed_output = process_seismic_data2(df,my_file_name)

            # Save the output to CSV
            output_filepath = os.path.join(output_directory2, 'moon_catalog.csv')
            processed_output.to_csv(output_filepath, index=False)
            
            flash(f'File processed and saved to {output_filepath}')
        except Exception as e:
            flash(f'Error processing file: {e}')
            return redirect(request.url)

        return "successful"
@app.route('/getfile/<filename>', methods=['GET'])
def get_file(filename):
    # Define the path to the file on the server
    if filename == "mars_catalog.csv":
        file_path = os.path.join('./output/mars/', filename)
    elif filename == "moon_catalog.csv":
        file_path = os.path.join('./output/moon/', filename)
          # Update with your actual path
    print(f"Looking for file at: {file_path}")  # Debugging line
    
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)


