#!/usr/bin/env python
# coding: utf-8

# ## 1. Import Python Libraries 

# In[ ]:


import os
import scipy
import numpy as np
import pandas as pd

import scipy.integrate as spi


# ## 2. Define Data Paths 

# In[ ]:


srcPath = r'D:/00_Data/FromALFGCC/CorrectedTimeSeries' ## change your source path
stationSensorIdFile = 'stationSensorId.csv'
rawTimeSeriesFile = 'historical_till9May2024.csv'

stationSensorIdDf = pd.read_csv(srcPath + '/' + stationSensorIdFile)
rawTimeSeriesDf = pd.read_csv(srcPath + '/' + rawTimeSeriesFile)

# ## 3. Data Extractions 

# In[ ]:


pressureStationsFolder = srcPath + '/' + 'pressureStations'
pressureStationsFolder
if (not os.path.exists(pressureStationsFolder)): 
    os.mkdir(pressureStationsFolder)

idLst = list(stationSensorIdDf['Id'])
sensorNamesLst = list(stationSensorIdDf['Name'])

rawDf_StationSensor = list(rawTimeSeriesDf['StationSensorId'])
rawDf_Value = list(rawTimeSeriesDf['Value'])
rawDf_Timestamp = list(rawTimeSeriesDf['Timestamp'])

for i in range(len(idLst)):
    valueLst = []; timeStampLst = []
    for k in range(len(rawTimeSeriesDf)):
        if (rawDf_StationSensor[k] == idLst[i]):
            valueLst.append(rawDf_Value[k])
            
            ## dates && times
            dateItem = rawDf_Timestamp[k].split(' ')[0]
            timeItem = rawDf_Timestamp[k].split(' ')[-1]
            
            year = dateItem.split('-')[0]
            month = dateItem.split('-')[1]
            if len(month) == 2 and month[0] == '0': month = month[-1]
            day = dateItem.split('-')[-1]
            if len(day) == 2 and day[0] == '0': day = day[-1]
                
            timeStampLst.append(dateItem + ' ' + timeItem.split('.')[0][0:5])
    
    stationPressureDf = pd.DataFrame() 
    stationPressureDf['Timestamp'] = timeStampLst
    stationPressureDf['Value'] = valueLst
    stationPressureDf.sort_values(by='Timestamp', inplace = True)
    stationPressureDf.to_csv(pressureStationsFolder + '/' + sensorNamesLst[i] + '.csv',
                             index = False)


# ## 4. Daily Moving Average Pressure 

# In[ ]:


resultPath = srcPath + '/' + 'TotalPressure'
if (not os.path.exists(resultPath)): 
    os.mkdir(resultPath)

pressureFilesLst = os.listdir(pressureStationsFolder)

movingAvgWindow = 7 ## change the moving average window size; default is 7 days
deltaT = 1/96 ## 1/96 for 15mins interval and 1/288 for 5mins interval
mANegSlope_df = pd.DataFrame()
for pressureFile in pressureFilesLst:
    pressureDf = pd.read_csv(pressureStationsFolder + '/' + pressureFile)
    
    if len(pressureDf) != 0:
    
        timeStampLst = list(pressureDf['Timestamp'])
        valueLst = list(pressureDf['Value'])

        valueDict = dict()
        for j in range(len(timeStampLst)):
            if valueDict.get(timeStampLst[j].split(' ')[0],0) == 0: 
                valueDict[timeStampLst[j].split(' ')[0]] = []
            valueDict[timeStampLst[j].split(' ')[0]].append(valueLst[j])

        datesLst = []
        totalPressureLst = []
        mAPressureLst = []
        mASlopeLst = []

        for date, subValueLst in valueDict.items():
            datesLst.append(date)
            totalPressureLst.append(spi.trapezoid(subValueLst, dx = deltaT))

        for k in range(0, movingAvgWindow):
            mAPressureLst.append(np.nanmean(totalPressureLst[0:k+1]))

        for k in range(movingAvgWindow, len(totalPressureLst)):
            mAPressureLst.append(np.nanmean(totalPressureLst[k-movingAvgWindow+1:k+1]))

        for k in range(0, 2*movingAvgWindow):
            mASlopeLst.append('')

        for k in range(2*movingAvgWindow, len(totalPressureLst)):
            xy = np.array([[i + 1 for i in range(movingAvgWindow)],
                           mAPressureLst[k-movingAvgWindow+1:k+1]])
            mASlopeLst.append(scipy.stats.linregress(xy).slope)

        avgPressureDf = pd.DataFrame()
        avgPressureDf['Dates'] = datesLst
        avgPressureDf['TotalPressure'] = totalPressureLst
        avgPressureDf['MovingAvgPressure'] = mAPressureLst
        avgPressureDf['MovingAvgSlope'] = mASlopeLst
        avgPressureDf.to_csv(resultPath + '/' + pressureFile.split('.')[0] + '_MA.csv',
                             index = False)
        
        #Clustering the negative slope values (values <= -0.1) using 3 days of consecutive days
        new_df = avgPressureDf[['Dates','MovingAvgSlope']]
        new_df.loc[:, 'MovingAvgSlope'] = pd.to_numeric(new_df['MovingAvgSlope'], errors='coerce')
        new_df = new_df.dropna(subset=['MovingAvgSlope'], inplace=False)

        new_df = new_df[new_df['MovingAvgSlope'] <= -0.1]
        new_df["Dates"] = pd.to_datetime(new_df["Dates"], format="%Y-%m-%d")
        adjacent = new_df["Dates"].diff().dt.days.fillna(1).eq(1)         #check if adjacent rows are 1 day apart
        mask = new_df.groupby(adjacent.ne(adjacent.shift()).cumsum())["Dates"].transform('count').ge(3)
        new_df = new_df[mask|mask.shift(-1)]
        new_df['Sensor'] = pressureFile.split('.')[0]
        new_df.to_csv(resultPath + '/' + pressureFile.split('.')[0] + '_MA_negativeSlope.csv',index = False)
    mANegSlope_df = pd.concat([mANegSlope_df,new_df])
    mANegSlope_df.to_csv(resultPath + '/' + 'AllStations_MA_negativeSlope.csv',index = False)
    print(pressureFile.split('.')[0],': ',len(new_df), 'days of negative MA slope with sequence minimum 3 days')


# ## 5. Overlap the detected clusters with the detected events and the reported leak events.
### 5.1. Read detected system event and reported events data
## Data of ALF detected system events
df_detected = pd.read_csv('D:/01_Smart Water Grid/03_ALF_R&D/Model Evaluation (2024)/EventsList.csv')
#df_detected = df_detected[df_detected['MNF_low pressure'] == 1].reset_index(drop=True)
#df_detected = df_detected[df_detected['MNF_high flow'] == 1].reset_index(drop=True)
df_detected = df_detected[['Start Time','End Time','Duration','Zone','Event Sensors']]
## Data of PUB reported events
df_reported = pd.read_csv('D:/01_Smart Water Grid/03_ALF_R&D/Model Evaluation (2024)/ReportedLeaks_Jan-Mar24.csv')
df_reported = df_reported[['Original Leak Dates','Zone','Stations']]

### 5.2. Prepare data for the calculation
detectedStartDateLst = list(pd.to_datetime(df_detected['Start Time']))
detectedEndDateLst = list(pd.to_datetime(df_detected['End Time']))
detectedSensorLst = list(df_detected['Event Sensors'])
df_reported['Original Leak Dates'] = pd.to_datetime(df_reported['Original Leak Dates'], format='%d/%m/%Y')
reportedDateLst = list(df_reported['Original Leak Dates'])
reportedSensorLst = list(df_reported['Stations'])
NegSlopeDateLst = list(mANegSlope_df['Dates'])
NegSlopeSensorLst = list(mANegSlope_df['Sensor'])


### 5.3. Find detective events with negative MA slope
detected_MANegSlopeLst = ['' for i in range(len(detectedStartDateLst))]
for i in range(len(detectedStartDateLst)):
    sensors = detectedSensorLst[i].split(', ')
    for k in range(len(NegSlopeDateLst)):
        if ((detectedStartDateLst[i] <= NegSlopeDateLst[k]) 
            and (detectedEndDateLst[i] >= NegSlopeDateLst[k]) 
                and (NegSlopeSensorLst[k] in sensors)):
            detected_MANegSlopeLst[i] = detected_MANegSlopeLst[i] + NegSlopeSensorLst[k] + ', '
df_detected['MA_NegSlope Sensors'] = detected_MANegSlopeLst
df_detected.to_csv('Detected events with Neg MA Slope.csv')

### 5.4. Find reported events with negative MA slope
reported_MANegSlopeLst = ['' for i in range(len(reportedDateLst))]
for i in range(len(reportedDateLst)):
    sensors = reportedSensorLst[i].split(', ')
    for k in range(len(NegSlopeDateLst)):
        if ((reportedDateLst[i] == NegSlopeDateLst[k]) 
                and (NegSlopeSensorLst[k] in sensors)):
            reported_MANegSlopeLst[i] = reported_MANegSlopeLst[i] + NegSlopeSensorLst[k] + ', '
df_reported['MA_NegSlope Sensors'] = reported_MANegSlopeLst
df_reported.to_csv('Reported events with Neg MA Slope.csv')
