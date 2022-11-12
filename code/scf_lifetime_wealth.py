"""
Lifetime wealth calculations and figures
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import time, datetime, pyreadstat, sys
import scf_data_clean, itertools
"""
Obtain data from scf_data_clean.
"""
data = scf_data_clean.data
age_labels, age_values = scf_data_clean.age_labels, scf_data_clean.age_values
slice_fun = scf_data_clean.slice_fun
qctile_dict, cancel_list = scf_data_clean.qctile_dict, scf_data_clean.cancel_list
c1, c2 = scf_data_clean.c1, scf_data_clean.c2
colorFader = scf_data_clean.colorFader
debt_list = scf_data_clean.debt_list
debt_brackets = scf_data_clean.debt_brackets
"""
Lifetime wealth function. Takes dataframe, aggregate growth rate (zero in Commentary),
discount rate (rf=0.04 in Commentary) and end date for one's life (80 in Commentary).
"""
def lifetime_wealth(df,g,rf,end_date):
    #create series for current income, per-capita income and discounted income.
    df['income0'] = df['income']
    df['percap_income0'] = df['percap_income']
    df['percap_income0disc'] = df['percap_income']
    #create median incomes for each age group.
    I_med = df.groupby(df['age_cat'])['income'].agg(lambda x: scf_data_clean.quantile(x,df.loc[x.index,"wgt"],0.5)).values
    #specify assumed growth rates of income.
    grow = np.append(np.log(I_med[1:]/I_med[:-1])/5 + g, g)
    #create dictionary mapping age groups to growth rates.
    grow_dict = dict(zip(range(len(age_labels)),list(grow)))
    #construct future income and per-capita income and discount.
    for t in range(end_date-1):
        #get growth between t and t+1 by applying grow_dict to age categorical.
        gr = pd.cut(df['age']+t,bins=age_values,labels=range(len(age_values)-1)).map(grow_dict)
        #compute next year income and discounted income if alive.
        df['income{0}'.format(t+1)] = (df['age']+t+1<=end_date)*df['income{0}'.format(t)]*np.exp(gr.astype(float))
        df['percap_income{0}'.format(t+1)] = (df['age']+t+1<=end_date)*df['percap_income{0}'.format(t)]*np.exp(gr.astype(float))
        df['percap_income{0}disc'.format(t+1)] = np.exp(-rf*(t+1))*df['percap_income{0}'.format(t+1)]
    df['percap_LT_income'] = df[['percap_income{0}disc'.format(t) for t in range(end_date)]].sum(axis=1)
    return df['percap_LT_income'] + df['percap_networth']
"""
Create qctiles for lifetime wealth. Takes dataframe, adds series
using above lifetime_wealth function and computes categorical variables.
"""
def lifetime_wealth_qctiles(df,g,rf,end_date,num):
    df['percap_'+'LT_wealth'] = lifetime_wealth(df,g,rf,end_date)
    for num in [10,5]:
        #whole population
        qctiles = np.array([scf_data_clean.quantile(df['percap_'+'LT_wealth'], df['wgt'], j/num) for j in range(num+1)])
        df['percap_'+'LT_wealth'+'_cat{0}'.format(num)] = pd.cut(df['percap_'+'LT_wealth'],bins=qctiles,labels=range(len(qctiles)-1),include_lowest=True, duplicates='drop')
        #now each age group
        for age_cat in range(len(age_labels)):
            df_temp = df[df['age_cat']==age_cat]
            qctiles = np.array([scf_data_clean.quantile(df_temp['percap_'+'LT_wealth'], df_temp['wgt'], j/num) for j in range(num+1)])
            #add additional suffix for age category
            df['percap_'+'LT_wealth'+'_cat{0}{1}'.format(num,age_cat)] = pd.cut(df_temp['percap_'+'LT_wealth'],bins=qctiles,labels=range(len(qctiles)-1),include_lowest=True, duplicates='drop')
    return df
"""
Average student debt by lifetime wealth qctiles. Takes dataframe and parameters
governing income growth and qctile number and produces and plots average debt levels.
"""
def lifetime_wealth_SD(df,g,rf,end_date,num,show=0):
    df, df_SD = lifetime_wealth_qctiles(df,g,rf,end_date,num), {}
    df_SD['borrowers'] = pd.DataFrame(columns=range(1,num+1),index=['LT_wealth'])
    df_SD['all'] = pd.DataFrame(columns=range(1,num+1),index=['LT_wealth'])
    for var2 in ['borrowers','all']:
        if var2 == 'borrowers':
            df_temp = df[df['percap_all_loans']>0]
        else:
            df_temp = df
        f = lambda x: np.average(x, weights=df_temp.loc[x.index, "wgt"])
        gb = df_temp.groupby('percap_'+'LT_wealth'+'_cat{0}'.format(num))['percap_'+'all_loans'].agg(f).values
        if len(gb) < num:
            df_SD[var2].loc['LT_wealth',num+1-len(gb):] = gb
            df_SD[var2].loc['LT_wealth',:num+1-len(gb)] = gb[0]
        else:
            df_SD[var2].loc['LT_wealth',:] = gb
        df_SD[var2] = (df_SD[var2]/1000).astype(float).round(1)
    width = 1/5
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i in range(1,num+1):
        if i==1:
            ax.bar(i-width, df_SD['borrowers'].loc['LT_wealth',i], 2*width, color=c1, label = "Borrowers")
            ax.bar(i+width, df_SD['all'].loc['LT_wealth',i], 2*width, color=c2, label = "All")
        else:
            ax.bar(i-width, df_SD['borrowers'].loc['LT_wealth',i], 2*width, color=c1)
            ax.bar(i+width, df_SD['all'].loc['LT_wealth',i], 2*width, color=c2)
    ax.set_xlabel('Per capita lifetime wealth {0}s ($r = ${1}%)'.format(qctile_dict[num],int(100*rf)))
    ax.set_title('Average student debt')
    ax.set_ylabel('\$000s')
    ax.legend(loc='upper left')
    plt.ylim([0,45])
    destin = '../main/figures/SD{0}lifetime_wealth{1}{2}.eps'.format(qctile_dict[num],int(100*g),int(100*rf))
    plt.savefig(destin, format='eps', dpi=1000)
    if show == 1:
        plt.show()
    plt.close()
"""
Count of debtors by lifetime wealth quintile
"""
def lifetime_wealth_debt_count(df,g,rf,end_date,num,show=0):
    df = lifetime_wealth_qctiles(df,g,rf,end_date,num)
    qctiles = np.array([scf_data_clean.quantile(df['percap_'+'LT_wealth'],data['wgt'], j/num) for j in range(num+1)])
    qct_lists, var_names = [qctiles,debt_list],['percap_'+'LT_wealth','percap_all_loans']
    d = [pd.cut(df[var_names[i]], bins=qct_lists[i],labels=range(len(qct_lists[i])-1),include_lowest=True,duplicates='drop') for i in range(2)]
    df['pairs'] = list(zip(d[0], d[1]))
    SD_debt_count = df.groupby(df['pairs'])['wgt'].sum()
    for key in list(itertools.product(range(num), range(len(debt_brackets)))):
        if key not in list(SD_debt_count.keys()):
            SD_debt_count = pd.concat([SD_debt_count, pd.Series([0], index=[key])])
    width = 1/5
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i in range(len(qctiles)-1):
        norm = sum([SD_debt_count[(i,j)] for j in range(len(debt_list)-1)])
        for j in range(len(debt_list)-1):
            if i==0:
                ax.bar(i+1-((len(debt_list)-2)/2-j)*width,SD_debt_count[(i,j)]/norm,width,color=colorFader(c1,c2,j/(len(debt_list)-2)),label=debt_brackets[j])
            else:
                ax.bar(i+1-((len(debt_list)-2)/2-j)*width,SD_debt_count[(i,j)]/norm,width,color=colorFader(c1,c2,j/(len(debt_list)-2)))
    ax.set_xlabel('Per capita lifetime wealth {0}s ($r = ${1}%)'.format(qctile_dict[num],int(100*rf)))
    ax.set_title('Fraction of population')
    ax.legend()
    ax.set_ylim([0, 1])
    destin = '../main/figures/lifetime_wealth_debt_count{0}{1}.eps'.format(int(100*g),int(100*rf))
    plt.savefig(destin, format='eps', dpi=1000)
    if show == 1:
        plt.show()
    plt.close()

def cancellation_lifetime_wealth(df,g,rf,end_date,num,show=0):
    df = lifetime_wealth_qctiles(df,g,rf,end_date,num)
    gb = df.groupby(df['percap_'+'LT_wealth'+'_cat{0}'.format(num)])
    f = lambda x: np.average(x, weights=df.loc[x.index, "wgt"])
    array_temp = np.zeros((num,len(cancel_list)))
    for i, cancel in enumerate(cancel_list):
        array_temp[:,i] = gb['percap_cancel{0}'.format(cancel)].agg(f)
        width = 2/5
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for j in range(num):
            ax.bar(j+1, array_temp[j,i], 2*width, color=c2)
        plt.xticks(np.arange(1, num+1))
        ax.set_xlabel('Per capita lifetime wealth {0}s ($r = ${1}%)'.format(qctile_dict[num],int(100*rf)))
        ax.set_ylabel('\$')
        ax.set_title('Up to \${0},000 forgiven'.format(int(cancel/10**3)))
        destin = '../main/figures/cancellifetime_wealth{0}{1}{2}{3}.eps'.format(qctile_dict[num],cancel,int(100*g),int(100*rf))
        plt.savefig(destin, format='eps', dpi=1000)
        if show == 1:
            plt.show()
    plt.close()

g_list, rf_list = [0], [0.04,0.07,0.1]
end_date = 80
num = 5 #5 = quintiles, 10 = deciles
for g in g_list:
    for rf in rf_list:
        print("Computing plots for (g,rf) = ", (g,rf))
        plt.rcParams.update({'figure.max_open_warning': 0})
        pd.set_option('mode.chained_assignment', None)
        lifetime_wealth_SD(data,g,rf,end_date,num,show=0)
        lifetime_wealth_debt_count(data,g,rf,end_date,num,show=0)
        cancellation_lifetime_wealth(data,g,rf,end_date,num,show=0)
