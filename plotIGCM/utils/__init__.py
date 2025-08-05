# -*- coding: utf-8 -*-
'''
libIGCM_utils : a few utilities

Author : olivier.marti@lsce.ipsl.fr

Github : https://github.com/oliviermarti/IPSLCM-Utilities

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
from typing import Callable, Any, Self, Literal, _LiteralGenericAlias
import typing

import numpy as np
import xarray as xr

from plotIGCM.options import OPTIONS    as OPTIONS
from plotIGCM.options import push_stack as push_stack
from plotIGCM.options import pop_stack  as pop_stack

Debug=True
Check=False

def validate_types (func: Callable) -> Callable :
    '''
    Decorator to check arguments and return types of a function deduced from annotations
    '''
    def wrapper (*args: Any, **kwargs: Any) -> Any :
        if Check :
            ## Validate arguments
            for (name, param_type), value in zip (func.__annotations__.items (), args) :
                if Debug :
                    print ( 'arg --')
                    print ( f'{name=}, {param_type=}, {value=}, {type(value)=}' )
                    print ( f'{param_type in [Literal,] =}' )
                if param_type not in [Any, Self, Literal, _LiteralGenericAlias] :
                    if Debug :
                        print ( 'Checking arg' )
                    if not param_type in [Any,] and not isinstance (value, param_type) :
                       raise TypeError (f"Argument {name} should be of type {param_type}, got {type(value)}")
                if Debug :
                    print ( '==')

            for key, value in kwargs.items () :
                param_type = func.__annotations__.get (key, Any)
                if Debug :
                    print ( 'kwarg --')
                    print ( f"{key}, {param_type=}, {value=}, {type(value)=} {type(param_type)=}" )
                if type(param_type) == typing._LiteralGenericAlias :
                    if Debug :
                        print ( f"kwarg non testable : {param_type = }")
                else : 
                    if Debug :
                        print ( 'Checking kwarg' )
                    if not param_type in  [Any,] and not isinstance (value, param_type) :
                        raise TypeError (f"k-Argument '{key}' should be of type {param_type}, got {type(value)}")

        ## Validate return type
        result = func (*args, **kwargs)
        if Check :
            return_type = func.__annotations__.get("return", Any)
            if Debug :
                print ( 'return --')
                print ( f"{return_type=}, {result=}, {type(result)=} {type(return_type)=}" )
            if return_type and return_type not in  [Any,] and not isinstance (result, return_type):
                raise TypeError (f"Return value should be of type {return_type}, got {type(result)}")

        return result
    return wrapper

def copy_attrs (ptab:xr.DataArray, pref:xr.DataArray, Debug:bool|None=False) -> xr.DataArray :
    '''
    Copy units and attrs of pref in ptab
    Convert from numpy to xarray if needed
    '''
    push_stack ( 'copy_attrs' )
    if OPTIONS['Debug'] or Debug : print ( f'ptab:{type(ptab)} pref:{type(pref)} {ptab.shape=} {pref.shape=}')

    if isinstance(pref, xr.DataArray) :
        if isinstance (ptab, xr.DataArray) :
            if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : ptab is xr' )
            ztab = ptab
        elif isinstance (ptab, np.ndarray) :
            if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : ptab is np or np.ma' )
            if ptab.shape == pref.shape :
                if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : convert ptab to xarray' )
                ztab = xr.DataArray (ptab, coords=pref.coords, dims=pref.dims)
                ztab.name = pref.name
        else :
            if OPTIONS['Debug'] or Debug : print ( 'copy_attrs : ptab copied' )
            ztab = ptab

    pop_stack ( 'copy_attrs')
    return ztab
