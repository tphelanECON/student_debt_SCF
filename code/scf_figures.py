"""
Main figures relevant for Commentary (excluding lifetime wealth calculations)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time, datetime, pyreadstat, sys
import scf_data_clean
"""
Obtain data, lists and functions from scf_data_clean.
"""
data = scf_data_clean.data
age_labels, values = scf_data_clean.age_labels, scf_data_clean.age_values
slice_fun = scf_data_clean.slice_fun
qctile_dict, cancel_list = scf_data_clean.qctile_dict, scf_data_clean.cancel_list

c1, c2 = scf_data_clean.c1, scf_data_clean.c2
colorFader = scf_data_clean.colorFader
debt_list = scf_data_clean.debt_list
debt_brackets = scf_data_clean.debt_brackets
quantile = scf_data_clean.quantile

num_age = 0
"""
Income and networth percentiles.
"""
num, var_list_dict = 10, {'income':'income','networth':'net worth','all_loans':'student debt'}
for var in ['income','networth']:
    array_temp = np.zeros((num+1,2))
    df = data[data['percap_all_loans']>0]
    array_temp[:,0] = np.array([scf_data_clean.quantile(df['percap_'+var], df['wgt'], j/num) for j in range(num+1)])
    array_temp[:,1] = np.array([scf_data_clean.quantile(data['percap_'+var], data['wgt'], j/num) for j in range(num+1)])
    width=2/5
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i in range(1,num,2): #only plot 10,30,50,70,90
        if i==1:
            ax.bar(i-width, array_temp[i,0]/10**3, 2*width, color=c1, label = "Borrowers")
            ax.bar(i+width, array_temp[i,1]/10**3, 2*width, color=c2, label = "All")
        else:
            ax.bar(i-width, array_temp[i,0]/10**3, 2*width, color=c1)
            ax.bar(i+width, array_temp[i,1]/10**3, 2*width, color=c2)
    plt.xticks(range(1,num,2), (100/num)*np.arange(1,num,2))
    ax.set_xlabel('Percentile')
    ax.set_title('Per-capita {0} percentiles'.format(var_list_dict[var]))
    ax.set_ylabel('\$000s')
    ax.legend()
    destin = '../figures/BvsNB{0}.eps'.format(var)
    plt.savefig(destin, format='eps', dpi=1000)
    plt.show()
"""
Average student debt by per-capita income and net worth for borrowers and non-borrowers.
"""
var_list = ['income','networth']
var_list_dict = {'income':'income','networth':'net worth'}
num, df_SD = 5, {}
df_SD['borrowers'] = pd.DataFrame(columns=range(1,num+1), index=var_list)
df_SD['all'] = pd.DataFrame(columns=range(1,num+1), index=var_list)
for var2 in ['borrowers','all']:
    for i in range(len(var_list)):
        if var2 == 'borrowers':
            df_temp = data[data['percap_all_loans']>0]
        else:
            df_temp = data
        f = lambda x: np.average(x, weights=df_temp.loc[x.index, "wgt"])
        gb = df_temp.groupby('percap_'+var_list[i]+'_cat{0}'.format(num))['percap_'+'all_loans'].agg(f).values
        if len(gb) < num:
            df_SD[var2].loc[var_list[i],num+1-len(gb):] = gb
            df_SD[var2].loc[var_list[i],:num+1-len(gb)] = gb[0]
        else:
            df_SD[var2].loc[var_list[i],:] = gb
    df_SD[var2] = (df_SD[var2]/1000).astype(float).round(1)
for var in var_list:
    width = 1/5
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i in range(1,num+1):
        if i==1:
            ax.bar(i-width, df_SD['borrowers'].loc[var,i], 2*width, color=c1, label = "Borrowers")
            ax.bar(i+width, df_SD['all'].loc[var,i], 2*width, color=c2, label = "All")
        else:
            ax.bar(i-width, df_SD['borrowers'].loc[var,i], 2*width, color=c1)
            ax.bar(i+width, df_SD['all'].loc[var,i], 2*width, color=c2)
    ax.set_xlabel('Per-capita {0} {1}s'.format(var_list_dict[var],qctile_dict[num]))
    ax.set_title('Average student debt')
    ax.set_ylabel('\$000s')
    ax.legend()
    destin = '../figures/SD{0}{1}.eps'.format(qctile_dict[num],var)
    plt.savefig(destin, format='eps', dpi=1000)
    plt.show()
"""
Age
"""
array_temp = np.zeros((len(scf_data_clean.age_labels),len(["Borrowers","All"])))
for i, val in enumerate(["Borrowers","All"]):
    df = slice_fun[val](data)
    gb = df.groupby(df['age_cat'])['wgt'].sum()
    array_temp[:,i] = 100*gb/gb.sum()
width=1/5
fig = plt.figure()
ax = fig.add_subplot(111)
for i in range(len(scf_data_clean.age_labels)):
    if i==0:
        ax.bar(i-width, array_temp[i,0], 2*width, color=c1, label = "Borrowers")
        ax.bar(i+width, array_temp[i,1], 2*width, color=c2, label = "All")
    else:
        ax.bar(i-width, array_temp[i,0], 2*width, color=c1)
        ax.bar(i+width, array_temp[i,1], 2*width, color=c2)
plt.xticks(range(len(scf_data_clean.age_labels)), scf_data_clean.age_labels)
ax.set_xlabel('Age')
ax.set_title('Population share (%)')
ax.legend()
destin = '../figures/BvsNBageFIG.eps'
plt.savefig(destin, format='eps', dpi=1000)
plt.show()
DF = pd.DataFrame(array_temp.round(decimals=1),index=scf_data_clean.age_labels, columns=["Borrowers","All"])
destin = '../figures/BvsNBage.tex'
with open(destin,'w') as tf:
    tf.write(DF.to_latex(column_format='lcc'))
"""
Aggregate debt by age group.
"""
df['debt_wgt'] = df['all_loans']*df['wgt']
dt = df.groupby(df['age_cat'])['debt_wgt'].sum()
width=2/5
fig = plt.figure()
ax = fig.add_subplot(111)
for i in range(len(scf_data_clean.age_labels)):
    ax.bar(i, dt[i]/10**9, 2*width, color=c2)
plt.xticks(range(len(scf_data_clean.age_labels)), scf_data_clean.age_labels)
ax.set_xlabel('Age')
ax.set_title('Aggregate debt held')
ax.set_ylabel('\$b')
destin = '../figures/BvsNBageAGG.eps'
plt.savefig(destin, format='eps', dpi=1000)
plt.show()
"""
Mean and median per-capita income and networth by age group.
"""
df = data
var_list = ['income','networth']
var_list_dict = {'income':'income','networth':'net worth'}
for var in var_list:
    array_temp = np.zeros((len(age_labels),2))
    gb = df.groupby(df['age_cat'])
    array_temp[:,0] = gb['percap_'+var].agg(lambda x: np.average(x,weights=df.loc[x.index,"wgt"]))/10**3
    array_temp[:,1] = gb['percap_'+var].agg(lambda x: scf_data_clean.quantile(x,df.loc[x.index,"wgt"],0.5))/10**3
    width = 1/5
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for j in range(len(age_labels)):
        if j==0:
            ax.bar(j+1-width, array_temp[j,0], 2*width, color=c1, label = "Mean")
            ax.bar(j+1+width, array_temp[j,1], 2*width, color=c2, label = "Median")
        else:
            ax.bar(j+1-width, array_temp[j,0], 2*width, color=c1)
            ax.bar(j+1+width, array_temp[j,1], 2*width, color=c2)
    plt.xticks(range(1,len(age_labels)+1),age_labels)
    ax.set_xlabel('Age groups')
    ax.set_title('Mean and median per-capita {0}'.format(var_list_dict[var]))
    ax.set_ylabel('\$000s')
    ax.legend(loc='upper left')
    destin = '../figures/{0}mmAGE.eps'.format(var)
    plt.savefig(destin, format='eps', dpi=1000)
    plt.show()
"""
Average debt by quintiles of income and net worth, fraction of borrowers in each bin.
"""
num, df_SD_quintiles = 5, {}
var_list = ['income','networth']
var_list_dict = {'income':'income','networth':'net worth'}
df_SD_quintiles = pd.DataFrame(columns=range(1,num+1), index=var_list)
for i in range(len(var_list)):
    f = lambda x: np.average(x, weights=data.loc[x.index, "wgt"])
    gb = data.groupby('percap_'+var_list[i]+'_cat{0}'.format(num))['percap_'+'all_loans'].agg(f).values
    df_SD_quintiles.loc[var_list[i],:] = gb
for var in var_list:
    width = 2/5
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i in range(1,6):
        ax.bar(i, df_SD_quintiles.loc[var,i], 2*width, color=c2)
    ax.set_xlabel('Per-capita {0} quintiles'.format(var_list_dict[var]))
    ax.set_title('Average student debt')
    ax.set_ylabel('\$')
    destin = '../figures/SDquintile{0}_all.eps'.format(var)
    plt.savefig(destin, format='eps', dpi=1000)
    plt.show()
    quintiles = np.array([scf_data_clean.quantile(data['percap_income'],data['wgt'], j/5) for j in range(6)])
    qct_lists, var_names = [quintiles,debt_list],['percap_income','percap_all_loans']
    d = [pd.cut(data[var_names[i]], bins=qct_lists[i],labels=range(len(qct_lists[i])-1),include_lowest=True,duplicates='drop') for i in range(2)]
    data['pairs'] = list(zip(d[0], d[1]))
    func = lambda x: np.sum(x*data.loc[x.index, "wgt"])
    SD_debt = data.groupby(data['pairs'])['percap_all_loans']
    SD_debt_count = data.groupby(data['pairs'])['wgt'].sum()
    width = 1/5
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i in range(len(quintiles)-1):
        norm = sum([SD_debt_count[(i,j)] for j in range(len(debt_list)-1)])
        for j in range(len(debt_list)-1):
            if i==0:
                ax.bar(i+1-((len(debt_list)-2)/2-j)*width,SD_debt_count[(i,j)]/norm,width,color=colorFader(c1,c2,j/(len(debt_list)-2)),label=debt_brackets[j])
            else:
                ax.bar(i+1-((len(debt_list)-2)/2-j)*width,SD_debt_count[(i,j)]/norm,width,color=colorFader(c1,c2,j/(len(debt_list)-2)))
    ax.set_xlabel('Per-capita {0} quintile'.format('income'))
    ax.set_title('Fraction of population')
    ax.legend()
    ax.set_ylim([0, 1])
    destin = '../figures/percap_{0}_debt_count.eps'.format(var)
    plt.savefig(destin, format='eps', dpi=1000)
    plt.show()
"""
Restrict to particular age groups.
"""
var_list = ['income','networth']
var_list_dict = {'income':'income','networth':'net worth'}
for age_cat in range(num_age):
    #create figures for particular age categor.
    num, df_SD = 5, {}
    df_SD['borrowers'] = pd.DataFrame(columns=range(1,num+1), index=var_list)
    df_SD['all'] = pd.DataFrame(columns=range(1,num+1), index=var_list)
    for var2 in ['borrowers','all']:
        for i in range(len(var_list)):
            if var2 == 'borrowers':
                df_temp = data[(data['percap_all_loans']>0)&(data['age_cat']==age_cat)]
            else:
                df_temp = data[data['age_cat']==age_cat]
            f = lambda x: np.average(x, weights=df_temp.loc[x.index, "wgt"])
            gb = df_temp.groupby('percap_'+var_list[i]+'_cat{0}{1}'.format(num,age_cat))['percap_'+'all_loans'].agg(f).values
            if len(gb) < num:
                df_SD[var2].loc[var_list[i],num+1-len(gb):] = gb
                df_SD[var2].loc[var_list[i],:num+1-len(gb)] = gb[0]
            else:
                df_SD[var2].loc[var_list[i],:] = gb
        df_SD[var2] = (df_SD[var2]/1000).astype(float).round(1)
    for var in var_list:
        width = 1/5
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for i in range(1,num+1):
            if i==1:
                ax.bar(i-width, df_SD['borrowers'].loc[var,i], 2*width, color=c1, label = "Borrowers")
                ax.bar(i+width, df_SD['all'].loc[var,i], 2*width, color=c2, label = "All")
            else:
                ax.bar(i-width, df_SD['borrowers'].loc[var,i], 2*width, color=c1)
                ax.bar(i+width, df_SD['all'].loc[var,i], 2*width, color=c2)
        ax.set_xlabel('Per-capita {0} {1}s'.format(var_list_dict[var],qctile_dict[num]))
        ax.set_title('Average student debt for {0} year olds'.format(age_labels[age_cat]))
        ax.set_ylabel('\$')
        ax.legend()
        plt.ylim([0,60])
        destin = '../figures/SD{0}{1}{2}.eps'.format(qctile_dict[num],var,age_cat)
        plt.savefig(destin, format='eps', dpi=1000)
        plt.show()
"""
Cancellation values broken down by income and networth distributions.
"""
f = lambda x: np.average(x, weights=data.loc[x.index, "wgt"])
num = 5
for var in ["income", "networth"]:
    array_temp = np.zeros((num,len(cancel_list)))
    gb = df.groupby(df['percap_'+var+'_cat{0}'.format(num)])
    for i, cancel in enumerate(cancel_list):
        array_temp[:,i] = gb['percap_cancel{0}'.format(cancel)].agg(f)
        width = 2/5
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for j in range(num):
            ax.bar(j+1, array_temp[j,i], 2*width, color=c2)
        plt.xticks(np.arange(1, num+1))
        ax.set_xlabel('Per-capita {0} {1}s'.format(var,qctile_dict[num]))
        #ax.set_title('Up to \${0},000 forgiven'.format(int(cancel/10**3)))
        ax.set_ylabel('\$')
        destin = '../figures/cancel{0}{1}{2}.eps'.format(var,qctile_dict[num],cancel)
        plt.savefig(destin, format='eps', dpi=1000)
        plt.show()
