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
personal. Be warned that the author himself may not respect the
prerequisites.                                                                 
'''

import copy
import time
import numpy as np
import xarray as xr
import pint

from libIGCM.utils import Container, OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack

try :
    from pint_xarray import unit_registry as ureg
except ImportError :
    from pint import UnitRegistry
    ureg  = UnitRegistry()
    pintx = False
else :
    pintx = True
##    
Q_ = ureg.Quantity


full_name = Container (
    {'tos':{'standard_name':'sea_surface_temperature', 'Title':'Sea surface temperature'},
     'sos':{'standard_name':'sea_surface_salinity'   , 'Title':'Sea surface salinity'   }
     })

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
    mtab = pmath (ptab)
    mref = pmath (pref)
    xr_unit   = None
    pint_unit = None

    if OPTIONS.Debug : print ( f'{mtab=} {mref=} {ptab.shape=} {pref.shape=}')

    if mref == xr :
        if 'pint' in dir (pref) :
            pint_unit = pref.pint.units
        else : 
            if 'units' in pref.attrs :
                xr_unit = pref.attrs['units']
    if mref in (np.ma, np):
        if 'units' in pref.attrs :
            pint_unit = pref.units

    if mref == xr :
        if mtab == xr :
            if OPTIONS.Debug : print ( 'copy_attrs : ptab is xr' )
            ztab = ptab
        elif mtab in [np, np.ma] :
            if OPTIONS.Debug : print ( 'copy_attrs : ptab is np or np.ma' )
            if ptab.shape == pref.shape :
                if OPTIONS.Debug : print ( 'copy_attrs : convert ptab to xarray' )
                ztab = xr.DataArray (ptab, coords=pref.coords, dims=pref.dims)
                ztab.name = pref.name
        else :
            if OPTIONS.Debug : print ( 'copy_attrs : ptab copied' )
            ztab = ptab

    if mref == xr :
        if pint_unit and pint in dir (ztab) :
            ztab = ztab.pint.quantify (pint_unit)
        if xr_unit and not pint_unit and pint in dir (ztab) :
            ztab = ztab.pint.quantify (pint_unit)
            
    if mref in [np, np.ma] :
        if pint_unit :
            ztab = Q_ (ztab, pint_unit)
       
    return ztab

def distance (lat1:float, lon1:float, lat2:float, lon2:float, radius:float=1.0, Debug=False) -> float :
    '''
    Compute distance on the sphere
    '''
    arg      = ( np.sin (np.deg2rad(lat1)) * np.sin (np.deg2rad(lat2))
               + np.cos (np.deg2rad(lat1)) * np.cos (np.deg2rad(lat2)) *
                 np.cos (np.deg2rad(lon1-lon2)) ) 
    
    zdistance = np.arccos (arg) * radius
    if OPTIONS.Debug or Debug :
        print ( f'1 - {zdistance.values = }' )

    zdistance = xr_quantify (zdistance)
    if OPTIONS.Debug or Debug :
        print ( f'2 - {zdistance.values = }' )

    if   'units' in dir(zdistance) :
        zdistance = zdistance / ureg.rad

    elif 'pint' in dir(zdistance) :
        zdistance = zdistance / ureg.rad

    if OPTIONS.Debug or Debug :
        print ( f'3 - {zdistance.values = }' )

    return zdistance

def aire_triangle (lat0: float, lon0: float, lat1: float, lon1: float, lat2: float, lon2: float, 
                   radius:float=1.0, Debug:bool=False) -> float :
    '''
    Area of a triangle on the sphere
    Girard's formula
    '''
    
    a = distance (lat0 , lon0, lat1 , lon1)
    b = distance (lat1 , lon1, lat2 , lon2)
    c = distance (lat2 , lon2, lat0 , lon0)

    if OPTIONS.Debug :
        print ( f'{a=}, {b=}, {c=}' )

    arg_alpha = (np.cos(a) - np.cos(b)*np.cos(c)) / (np.sin(b)*np.sin(c)) 
    arg_beta  = (np.cos(b) - np.cos(a)*np.cos(c)) / (np.sin(a)*np.sin(c)) 
    arg_gamma = (np.cos(c) - np.cos(a)*np.cos(b)) / (np.sin(a)*np.sin(b))

    if OPTIONS.Debug or Debug :
        print ( f'{arg_alpha=}, {arg_beta=}, {arg_gamma=}' )
    
    alpha = np.arccos (arg_alpha) 
    beta  = np.arccos (arg_beta ) 
    gamma = np.arccos (arg_gamma)

    if OPTIONS.Debug or Debug :
        print ( f'{alpha=}, {beta=}, {gamma=} {radius.item()=}' )

    Saire = (alpha + beta + gamma - np.pi) * radius * radius
    Saire = xr_quantify (Saire)

    return Saire

def aire_quadri (lat0:float, lon0:float, lat1:float, lon1:float, lat2:float, lon2:float, lat3:float, lon3:float, radius:float=1.0) -> float :
    '''
    Area of a quadrilatere on the sphere
    Girard's formula
    '''
    
    Saire = aire_triangle (lat0, lon0, lat1, lon1, lat2, lon2, radius ) \
          + aire_triangle (lat2, lon2, lat3, lon3, lat0, lon0, radius )
          
    return Saire

