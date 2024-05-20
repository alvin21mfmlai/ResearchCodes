import numpy as np
import pandas as pd

### Data
## Data of ALF detected system events
df_detected = pd.read_csv('EventsList.csv')
df_detected = df_detected[['Start Time','Duration','Zone','Event Sensors']]
detectedDateLst = list(pd.to_datetime(df_detected['Start Time']))
detectedSensorLst = list(df_detected['Event Sensors'])

## Data of PUB reported events
df_reported = pd.read_csv('ReportedLeaks_Jan-Mar24.csv')
df_reported = df_reported[['Original Leak Dates','Zone','Stations']]
df_reported['Original Leak Dates'] = pd.to_datetime(df_reported['Original Leak Dates'], format='%d/%m/%Y')
reportedDateLst = list(df_reported['Original Leak Dates'])
reportedSensorLst = list(df_reported['Stations'])

## Set leak window
#pd.Timedelta(days=3) #lead-time
#pd.Timedelta(days=1) #lag-time


### Detect true positive or false positive
TPLst = []
for i in range(len(detectedDateLst)):
    index = 0
    sensors = detectedSensorLst[i].split(', ')
    for k in range(len(reportedDateLst)):
        if (detectedDateLst[i] < reportedDateLst[k]+pd.Timedelta(days=1)) and (detectedDateLst[i] > reportedDateLst[k]-pd.Timedelta(days=3)) and (reportedSensorLst[k] in sensors):
            index = 1
            break
    if (index == 1):
            TPLst.append(1)
    else:
            TPLst.append(0)

df_TorF = pd.concat([df_detected,pd.DataFrame(TPLst,columns=['T/F'])],axis=1)
df_TorF.to_csv('True or false of detected events.csv')


### Calculate TP, FP and precision (Confusion matrix)
df = df_TorF.groupby('Zone')['T/F'].agg(['sum','count']).rename(columns={'sum':'TP'})
df['Total detected events'] = df['count']
df['FP'] = df['Total detected events']-df['TP']
df['Precision%']=df['TP']/df['Total detected events']*100
df = df[['TP','FP','Total detected events','Precision%']]
df.to_csv('confusion matrix.csv')

######################## end of code ######################################################


