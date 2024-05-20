import numpy as np
import pandas as pd

scenarioDict = {"S1":0,
                "S2":1440,
                "S3":2880,
                "S4":4320}

### 1. Read detected system event and reported events data
## Data of ALF detected system events
df_detected = pd.read_csv('EventsList.csv')
df_detected = df_detected[['Start Time','End Time','Duration','Zone','Event Sensors']]

## Data of PUB reported events
df_reported = pd.read_csv('ReportedLeaks_Jan-Mar24.csv')
df_reported = df_reported[['Original Leak Dates','Zone','Stations']]

### 2. Prepare data for the calculation
detectedStartDateLst = list(pd.to_datetime(df_detected['Start Time']))
detectedEndDateLst = list(pd.to_datetime(df_detected['End Time']))
detectedSensorLst = list(df_detected['Event Sensors'])
df_reported['Original Leak Dates'] = pd.to_datetime(df_reported['Original Leak Dates'], format='%d/%m/%Y')
reportedDateLst = list(df_reported['Original Leak Dates'])
reportedSensorLst = list(df_reported['Stations'])

## Set leak window
leadTime = 3
lagTime = 1

### 3. Detect true positive or false positive
TPLst = []; leakDetectedLst = ['' for i in range(len(detectedStartDateLst))]
for i in range(len(detectedStartDateLst)):
    index = 0
    sensors = detectedSensorLst[i].split(', ')
    for k in range(len(reportedDateLst)):
        if ((detectedStartDateLst[i] <= reportedDateLst[k]+pd.Timedelta(days=lagTime)) \
            and (detectedStartDateLst[i] >= reportedDateLst[k]-pd.Timedelta(days=leadTime)) \
                and (reportedSensorLst[k] in sensors)) \
                    or ((detectedEndDateLst[i] <= reportedDateLst[k]+pd.Timedelta(days=lagTime)) \
                        and (detectedEndDateLst[i] >= reportedDateLst[k]-pd.Timedelta(days=leadTime)) \
                            and (reportedSensorLst[k] in sensors)):
            index = 1
            leakDetectedLst[i] = reportedDateLst[k]
            break
    if (index == 1): TPLst.append(1)
    else: TPLst.append(0)

df_detected['Leak Date Detected'] = leakDetectedLst
df_TorF = pd.concat([df_detected,pd.DataFrame(TPLst,columns=['T/F'])],axis=1)
df_TorF.to_csv('True or false of detected events.csv')

### 4. Calculate TP, FP and precision (Confusion matrix)
for scenario, timeThreshold in scenarioDict.items():
    df_ZoneGroup = df_TorF.groupby('Zone')
    df_ZoneGroup = df_ZoneGroup[['Duration', 'T/F']].apply(lambda x: x[x['Duration'] >= timeThreshold]['T/F'].agg(['sum','count'])).rename(columns={'sum':'TP'})
    df_ZoneGroup['Total detected events'] = df_ZoneGroup['count']
    df_ZoneGroup['FP'] = df_ZoneGroup['Total detected events']-df_ZoneGroup['TP']
    df_ZoneGroup['Precision%']=(df_ZoneGroup['TP']/df_ZoneGroup['Total detected events'])*100
    df_ZoneGroup = df_ZoneGroup[['TP','FP','Total detected events','Precision%']]
    df_ZoneGroup.to_csv('Confusion matrix_Scenario' + str(scenario) + '_' + str(timeThreshold) + 'mins.csv',
                         index = False)

# ### 4. Calculate TP, FP and precision (Confusion matrix)
# # Scenario 1: consider all system events
# df_ZoneGroup1 = df_TorF.groupby('Zone')['T/F'].agg(['sum','count']).rename(columns={'sum':'TP'})
# df_ZoneGroup1['Total detected events'] = df_ZoneGroup1['count']
# df_ZoneGroup1['FP'] = df_ZoneGroup1['Total detected events']-df_ZoneGroup1['TP']
# df_ZoneGroup1['Precision%']=df_ZoneGroup1['TP']/df_ZoneGroup1['Total detected events']*100
# df_ZoneGroup1 = df_ZoneGroup1[['TP','FP','Total detected events','Precision%']]
# df_ZoneGroup1.to_csv('Confusion matrix_Scenario 1.csv')

# # Scenario 2: duration<1440 (0 day)
# df_ZoneGroup2 = df_TorF.groupby('Zone')
# df_ZoneGroup2 = df_ZoneGroup2[['Duration', 'T/F']].apply(lambda x: x[x['Duration'] < 1440]['T/F'].agg(['sum','count'])).rename(columns={'sum':'TP'})
# df_ZoneGroup2['Total detected events'] = df_ZoneGroup2['count']
# df_ZoneGroup2['FP'] = df_ZoneGroup2['Total detected events']-df_ZoneGroup2['TP']
# df_ZoneGroup2['Precision%']=df_ZoneGroup2['TP']/df_ZoneGroup2['Total detected events']*100
# df_ZoneGroup2 = df_ZoneGroup2[['TP','FP','Total detected events','Precision%']]
# df_ZoneGroup2.to_csv('Confusion matrix_Scenario 2.csv')

# # Scenario 3: 1440<=duration<4320 (1-3 days)
# df_ZoneGroup3 = df_TorF.groupby('Zone')
# df_ZoneGroup3 = df_ZoneGroup3[['Duration', 'T/F']].apply(lambda x: x[(x['Duration'] >= 1440) & (x['Duration'] < 4320)]['T/F'].agg(['sum','count'])).rename(columns={'sum':'TP'})
# df_ZoneGroup3['Total detected events'] = df_ZoneGroup3['count']
# df_ZoneGroup3['FP'] = df_ZoneGroup3['Total detected events']-df_ZoneGroup3['TP']
# df_ZoneGroup3['Precision%']=df_ZoneGroup2['TP']/df_ZoneGroup3['Total detected events']*100
# df_ZoneGroup3 = df_ZoneGroup3[['TP','FP','Total detected events','Precision%']]
# df_ZoneGroup3.to_csv('Confusion matrix_Scenario 3.csv')

# # Scenario 4: duration>=4320 (>3 days)
# df_ZoneGroup4 = df_TorF.groupby('Zone')
# df_ZoneGroup4 = df_ZoneGroup4[['Duration', 'T/F']].apply(lambda x: x[x['Duration'] >= 4320]['T/F'].agg(['sum','count'])).rename(columns={'sum':'TP'})
# df_ZoneGroup4['Total detected events'] = df_ZoneGroup4['count']
# df_ZoneGroup4['FP'] = df_ZoneGroup4['Total detected events']-df_ZoneGroup4['TP']
# df_ZoneGroup4['Precision%']=df_ZoneGroup4['TP']/df_ZoneGroup4['Total detected events']*100
# df_ZoneGroup4 = df_ZoneGroup4[['TP','FP','Total detected events','Precision%']]
# df_ZoneGroup4.to_csv('Confusion matrix_Scenario 4.csv')

######################## end of code ######################################################


