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


srcPath = r'D:\ALFTool\Data\FromALFGCC\CorrectedTimeSeries' ## change your source path
stationSensorIdFile = 'stationSensorId.csv'
rawTimeSeriesFile = 'historical_till9May2024.csv'

stationSensorIdDf = pd.read_csv(srcPath + '/' + stationSensorIdFile)
rawTimeSeriesDf = pd.read_csv(srcPath + '/' + rawTimeSeriesFile)


# ## 3. Data Extractions 

# In[ ]:


pressureStationsFolder = srcPath + '/' + 'pressureStations'
if not os.path.exists(pressureStationsFolder): os.mkdir(pressureStationsFolder)

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
if not os.path.exists(resultPath): os.mkdir(resultPath)

pressureFilesLst = os.listdir(pressureStationsFolder)

movingAvgWindow = 7 ## change the moving average window size; default is 7 days
deltaT = 1/96 ## 1/96 for 15mins interval and 1/288 for 5mins interval

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


# In[ ]:

