# -*- coding: utf-8 -*-
# Ryoga Maruko (https://github.com/marukory66) and Naomichi Fujiuchi (https://github.com/naofujiuchi, naofujiuchi@gmail.com), April 2024
# This is an original work by Fujiuchi (MIT license).
import math
import statistics
import copy
import itertools
import datetime
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from dateutil import parser

class dataset:
    def __init__(self, dfleafnum, dffruitnum, dfleafsize, dffruitsize, colleafnumcntruss='id_truss', colleafnumcnvalue='n_leaf', colfruitnumcntruss='id_truss', colfruitnumcnvalue='n_fruit', colleafsizecntruss='id_truss', colleafsizecnleaf='id_leaf', colleafsizecnvalue='value', colfruitsizecntruss='id_truss', colfruitsizecnfruit='id_fruit', colfruitsizecnvalue='value', unit='cm', ncompleaf=4, ncompfruit=1):
        """
        Arguments
        ----------
        dfleafnum: pandas dataframe
            2 columns: truss id (integer), value = leaf number (integer)
            The truss id of the lowest truss is 1.
            Leaf number is the number of leaves between two trusses.
            Don't contain "None" or "NaN" values.
        dffruitnum: pandas dataframe
            2 columns: truss id (integer), value = fruit number (integer)
            The truss id of the lowest truss is 1.
            Fruit number is the number of fruits (including flowers that are expected to become fruits) on a truss.
            Don't contain "None" or "NaN" values.
        dfleafsize: pandas dataframe
            Measured sizes of leaves, usually leaf area [cm2]. The leaf length of the uppermost is expected to be approximately 10 cm.
            3 columuns: truss id (integer), leaf id (integer), value = e.g. leaf area (integer or floata)
            id_leaf of the leaf just below a truss is usually 3 (e.g. the leaf just below no.5 fruit truss has id_truss=5 and id_leaf=3. The leaf just above no.5 fruit truss has id_truss=6 and id_leaf=1).
            The default unit of value is cm2.
            Don't contain "None" or "NaN" values.
        dffruitsize: pandas dataframe
            Measured sizes of fruits, usually fruit diameter [cm]
            3 columuns: truss id (integer), fruit id (integer), value = e.g. fruit diameter (integer or floata)
            id_fruit of the proximal fruit is 1.
            The default unit of value is cm.
            Don't contain "None" or "NaN" values.
        dfleafnumcntruss, dfleafnumcnvalue, dffruitnumcntruss, dffruitnumcnvalue, dfleafsizecntruss, dfleafsizecnleaf, dfleafsizecnvalue, dffruitsizecntruss, dffruitsizecnfruit, dffruitsizecnvalue: string
            Column names.
        """

        self.ncompleaf = copy.deepcopy(ncompleaf) # The number of trusses which will be complemented for leaves above the uppermost measured leaf
        self.ncompfruit = copy.deepcopy(ncompfruit) # The number of trusses which will be complemented for fruits above the uppermost measured leaf

        # copying input dataframes
        self.nleaf = copy.deepcopy(dfleafnum)
        self.nleaf = self.nleaf.rename(columns={colleafnumcntruss:'id_truss', colleafnumcnvalue:'n_leaf'})
        self.nleaf = self.nleaf.sort_values(['id_truss'], ascending=True)
        self.nfruit = copy.deepcopy(dffruitnum)
        self.nfruit = self.nfruit.rename(columns={colfruitnumcntruss:'id_truss', colfruitnumcnvalue:'n_fruit'})
        self.nfruit = self.nfruit.sort_values(['id_truss'], ascending=True)
        self.leaf = copy.deepcopy(dfleafsize)
        self.leaf = self.leaf.rename(columns={colleafsizecntruss:'id_truss', colleafsizecnleaf:'id_leaf', colleafsizecnvalue:'value'})
        self.leaf = self.leaf.sort_values(['id_truss','id_leaf'], ascending=True)
        self.fruit = copy.deepcopy(dffruitsize)
        self.fruit = self.fruit.rename(columns={colfruitsizecntruss:'id_truss', colfruitsizecnfruit:'id_fruit', colfruitsizecnvalue:'value'})
        self.fruit = self.fruit.sort_values(['id_truss','id_fruit'], ascending=True)

    def expand_grid(self, data_dict):
        """Create a dataframe from every combination of given values."""
        rows = itertools.product(*data_dict.values())
        return pd.DataFrame.from_records(rows, columns=data_dict.keys())

    # def twoddf(self):
    #     """
    #     Making a dataframe based on the number of leaves and fruits.
    #     """
    #     nleafmax = self.nleaf['n_leaf'].max()
    #     nfruitmax = self.nfruit['n_fruit'].max()
    #     self.gridleaf = self.expand_grid({'id_truss': range(1,self.idtrussmax+1), 'id_leaf': range(1,nleafmax+1)})
    #     self.gridfruit = self.expand_grid({'id_truss': range(1,self.idtrussmax+1), 'id_fruit': range(1,nfruitmax+1)})        
    #     self.gridleaf = pd.merge(self.gridleaf, self.leaf, how='left')
    #     self.gridleaf2d = self.gridleaf.set_index(['id_truss','id_leaf']).unstack('id_leaf').value.rename_axis([None],axis=1).reset_index()
    #     self.gridfruit = pd.merge(self.gridfruit, self.fruit, how='left')
    #     self.gridfruit2d = self.gridfruit.set_index(['id_truss','id_fruit']).unstack('id_fruit').value.rename_axis([None],axis=1).reset_index()

    def twoddf(self, df, coltruss, colindiv, colvalue, idtrussmax=60):
        """
        Making a dataframe based on the number of leaves and fruits.

        Arguments
        ----------
        idtrussmax: integer
            Number of trusses = Number of rows of 2d table.
        """

        _df = df.rename(columns={coltruss:'id_truss'})
        nmax = int(_df[colindiv].max())
        grid = self.expand_grid({'id_truss': range(1,idtrussmax+1), colindiv: range(1,nmax+1)})        
        grid = pd.merge(grid, _df, how='left').filter(['id_truss', colindiv, colvalue])
        grid2d = grid.set_index(['id_truss',colindiv]).unstack(colindiv)[colvalue].rename_axis([None],axis=1).reset_index()
        return grid2d

    def complement(self, date, maxfruitsonbranch=10, nfruit=np.nan):
        """
        Complementing the sizes of the fruits and leaves that existed but were not measured.

        Arguments
        --------
        date: string
            The date when the plant appearance measured. Format should be '%Y-%m-%d', e.g. '2024-01-01' 
        maxfruitsonbranch: integer
            Maximum number of fruits on a branch in a truss is 10 (default).
        nfruit: integer
            Number of fruits on each complemented truss. If a value is np.nan, average number of fruits on measured trusses is uses.

        Outputs
        --------
        nbranchontruss: integer
            Number of branches of a truss for complemented trusses
        DVS: float
            Initial development stage of plant (number of flowered truss)
        LVAGE: integer
            Leaf age [d]
        DOEL: datetime.datetime.date()
            Date of energence of a leaf
        """

        measureddate = datetime.datetime.strptime(date, '%Y-%m-%d').date()

        # Leaf
        measuredtopleaf = self.leaf.tail(1)
        measuredtopleafpos = (measuredtopleaf.id_truss - 1) + (measuredtopleaf.id_leaf - 1) * (1/3)
        measuredtopleafpos = float(measuredtopleafpos) + 0.001
        nleafmax = self.nleaf['n_leaf'].max()
        nleafave = int(3)

        # Getting the uppermost leaf
        topleaf = pd.DataFrame({'id_truss':measuredtopleaf.id_truss+self.ncompleaf, 'id_leaf':measuredtopleaf.id_leaf}) # id_truss and id_leaf of top leaf that has just generated.
        topleafpos = (topleaf.id_truss - 1) + (topleaf.id_leaf - 1) * (1/3) # Leaf position of top leaf that has just generated. The default value of ncompleaf is 4.
        topleafpos = float(topleafpos) + 0.001

        # Interpolating leaf measured data
        idtrussarray = []
        idleafarray = []
        for i in range(0, self.nleaf.shape[0]): # Making as rows of all the combination of id_truss and id_leaf included in the nleaf dataframe.
            appendarray = [self.nleaf['id_truss'][i]] * self.nleaf['n_leaf'][i]
            idtrussarray = np.concatenate([idtrussarray, appendarray])
            idleafarray = np.concatenate([idleafarray, range(1,int(self.nleaf['n_leaf'][i])+1)])
        leafdfform = pd.DataFrame({'id_truss': idtrussarray, 'id_leaf': idleafarray})
        self.leaf['method'] = 'measured'
        self.leaf = pd.merge(leafdfform, self.leaf, how='left')
        self.leaf['pos'] = (self.leaf.id_truss-1) + (self.leaf.id_leaf-1) * (1/3)
        self.leaf = self.leaf[(self.leaf['pos']<=measuredtopleafpos)]
        self.leaf['method'] = self.leaf['method'].replace({np.nan:'interpolated'})

        # Leaf complementing data
        compleafmeasuredtoptruss = self.expand_grid({'id_truss': range(int(measuredtopleaf.id_truss),int(measuredtopleaf.id_truss)+1), 'id_leaf': range(1,int(self.nleaf.tail(1)['n_leaf'])+1)})
        self.compleaf = self.expand_grid({'id_truss': range(int(measuredtopleaf.id_truss+1),int(topleaf.id_truss+1)), 'id_leaf': range(1,nleafave+1)})
        self.compleaf = pd.concat([compleafmeasuredtoptruss, self.compleaf]).reset_index(drop=True)
        self.compleaf['pos'] = (self.compleaf.id_truss-1) + (self.compleaf.id_leaf-1) * (1/3)
        self.compleaf['method'] = 'complemented'
        self.compleaf = self.compleaf[(self.compleaf['pos']>=measuredtopleafpos)]
        self.compleaf = self.compleaf[(self.compleaf['pos']<=topleafpos)]

        # Integrating with measured data
        self.compleaf = pd.concat([self.leaf,self.compleaf]).reset_index(drop=True)
        nleafonplant = self.compleaf.shape[0] # If the number of leaves in simulated plant appearance is over nleaf, deleaf the lowest leaf.

        # Adding leaf information required for initializing TOMULATION
        self.compleaf['LVAGE'] = (int(topleaf.id_truss) - self.compleaf.id_truss) * 7 + (int(topleaf.id_leaf) - self.compleaf.id_leaf) * 1/3 * 7
        self.compleaf['DOEL'] = self.compleaf['LVAGE'].apply(lambda x: measureddate - datetime.timedelta(days=int(x)))

        # Fruit
        measuredtopfruit = self.fruit.tail(1)
        measuredtopfruitpos = measuredtopfruit.id_truss + (measuredtopfruit.id_fruit - 1) * (1/int(self.nfruit.tail(1)['n_fruit']))
        measuredtopfruitpos = float(measuredtopfruitpos) + 0.001
        nfruitmax = self.nfruit['n_fruit'].max()
        if np.isnan(nfruit): 
            nfruitave = int(self.nfruit['n_fruit'].mean())
        else:
            nfruitave = nfruit
        nbranchontruss = nfruitave // maxfruitsonbranch + 1

        # Getting the uppermost fruit
        DVS = (measuredtopleaf.id_truss - 1) + (measuredtopleaf.id_leaf - 1) * (1/3) + self.ncompfruit # The flower truss on ((uppermost leaf position) + ncompfruit) has just flowered. The default value of ncompfruit is 1.
        DVS = float(DVS)
        topfruit = pd.DataFrame({'id_truss':math.floor(DVS), 'id_fruit':math.ceil(math.modf(DVS)[0]*nfruitave+1)},index=[0]) # id_truss and id_fruit of top fruit that has just flowered.
        topfruitpos = DVS + 0.001

        # Interpolating fruit measured data
        idtrussarray = []
        idfruitarray = []
        for i in range(0, self.nfruit.shape[0]): # Making as rows of all the combination of id_truss and id_fruits included in the nfruit dataframe.
            appendarray = [self.nfruit['id_truss'][i]] * self.nfruit['n_fruit'][i]
            idtrussarray = np.concatenate([idtrussarray, appendarray])
            idfruitarray = np.concatenate([idfruitarray, range(1,int(self.nfruit['n_fruit'][i])+1)])
        fruitdfform = pd.DataFrame({'id_truss': idtrussarray, 'id_fruit': idfruitarray})
        self.fruit['method'] = 'measured'
        self.fruit = pd.merge(fruitdfform, self.fruit, how='left')
        self.fruit['method'] = self.fruit['method'].replace({np.nan:'interpolated'})

        # Fruit complementing data
        compfruitmeasuredtoptruss = self.expand_grid({'id_truss': range(int(measuredtopfruit.id_truss),int(measuredtopfruit.id_truss)+1), 'id_fruit': range(1,int(self.nfruit.tail(1)['n_fruit'])+1)})
        compfruitmeasuredtoptruss['pos'] = compfruitmeasuredtoptruss.id_truss + (compfruitmeasuredtoptruss.id_fruit-1) * (1/int(self.nfruit.tail(1)['n_fruit']))
        self.compfruit = self.expand_grid({'id_truss': range(int(measuredtopfruit.id_truss+1),int(topfruit.id_truss+1)), 'id_fruit': range(1,nfruitave+1)})
        self.compfruit['pos'] = self.compfruit.id_truss + (self.compfruit.id_fruit-1) * (1/nfruitave)
        self.compfruit = pd.concat([compfruitmeasuredtoptruss, self.compfruit]).reset_index(drop=True)
        self.compfruit['method'] = 'complemented'
        self.compfruit = self.compfruit[(self.compfruit['pos']>=measuredtopfruitpos)]
        self.compfruit = self.compfruit[(self.compfruit['pos']<=topfruitpos)]
        self.compfruit = self.compfruit.drop('pos', axis=1)

        # Integrating with measured data
        self.compfruit = pd.concat([self.fruit,self.compfruit]).reset_index(drop=True)
        self.compfruit = self.compfruit.drop_duplicates(subset=['id_truss', 'id_fruit'], keep='last')
        self.compfruit = pd.merge(self.compfruit, self.nfruit, how='left') # Adding column of n_fruit (number of fruits on each truss)
        self.compfruit['n_fruit'] = self.compfruit['n_fruit'].fillna(nfruitave)
        # maxdvsf = self.compfruit['DVSF'].max() # Maximum DVSF. If DVSF of a fruit exceeds the value, the fruit is ready to harvest.

        # Adding fruit information required for initializing TOMULATION
        self.compfruit['n_branch'] = self.compfruit.n_fruit // maxfruitsonbranch + 1
        self.compfruit['order'] = (self.compfruit.id_fruit - 1) // self.compfruit.n_branch + 1 # e.g. if id_fruit=3 and nbranchontruss=3, then order=1. If id_fruit=4 and nbranchontruss=3, then order=2.
        topfruit['order'] = (topfruit.id_fruit - 1) // nbranchontruss + 1
        self.compfruit['FAGE'] = (int(topfruit.id_truss) - self.compfruit.id_truss) * 7 + (int(topfruit.order) - self.compfruit.order)
        self.compfruit['DOEF'] = self.compfruit['FAGE'].apply(lambda x: measureddate - datetime.timedelta(days=int(x)))

        return nleafonplant, nfruitave, nbranchontruss, self.compleaf, self.compfruit, DVS, measureddate
    
    def Gompertz(self, t, a, b, c):
        f = a * np.exp(-b * c**t)
        return f

    def Gompertz_fit(self, df, x, y, inib, inic):
        """
        Initial value of parameter a for Gompertz curve fitting is mean value of y.

        Arguments
        --------
        df: pandas DataFrame
            Data including a explanatory variable (x) and an objective variable (y) for training
        x: string
            Column name of explanatory variable.
        y: string
            Column name of objective variable.
        inib: float
            Gompertz parameter b, affecting the y value at x=0. Lower value result in higher y value at x=0. inib=7, then y at x=0 is almost 0.
        inic: float
            Gompertz parameter c. If the y value is plateau over x=50, then inic=0.9. Lower value result in early plateau.
        """

        df_train = df[[x,y]].dropna(subset=[y])
        x_train = df_train[x]
        y_train = df_train[y]
        ymean = statistics.mean(y_train)
        ymax = max(y_train)
        popt, pcov = curve_fit(f = self.Gompertz, xdata = x_train, ydata = y_train, p0 = [ymean, inib, inic], maxfev = 800)
        return popt, pcov, ymax
    
    def DVSI(self, dfcomp, coldoe, coldvsi, measureddate, dftemp, coldate, coltemp): 
        """
        Develepment stage of individual fruit (DVSF) or leaf (DVSL).
        Initial value of parameter 'a' for Gompertz curve fitting is mean value of y.

        Arguments
        --------
        dfcomp: pandas DataFrame
            self.compfruit or self.compleaf output in the predescribed 'def complement()' function
        coldoe: string
            Column name of Day of Emergence of fruit (DOEF) or leaf (DOEL)
        coldvsi: string
            Output Column name of DVSI.
        measureddate: datetime.date
            measureddate output in the predescribed 'def complement()' function 
        dftemp: pandas DataFrame
            Data including date (type: string) and daily average temperature [C] (type: numpy integer or float).
        coldate: string
            Column name of date.
        coltemp: string
            Column name of objective variable.
        """
        
        self.compdvsi = copy.deepcopy(dfcomp)
        self.temp = copy.deepcopy(dftemp)
        self.temp = self.temp.rename(columns={coldate:'date', coltemp:'temp'})
        self.temp['date'] = self.temp['date'].apply(lambda x: parser.parse(x).date()) 
        
        arrayDVSI = []
        for index, row in self.compdvsi.iterrows():
            iter_date = row[coldoe]
            end_date = measureddate
            delta = datetime.timedelta(days=1)
            _DVSI = 0
            while iter_date < end_date:
                temp_today = self.temp[self.temp['date']==iter_date]['temp']
                _DVRI = self.DVRI(temp_today, _DVSI)
                _DVSI += _DVRI
                iter_date += delta
            arrayDVSI = np.concatenate([arrayDVSI, [_DVSI]])
        self.compdvsi[coldvsi] = arrayDVSI
        return self.compdvsi

    def DVRI(self, temp, DVSI):
        """
        DVRF (rate of developing stage of fruit) depends on daily mean temperature as the following equation (De Koning, 1994).
        In this study, leaf also follows this development mechanism.
        """

        DVRI = 0.0181 + math.log(temp/20) * (0.0392 - 0.213 * DVSI + 0.415 * DVSI**2 - 0.24 * DVSI**3)
        return(DVRI)

    # def DVSF(self, compfruit, measureddate, dftemp, coldate, coltemp): 
    #     """
    #     Initial value of parameter 'a' for Gompertz curve fitting is mean value of y.

    #     Arguments
    #     --------
    #     compfriut: pandas DataFrame
    #         self.compfruit output in the predescribed 'def complement()' function
    #     measureddate: datetime.date
    #         measureddate output in the predescribed 'def complement()' function 
    #     dftemp: pandas DataFrame
    #         Data including date (type: string) and daily average temperature [C] (type: numpy integer or float).
    #     coldate: string
    #         Column name of date.
    #     coltemp: string
    #         Column name of objective variable.
    #     """
        
    #     self.compfruitdvsf = copy.deepcopy(compfruit)
    #     self.temp = copy.deepcopy(dftemp)
    #     self.temp = self.temp.rename(columns={coldate:'date', coltemp:'temp'})
    #     self.temp['date'] = self.temp['date'].apply(lambda x: parser.parse(x).date()) 
        
    #     arrayDVSF = []
    #     for index, row in self.compfruitdvsf.iterrows():
    #         iter_date = row['DOEF']
    #         end_date = measureddate
    #         delta = datetime.timedelta(days=1)
    #         _DVSF = 0
    #         while iter_date < end_date:
    #             temp_today = self.temp[self.temp['date']==iter_date]['temp']
    #             _DVRF = self.DVRF(temp_today, _DVSF)
    #             _DVSF += _DVRF
    #             iter_date += delta
    #         arrayDVSF = np.concatenate([arrayDVSF, [_DVSF]])
    #     self.compfruitdvsf['DVSF'] = arrayDVSF
    #     return self.compfruitdvsf

    # def DVRF(self, temp, DVSF):
    #     """
    #     DVRF (rate of developing stage of fruit) depends on daily mean temperature as the following equation (De Koning, 1994).
    #     """

    #     DVRF = 0.0181 + math.log(temp/20) * (0.0392 - 0.213 * DVSF + 0.415 * DVSF**2 - 0.24 * DVSF**3)
    #     return(DVRF)
    
    def interpolate_and_Gompertz_est(self, df, colx, coly, Gompparams): 
        dfest = copy.deepcopy(df)
        interpolatedvalue = dfest[coly].interpolate()
        for index, row in df.iterrows():
            if np.isnan(row[coly]):
                estimatedvalue = self.Gompertz(row[colx], *Gompparams)
                if row['method'] == 'interpolated': 
                    dfest.loc[index, coly] = interpolatedvalue.loc[index]
                elif row['method'] == 'complemented': 
                    dfest.loc[index, coly] = estimatedvalue
        return dfest        

    def initial_fruit(self, df, coldiameter, DMC, unit_diameter='cm'):
        """
        Make initial values for TOMULATION.
        FF: fruit fresh mass [gFM]
        FD: fruit dry mass [gDM]
        DMC: fruit dry matter content [gDM/gFM]

        Arguments
        --------
        df: pandas DataFrame
            Data with fruit diameter.
        coldiameter: string
            Column name of fruit diameter.
        DMC: float
            Fruit dry matter content.
        """
        
        dfinit = copy.deepcopy(df)
        if unit_diameter == 'cm': 
            r = dfinit[coldiameter]/2
        elif unit_diameter == 'mm':
            r = dfinit[coldiameter]/10/2
        dfinit['FF'] = 4/3 * math.pi * r **3
        dfinit['DMC'] = DMC
        dfinit['FD'] = dfinit['FF'] * dfinit['DMC']
        return dfinit

    def initial_leaf(self, df, colarea, SLA=0.05, unit_area='m2'):
        """
        Make initial values for TOMULATION.

        Arguments
        --------
        df: pandas DataFrame
            Data with leaf area.
        colarea: string
            Column name of leaf area.
        SLA: float
            Specific leaf area [m2/gDM].
        """
        
        dfinit = copy.deepcopy(df)
        dfinit = dfinit.rename(columns={colarea:'LA'})
        dfinit['SLA'] = SLA
        if unit_area == 'm2': 
            dfinit['LV'] = dfinit['LA'] / dfinit['SLA']
        elif unit_area == 'cm2':
            dfinit['LV'] = dfinit['LA'] / 10000 / dfinit['SLA']
        return dfinit


# class initial_values_for_tomulation(dataset):
#     def __init__(self, nleaf, leaf, nfruit, fruit, DMC, ):
#         super().__init__(nleaf, leaf, nfruit, fruit)


#     def DMCI(self):

#     def DOEFI(self):

#     def DOELI(self):

#     def DOHFI(self):

#     def DOHLI(self):

#     def DVSFI(self):

#     def FDI(self):

#     def FFI(self):

#     def LAI(self):

#     def LVAGE(self):

#     def LVI(self):


