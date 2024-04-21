#%%
# How to use shootappearance library
import shootappearance.shootappearance as sa
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

dfleafnum = pd.read_csv('dfleafnum.csv')
dffruitnum = pd.read_csv('dffruitnum.csv')
dfleafsize = pd.read_csv('dfleafsize.csv')
dffruitsize = pd.read_csv('dffruitsize.csv')
dftemp = pd.read_csv('dftemp.csv')
# How many leaves are above the measured leaf? (= ncompleaf [trusses])
# How many fruit tursses are above the measured fruit truss? (= ncompfruit [trusses])
shootdata = sa.dataset(ncompleaf=2, ncompfruit=1, dfleafnum=dfleafnum, dffruitnum=dffruitnum, dfleafsize=dfleafsize, dffruitsize=dffruitsize, colleafnumcntruss='id_truss', colleafnumcnvalue='n_leaf', colfruitnumcntruss='id_truss', colfruitnumcnvalue='n_fruit', colleafsizecntruss='id_truss', colleafsizecnleaf='id_leaf', colleafsizecnvalue='value', colfruitsizecntruss='id_truss', colfruitsizecnfruit='id_fruit', colfruitsizecnvalue='value')
nleafonplant, nfruitave, nbranchontruss, dfleaf, dffruit, DVSI, measureddate = shootdata.complement('2024-01-01')

# Fruit
dffruitdvsf = shootdata.DVSI(dfcomp=dffruit, coldoe='DOEF', coldvsi='DVSF', measureddate=measureddate, dftemp=dftemp, coldate='Date', coltemp='Temp')
poptfruit, pcovfruit, ymaxfruit = shootdata.Gompertz_fit(df=dffruitdvsf, x='DVSF', y='value', inib=7, inic=0.1)
dffruitdvsfest = shootdata.interpolate_and_Gompertz_est(df=dffruitdvsf, colx='DVSF', coly='value', Gompparams=poptfruit)
dffruitdvsfestinit = shootdata.initial_fruit(df=dffruitdvsfest, coldiameter='value', DMC=0.08, unit_diameter='mm')
FFI = shootdata.twoddf(df=dffruitdvsfestinit, coltruss='id_truss', colindiv='id_fruit', colvalue='FF')
FDI = shootdata.twoddf(df=dffruitdvsfestinit, coltruss='id_truss', colindiv='id_fruit', colvalue='FD')
DOEFI = shootdata.twoddf(df=dffruitdvsfestinit, coltruss='id_truss', colindiv='id_fruit', colvalue='DOEF')
DVSFI = shootdata.twoddf(df=dffruitdvsfestinit, coltruss='id_truss', colindiv='id_fruit', colvalue='DVSF')

# Leaf
dfleafdvsl = shootdata.DVSI(dfcomp=dfleaf, coldoe='DOEL', coldvsi='DVSL', measureddate=measureddate, dftemp=dftemp, coldate='Date', coltemp='Temp')
# poptleaf, pcovleaf, ymaxleaf = shootdata.Gompertz_fit(df=dfleaf, x='LVAGE', y='value', inib=7, inic=0.9)
poptleaf, pcovleaf, ymaxleaf = shootdata.Gompertz_fit(df=dfleafdvsl, x='DVSL', y='value', inib=7, inic=0.1)
dfleafdvslest = shootdata.interpolate_and_Gompertz_est(df=dfleafdvsl, colx='DVSL', coly='value', Gompparams=poptleaf)
dfleafdvslestinit = shootdata.initial_leaf(df=dfleafdvslest, colarea='value', SLA=0.05, unit_area='cm2')
LAI = shootdata.twoddf(df=dfleafdvslestinit, coltruss='id_truss', colindiv='id_leaf', colvalue='LA')
LVI = shootdata.twoddf(df=dfleafdvslestinit, coltruss='id_truss', colindiv='id_leaf', colvalue='LV')
DOELI = shootdata.twoddf(df=dfleafdvslestinit, coltruss='id_truss', colindiv='id_leaf', colvalue='DOEL')
LVAGEI = shootdata.twoddf(df=dfleafdvslestinit, coltruss='id_truss', colindiv='id_leaf', colvalue='LVAGE')
SLAI = shootdata.twoddf(df=dfleafdvslestinit, coltruss='id_truss', colindiv='id_leaf', colvalue='LVAGE')

# Figure of Gompertz estimation
def Gompertz(t, a, b, c):
    f = a * np.exp(-b * c**t)
    return f

def curve_plot(x_train, y_train, est):
    x_est = np.linspace(start = 0, stop = max(x_train), num = 100)
    plt.scatter(x_train, y_train, color = 'r', label = 'Actual')
    plt.plot(x_est, Gompertz(x_est, *est), label = 'Estimation with train data')
    plt.legend()    
    plt.show()

print(poptfruit)
curve_plot(x_train=dfleafdvsl['DVSL'], y_train = dfleafdvsl['value'], est=poptleaf)
