import os
import gzip
import pandas as pd
import numpy as np
from scipy.signal import welch
from PyEMD import EEMD

def extract_datetime(file_content):
    """
    Extracts the datetime from the file content.
    """
    date_item = file_content[3].split("_")[0]
    time_item = file_content[3].split("_")[1][0:5]
    month, day, year = map(lambda x: x.lstrip('0'), date_item.split("-"))
    return f"{month}/{day}/{year} {time_item}"

def read_hydrophone_data(src_path):
    """
    Reads hydrophone data from the given source path and organizes it into a dictionary.
    """
    data_dict = dict()
    stations_list = os.listdir(src_path)
    
    for station in stations_list:
        station_path = os.path.join(src_path, station)
        readings_path = os.path.join(station_path, 'hydrophone', 'readings')
        data_series_folder = os.path.join(station_path, 'hydrophone', 'dataSeries')
        
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
    
    return data_dict

def compute_psd_and_save(data, sample_rate, output_folder, data_file):
    """
    Computes Power Spectral Density (PSD) and saves it to a CSV file.
    """
    frequencies, psd = welch(data, fs=sample_rate, nperseg=4096)
    psd_df = pd.DataFrame({'Frequency (Hz)': frequencies, 'PSD': psd})
    psd_df.to_csv(os.path.join(output_folder, f"{data_file}_psd.csv"), index=False)

def compute_imfs_and_save(data, sample_rate, output_folder, data_file, parallel=True, processes=4):
    """
    Computes Intrinsic Mode Functions (IMFs) using EEMD and saves them along with their PSDs.
    """
    eemd = EEMD(parallel=parallel, processes=processes)
    IMFs = eemd.eemd(data)
    
    imf_df = pd.DataFrame(IMFs).T
    imf_df.columns = [f'IMF_{i+1}' for i in range(len(IMFs))]
    imf_df.insert(0, 'Original', data)
    
    # Save all IMFs to CSV
    imf_df.to_csv(os.path.join(output_folder, f"{data_file}_IMFs.csv"), index=False)
    
    # Compute and save PSD for each IMF
    psd_imf_df = pd.DataFrame()
    psd_imf_df['Frequency (Hz)'] = welch(data, fs=sample_rate, nperseg=4096)[0]
    
    for i in range(len(IMFs)):
        _, psd_imf = welch(IMFs[i], fs=sample_rate, nperseg=4096)
        psd_imf_df[f'PSD_IMF_{i+1}'] = psd_imf
    
    psd_imf_df.to_csv(os.path.join(output_folder, f"{data_file}_All_IMFs_psd.csv"), index=False)

def process_hydrophone_data(src_path, sample_rate=16000):
    """
    Processes hydrophone data: reads data, computes PSDs and IMFs, and saves the results.
    """
    data_dict = read_hydrophone_data(src_path)
    
    for station in os.listdir(src_path):
        station_path = os.path.join(src_path, station)
        data_series_path = os.path.join(station_path, 'hydrophone', 'dataSeries')
        psd_folder = os.path.join(station_path, 'hydrophone', 'PSD')
        imf_folder = os.path.join(station_path, 'hydrophone', 'IMFs')
        
        os.makedirs(psd_folder, exist_ok=True)
        os.makedirs(imf_folder, exist_ok=True)
        
        for data_file in os.listdir(data_series_path):
            data = pd.read_csv(os.path.join(data_series_path, data_file))['Values'].values
            
            # Compute and save PSD
            compute_psd_and_save(data, sample_rate, psd_folder, data_file[:-4])
            
            # Compute and save IMFs and their PSDs
            compute_imfs_and_save(data, sample_rate, imf_folder, data_file[:-4])

if __name__ == "__main__":
    src_path = r'D:\ALFTool\Data\Hydrophones\Sample' ## change src path
    process_hydrophone_data(src_path)
