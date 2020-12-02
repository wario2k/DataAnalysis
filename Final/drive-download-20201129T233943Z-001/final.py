import numpy as np
import pandas as pd 
from pandas.tseries.offsets import *
from scipy import stats
import matplotlib.pyplot as plt
#this library is called for converting string dates to date time objects for comparison
import datetime as dt
import statsmodels.formula.api as smf
#disabling copy warnings for testing
pd.set_option('mode.chained_assignment', None)

MonthlReturns = "monthly_return_data.csv"
ResearchData = "research_data.CSV"
Annual = "annual_returns.csv"

# Load raw data
raw_data_monthly_returns = pd.read_csv(MonthlReturns) 
raw_data_research = pd.read_csv(ResearchData)
raw_data_research['DATE'] = pd.to_datetime(raw_data_research['DATE'],format="%Y%m")
#raw_data_research = raw_data_research.set_index('DATE')

_tmp_crsp = raw_data_monthly_returns[['PERMNO','DATE','RET']].sort_values(['PERMNO','DATE'])

_tmp_crsp['RET']= _tmp_crsp['RET'].fillna(0) 
_tmp_crsp['logret']=np.log(1+_tmp_crsp['RET'])

J = 6
_tmp_crsp2 = _tmp_crsp[['PERMNO','DATE','RET','logret']].sort_values(['PERMNO','DATE']).set_index('DATE')

umd = _tmp_crsp2.groupby(['PERMNO'])['logret'].rolling(J, min_periods=J).sum() 
umd = umd.reset_index()
#Calculate cumilative returns 
umd['cumret'] = np.exp(umd['logret']) - 1

# For each date assigning ranking 1-10 based on cumret
umd = umd.dropna(axis=0, subset=['cumret'])
umd['momr']=umd.groupby('DATE')['cumret'].transform(lambda x: pd.qcut(x, 10, labels=False))
# shift momr from 0-9 to 1-10
umd.momr=1+umd.momr.astype(int)

#Calculate Holding Period Return
#Line up month end date
umd['DATE'] = pd.to_datetime(umd['DATE'],format="%Y%m%d")
umd['form_date'] = umd['DATE']
umd['medate'] = umd['DATE']+ MonthEnd(0)
#start date of holding period
umd['hdate1']=umd['medate']+ MonthBegin(1) 
umd['hdate2']=umd['medate']+ MonthEnd(1) 
umd = umd[['PERMNO', 'form_date','momr','hdate1','hdate2']]

#calculate portfolio returns in the next month.
_tmp_ret = raw_data_monthly_returns[['DATE','PERMNO','RET']]
port = pd.merge(_tmp_ret, umd, on=['PERMNO'], how='inner')
port['DATE'] = pd.to_datetime(port['DATE'],format="%Y%m%d")
port = port[(port['hdate1']<=port['DATE']) & (port['DATE']<=port['hdate2'])] 
# rearrange cols
port = port[['PERMNO','form_date', 'momr', 'hdate1','hdate2', 'DATE', 'RET']]
umd_port = port.groupby(['DATE','momr', 'form_date'])['RET'].mean().reset_index()
umd_port = umd_port.sort_values(by=['DATE','momr'])

#umd2 = port.sort_values(by=['DATE','momr','form_date','PERMNO']).drop_duplicates() 
ewret = umd_port.groupby(['DATE','momr'])['RET'].mean().reset_index()
ewstd = umd_port.groupby(['DATE','momr'])['RET'].std().reset_index()

ewret = ewret.rename(columns={'RET':'ewret'})
ewstd = ewstd.rename(columns={'ret':'ewretstd'})

#create df for portfolio summary
ewretdf = pd.merge(ewret, ewstd, on=['DATE','momr'], how='inner')
ewretdf = ewretdf.sort_values(by=['momr', 'DATE'])
#summary for portfolio


# Transpose portfolio layout to have columns as portfolio returns
ewret_transposed = ewretdf.pivot(index='DATE', columns='momr', values='ewret')
ewret_transposed = ewret_transposed.add_prefix('port') # adding prefix for easier readability 
ewret_transposed = ewret_transposed.rename(columns={'port1':'losers', 'port10':'winners'})
ewret_transposed['long_short'] = ewret_transposed.winners - ewret_transposed.losers

# Compute Long-Short Portfolio Cumulative Returns
ewret_transposed['cumret_winners']   = (1+ewret_transposed.winners).cumprod()-1
ewret_transposed['cumret_losers']    = (1+ewret_transposed.losers).cumprod()-1
ewret_transposed['cumret_long_short'] = (1+ewret_transposed.long_short).cumprod()-1

# Portfolio Summary #
# Mean #
mom_mean = ewret_transposed[['winners', 'losers', 'long_short']].mean().to_frame()
mom_mean = mom_mean.rename(columns={0:'mean'}).reset_index()
# T-Value and P-Value #
t_losers = pd.Series(stats.ttest_1samp(ewret_transposed['losers'],0.0)).to_frame().T
t_winners = pd.Series(stats.ttest_1samp(ewret_transposed['winners'],0.0)).to_frame().T
t_long_short = pd.Series(stats.ttest_1samp(ewret_transposed['long_short'],0.0)).to_frame().T

t_losers['momr']='losers'
t_winners['momr']='winners'
t_long_short['momr']='long_short'

t_output = pd.concat([t_winners, t_losers, t_long_short]).rename(columns={0:'t-stat', 1:'p-value'})

# Combine mean, t and p and format output
mom_output = pd.merge(mom_mean, t_output, on=['momr'], how='inner')

mom_output['mean'] = mom_output['mean'].map('{:.2%}'.format)
mom_output['t-stat'] = mom_output['t-stat'].map('{:.2f}'.format)
mom_output['p-value'] = mom_output['p-value'].map('{:.3f}'.format)

print('Momentum Strategy Summary:\n\n', mom_output)


# # Regression Calculator #

ewret_subset = ewret_transposed.reset_index()
ewret_subset = ewret_subset[['DATE','long_short']]
#removing day for merge compatability 
ewret_subset['DATE'] = ewret_subset['DATE'].apply(lambda x: x.strftime('%Y-%m'))
raw_data_research['DATE'] = raw_data_research['DATE'].apply(lambda x: x.strftime('%Y-%m'))

regression_data = pd.merge(ewret_subset, raw_data_research, on=['DATE'], how='inner')
regression_data = regression_data.set_index("DATE")



### Graphing ###
plt.figure(figsize=(12,9))
plt.suptitle('Momentum Strategy', fontsize=20)
ax1 = plt.subplot(211)
ax1.set_title('Long/Short Momentum Strategy', fontsize=15)
ax1.set_xlim([dt.datetime(2000,1,1), dt.datetime(2020,12,31)])
ax1.plot(ewret_transposed['cumret_long_short'])
ax2 = plt.subplot(212)
ax2.set_title('Cumulative Momentum Portfolios', fontsize=15)
ax2.plot(ewret_transposed['cumret_winners'], 'b-', ewret_transposed['cumret_losers'], 'r--')
ax2.set_xlim([dt.datetime(2000,1,1), dt.datetime(2020,12,31)])
ax2.legend(('Winners','Losers'), loc='upper left', shadow=True)
plt.subplots_adjust(top=0.92, hspace=0.2)
plt.show()
