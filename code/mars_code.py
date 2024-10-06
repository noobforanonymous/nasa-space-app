import numpy as np
import pandas as pd
from obspy.signal.trigger import classic_sta_lta, trigger_onset
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
import os

# Bandpass filter functions
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

# Function to handle missing data
def handle_missing_data(data):
    data = np.nan_to_num(data)  # Replace NaN with zeros
    return data

# List of CSV files
test_filenames_csv = [
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2019-05-23HR02_evid0041.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2019-07-26HR12_evid0033.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2019-07-26HR12_evid0034.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2019-09-21HR03_evid0032.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2021-05-02HR01_evid0017.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2021-10-11HR23_evid0011.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2021-12-24HR22_evid0007.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2022-04-09HR22_evid0002.csv",
r"D://webdev/planet_quaker/server/data/mars/test/XB.ELYSE.02.BHV.2022-05-04HR23_evid0001.csv",
]

# Directory containing the CSV files
data_directory = r'../server/data/mars/test/'

# Loop through the test filenames
for filename in test_filenames_csv:
    csv_file = r'../server/data/mars/test/XB.ELYSE.02.BHV.2022-05-04HR23_evid0001.csv'
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        continue  # Skip this file and continue with the next one

    # Assuming the CSV has columns 'time_abs', 'time_rel', and 'velocity(m/s)'
    tr_times_abs = pd.to_datetime(df['time(%Y-%m-%dT%H:%M:%S.%f)'])
    tr_times_rel = df['rel_time(sec)'].values
    tr_data = df['velocity(c/s)'].values
    fs = 1 / (tr_times_rel[1] - tr_times_rel[0])  # Calculate sampling frequency from time intervals
    
    # Apply bandpass filter (to handle planetary-specific noise and anomalies)
    lowcut = 0.01  # Adjust to target specific seismic frequencies
    highcut = 1.0
    tr_data_filt = bandpass_filter(tr_data, lowcut, highcut, fs)

    # Handle missing data after filtering
    tr_data_filt = handle_missing_data(tr_data_filt)

    # Apply Short-Term Average / Long-Term Average (STA/LTA) algorithm
    sta_len = 120  # Short-term window in seconds
    lta_len = 600  # Long-term window in seconds
    cft = classic_sta_lta(tr_data_filt, int(sta_len * fs), int(lta_len * fs))

    # Plot characteristic function for STA/LTA
    fig, ax = plt.subplots(1, 1, figsize=(12, 3))
    ax.plot(tr_times_rel, cft)
    ax.set_xlim([min(tr_times_rel), max(tr_times_rel)])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Characteristic Function')

    # Define trigger thresholds and identify seismic events
    thr_on = 4  # On threshold
    thr_off = 1.5  # Off threshold
    on_off = np.array(trigger_onset(cft, thr_on, thr_off))

    # Plot triggers
    fig, ax = plt.subplots(1, 1, figsize=(12, 3))
    for i in range(len(on_off)):
        triggers = on_off[i]
        ax.axvline(x=tr_times_rel[triggers[0]], color='red', label='Trig. On')
        ax.axvline(x=tr_times_rel[triggers[1]], color='purple', label='Trig. Off')

    # Plot filtered trace with marked detections
    ax.plot(tr_times_rel, tr_data_filt)
    ax.set_xlim([min(tr_times_rel), max(tr_times_rel)])
    ax.legend()

    # Convert relative time to absolute
    starttime = tr_times_abs[0]
    detection_times = []
    fnames = []
    for i in range(len(on_off)):
        triggers = on_off[i]
        on_time = starttime + timedelta(seconds=tr_times_rel[triggers[0]])
        detection_times.append(on_time)
        fnames.append(filename)

    # Compile detected events into a DataFrame and export to CSV
    detect_df = pd.DataFrame({
        'filename': fnames, 
        'time(%Y-%m-%dT%H:%M:%S.%f)': [dt.strftime('%Y-%m-%dT%H:%M:%S.%f') for dt in detection_times],
        'rel_time(sec)': tr_times_rel[on_off[:,0]]
    })

    # Save to CSV
    output_directory = '../server/output/mars'
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    detect_df.to_csv(f'{output_directory}/mars_catalog.csv', index=False)