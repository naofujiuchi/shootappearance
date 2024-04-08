# -*- coding: utf-8 -*-
# Ryoga Maruko (https://github.com/marukory66) and Naomichi Fujiuchi (https://github.com/naofujiuchi, naofujiuchi@gmail.com), April 2024
# This is an original work by Fujiuchi (MIT license).
import copy
import itertools
import numpy as np
import pandas as pd
from .leaf import *
from .fruit import *

class dataset:
    def __init__(self, dfleafnum, dffruitnum, dfleafsize, dffruitsize, dfleafnumcntruss, dfleafnumcnvalue, dffruitnumcntruss, dffruitnumcnvalue, dfleafsizecntruss, dfleafsizecnleaf, dfleafsizecnvalue, dffruitsizecntruss, dffruitsizecnfruit, dffruitsizecnvalue, unit='mm'):
        """
        Arguments
        ----------
        dfleafnum: pandas dataframe
            2 columns: truss id (integer), value = leaf number (integer)
            The truss id of the lowest truss is 1.
            Leaf number is the number of leaves below a truss.
            Don't contain "None" or "NaN" values.
        dffruitnum: pandas dataframe
            2 columns: truss id (integer), value = fruit number (integer)
            The truss id of the lowest truss is 1.
            Fruit number is the number of fruits on a truss.
            Don't contain "None" or "NaN" values.
        dfleafsize: pandas dataframe
            3 columuns: truss id (integer), leaf id (integer), value = e.g. leaf area (integer or floata)
            id_leaf of the leaf just below a truss is 1 (e.g. the leaf just below no.5 fruit truss has id_truss=5 and id_leaf=1).
            The default unit of value is mm2.
            Don't contain "None" or "NaN" values.
        dffruitsize: pandas dataframe
            3 columuns: truss id (integer), fruit id (integer), value = e.g. fruit diameter (integer or floata)
            id_fruit of the proximal fruit is 1.
            The default unit of value is mm.
            Don't contain "None" or "NaN" values.
        dfleafnumcntruss, dfleafnumcnvalue, dffruitnumcntruss, dffruitnumcnvalue, dfleafsizecntruss, dfleafsizecnleaf, dfleafsizecnvalue, dffruitsizecntruss, dffruitsizecnfruit, dffruitsizecnvalue: string
            Column names.
        """
        self.nleaf = copy.deepcopy(dfleafnum)
        self.nleaf = self.nleaf.rename(columns={'id_truss':dfleafnumcntruss,'n_leaf':dfleafnumcnvalue})
        self.nfruit = copy.deepcopy(dffruitnum)
        self.nfruit = self.nfruit.rename(columns={'id_truss':dffruitnumcntruss,'n_leaf':dffruitnumcnvalue})
        self.leaf = copy.deepcopy(dfleafsize)
        self.leaf = self.leaf.rename(columns={'id_truss':dfleafsizecntruss,'id_leaf':dfleafsizecnleaf,'value':dfleafsizecnvalue})
        self.fruit = copy.deepcopy(dffruitsize)
        self.fruit = self.fruit.rename(columns={'id_truss':dffruitsizecntruss,'id_leaf':dffruitsizecnfruit,'value':dffruitsizecnvalue})
        self.idtrussmax = 60

    def twoddf(self):
        """
        Making a dataframe based on the number of leaves and fruits.
        """
        nleafmax = self.nleaf['n_leaf'].max()
        nfruitmax = self.nfruit['n_fruit'].max()
        dfleaf = self.expand_grid({'id_truss': range(1,self.idtrussmax+1), 'id_leaf': range(1,nleafmax+1)})
        dffruit = self.expand_grid({'id_truss': range(1,self.idtrussmax+1), 'id_fruit': range(1,nfruitmax+1)})        
        self.leaf = pd.merge(dfleaf, self.leaf, how='left').replace(np.nan, None).set_index(['id_truss','id_leaf']).unstack('id_leaf').value.rename_axis([None],axis=1).reset_index()
        self.fruit = pd.merge(dffruit, self.fruit, how='left').replace(np.nan, None).set_index(['id_truss','id_fruit']).unstack('id_leaf').value.rename_axis([None],axis=1).reset_index()

    # def implement(self):
    #     """
    #     Implementing the sizes of the fruits and leaves that existed but were not measured.
    #     """
    #     self.leaf = implement_leaf(self.leaf)
    #     self.fruit = implement_fruit(self.fruit)

    def expand_grid(data_dict):
        """Create a dataframe from every combination of given values."""
        rows = itertools.product(*data_dict.values())
        return pd.DataFrame.from_records(rows, columns=data_dict.keys())

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


