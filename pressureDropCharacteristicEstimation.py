# Purpose:
# In ALF we use 3 sigma rule to detect the outliers. 
# In order to understand more about the leak behavior for each specific zones and determine the optimal number of sigma.
# Here we perform back-engineering to estimate delta P 
# and its affiliated number of sigma values under leakage conditions.

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 20})


srcPath = r'D:/01_Smart Water Grid/03_ALF_R&D\Model Evaluation (2024)' ## change your source path
reportedLeakFile = 'ReportedLeaks_Jan-Mar24.csv'
reportedLeakDf = pd.read_csv(srcPath + '/' + reportedLeakFile)
reportedLeakDateList = list(reportedLeakDf['Original Leak Dates'])
reportedLeakStationList = list(reportedLeakDf['Stations'])
reportedLeakDf.shape[0]

#zoneLst = ["BBSR","NYSR","MNSR","SSR"]
zoneLst = ["SSR"]
#zoneLst = ["BBSR","NYSR","SSR"]

srcPath = srcPath + '/' + 'delta P estimation for historical events'

for zone in zoneLst:
    pressureStationsFolder = srcPath + '/' + 'leaks data' + '/' + zone
    #rawTimeSeriesFile = 'nysr_12.xlsx'
    pressureFilesLst = os.listdir(pressureStationsFolder)
    pressureFilesLst = [filename for filename in pressureFilesLst if filename.endswith('.xlsx')]

#######################################################################################################

    mNFHrLst = ['T02', 'T03', 'T04', 'T05:00']

    for pressureFile in pressureFilesLst:

        rawDf1 = pd.read_excel(pressureStationsFolder + '/' + pressureFile,'Forecasting')
        rawDf2 = pd.read_excel(pressureStationsFolder + '/' + pressureFile,'Adjusted Monitored')
        #print(len(rawDf1),'rows of time series pressure data')
        #print(rawDF1)

        # Back-engineering to estimate delta P
        resultPath = srcPath + '/' + 'delta P' + '/' + zone



        deltaPressureDf = rawDf1
        deltaPressureDf['Adjusted Monitored Value'] = rawDf2['Adjusted Monitored Value']
        deltaPressureDf['delta_P'] = rawDf1['Predicted Value'] - rawDf2['Adjusted Monitored Value']
        deltaPressureDf['sigma'] = (rawDf1['Upper Boundary']-rawDf1['Lower Boundary'])/6
        deltaPressureDf['mean'] = rawDf1['Lower Boundary']+3*rawDf1['sigma']
        #deltaPressureDf['delta_P'].replace('', np.nan, inplace=True)
        #deltaPressureDf.dropna(subset=['delta_P'], inplace=True)


        # calculate number of sigma
        deltaPressureDf['n_of_t'] = rawDf1['delta_P']/rawDf1['sigma']

        deltaPressureDf.to_csv(resultPath + '/' + pressureFile.split('.')[0] + '_delta P.csv',
                             index = False)
        deltaPressureMNFDf = deltaPressureDf[deltaPressureDf['Timestamp'].apply(lambda x: any(i in x for i in mNFHrLst))]

        
      
        
        # plot the histogram of n(t)
        plt.figure(figsize=[15,6])

        plt.subplot(121)
        n_bins = 20
#       bins = np.arange(-10, 10, 0.3)
        plt.hist(deltaPressureDf['n_of_t'], bins = 20, density=True, edgecolor='black', label='PDF')         # Plot PDF
#        plt.ecdf(deltaPressureDf['n_of_t'], label='CDF')         # Plot CDF
        plt.hist(deltaPressureDf['n_of_t'], n_bins, density=True, cumulative=True, label='CDF', histtype='step', alpha=0.6, color='r')
        plt.xlabel('n(t)')
        plt.ylabel('Probability')
#       xtick = [-9,-6,-3,0,3,6,9]
#       plt.xticks(xtick)
#       plt.xaxis.grid(True, which='minor')
#       plt.gca().tick_params(axis='x', which='minor', bottom=False)
#       plt.minorticks_on()
        plt.title(pressureFile.split('.')[0], )
        plt.legend()


        plt.subplot(122)
        n_bins = 10
        plt.hist(deltaPressureMNFDf['n_of_t'], bins = 10, density=True, edgecolor='black', color='turquoise', label='PDF')
#        plt.ecdf(deltaPressureMNFDf['n_of_t'], label='CDF', color='orange')         # Plot CDF
        plt.hist(deltaPressureMNFDf['n_of_t'], n_bins, density=True, cumulative=True, label='CDF', histtype='step', alpha=0.6, color='r')
        plt.xlabel('n(t)')
        plt.ylabel('Probability')
        plt.title(pressureFile.split('.')[0] + ' (MNF)')
        plt.legend()
        
        #hist, bins = np.histogram([item for item in deltaPressureMNFDf['n_of_t'] if item > 0], bins=10, density=True)
        #plt.show()

        plt.savefig(resultPath + '/' + pressureFile.split('.')[0] + '_histogram.png',dpi=200)

############################ Check sum of probabilities to be 1 ############################        
        #hist, bins = np.histogram([item for item in deltaPressureDf['n_of_t'] if item > 0], bins=100, density=False)
        #width = bins[1] - bins[0]  # Assuming equal width for all bins
        #finalN = np.sum([hist[i]*bins[i] for i in range(len(hist))]) / (np.sum(hist))
        #print(pressureFile.split('.')[0], ', E[n|n>0]=', finalN)
        #m = deltaPressureDf['n_of_t'].mean() if item > 0
        finalN = deltaPressureMNFDf.loc[deltaPressureMNFDf['n_of_t'] > 0, 'n_of_t'].mean() # Conditional expectation of n(t)|n(t)>0
        print(pressureFile.split('.')[0], ', E[n|n>0]=', finalN)

#cdf = 0
#for i in hist:
#     cdf = cdf+i
#print(cdf)







#plt.boxplot(deltaPressureDf['n_of_t'])
#plt.show()




