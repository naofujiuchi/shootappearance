# -*- coding: utf-8 -*-
# Ryoga Maruko (https://github.com/marukory66) and Naomichi Fujiuchi (https://github.com/naofujiuchi, naofujiuchi@gmail.com), April 2024
# This is an original work by Fujiuchi (MIT license).
import copy

def implement_leaf(dfleaf, nimpleaf):
    """
    Implementing the sizes of the fruits and leaves that existed but were not measured.
    For leaf, the leaves in the same truss have the same sizes.
    """
    dfleaf = copy.deepcopy(dfleaf)
    
