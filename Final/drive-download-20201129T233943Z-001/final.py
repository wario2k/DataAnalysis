import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
#this library is called for converting string dates to date time objects for comparison
import datetime 
#disabling copy warnings for testing
pd.set_option('mode.chained_assignment', None)

MonthlReturns = "monthly_return_data.csv"
ResearchData = "research_data.CSV"

#load raw data
raw_data_monthly_returns = pd.read_csv(MonthlReturns) 
raw_data_research = pd.read_csv(ResearchData)
#parse date string into date time object
#raw_data_monthly_returns['DATE'] = pd.to_datetime(raw_data_monthly_returns['DATE'],format="%Y%m%d")
#print(raw_data_monthly_returns.head(5))
#print('----------------------')
#print(raw_data_research.head(5))

#Calculate cumulative returns for past 12 months.
NumberOfMonths = 12
_tmp_crsp = raw_data_monthly_returns[['PERMNO','DATE','RET']].sort_values(['PERMNO','DATE']).set_index('DATE')

_tmp_crsp['RET']= _tmp_crsp['RET'].fillna(0) 
_tmp_crsp['logret']=np.log(1+_tmp_crsp['RET'])

umd = _tmp_crsp.groupby(['PERMNO'])['logret'].rolling(12, min_periods=12).sum() 
umd = umd.reset_index()
#calculate cumilative returns 
umd['cumret'] = np.exp(umd['logret']) - 1
umd = umd.dropna(subset=['cumret', 'logret'])


umd['momr']=umd.groupby('DATE')['cumret'].transform(lambda x: pd.qcut(x, 12, labels=False))

umd = umd.set_index('DATE')

print(umd.head(13))
