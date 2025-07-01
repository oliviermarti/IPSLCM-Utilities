# -*- coding: utf-8 -*-
'''
plotIGCM : a few utilities for post processing

Author : olivier.marti@lsce.ipsl.fr

GitHub : https://github.com/oliviermarti/IPSLCM-Utilities

This software is governed by the CeCILL  license under French law and      
abiding by the rules of distribution of free software.  You can  use,      
modify and/ or redistribute the software under the terms of the CeCILL     
license as circulated by CEA, CNRS and INRIA at the following URL          
"http://www.cecill.info".                                                  
                                                                           
Warning, to install, configure, run, use any of Olivier Marti's            
software or to read the associated documentation you'll need at least      
one (1) brain in a reasonably working order. Lack of this implement        
will void any warranties (either express or implied).                      
O. Marti assumes no responsability for errors, omissions,                 
data loss, or any other consequences caused directly or indirectly by      
the usage of his software by incorrectly or partially configured           
personal. Be warned that the author himself may not respect the prerequisites.                                                                  
'''

import copy
import time
from typing import Any, Self, Literal, Dict, Union, Hashable

import numpy as np
import xarray as xr

from plotIGCM.utils import OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack
from plotIGCM.interp1d import interp1d
from plotIGCM import sphere

def pmath (ptab:Union[xr.DataArray,np.ndarray], default=None) :
    '''
    Determines the type of tab : xarray, numpy or numpy.ma object ?

    Returns type : xr, np or np.ma
    '''
    push_stack ( f'pmmath ( ptab, {default=} )' )
    mmath = default
    if   isinstance (ptab, xr.core.dataarray.DataArray) :
        mmath = xr
    elif isinstance (ptab, xr.core.dataset.Dataset)     :
        mmath = 'dataset'
    elif isinstance (ptab, np.ndarray)                  :
        mmath = np
    elif isinstance (ptab, np.ma.MaskType)              :
        mmath = np.ma

    pop_stack ( f'pmath : {mmath}' )
    return mmath

def copy_attrs (ptab:xr.DataArray, pref:xr.DataArray, Debug:Union[bool,None]=False) -> xr.DataArray :
    '''
    Copy units and attrs of pref in ptab
    Convert from numpy to xarray if needed
    '''
    mtab = pmath (ptab)
    mref = pmath (pref)

    if OPTIONS['Debug'] or Debug : print ( f'{mtab=} {mref=} {ptab.shape=} {pref.shape=}')

    if mref == xr :
        if mtab == xr :
            if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : ptab is xr' )
            ztab = ptab
        elif mtab in [np, np.ma] :
            if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : ptab is np or np.ma' )
            if ptab.shape == pref.shape :
                if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : convert ptab to xarray' )
                ztab = xr.DataArray (ptab, coords=pref.coords, dims=pref.dims)
                ztab.name = pref.name
        else :
            if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : ptab copied' )
            ztab = ptab
       
    return ztab
