# -*- coding: utf-8 -*-
'''
libIGCM_utils : a few utilities

Author : olivier.marti@lsce.ipsl.fr

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
personal.                                                                  
'''

import copy
import time
import numpy as np
import xarray as xr
import pint
try :
    from pint_xarray import unit_registry as ureg
except ImportError :
    from pint import UnitRegistry
    ureg = UnitRegistry()
    pintx = False
else :
    pintx = True
    
Q_ = ureg.Quantity

## ============================================================================
class Container :
    '''
    Void class to act as a container
    Class members can be accessed either with dictionnary or namespace syntax
       i.e  <Container>['member'] or <Container>.member
    '''
    def update (self, dico=None, **kwargs):
        '''Use a dictionnary to update values'''
        if dico : 
            for attr in dico.keys () :
                super().__setattr__(attr, dico[attr])
        self.__dict__.update (kwargs)
    def keys    (self) :
        return self.__dict__.keys()
    def values  (self) :
        return self.__dict__.values()
    def items   (self) :
        return self.__dict__.items()
    def dict    (self) :
        return self.__dict__
    ## Hidden functions
    def __str__     (self) :
        return str  (self.__dict__)
    def __repr__    (self) :
        return repr (self.__dict__)
    def __name__    (self) :
        return self.__class__.__name__
    def __getitem__ (self, attr) :
        return getattr (self, attr)
    def __setitem__ (self, attr, value) :
        setattr (self, attr, value)
    def __iter__    (self) :
        return self.__dict__.__iter__()
    def __next__    (self) :
        return self.__dict__.__next__()
    def __len__     (self) :
        return len (self.__dict__)
    def __init__ (self, **kwargs) :
        for attr, value in kwargs.items () :
            super().__setattr__(attr, value)
        return None

## ============================================================================
DEFAULT_OPTIONS = Container (Debug  = False,
                             Trace  = False,
                             Timing = None,
                             t0     = None,
                             Depth  = None,
                             Stack  = None)
OPTIONS = copy.deepcopy (DEFAULT_OPTIONS)

class set_options :
    '''
    Set options for libIGCM_utils
    '''
    def __init__ (self, **kwargs) :
        self.old = Container ()
        for k, v in kwargs.items() :
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update (self, options_dict) :
        OPTIONS.update (options_dict)
    def __enter__ (self) :
        return
    def __exit__ (self, type, value, traceback) :
        self._apply_update (self.old)

def get_options () -> dict :
    '''
    Get options for nemo

    See Also
    ----------
    set_options

    '''
    return OPTIONS

def reset_options():
    return set_options (**DEFAULT_OPTIONS)

def return_stack () :
    return OPTIONS.Stack

def push_stack (string:str) :
    if OPTIONS.Depth :
        OPTIONS.Depth += 1
    else             :
        OPTIONS.Depth = 1
    if OPTIONS.Trace :
        print ( '  '*(OPTIONS.Depth-1), f'-->{__name__}.{string}' )
    #
    if OPTIONS.Stack :
        OPTIONS.Stack.append (string)
    else             :
        OPTIONS.Stack = [string,]
    #
    if OPTIONS.Timing :
        if OPTIONS.t0 :
            OPTIONS.t0.append ( time.time() )
        else :
            OPTIONS.t0 = [ time.time(), ]

def pop_stack (string:str) :
    if OPTIONS.Timing :
        dt = time.time() - OPTIONS.t0[-1]
        OPTIONS.t0.pop()
    else :
        dt = None
    if OPTIONS.Trace or dt :
        if dt :
            if dt < 1e-3 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1e6:5.1f} micro s')
            if dt >= 1e-3 and dt < 1 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1e3:5.1f} milli s')
            if dt >= 1 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1:5.1f} second')
        else : 
            print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string}')
    #
    OPTIONS.Depth -= 1
    if OPTIONS.Depth == 0 :
        OPTIONS.Depth = None
    OPTIONS.Stack.pop ()
    if OPTIONS.Stack == list () :
        OPTIONS.Stack = None
    #
    
## ============================================================================
def pmath (ptab, default=None) :
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

def xr_quantify (zz) :
    '''
    If zz is an xarray DataArray of DataSet, use pint to set the unit(s)
    '''
    if 'pint' in dir (zz) :
        return zz.pint.quantify ()
    else :
        return zz
    
def xr_dequantify (zz) :
    '''
    If zz is an xarray DataArray of DataSet with a pint unit, reverses back to standard DataArray or DataSet
    '''
    if 'pint' in dir(zz) :
        return zz.pint.dequantify ()
    else :
        return zz

def pint_unit (ptab) :
    zu = None
    
    if isinstance (ptab, Q_) :
        zu = ptab.units
    if isinstance (ptab, xr.core.dataarray.DataArray) :
        if 'pint' in dir(ptab) :
            zu = ptab.pint.units
    return zu

def copy_attrs (ptab, pref) :
    '''
    Copy units and attrs of pref in ptab
    Copy pint units if available
    Convert from numpy to xarray if needed
    '''
    _mtab = pmath (ptab)
    _mref = pmath (pref)
    xr_unit  = None
    pint_unit = None

    if _mref == xr :
        if 'pint' in dir (pref) :
            pint_unit = pref.pint.units
        else : 
            if 'units' in pref.attrs :
                xr_unit = pref.attrs['units']
    if _mref in (np.ma, np):
        if 'units' in pref.attrs :
            pint_unit = pref.units

    if _mref == xr :
        if _mtab == xr :
            if OPTIONS.Debug :
                print ( 'copy_attrs : ptab is xr' )
            ztab = ptab
        elif _mtab in [np, np.ma] :
            if OPTIONS.Debug :
                print ( 'copy_attrs : ptab is np or np.ma' )
            if ptab.shape == pref.shape :
                if OPTIONS.Debug :
                    print ( 'copy_attrs : convert ptab to xarray' )
                ztab = xr.DataArray (ptab, coords=pref.coords, dims=pref.dims)
                ztab.name = pref.name
        else :
            if OPTIONS.Debug :
                print ( 'copy_attrs : ptab copied' )
            ztab = ptab

    if _mref == xr :
        if pint_unit :
            ztab = ztab.pint.quantify (pint_unit)
        if xr_unit and not pint_unit :
            ztab = ztab.pint.quantify (pint_unit)
            
    if _mref in [np, np.ma] :
        if pint_unit :
            ztab = Q_ (ztab, pint_unit)
       
    return ztab

