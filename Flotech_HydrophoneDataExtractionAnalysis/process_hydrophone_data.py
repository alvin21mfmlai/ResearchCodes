import os
import gzip
import pandas as pd
import numpy as np
from scipy.signal import welch
from PyEMD import EEMD
from scipy.io.wavfile import write, read

def extract_datetime(file_content):
    """
    Extracts the datetime from the file content.
    """
    date_item = file_content[3].split("_")[0]
    time_item = file_content[3].split("_")[1][0:5]
    month, day, year = map(lambda x: x.lstrip('0'), date_item.split("-"))
    return f"{month}/{day}/{year} {time_item}"

def read_hydrophone_data(src_path, samplingRate):
    """
    Reads hydrophone data from the given source path and organizes it into a dictionary.
    """
    data_dict = dict()
    stations_list = os.listdir(src_path)
    
    for station in stations_list:
        station_path = os.path.join(src_path, station)
        readings_path = os.path.join(station_path, 'hydrophone', 'readings')
        data_series_folder = os.path.join(station_path, 'hydrophone', 'dataSeries')
        wav_files_folder = os.path.join(station_path, 'hydrophone', 'wavFiles')
        if not os.path.exists(wav_files_folder): os.mkdir(wav_files_folder)
        
        os.makedirs(data_series_folder, exist_ok=True)
        data_dict[station] = dict()
        
        for hydrophone_file in os.listdir(readings_path):
            with gzip.open(os.path.join(readings_path, hydrophone_file), 'r') as f:
                file_content = f.read().decode("utf-8").split("\n")
                
                datetime_str = extract_datetime(file_content)
                data_values = [float(data.strip()[1:-1]) for data in file_content[-1].split("\n")[-1][1:-1].split(",")]
                
                if datetime_str not in data_dict[station]:
                    data_dict[station][datetime_str] = []
                data_dict[station][datetime_str].extend(data_values)
                
                # Save data to CSV
                datadf = pd.DataFrame({'Values': data_dict[station][datetime_str]})
                sanitized_datetime_str = datetime_str.replace('/', "_").replace(':', "_")
                datadf.to_csv(os.path.join(data_series_folder, f"{sanitized_datetime_str}.csv"), index=False)
                
                # Convert data to WAV files using following steps:
                
                ## a. Normalize the data to the range of -1 to 1
                normalized_data = (data_values - np.min(data_values)) / (np.max(data_values) - np.min(data_values))
                normalized_data = 2 * (normalized_data - 0.5)

                ## b. Convert to 16-bit PCM format
                pcm_data = np.int16(normalized_data * 32767)

                ## c. Save the data to a WAV file with a sample rate of 8000 Hz
                output_wav_path = wav_files_folder + '/' + hydrophone_file.split('.')[0] + '.wav'
                write(output_wav_path, samplingRate, pcm_data)
                
                ## d. Extract data from WAV file to double check if extracted data aligns with original data values
                ### d.1. Read the WAV file
                sample_rate, pcm_data = read(output_wav_path)

                ### d.2. Normalize the data back to the original range
                normalized_data = pcm_data / 32767.0

                ### d.3. Convert the normalized data back to the original range
                original_min = np.min(data_values)
                original_max = np.max(data_values)
                extracted_data = normalized_data * (original_max - original_min) / 2 + (original_max + original_min) / 2
                if (np.array(extracted_data).all() == np.array(data_values).all()): 
                    print("Ok for File: " + hydrophone_file)
                    print(np.array(extracted_data)[:10])
                    print(np.array(data_values)[:10])
                    print()
    
    return data_dict

def process_hydrophone_data(src_path,sampling_rate):
    """
    Processes hydrophone data: reads data, computes PSDs and IMFs, and saves the results.
    """
    data_dict = read_hydrophone_data(src_path,sampling_rate)

if __name__ == "__main__":
    src_path = r'D:\ALFTool\Data\Hydrophones\Sample'
    sampling_rate = 8000 ## measured in Hz
    process_hydrophone_data(src_path,sampling_rate)
