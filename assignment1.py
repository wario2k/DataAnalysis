import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
#this library is called for converting string dates to date time objects for comparison
import datetime 
#disabling copy warnings for testing
pd.set_option('mode.chained_assignment', None)
#location of our input data
INPUT_FILE_NAME = 'smallerSubset.csv' 
# Step 1 : reading data from the csv into a pandas dataframe 
raw_data = pd.read_csv(INPUT_FILE_NAME) 
#convert date strings to date objects for comparison later
raw_data['date'] = pd.to_datetime(raw_data['date'],infer_datetime_format=True)
raw_data['exdate'] = pd.to_datetime(raw_data['exdate'],infer_datetime_format=True)
#1a. is the volume > 0
isVolumeNotZero = raw_data['volume'] > 0
#store filtered values where volume is greater than zero
pVd = raw_data[isVolumeNotZero]

#filter for maturity days 
#calculating date difference and storing it in new maturityDays column 
pVd['maturityDays'] = pVd['exdate'] - pVd['date'] 
pVd['maturityDays'] = pVd['maturityDays']/np.timedelta64(1,'D')

#condition for 1b 
sevenFilter = pVd['maturityDays'] > 7
yearFilter = pVd['maturityDays'] <= 365
#1b.store maturity days between 7 & 365 
mFlt = pVd[sevenFilter & yearFilter]

#deleting extra data column 
#del mFlt['maturityDays'] leaving this in since it might be useful for sorting data later

#1c
#select call options whose strike-to-forward ratio > 1. As result, you
#only select out-of-the-money call options. (strike-to-forward ratio = strike price * 10^-3 / forward price)
mFlt['sfRatio'] = (mFlt['strike_price']/1000) / mFlt['forward_price']
checkSfRatio = mFlt['sfRatio'] > 1

#select call options whose strike-to-forward ratio > 1
posSfRatioCallOptions = mFlt[checkSfRatio & (mFlt['cp_flag'] == 'C')]

#condition for 1d sfRatio < 1 for put options
negSfRation = mFlt['sfRatio'] < 1
negSfRatioPutOptions = mFlt[negSfRation & (mFlt['cp_flag'] == 'P')]
print(negSfRatioPutOptions.head(3))

#merging the two data sets to get combined list that matches all criterias
validCallPutOptions = pd.concat([posSfRatioCallOptions,negSfRatioPutOptions])

#1e.drop values with empty implied volatility values
#dropna() is a function that drops any rows with empty values which would mean any empty impl-volatil rows would be dropped
dropEmpty = validCallPutOptions.dropna()

#1f. ask-bid > 0
dropEmpty['askBid'] = dropEmpty['best_offer'] - dropEmpty['best_bid'] #computing and storing it in a new column
#condition to check for positive askBids 
filterPositiveAskBid = dropEmpty['askBid'] > 0

#store filtered values in new table 
cleanData = dropEmpty[filterPositiveAskBid]
#delete extra column
del cleanData['askBid']

#allocating to DTM bins 
dtmBins = [0, 30, 60, 90, 120, 365]
binLabels = ['<30', '30-60', '60-90', '90-120','>120']
cleanData['Maturity_Bins'] = pd.cut(cleanData.maturityDays, dtmBins, labels= binLabels, right = False)

#cleanData.to_csv('maturityBins.csv',index = False)

#allocating bins for strike-forward ratios 
sfrBins = [0, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 5]
sfrLabels = ['<0.8', '0.8-1.0', '1.0-1.2', '1.2-1.4', '1.4-1.6', '1.6-1.8','>1.8']
cleanData['sfr_Bins'] = pd.cut(cleanData.sfRatio, sfrBins, labels=sfrLabels, right = False)


#example of group by usage -> df.groupby(['Animal']).mean()
#dfg = cleanData.groupby('Maturity_Bins').count()
#print(dfg)

dfr = cleanData.groupby('sfr_Bins').count()
print(dfr)

#finalDataSet.to_csv('out.csv', index=False)

# dfg.columns = dfg.columns.droplevel()
# dfg.columns = ['Observations', 'mean']