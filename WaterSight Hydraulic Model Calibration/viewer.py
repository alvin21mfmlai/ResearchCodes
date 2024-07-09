weekday_weekend_dict = dict()
weekday_weekend_dict[0] = 'Monday'
weekday_weekend_dict[1] = 'Tuesday'
weekday_weekend_dict[2] = 'Wednesday'
weekday_weekend_dict[3] = 'Thursday'
weekday_weekend_dict[4] = 'Friday'
weekday_weekend_dict[5] = 'Saturday'
weekday_weekend_dict[6] = 'Sunday'

weekday_weekend_baseDates_dict = dict()
weekday_weekend_baseDates_dict[0] = '1/1/2000'
weekday_weekend_baseDates_dict[1] = '2/1/2000'
weekday_weekend_baseDates_dict[2] = '3/1/2000'
weekday_weekend_baseDates_dict[3] = '4/1/2000'
weekday_weekend_baseDates_dict[4] = '5/1/2000'
weekday_weekend_baseDates_dict[5] = '6/1/2000'
weekday_weekend_baseDates_dict[6] = '7/1/2000'

import os
import dash
import json
import datetime
import pandas as pd
import numpy as np
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

selectedZone = 'Schiedam Vlaardingen' ## change zone name
srcPath = r'D:\WaterSights\Netherlands\HydraulicData\zones' ## change src path 

zoneSrcPath = os.path.join(srcPath, selectedZone, 'Raw')
if not os.path.exists(zoneSrcPath): os.mkdir(zoneSrcPath)
zoneProcessedPath = os.path.join(srcPath, selectedZone, 'Processed')
if not os.path.exists(zoneProcessedPath): os.mkdir(zoneSrcPath)

# List of CSV file paths
file_paths = [os.path.join(zoneSrcPath, item) for item in os.listdir(zoneSrcPath) if item.endswith('.csv')]

# Dictionary to hold data for each file
data_dict = {}

# Load and process each file
for file_path in file_paths:
    data = pd.read_csv(file_path)
    data['datetime'] = pd.to_datetime(data['Datetime'])
    data = data.sort_values(by='datetime')
    min_value = data['Value'].min()
    max_value = data['Value'].max()
    std_value = data['Value'].std()
    data_dict[file_path] = {
        'data': data,
        'min': min_value,
        'max': max_value,
        'std': std_value
    }

# Global variables to store the dates and current file
start_date_global = None
end_date_global = None
current_file = None

# Create the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(
        id='file-dropdown',
        options=[{'label': os.path.basename(file_path)[:-4], 
                  'value': file_path} for file_path in file_paths],
        value=file_paths[0]  # Default value
    ),
    dcc.Graph(id='time-series-plot'),
    html.Div(id='output-container-range-slider'),
    html.Div(id='resampled-data-output')
])

# Create summary averaged dataframe
try:
    avgSummaryDf = pd.read_csv(os.path.join(zoneProcessedPath, f'{selectedZone}_AvgData.csv'))
except FileNotFoundError:
    avgSummaryDf = pd.DataFrame()

# Create dictionary of start and end dates for each sensor
try:
    with open(os.path.join(zoneProcessedPath, f'{selectedZone}_Dates.json'), 'r') as f:
        stationDatesRecords = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    stationDatesRecords = {}

@app.callback(
    [Output('time-series-plot', 'figure'),
     Output('output-container-range-slider', 'children'),
     Output('resampled-data-output', 'children')],
    [Input('file-dropdown', 'value'),
     Input('time-series-plot', 'relayoutData')]
)
def update_output(selected_file, relayoutData):
    global start_date_global, end_date_global, current_file, avgSummaryDf, stationDatesRecords

    if current_file != selected_file:
        start_date_global = None
        end_date_global = None

    current_file = selected_file
    data_info = data_dict[selected_file]
    data = data_info['data']
    min_value = data_info['min']
    max_value = data_info['max']
    std_value = data_info['std']

    figure = {
        'data': [
            go.Scatter(
                x=data['datetime'],
                y=data['Value'],
                mode='lines',
                name=os.path.basename(selected_file).split('.')[0]
            )
        ],
        'layout': go.Layout(
            title=os.path.basename(selected_file).split('.')[0] + f' (Min: {min_value}, Max: {max_value}, Std: {std_value:.2f})',
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label='1d', step='day', stepmode='backward'),
                        dict(count=7, label='1w', step='day', stepmode='backward'),
                        dict(count=1, label='1m', step='month', stepmode='backward'),
                        dict(step='all')
                    ])
                ),
                rangeslider=dict(visible=True),
                type='date',
                range=[start_date_global, end_date_global] if start_date_global and end_date_global else [data['datetime'].min(), data['datetime'].max()]
            )
        )
    }

    if relayoutData and 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
        start_date_global = relayoutData['xaxis.range[0]']
        end_date_global = relayoutData['xaxis.range[1]']
        
        firstIndex = [str(item).split(" ")[0] for item in data['datetime']].index(str(start_date_global).split(" ")[0])
        endIndex = [str(item).split(" ")[0] for item in data['datetime']].index(str(end_date_global).split(" ")[0])
        
        extractedDf = data.iloc[firstIndex:endIndex,:]

        ## Generate weekly averaged data ##
        dataDict = dict()
        dateTimeLst = list(extractedDf['Datetime'])
        valueLst = list(extractedDf['Value'])
        summaryDf = pd.DataFrame()
        summaryDf['Datetime'] = dateTimeLst
        summaryDf['Value'] = valueLst
        summaryDf.to_csv(os.path.join(zoneProcessedPath, f"{os.path.basename(selected_file)[:-4]}.csv"), index=False)
        
        for i in range(len(dateTimeLst)):
            dummyDate = dateTimeLst[i].split(' ')[0]
            dummyTime = dateTimeLst[i].split(' ')[-1]
            dummyDate = dummyDate.split('/')[1] + '/' + dummyDate.split('/')[0] + '/' + dummyDate.split('/')[-1]
            given_date = datetime.datetime.strptime(dummyDate, '%d/%m/%Y')
            
            if dataDict.get(weekday_weekend_dict[given_date.weekday()],0) == 0:
                dataDict[weekday_weekend_dict[given_date.weekday()]] = dict()
                if dataDict[weekday_weekend_dict[given_date.weekday()]].get(dummyTime,0) == 0: 
                    dataDict[weekday_weekend_dict[given_date.weekday()]][dummyTime] = []
                    dataDict[weekday_weekend_dict[given_date.weekday()]][dummyTime].append(valueLst[i])
                else:
                    dataDict[weekday_weekend_dict[given_date.weekday()]][dummyTime].append(valueLst[i])
            else:
                if dataDict[weekday_weekend_dict[given_date.weekday()]].get(dummyTime,0) == 0: 
                    dataDict[weekday_weekend_dict[given_date.weekday()]][dummyTime] = []
                    dataDict[weekday_weekend_dict[given_date.weekday()]][dummyTime].append(valueLst[i])
                else:
                    dataDict[weekday_weekend_dict[given_date.weekday()]][dummyTime].append(valueLst[i])
            dataDict[weekday_weekend_dict[given_date.weekday()]][dummyTime].append(valueLst[i])
        
        averagedDateTimesLst = []
        avgValuesLst = []
        for z in range(len(dataDict)):
            weekday_weekend = weekday_weekend_dict[z]
            dateItem = weekday_weekend_baseDates_dict[z]
            extractedData = dataDict[weekday_weekend]
            for key, valueLst in extractedData.items():
                averagedDateTimesLst.append(dateItem + ' ' + key)
                avgValuesLst.append(np.nanmean(valueLst))

        avgSummaryDf['Datetime'] = averagedDateTimesLst
        avgSummaryDf[os.path.basename(selected_file)[:-4]] = avgValuesLst
        avgSummaryDf.to_csv(zoneProcessedPath + '/' + selectedZone + '_AvgData.csv',
                            index = False)
        avgSummaryDf.to_csv(os.path.join(zoneProcessedPath, f'{selectedZone}_AvgData.csv'), index=False)

        stationDatesRecords[os.path.basename(selected_file)[:-4]] = {
            'StartDate': start_date_global,
            'EndDate': end_date_global
        }
        with open(os.path.join(zoneProcessedPath, f'{selectedZone}_Dates.json'), 'w') as outfile:
            json.dump(stationDatesRecords, outfile)

        return figure, f'Start: {start_date_global}, End: {end_date_global}', f"Summary Data: {summaryDf.head().to_dict('records')}"

    return figure, 'Slide the range slider to capture the start and end dates.', ''

if __name__ == '__main__':
    app.run_server(debug=True)
