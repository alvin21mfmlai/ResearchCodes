# Purpose:
# In ALF we use 3 sigma rule to detect the outliers. But currently the actual leak quantum is unknown.
# In order to understand more about the leak behavior for each specific zones and determine the optimal number of sigma.
# Here we perform back-engineering to estimate delta P 
# and its affiliated number of sigma values under leakage conditions.

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



#zone = 'BBSR' ## change zone
srcPath = r'D:/01_Smart Water Grid/03_ALF_R&D\Model Evaluation (2024)' ## change your source path
reportedLeakFile = 'ReportedLeaks_Jan-Mar24.csv'
reportedLeakDf = pd.read_csv(srcPath + '/' + reportedLeakFile)
reportedLeakDateList = list(reportedLeakDf['Original Leak Dates'])
reportedLeakStationList = list(reportedLeakDf['Stations'])

zoneLst = ["BBSR","NYSR","MNSR","SSR"]
srcPath = srcPath + '/' + 'delta P estimation for historical events'

for zone in zoneLst:
    pressureStationsFolder = srcPath + '/' + 'leaks data' + '/' + zone
    #rawTimeSeriesFile = 'nysr_12.xlsx'
    pressureFilesLst = os.listdir(pressureStationsFolder)
    pressureFilesLst = [filename for filename in pressureFilesLst if filename.endswith('.xlsx')]

#######################################################################################################
    plt.rcParams.update({'font.size': 20})

    mNFHrLst = ['T02', 'T03', 'T04', 'T05:00']

    for pressureFile in pressureFilesLst:
        #pressureFile = pressureFilesLst[0]

        rawDf1 = pd.read_excel(pressureStationsFolder + '/' + pressureFile,'Forecasting')
        rawDf2 = pd.read_excel(pressureStationsFolder + '/' + pressureFile,'Adjusted Monitored')
        print(len(rawDf1),'rows of time series pressure data')


        # Back-engineering to estimate delta P
        resultPath = srcPath + '/' + 'delta P' + '/' + zone



        deltaPressureDf = rawDf1
        deltaPressureDf['Adjusted Monitored Value'] = rawDf2['Adjusted Monitored Value']
        deltaPressureDf['delta_P'] = rawDf1['Predicted Value'] - rawDf2['Adjusted Monitored Value']
        deltaPressureDf['sigma'] = (rawDf1['Upper Boundary']-rawDf1['Lower Boundary'])/6
        deltaPressureDf['mean'] = rawDf1['Lower Boundary']+3*rawDf1['sigma']

        # calculate number of sigma
        deltaPressureDf['n_of_t'] = rawDf1['delta_P']/rawDf1['sigma']

        deltaPressureDf.to_csv(resultPath + '/' + pressureFile.split('.')[0] + '_delta P.csv',
                             index = False)
        deltaPressureMNFDf = deltaPressureDf[deltaPressureDf['Timestamp'].apply(lambda x: any(i in x for i in mNFHrLst))]

        # plot the histogram of n(t)
        bins = np.arange(0, 6, 0.3)
        plt.figure(figsize=[15,6])

        plt.subplot(121)
        plt.hist(deltaPressureDf['n_of_t'], bins, edgecolor='black')
        plt.xlabel('n(t)')
        plt.ylabel('Frequency')
        plt.title(pressureFile.split('.')[0], )

        plt.subplot(122)
        plt.hist(deltaPressureMNFDf['n_of_t'], bins, edgecolor='black', color='turquoise')
        plt.xlabel('n(t)')
        plt.ylabel('Frequency')
        plt.title(pressureFile.split('.')[0] + ' (MNF)')
        plt.savefig(resultPath + '/' + pressureFile.split('.')[0] + '_histogram.png',dpi=200)
    #    plt.show()

## Set the y-axis lower limit to 0
#ax = plt.gca()
#ax.set_ylim(bottom=0.)




#plt.boxplot(deltaPressureDf['n_of_t'])
#plt.show()


