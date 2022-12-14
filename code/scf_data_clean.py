"""
Download and create variables used in the Commentary.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import time, datetime, pyreadstat, sys, os
from io import BytesIO
from zipfile import ZipFile
import requests, zipfile
from urllib.request import urlopen
"""
Make folder for figures and data if none exists
"""
if not os.path.exists('../main/figures'):
    os.makedirs('../main/figures')

if not os.path.exists('../data'):
    os.makedirs('../data')
"""
Download data, list variables to keep, and join full public and summary dataset
"""
def data_from_url(url):
    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(BytesIO(r.content))
    z.extractall('../data/')
    return pd.read_stata('../data/{0}'.format(z.namelist()[0]))

tic = time.time()
url = 'https://www.federalreserve.gov/econres/files/scfp2019s.zip'
rscfp2019 = data_from_url(url)
toc = time.time()
print("Time to download summary dataset rscfp2019:", toc-tic)
tic = time.time()
url = 'https://www.federalreserve.gov/econres/files/scf2019s.zip'
p19i6 = data_from_url(url)
toc = time.time()
print("Time to download full public dataset p19i6:", toc-tic)

qctile_dict, cancel_list = {5:"quintile", 10:"decile"}, [10**4, 5*10**4]
var_list_p19i6 = ['yy1','y1','x7978','x7883','x7888','x7893','x7898','x7993',
'x7824','x7847','x7870','x7924','x7947','x7970']
p19i6 = p19i6[var_list_p19i6]
p19i6.set_index(['yy1','y1'],inplace=True)
rscfp2019.set_index(['yy1','y1'],inplace=True)
data = p19i6.join(rscfp2019, how='inner')
"""
Debt lists and debt brackets, and two functions for convenience
"""
debt_list = [0,1, 1.5*10**4, 4*10**4, np.inf]
debt_brackets = ["No debt","\$1-\$15,000", "\$15,001-\$40,000", "\$40,001+"]

c1,c2='lightsteelblue','darkblue'
def colorFader(c1,c2,mix):
    return mpl.colors.to_hex((1-mix)*np.array(mpl.colors.to_rgb(c1)) + mix*np.array(mpl.colors.to_rgb(c2)))

#weighted quantile function
def quantile(data, weights, quantile):
    if not isinstance(data, np.matrix):
        data = np.asarray(data)
    if not isinstance(weights, np.matrix):
        weights = np.asarray(weights)
    ind_sorted = np.argsort(data) #argsort gets the indices that sort the given array
    sorted_weights = weights[ind_sorted] #think of this as effectively the definition of argsort
    Sn = np.cumsum(sorted_weights)
    Pn = Sn/Sn[-1] #alternative: Pn = (Sn-0.5*sorted_weights)/Sn[-1]
    return np.interp(quantile, Pn, data[ind_sorted]) #x, xp, fp
slice_fun = {}
slice_fun['Borrowers'] = lambda df: df[df['percap_all_loans']>0]
slice_fun['All'] = lambda df: df
"""
Variables and questions for student debt
"""
#For whose education was (this/the largest/the next largest) loan taken out?
#1=self, 2=spouse, 3=child, 4=grandchild, 5=other relative, -7=other, 0=NA/Inappropriate
whom_list = ['x7978', 'x7883', 'x7888', 'x7893', 'x7898', 'x7993']
#How much is still owed on this loan? 0=NA/Inappropriate, otherwise dollar amount
bal_list = ['x7824', 'x7847', 'x7870', 'x7924', 'x7947', 'x7970']
"""
Following suppresses a Python warning about defining too many variables
(taken from https://github.com/twopirllc/pandas-ta/issues/340)
"""
from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
"""
Loans (parent and grandparent absorbed into "parent" category) and categorical age variable
"""
for i in range(6):
    data['self_loan{0}'.format(i+1)] = data[bal_list[i]]*(data[whom_list[i]]==1)
    data['spouse_loan{0}'.format(i+1)] = data[bal_list[i]]*(data[whom_list[i]]==2)
    data['parent_loan{0}'.format(i+1)] = data[bal_list[i]]*data[whom_list[i]].isin([3,4])
data['self_loans'] = data[['self_loan{0}'.format(i+1) for i in range(6)]].sum(axis=1)
data['spouse_loans'] = data[['spouse_loan{0}'.format(i+1) for i in range(6)]].sum(axis=1)
data['parent_loans'] = data[['parent_loan{0}'.format(i+1) for i in range(6)]].sum(axis=1)
data['all_loans'] = data['self_loans'] + data['spouse_loans'] + data['parent_loans']
for var in ['all_loans','wageinc','income','asset','networth']:
    data['percap_' + var] = (1 - (data['married']==1)/2)*data[var]
age_labels = ["26-30","31-35","36-40","41-45","46-50","51-55","56-60"]
age_values = [25,30,35,40,45,50,55,60]
#remember pd.cut does not include the left-hand point in the bracket
data['age_cat'] = pd.cut(data['age'],bins=age_values,labels=range(len(age_values)-1))
"""
Deciles and quintiles for networth and income for whole population and by age.
Sometimes need duplicates='drop' as argument of pd.cut if qctiles not unique.
"""
for var in ["income", "networth"]:
    for num in [10,5]:
        #var+'_cat{0}' will begin at zero. qctiles inclusive of endpoints.
        qctiles = np.array([quantile(data[var], data['wgt'], j/num) for j in range(num+1)])
        data[var+'_cat{0}'.format(num)] = pd.cut(data[var], bins=qctiles, labels=range(len(qctiles)-1))
        qctiles = np.array([quantile(data['percap_'+var], data['wgt'], j/num) for j in range(num+1)])
        data['percap_'+var+'_cat{0}'.format(num)] = pd.cut(data['percap_'+var], bins=qctiles, labels=range(len(qctiles)-1))
        #age-specific quantiles
        for age_cat in range(len(age_labels)):
            data_temp = data[data['age_cat']==age_cat]
            qctiles = np.array([quantile(data_temp[var], data_temp['wgt'], j/num) for j in range(num+1)])
            data[var+'_cat{0}{1}'.format(num,age_cat)] = pd.cut(data_temp[var], bins=qctiles, labels=range(len(qctiles)-1))
            qctiles = np.array([quantile(data_temp['percap_'+var], data_temp['wgt'], j/num) for j in range(num+1)])
            data['percap_'+var+'_cat{0}{1}'.format(num,age_cat)] = pd.cut(data_temp['percap_'+var],bins=qctiles,labels=range(len(qctiles)-1))
"""
Cancelled quantities
"""
for cancel in cancel_list:
    data['self_cancel{0}'.format(cancel)] = np.minimum(cancel, data['self_loans'] + data['parent_loans'])
    data['spouse_cancel{0}'.format(cancel)] = np.minimum(cancel, data['spouse_loans'])
    data['percap_cancel{0}'.format(cancel)] = (1 - (data['married']==1)/2)*(data['self_cancel{0}'.format(cancel)] + data['spouse_cancel{0}'.format(cancel)])
