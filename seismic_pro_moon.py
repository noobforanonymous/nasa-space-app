import os
import numpy as np
import pandas as pd
from obspy.signal.trigger import classic_sta_lta, trigger_onset
from scipy.signal import butter, lfilter
from datetime import timedelta

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

def process_seismic_data2(df,myfilename):
    # Extract time and velocity data from the DataFrame
    tr_times_abs = pd.to_datetime(df['time_abs(%Y-%m-%dT%H:%M:%S.%f)'])
    tr_times_rel = df['time_rel(sec)'].values
    tr_data = df['velocity(m/s)'].values
    fs = 1 / (tr_times_rel[1] - tr_times_rel[0])  # Calculate sampling frequency

    # Apply bandpass filter
    lowcut = 0.01  # Adjust based on needs
    highcut = 1.0
    tr_data_filt = bandpass_filter(tr_data, lowcut, highcut, fs)

    # Apply STA/LTA trigger detection
    sta_len = 120  # Short-term window in seconds
    lta_len = 600  # Long-term window in seconds
    cft = classic_sta_lta(tr_data_filt, int(sta_len * fs), int(lta_len * fs))
    
    # Define trigger thresholds and detect events
    thr_on = 4
    thr_off = 1.5
    on_off = trigger_onset(cft, thr_on, thr_off)

    # Convert relative time to absolute and prepare output DataFrame
    starttime = tr_times_abs[0]
    detection_times = []
    
    for triggers in on_off:
        on_time = starttime + timedelta(seconds=tr_times_rel[triggers[0]])
        detection_times.append(on_time)

    # Prepare output DataFrame with detected events
    output_df = pd.DataFrame({
        'filename': myfilename,  # Change this as necessary
        'time_abs(%Y-%m-%dT%H:%M:%S.%f)': [dt.strftime('%Y-%m-%dT%H:%M:%S.%f') for dt in detection_times],
        'time_rel(sec)': tr_times_rel[on_off[:, 0]]
    })

    return output_df

# Example of reading a CSV file and calling the processing function
# df = pd.read_csv('path_to_uploaded_file.csv')
# output_df = process_seismic_data(df)
# output_df.to_csv('output_file.csv', index=False)
