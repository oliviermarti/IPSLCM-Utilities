# -*- coding: utf-8 -*-
## ============================================================================
##                                                                             
##  This software is governed by the CeCILL  license under French law and      
##  abiding by the rules of distribution of free software.  You can  use,      
##  modify and/ or redistribute the software under the terms of the CeCILL     
##  license as circulated by CEA, CNRS and INRIA at the following URL          
##  "http://www.cecill.info".                                                  
##                                                                             
##  Warning, to install, configure, run, use any of Olivier Marti's            
##  software or to read the associated documentation you'll need at least      
##  one (1) brain in a reasonably working order. Lack of this implement        
##  will void any warranties (either express or implied).                      
##  O. Marti assumes no responsability for errors, omissions,                  
##  data loss, or any other consequences caused directly or indirectly by      
##  the usage of his software by incorrectly or partially configured           
##  personal.                                                                  
##                                                                             
## ============================================================================
'''
Utilities for LMDZ grid

- Lots of tests for xarray object
- Not much tested for numpy objects

Author: olivier.marti@lsce.ipsl.fr

## SVN information                                                             
__Author__   = "$Author: omamce$"
__Date__     = "$Date: 2023-10-10 12:58:04 +0200 (Tue, 10 Oct 2023)$"
__Revision__ = "$Revision: 6647$"
__Id__       = "$Id: $"
__HeadURL    = "$HeadURL: svn+ssh://omamce@forge.ipsl.jussieu.fr/ipsl/forge/projets/igcmg/svn/TOOLS/WATER_BUDGET/lmdz.py$"
'''

import numpy as np
import xarray as xr
import cartopy
import cf_xarray.units 
import pint_xarray
from pint_xarray import unit_registry as ureg
Q_ = ureg.Quantity

if cartopy.__version__ > '0.20' :
    import cartopy.util as cutil
else :
    import my_cyclic as cutil
from Utils import Container
    
REPSI = np.finfo (1.0).eps

RAAMO  = xr.DataArray (12)        ; RAAMO .name='RAAMO'  ; RAAMO.attrs.update  ({'units':"mth"    , 'long_name':"Number of months in one year" })
RJJHH  = xr.DataArray (24)        ; RJJHH .name='RJJHH'  ; RJJHH.attrs.update  ({'units':"h"      , 'long_name':"Number of hours in one day"} )
RHHMM  = xr.DataArray (60)        ; RHHMM .name='RHHMM'  ; RHHMM.attrs.update  ({'units':"min"    , 'long_name':"Number of minutes in one hour"} )
RMMSS  = xr.DataArray (60)        ; RMMSS .name='RMMSS'  ; RMMSS.attrs.update  ({'units':"s"      , 'long_name':"Number of seconds in one minute"} )
RA     = xr.DataArray (6371229.0) ; RA    .name='RA'     ; RA.attrs.update     ({'units':"m"      , 'long_name':"Earth radius"} )
GRAV   = xr.DataArray (9.80665)   ; GRAV  .name='GRAV'   ; GRAV.attrs.update   ({'units':"m/s2"   , 'long_name':"Gravity"} )
RT0    = xr.DataArray (273.15)    ; RT0   .name='RT0'    ; RT0.attrs.update    ({'units':"K"      , 'long_name':"Freezing point of fresh water"} )
RAU0   = xr.DataArray (1026.0)    ; RAU0  .name='RAU0'   ; RAU0.attrs.update   ({'units':"kg/m3"  , 'long_name':"Volumic mass of sea water"} )
SICE   = xr.DataArray (6.0)       ; SICE  .name='SICE'   ; SICE.attrs.update   ({'units':"psu"    , 'long_name':"Salinity of ice (for pisces)"} )
SOCE   = xr.DataArray (34.7)      ; SOCE  .name='SOCE'   ; SOCE.attrs.update   ({'units':"psu"    , 'long_name':"Salinity of sea (for pisces and isf)"} )
RLEVAP = xr.DataArray (2.5e+6)    ; RLEVAP.name='RLEVAP' ; RLEVAP.attrs.update ({'units':"J/K"    , 'long_name':"Latent heat of evaporation (water)"} )
VKARMN = xr.DataArray (0.4)       ; VKARMN.name='VKARMN' ; VKARMN.attrs.update ({'units':"-"      , 'long_name':"Von Karman constant"} )
STEFAN = xr.DataArray (5.67e-8)   ; STEFAN.name='STEFAN' ; STEFAN.attrs.update ({'units':"W/m2/K4", 'long_name':"Stefan-Boltzmann constant"} )

RDAY   = RJJHH * RHHMM * RMMSS               ; RDAY.attrs.update   ({'units':"s"      , 'long_name':"Day length"})
RSIYEA = 365.25 * RDAY * 2. * np.pi / 6.283076 ; RSIYEA.attrs.update ({'units':"s"      , 'long_name':"Sideral year length"})
RSIDAY = RDAY / (1. + RDAY / RSIYEA)         ; RSIDAY.attrs.update ({'units':"s"      , 'long_name':"Sideral day length"})
ROMEGA = 2. * np.pi / RSIDAY                   ; ROMEGA.attrs.update ({'units':"s-1"    , 'long_name':"Earth rotation parameter"})

## Default names of dimensions                                                 
UDIMS = { 'x':'lon', 'y':'lat', 'z':'presnivs', 't':'time_counter' }

## All possible names of dimensions in LMDZ files                              
XNAME = [ 'x', 'X', 'lon', ]
YNAME = [ 'y', 'Y', 'lat', ]
CNAME = [ 'c', 'cell', ]
ZNAME = [ 'z', 'Z', 'presnivs', ]
TNAME = [ 't', 'T', 'tt', 'TT', 'time', 'time_counter', 'time_centered', 'TIME', 'TIME_COUNTER', 'TIME_CENTERED', ]

## All possibles name of units of dimensions in LMDZ files                     
XUNIT = [ 'degrees_east', ]
YUNIT = [ 'degrees_north', ]
CUNIT = [ 'cell', ]
ZUNIT = [ 'Pa', ]
TUNIT = [ 'second', 'minute', 'hour', 'day', 'month', 'year', ]

## All possibles size of dimensions in LMDZ files                              
XLENGTH  = [ 96, 144, 180, 360, ]
YLENGTH  = [ 95, 96, 143, 144, 180, 360, ]
XYLENGTH = [ [96,95], [144, 143], [180, 180], [360, 360]]
CLENGTH  = [ 16002, ]
ZLENGTH  = [ 39, 59, 79, ]

## Units not recognize by pint
ureg.define ('degree_C = degC'   )
ureg.define ('DU  = 10^-5 * m'   )
ureg.define ('ppb = 10^-9 * kg/kg' )

pint_dict = {
    # 'R_ecc'         : "m/m" ,
    # 'R_ecc'         : "m/m" ,
    # 'R_peri'        : "m/m" ,
    # 'R_peri'        : "m/m" ,
    # 'abs550aer'     : "m/m" ,
    # 'aire'          : "m^2" ,
    # 'aire'          : "m/m" ,
    # 'alb1'          : "m/m" ,
    # 'alb1'          : "m/m" ,
    # 'alb2'          : "m/m" ,
    # 'albe_lic'      : "m/m" ,
    # 'albe_oce'      : "m/m" ,
    # 'albe_sic'      : "m/m" ,
    # 'albe_ter'      : "m/m" ,
    # 'bnds'          : "m/m" ,
    # 'cdrh'          : "m/m" ,
    # 'cdrm'          : "m/m" ,
    # 'cldh'          : "m/m" ,
    # 'cldicemxrat'   : "m/m" ,
    # 'cldl'          : "m/m" ,
    # 'cldm'          : "m/m" ,
    # 'cldt'          : "m/m" ,
    # 'cldwatmxrat'   : "m/m" ,
    # 'dqajs2d'       : "kg/m^2/s" ,
    # 'dqcon2d'       : "kg/m^2/s" ,
    # 'dqdyn2d'       : "kg/m^2/s" ,
    # 'dqeva2d'       : "kg/m^2/s" ,
    # 'dqldyn2d'      : "kg/m^2/s" ,
    # 'dqlphy2d'      : "kg/m^2/s" ,
    # 'dqlsc2d'       : "kg/m^2/s" ,
    # 'dqphy2d'       : "kg/m^2/s" ,
    # 'dqsdyn2d'      : "kg/m^2/s" ,
    # 'dqsphy2d'      : "kg/m^2/s" ,
    # 'dqthe2d'       : "kg/m^2/s" ,
    # 'dqvdf2d'       : "kg/m^2/s" ,
    # 'dqwak2d'       : "kg/m^2/s" ,
    # 'dryod550aer'   : "m/m" ,
    # 'ec550aer'      : "m^-1" ,
    # 'ec550aer'      : "m^-1" ,
    # 'evap'          : "kg/s/m^2" ,
    # 'evap_lic'      : "kg/s/m^2" ,
    # 'evap_oce'      : "kg/s/m^2" ,
    # 'evap_sic'      : "kg/s/m^2" ,
    # 'evap_ter'      : "kg/s/m^2" ,
    # 'fl'            : "m/m" ,
    # 'fract_lic'     : "m/m" ,
    # 'fract_lic'     : "m/m" ,
    # 'fract_oce'     : "m/m" ,
    # 'fract_oce'     : "m/m" ,
    # 'fract_sic'     : "m/m" ,
    # 'fract_sic'     : "m/m" ,	
    # 'fract_ter'     : "m/m" ,
    # 'fract_ter'     : "m/m" ,
    # 'fsnow'         : "m/m" ,
    # 'ftime_con'     : "m/m" ,
    # 'ftime_deepcv'  : "m/m" ,
    # 'ftime_th'      : "m/m" ,
    # 'klev'          : "m/m" ,
    # 'klevp1'        : "m/m" ,
    # 'n2'            : "m/m" ,
    # 'ndayrain'      :  "days" ,
    # 'ndayrain'      : "m/m" ,
    # 'od550_STRAT'   : "m/m" ,
    # 'od550aer'      : "m/m" ,
    # 'od550lt1aer'   : "m/m" ,
    # 'od550lt1aer'   : "m/m" ,
    # 'od865aer'      : "m/m" ,
    # 'ozone'         : "m/m" ,
    # 'ozone_daylight': "m/m" ,
    # 'pluc'          : "kg/s/m^2" ,
    # 'plul'          : "kg/s/m^2" ,
    # 'plun'          : "kg/s/m^2" ,
    # 'pr_con_i'      : "m/m" ,
    # 'pr_con_l'      : "m/m" ,
    # 'pr_lsc_i'      : "m/m" ,
    # 'pr_lsc_l'      : "m/m" ,
    # 'precip'        : "kg/s/m^2" ,
    # 'proba_notrig'  : "m/m" ,
    # 'rain_con'      : "kg/s/m^2" ,
    # 'rain_fall'     : "kg/s/m^2" ,
    # 'random_notrig' : "m/m" ,
    # 'rhum'          : "m/m" ,
    # 'rneb'          : "m/m" ,
    # 'rsu'           : "W m-2" ,
    # 'sicf'          : "m/m" ,
    # 'snow'          : "kg/s/m^2" ,
    # 'stratomask'    : "m/m" ,
    # 'ue'            : "m/m" ,
    # 'uq'            : "m/m" ,
    # 'uwat'          : "m/m" ,
    # 've'            : "m/m" ,
    # 'vq'            : "m/m" ,
    # 'vwat'          : "m/m" ,
    # 'wake_dens'     : "m^-2" ,
    # 'wake_h'        : "m/m" ,
    # 'wake_s'        : "m/m" ,
    # 'wape'          : "m/m" ,
    # 'wbilo_lic'     : "kg/m^2/s" ,
    # 'wbilo_oce'     : "kg/m^2/s" ,
    # 'wbilo_sic'     : "kg/m^2/s" ,
    # 'wbilo_ter'     : "kg/m^2/s" ,
    # 'wevap_lic'     : "kg/m^2/s" ,
    # 'wevap_oce'     : "kg/m^2/s" ,
    # 'wevap_sic'     : "kg/m^2/s" ,
    # 'wevap_ter'     : "kg/m^2/s" ,
    # 'wrain_lic'     : "kg/m^2/s" ,
    # 'wrain_oce'     : "kg/m^2/s" ,
    # 'wrain_sic'     : "kg/m^2/s" ,
    # 'wrain_ter'     : "kg/m^2/s" ,
    # 'wsnow_lic'     : "kg/m^2/s" ,
    # 'wsnow_oce'     : "kg/m^2/s" ,
    # 'wsnow_sic'     : "kg/m^2/s" ,
    # 'wsnow_ter'     : "kg/m^2/s" ,
    # 'wvapp'         : "m/m" ,
    'epmax'             : 'W m^-2' , # A verifier !!! Que veut dire su ?
    'ep'                : 'W m^-2' , # A verifier !!!
    #'flx_co2_ocean'     : "kg/m2/s" ,
    #'flx_co2_land'      : "kg/m2/s" ,
    #'flx_co2_ocean_cor' : "kg/m2/s" ,
    #'flx_co2_land_cor'  : "kg/m2/s" ,
    #'flx_co2_ff'        : "kg/m2/s" ,
    #'flx_co2_bb'        : "kg/m2/s" ,
    }

orch_dict = {
    'ksat'        : "microm/s" ,
    'npp'         : "g/m^2/s"  ,
    'TWS'         : "kg/m^2"   ,
    'TWBR'        : "kg/m^2"   ,
    'mrso'        : "kg/m^2"   ,
    'undermcr'    : 'm/m'      ,
    'gpp'         : "g/m^2/s"  , 
    'gppCrop'     : "g/m^2/s"  , 
    'nee'         : "g/m^2/s"  , 
    'maint_resp'  : "g/m^2/s"  , 
    'hetero_resp' : "g/m^2/s"  , 
    'growth_resp' : "g/m^2/s"  , 
    'rhCrop'      : "g/m^2/s"  , 
    }

## lmdz internal options                                                       
OPTIONS = Container (Debug=False, Trace=False, Timing=None, t0=None, Depth=None, Stack=None)

class set_options :
    '''
    Set options for LMDZ
    '''
    def __init__ (self, **kwargs):
        self.old = Container ()
        for k, v in kwargs.items():
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update (self, options_dict):
        OPTIONS.update (options_dict)

    def __enter__ (self):
        return

    def __exit__ (self, type, value, traceback):
        self._apply_update (self.old)

def get_options () -> dict :
    '''
    Get options for LMDZ

    See Also
    ----------
    set_options

    '''
    return OPTIONS

def return_stack () :
    return OPTIONS.Stack

def push_stack (string:str) :
    if OPTIONS.Depth : OPTIONS.Depth += 1
    else                : OPTIONS.Depth = 1
    if OPTIONS.Trace : print ( '  '*(OPTIONS.Depth-1), f'-->{__name__}.{string}' )
    #
    if OPTIONS.Stack : OPTIONS.Stack.append (string)
    else             : OPTIONS.Stack = [string,]
    #
    if OPTIONS.Timing :
        if OPTIONS.t0 :
            OPTIONS.t0.append ( time.time() )
        else :
            OPTIONS.t0 = [ time.time(), ]

def pop_stack (string:str) :
    if OPTIONS.Timing :
        dt = time.time() - OPTIONS.t0[-1]
        OPTIONS['t0'].pop()
    else :
        dt = None
    if OPTIONS['Trace'] or dt :
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
    if OPTIONS.Depth == 0 : OPTIONS.Depth = None
    OPTIONS.Stack.pop ()
    if OPTIONS.Stack == list () : OPTIONS.Stack = None
    #

## ============================================================================

def __mmath__ (ptab, default=None) :
    '''
    Determines the type of tab : xarray, numpy or numpy.ma object ?

    Returns type : xr, np or np.ma
    '''
    push_stack ( f'__mmath__ ( ptab, {default=} )' )
    mmath = default
    if isinstance (ptab, xr.core.dataarray.DataArray) : mmath = xr
    if isinstance (ptab, np.ndarray)                  : mmath = np
    if isinstance (ptab, np.ma.MaskType)              : mmath = np.ma
        
    pop_stack ( f'__math_ : {mmath}' )
    return mmath

def __find_axis__ (ptab, axis='z', back=True) :
    '''
    Returns name and name of the requested axis
    '''
    push_stack ( f'__find_axis__ ( ptab, {axis=} {back=} )' )

    mmath = __mmath__ (ptab)
    ax, ix = None, None

    if axis in XNAME :
        ax_name, unit_list, length = XNAME, XUNIT, XLENGTH
        if OPTIONS.Debug : print ( f'Working on xaxis found by name : {axis=} : {XNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in YNAME :
        ax_name, unit_list, length = YNAME, YUNIT, YLENGTH
        if OPTIONS.Debug : print ( f'Working on yaxis found by name : {axis=} : {YNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in CNAME :
        ax_name, unit_list, length = CNAME, CUNIT, CLENGTH
        if OPTIONS.Debug : print ( f'Working on caxis found by name : {axis=} : {CNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in ZNAME :
        ax_name, unit_list, length = ZNAME, ZUNIT, ZLENGTH
        if OPTIONS.Debug : print ( f'Working on zaxis found by name : {axis=} : {ZNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in TNAME :
        ax_name, unit_list, length = TNAME, TUNIT, None
        if OPTIONS.Debug : print ( f'Working on taxis found by name : {axis=} : {TNAME=} {ax_name=} {unit_list=} {length=}' )

    if mmath == xr :
        # Try by name
        for dim in ax_name :
            if dim in ptab.dims :
                if OPTIONS.Debug : print ( f'Rule 2 : {name=} axis found by unit : {axis=} : {XNAME=}' )
                ix, ax = ptab.dims.index (dim), dim

        # If not found, try by axis attributes
        if not ix :
            for i, dim in enumerate (ptab.dims) :
                if 'axis' in ptab.coords[dim].attrs.keys() :
                    l_axis = ptab.coords[dim].attrs['axis']
                    if OPTIONS.Debug : print ( f'Rule 3 : Trying {i=} {dim=} {l_axis=}' )
                    if l_axis in ax_name and l_axis == 'X' :
                        if OPTIONS.Debug : print ( f'Rule 3 : xaxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {i=} {dim=}' )
                        ix, ax = (i, dim)
                    if l_axis in ax_name and l_axis == 'Y' :
                        if OPTIONS.Debug : print ( f'Rule 3 : yaxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {i=} {dim=}' )
                        ix, ax = (i, dim)
                    if l_axis in ax_name and l_axis == 'C' :
                        if OPTIONS.Debug : print ( f'Rule 3 : caxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {i=} {dim=}' )
                        ix, ax = (i, dim)
                    if l_axis in ax_name and l_axis == 'Z' :
                        if OPTIONS.Debug : print ( f'Rule 3 : zaxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {i=} {dim=}' )
                        ix, ax = (i, dim)
                    if l_axis in ax_name and l_axis == 'T' :
                        if OPTIONS.Debug : print ( f'Rule 3 : taxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {i=} {dim=}' )
                        ix, ax = (i, dim)

        # If not found, try by units
        if not ix :
            for i, dim in enumerate (ptab.dims) :
                if 'units' in ptab.coords[dim].attrs.keys() :
                    for name in unit_list :
                        if name in ptab.coords[dim].attrs['units'] :
                            if OPTIONS.Debug : print ( f'Rule 4 : axis found by unit {name} : {unit_list=} {i=} {dim=}' )
                            ix, ax = i, dim

    # If numpy array or dimension not found, try by length
    if mmath != xr or not ix :
        if length :
            l_shape = ptab.shape
            for nn in np.arange ( len(l_shape) ) :
                if l_shape[nn] in length :
                    if OPTIONS.Debug : print ( f'Rule 5 : axis found by length : {axis=} : {XNAME=} {i=} {dim=}' )
                    ix = nn

    if ix and back :
        ix -= len(ptab.shape)

    pop_stack ( f'__find_axis__ ( {ax=} {ix=} )' )
    return ax, ix

def find_axis ( ptab, axis='z', back=True ) :
    '''
    Version of find_axis with no __'''
    push_stack ( f'find_axis__ ( ptab {axis=} {back=} )' )
    ix, xx = __find_axis__ (ptab, axis, back, verbose)
    pop_stack ( f'find_axis ( {ax=} {ix=} )' )
    return xx, ix

def get_shape ( ptab ) :
    '''
    Get shape of ptab return a string with axes names

    shape may contain X, Y, C, Z or T
    Y is missing for a latitudinal slice
    X is missing for on longitudinal slice
    etc ...
    '''
    push_stack ( f'get_shape ( ptab) ' )

    g_shape = ''
    if __find_axis__ (ptab, 'x')[0] : g_shape = 'X'
    if __find_axis__ (ptab, 'y')[0] : g_shape = 'Y' + g_shape
    if __find_axis__ (ptab, 'c')[0] : g_shape = 'C' + g_shape
    if __find_axis__ (ptab, 'z')[0] : g_shape = 'Z' + g_shape
    if __find_axis__ (ptab, 't')[0] : g_shape = 'T' + g_shape

    push_stack ( f'get_shape : {g_shape=} ' )
    return g_shape

def extend (tab, Lon=False, jplus=25, jpi=None, lonplus=360.0) :
    '''
    Returns extended field eastward to have better plots, and box average crossing the boundary

    Works only for xarray and numpy data (?)

    tab : field to extend.
    Lon : (optional, default=False) : if True, add 360 in the extended parts of the field
    jpi : normal longitude dimension of the field. exrtend does nothing it the actual
        size of the field != jpi (avoid to extend several times)
    jplus (optional, default=25) : number of points added on the east side of the field
    '''
    push_stack ( f'extend (tab, {Lon=}, {jplus=}, {jpi=}, {lonplus=})' )

    math = __mmath__ (tab)
    if tab.shape[-1] == 1 :
        ztab = tab

    else :
        if jpi is None : jpi = tab.shape[-1]

        if Lon : xplus =  lonplus
        else   : xplus =    0.0

        if tab.shape[-1] > jpi :
            ztab = tab
        else :
            istart = 0
            le     = jpi+1
            la     = 0
            if math == xr :
                lon = tab.dims[-1]
                ztab         = xr.concat      ((
                    tab.isel (lon=slice(istart   ,istart+le      )),
                    tab.isel (lon=slice(istart+la,istart+la+jplus))+xplus  ), dim=lon)
                if 'lon' in tab.dims :
                    extend_lon = xr.concat      ((
                        tab.coords[lon].isel(lon=slice(istart   ,istart+le      )),
                        tab.coords[lon].isel(lon=slice(istart+la,istart+la+jplus))+lonplus), dim=lon)
                    ztab = ztab.assign_coords ( {tab.dims[-1]:extend_lon} )
            if math in [np, np.ma] :
                ztab = np.concatenate ((tab    [..., istart:istart+le],
                                        tab    [..., istart+la:jplus]+xplus  ), axis=-1)

    pop_stack ( f'extend ' )
    return ztab

def interp1d (x, xp, yp, zdim='presnivs', units=None, method='linear') :
    '''
    One-dimensionnal interpolation of a multi-dimensionnal field

    Intended to interpolate on standard pressure level

    All inputs shoud be xarray data arrays

    Input :
       x      : levels at wich we want to interpolate (i.e. standard pressure levels)
       xp     : position of the input points (i.e. pressure)
       yp     : fields values at these points (temperature, humidity, etc ..)
       zdim   : name of the dimension that we want to interpolate
       method : available methods are
           linear
           log[arithmic]. Available for positive values only
           nearest : nearest neighbor

           Warning : xp should be decreasing values along zdim axis
    '''
    push_stack ( f'interp1d (x, xp, yp, {zdim=}, {units=}, {method=})' )

    # Get the number of dimension with dim==zdim in input array
    axis = list (yp.dims).index(zdim)
    if OPTIONS.Debug : print ( f'{axis=}' )

    # Get the number of levels in each arrays
    nk_ou = len (x)

    # Define the result array
    in_shape       = np.array (yp.shape)
    if OPTIONS.Debug : print ( f'{in_shape=}' )
    ou_shape       = np.array (in_shape)
    if OPTIONS.Debug : print ( f'{ou_shape=}' )
    ou_shape[axis] = nk_ou

    in_dims        = list (yp.dims)
    if OPTIONS.Debug : print ( f'{in_dims=}' )
    ou_dims        = in_dims

    pdim           = x.dims[0]
    ou_dims[axis]  = pdim

    if OPTIONS.Debug : print ( f'{pdim=}' )

    new_coords = []
    for i, dim in enumerate (yp.dims) :
        if dim == zdim :
            ou_dims[i] = x.dims[0]
            if units is not None :
                yp[dim].attrs['units'] = units
            if OPTIONS.Debug : print ( f'append new coord for {dim=} {x.shape=}' )
            new_coords.append (x             .values)
        else :
            if OPTIONS.Debug : print ( f'append coord for {dim=} {yp.coords[dim].shape=}' )
            new_coords.append (yp.coords[dim].values)

    #if OPTIONS.Debug :
    #    print ( f'{ou_dims   =}' )
    #    print ( f'{new_coords=}' )

    ou_tab = xr.DataArray (np.empty (ou_shape), dims=ou_dims, coords=new_coords)

    if OPTIONS.Debug :
        print ( f'{ou_tab.shape=} {ou_tab.dims=}' )
    
    if 'log' in method :
        yp_min = yp.min()
        yp_max = yp.max()
        indic  = yp_min * yp_max
        if indic <= 0. :
            print ( 'Input data have a change of sign')
            print ( 'Error: logarithmic method is available only for')
            print ( 'strictly positive or strictly negative input values. ')
            raise ValueError

    def __interp (x, xp, yp, pdim='presnivs') :
        # Interpolate
        # Find index of the just above level
        push_stack ( f'interp1d.__interp (x, xp, yp, {pdim=})' )

        #if OPTIONS.Debug :
        #    print ( f'{x.shape=} {x.dims=} {xp.shape=} {yp.shape=}' )
        #    print ( f'{pdim=}' )
        idk1 = np.minimum ( (x-xp), 0.).argmax (dim=pdim)
        idk2 = idk1 - 1
        idk2 = np.maximum (idk2, 0)

        #if OPTIONS.Debug :
        #    print ( f'{idk1=} {idk2=}' )
        
        x1   = xp[{pdim:idk1}]
        x2   = xp[{pdim:idk2}]

        dx1  = x  - x1
        dx2  = x2 - x
        dx   = x2 - x1
        dx1  = dx1/dx
        dx2  = dx2/dx

        y1   = yp[{pdim:idk1}]
        y2   = yp[{pdim:idk2}]

        if 'linear'  in method :
            result = dx1*y2 + dx2*y1
        if 'log'     in method :
            if yp_min > 0. : result = np.power(y2, dx1) * np.power(y1, dx2)
            if yp_max < 0. : result = -np.power(-y2, dx1) * np.power(-y1, dx2)
        if 'nearest' in method :
            result = xr.where ( dx2>=dx1, y1, y2)

        pop_stack ( f'interp1d.__interp' )
        return result

    for k in np.arange (nk_ou) :
        zlev = x[{pdim:k}]
        result = __interp  (zlev, xp, yp)

        # Put result in the final array
        ou_tab [{pdim:k}] = result

    pop_stack ( f'interp1d' )
    return ou_tab.squeeze()

def correct_uv (u, v, lon, lat) :
    '''
    Corrects a Cartopy bug in orthographic projection

    See https://github.com/SciTools/cartopy/issues/1179

    The correction is needed with cartopy <= 0.20
    It seems that version 0.21 will correct the bug (https://github.com/SciTools/cartopy/pull/1926)
    Later note : the bug is still present in Cartopy 0.22

    Inputs :
       u, v : eastward/northward components
       lat  : latitude of the point (degrees north)

    Outputs :
       modified eastward/nothward components to have correct polar projections in cartopy
    '''
    push_stack ( f'correct_uv (u, v, lon, lat)' )
    
    uv = np.sqrt (u*u + v*v)           # Original modulus
    zu = u
    zv = v * np.cos (np.deg2rad(lat))
    zz = np.sqrt ( zu*zu + zv*zv )     # Corrected modulus
    uc = zu*uv/zz
    vc = zv*uv/zz                      # Final corrected values
    
    uc[...,  0, :] = np.nan
    uc[..., -1, :] = np.nan
    vc[...,  0, :] = np.nan #p.nan
    vc[..., -1, :] = np.nan #np.nan
    # Keep only one value at poles

    pop_stack ( f'correct_uv' )
    return uc, vc

def fixed_lon (lon, center_lon=0.0) :
    '''Returns corrected longitudes for nicer plots

    lon        : longitudes of the grid. At least 1D.
    center_lon : center longitude. Default=0.

    Designed by Phil Pelson. See https://gist.github.com/pelson/79cf31ef324774c97ae7
    '''
    push_stack ( f'fixed_lon (lon {center_lon=})' )

    mmath = __mmath__ (lon)

    zfixed_lon = lon.copy ()

    zfixed_lon = mmath.where (zfixed_lon > center_lon+180., zfixed_lon-360.0, fixed_lon)
    zfixed_lon = mmath.where (zfixed_lon < center_lon-180., zfixed_lon+360.0, fixed_lon)

    start = np.argmax (np.abs (np.diff (zfixed_lon, axis=-1)) > 180., axis=-1)
    zfixed_lon [start+1:] += 360.

    pop_stack ( f'fixed_lon' )
    return zfixed_lon

def nord2sud (p2d) :
    '''
    Swap north to south a 2D field
    '''
    pop_stack ( f'nord2sud (p2d)' )
    z2d_inv = p2d[..., -1::-1, : ]
    pop_stack ( f'nord2sud' )
    return z2d_inv 

def unify_dims ( dd, x='x', y='y', z='olevel', t='time_counter', c='cell' ) :
    '''
    Rename dimensions to unify them between LMDZ versions
    '''
    push_stack ( f'unify_dims ( dd, {x=}, {y=}, {z=}, {t=}, {c=} )' )

    for xx in XNAME :
        if xx in dd.dims and xx != x :
            if OPTIONS.Debug : print ( f"{xx} renamed to {x}" )
            dd = dd.rename ( {xx:x})

    for yy in YNAME :
        if yy in dd.dims and yy != y  :
            if OPTIONS.Debug : print ( f"{yy} renamed to {y}" )
            dd = dd.rename ( {yy:y} )

    for cc in CNAME :
        if cc in dd.dims and cc != c  :
            if OPTIONS.Debug : print ( f"{cc} renamed to {c}" )
            dd = dd.rename ( {cc:c} )

    for zz in ZNAME :
        if zz in dd.dims and zz != z :
            if OPTIONS.Debug : print ( f"{zz} renamed to {z}" )
            dd = dd.rename ( {zz:z} )

    for tt in TNAME  :
        if tt in dd.dims and tt != t :
            if OPTIONS.Debug : print ( f"{tt} renamed to {t}" )
            dd = dd.rename ( {tt:t} )

    pop_stack ( f'unify_dims' )
    return dd

def add_cyclic (ptab, x, y, axis=-1, cyclic=360, precision=0.0001) :
    '''
    Add a cyclic point to an array and optionally corresponding x/longitude and y/latitude coordinates.
    
    Same as cartopy.util.add_cyclic, but returns xarray instead of numy arrays.

    Use cartopy.util.add_cyclic
    '''
    push_stack ( f'add_cyclic ({ptab.shape=} {axis=} {cyclic=} {precision=} )' )

    #yy1, xx1 = xr.broadcast (y, x)
    xx1=x
    yy1=y
    ztab, xx, yy = cutil.add_cyclic (data=ptab, x=xx1, y=yy1, axis=axis, cyclic=360, precision=0.0001)
    #xx = xr.DataArray (xx, dims=(y.dims[0], x.dims[0]), coords=(yy[:,0].squeeze(), xx[0,:].squeeze()) )
    #yy = xr.DataArray (yy, dims=(y.dims[0], x.dims[0]), coords=(yy[:,0].squeeze(), xx[0,:].squeeze()) )
    xx = xr.DataArray (xx, dims=(x.dims[0],), coords=(xx.squeeze(),) )
    yy = xr.DataArray (yy, dims=(y.dims[0],), coords=(yy.squeeze(),) )

    new_coords = []
    for i, dim in enumerate (ptab.dims) :
        if dim == ptab.dims[axis] : new_coords.append (xx)
        else                      : new_coords.append (ptab.coords[dim].values)

    ztab = xr.DataArray (ztab, dims=ptab.dims, coords=new_coords)

    pop_stack ( f'add_cyclic' )
    return ztab, xx, yy

def point2geo (p1d, lon=False, lat=False, jpi=None, jpj=None, share_pole=False, lon_name=None, lat_name=None) :
    '''
    From 1D [..., points_physiques] (restart type) to 2D [..., lat, lon]

    if jpi/jpj are not set, try to guess them from the number of points

    if lon/lat is True, add longitude/latitude values (regular grid), with name lon_name (or 'lon' if lon_name not defined)
    if lon/lat is a string, add longitude/latitude values (regular grid), with name lon/lat
    '''
    push_stack (f'point2geo (p1d, {lon=}, {lat=}, {jpi=}, {jpj=}, {share_pole=}, {lon_name=}, {lat_name=})')
    
    math = __mmath__ (p1d)

    # Get the horizontal dimension
    jpn = p1d.shape[-1]
    # Get other dimension(s)
    form1 = list (p1d.shape [0:-1])

    if not jpi : jpi=0
    if not jpj : jpj=0

    # Check or compute 2D horizontal dimensions
    if jpi != 0 and jpj != 0 :
        if jpi*(jpj-2) + 2 != jpn :
            raise ValueError (f'{jpn=} {jpi=}, {jpj}, {jpi*(jpj-2)+2=} does match rule jpi·(jpj-2)+2==p1d.shape[-1]')
    if jpi==0 and jpj>0    : jpi = (jpn-2)//(jpj-2)
    if jpi>0  and jpj == 0 : jpj = (jpn-2)//jpi +2            
    if jpi==0 and jpi==0 :
        for [jj, ji] in [ [36,45], [72,96], [95,96], [96,96], [143,144], [144,144], [180,180] ] :
            if ji*(jj-2) + 2 == jpn :
                jpj = jj ; jpi = ji
        if jpi==0 and jpi==0 :
            raise ValueError (f'1D horizontal dimension {jpn=} not known. Cannot not guess horizontal dimensions jpj, jpi')
                
    form_all   = form1 + [jpj  , jpi]
    form_shape = form1 + [jpj-2, jpi]

    p2d = np.empty (form_all)
    p2d [..., 1:-1, :] = np.reshape (np.float64 (p1d [..., 1:-1]), form_shape )
    if OPTIONS.Debug : print (f'{math=} {jpn=} {jpi=} {jpi=} {form1=} {form_all=} {form_shape=} {p2d.shape=}')

    if share_pole :
        p2d [...,  0 , :].flat = p1d [...,  0] / float (jpi)
        p2d [..., -1 , :].flat = p1d [..., -1] / float (jpi)
    else :
        p2d [...,  0 , :].flat = p1d [...,  0]
        p2d [..., -1 , :].flat = p1d [..., -1]
        
    # Adding metadata, coordinates, etc ...
    if math == xr :
        p2d = xr.DataArray (p2d)
        p2d.attrs.update ( p1d.attrs )
        for idim in np.arange ( len(p1d.shape [0:-1]) ):
            dim = p1d.dims[idim]
            p2d = p2d.rename        ({p2d.dims[idim]:p1d.dims[idim]} )
            p2d = p2d.assign_coords ({p2d.dims[idim]:p1d.coords[dim]})
  
        if isinstance (lon, str) :
            if not lon_name : lon_name = lon
            lon = np.linspace ( -180, 180, jpi, endpoint=False)
        if isinstance (lat, str) :
            if not lat_name : lat_name = lat
            lat = np.linspace ( 90, -90, jpj, endpoint=True) 
        if isinstance(lon, bool) :
            if lon :
                if not lon_name : lon_name = 'lon'
                lon = np.linspace ( -180, 180, jpi, endpoint=False)
        if isinstance (lat, bool) :
            if lat :
                if not lat_name : lat_name = 'lat'
                lat = np.linspace ( 90, -90, jpj, endpoint=True)
        if OPTIONS.Debug : print ( f'{lon_name=} {type(lon)=}' )

        if __mmath__(lon) == np :
            if math == xr :
                if not lon_name : lon_name = 'lon'
                lon = xr.DataArray ( lon, dims=(lon_name,), coords=(lon,) )
                for aa in { 'units':'degrees_east', 'long_name':'Longitude', 'standard_name':'longitude', 'axis':'X' }.items() :
                    if aa[0] not in lon.attrs :
                        lon.attrs.update ( { aa[0]:aa[1] } )
        if __mmath__(lat) == np :
            if math == xr :
                if not lat_name : lat_name = 'lat'
                lat = xr.DataArray ( lat, dims=(lat_name,), coords=(lat,) )
                for aa in  { 'units':'degrees_north', 'long_name':'Latitude' , 'standard_name':'latitude' , 'axis':'Y' }.items () :
                     if aa[0] not in lat.attrs :
                        lat.attrs.update ( { aa[0]:aa[1] } )
        if not isinstance (lat, bool) :
            if not lat_name : 
                if  __mmath__ (lat) == xr : lat_name = lat.name
                else                      : lat_name = 'lat'
        if not isinstance (lon, bool) :
            if not lon_name :
                if __mmath__ (lon) == xr : lon_name = lon.name
                else                     : lon_name = 'lon'

        if not lon_name : lon_name = 'x'
        if not lat_name : lat_name = 'y'

        if OPTIONS.Debug : print ( f'{lon_name=}' )
            
        if lon_name != p2d.dims[-1] : p2d = p2d.rename ( {p2d.dims[-1]:lon_name} ) 
        if lat_name != p2d.dims[-2] : p2d = p2d.rename ( {p2d.dims[-2]:lat_name} )
        if __mmath__ (lon) in [xr, np, np.ma] : 
            p2d = p2d.assign_coords ( {lon_name:lon} )
            if __mmath__ (lon) in [xr, np, np.ma] :
                p2d[lon_name].attrs.update ( lon.attrs )
            else : 
                p2d[lon_name].attrs.update ( { 'units':'degrees_east' , 'long_name':'Longitude', 'standard_name':'longitude', 'axis':'X' } )
        if __mmath__ (lat) in [xr, np, np.ma] :  
            p2d = p2d.assign_coords ( {lat_name:lat} )
            if __mmath__ (lat) == xr : p2d[lon_name].attrs.update ( lat.attrs )
            else                     : p2d[lat_name].attrs.update ( { 'units':'degrees_north', 'long_name':'Latitude' , 'standard_name':'latitude' , 'axis':'Y' }  )

    pop_stack (f'point2geo')
    return p2d

def point3geo (p1d, lon=False, lat=False, lev=False, jpi=None, jpj=None, jpk=None, share_pole=False, lon_name=None, lat_name=None, lev_name=None) :
    '''
    From 2D [..., horizon_vertical] (restart type) to 3D [..., lev, lat, lon]

    if jpi/jpj/jpk are not set, try to guess them from the number of points

    if lon/lat is True, add longitude/latitude values (regular grid), with name lon_name (or 'lon' if lon_name not defined)
    if lon/lat is a string, add longitude/latitude values (regular grid), with name lon/lat
    '''
    push_stack ( f'point3geo (p1d, {lon=}, {lat=}, {lev=}, {jpi=}, {jpj=}, {jpk=}, {share_pole=}, {lon_name=}, {lat_name=}, {lev_name=}) ' )
    math = __mmath__ (p1d)

    # Get the horizontal dimension
    jpn = p1d.shape[-1]
    # Get other dimension(s)
    form1 = list (p1d.shape [0:-2])

    if not jpi : jpi=0
    if not jpj : jpj=0
    if not jpk : jpk=0
    
    # Check or compute 3D horizontal dimensions
    if jpk == 0 :
        if jpi==0 and jpi==0 :
            liste2D = [ [36,45], [72,96], [95,96], [96,96], [143,144], [144,144], [180,180] ]
        if jpi==0 and jpj>0 :
            liste2D = [ [jpj,45], [jpj,96], [jpj,96], [jpi, 144], [jpj,180] ]
        if jpi>0  and jpj == 0 :
            liste2D = [ [36,jpi], [72,jpi], [95,jpi], [96,jpi], [143,jpi], [144,jpi], [180,jpi] ]
        for jk in [11, 15, 16, 39, 40, 79, 80 ] : 
            for [jj, ji] in liste2D :
                if jk*(ji*(jj-2) + 2) == jpn : jpk = jk ; jpj = jj ; jpi = ji
        jpij = jpn / jpk
    else :
        jpij = jpn / jpk
        if jpi*jpj !=0 : 
            if jpk * ( jpi*(jpj-2) + 2 ) != jpn :
                raise ValueError (f'{jpn=}, {jpij=} {jpi=}, {jpj}, {jpk=}, {jpi*(jpj-2)+2=} does match rule jpi·(jpj-2)+2==p1d.shape[-1]')
        if jpi==0 and jpj>0    : jpi = (jij-2)//(jpj-2)
        if jpi>0  and jpj == 0 : jpj = (jij-2)//jpi +2            
        if jpi==0 and jpi==0 :
            for [jj, ji] in [ [36,45], [72,96], [95,96], [96,96], [143,144], [144,144], [180,180] ] :
                if ji*(jj-2) + 2 == jpij :
                    jpj = jj ; jpi = ji

    form_2D = form1 + list ( (jpk, jpi*(jpj-2) + 2, ) )

    if OPTIONS.Debug :
        print ( f'{jpn=}, {jpij=} {jpi=}, {jpj=}, {jpk=}' )
        print ( f'{form1=}, {form_2D=}' )
    if math == xr : p2d = np.reshape ( p1d.values, form_2D )
    else          : p2d = np.reshape ( p1d, form_2D )
        
    if OPTIONS.Debug :
        print ( f'{p2d.shape=}' )
    
    if math == xr :
        p2d = xr.DataArray (p2d)
        p2d.attrs.update ( p1d.attrs )
        for idim in np.arange ( len(p1d.shape [0:-1]) ):
            dim = p1d.dims[idim]
            p2d = p2d.rename        ( {p2d.dims[idim]:p1d.dims[idim]}  )
            p2d = p2d.assign_coords ( {p2d.dims[idim]:p1d.coords[dim]} )
            
    p3d = point2geo ( p2d, lon=lon, lat=lat, jpi=jpi, jpj=jpj, share_pole=share_pole, lon_name=lon_name, lat_name=lat_name )

    if lev_name != p3d.dims[-3] :
        p3d = p3d.rename ( {p3d.dims[-3]:lev_name} ) 
    if __mmath__ (lev) in [xr, np, np.ma] : 
            p2d = p2d.assign_coords ( {lev_name:lev} )
            if __mmath__ (lon) in [xr, np, np.ma] : p2d[lon_name].attrs.update ( lon.attrs )
            #else : 
            #    p2d[lon_name].attrs.update ( { 'units':'degrees_east', 'long_name':'Longitude', 'standard_name':'longitude', 'axis':'X' } )

    push_stack ( f'point3geo')
    return p3d

def geo2point ( p2d, cumul_poles=False, dim1d='points_physiques' ) :
    '''
    From 2D [..., lat, lon] to 1D [..., points_phyiques]
    '''
    push_stack ( f'geo2point ( p2d, {cumul_poles=}, {dim1d=} )' )
    math = __mmath__ (p2d)
    #
    # Get the horizontal dimensions
    (jpj, jpi) = p2d.shape[-2:]
    jpn = jpi*(jpj-2) + 2

    # Get other dimensions
    form1   = list(p2d.shape [0:-2]) 
    form_2D = form1 + [jpn,]
        
    p1d     = np.empty (form_2D)
    form_1D = form1 + [jpn-2,]
    
    if math == xr : p1d [..., 1:-1] = np.reshape ( np.float64 (p2d[..., 1:-1, :].values).ravel(), form_1D )
    else          : p1d [..., 1:-1] = np.reshape ( np.float64 (p2d[..., 1:-1, :]       ).ravel(), form_1D )
    if cumul_poles :
        p1d [...,  0] = np.sum ( p2d[...,  0, :], axis=-1 )
        p1d [..., -1] = np.sum ( p2d[..., -1, :], axis=-1 )
    else :
        p1d [...,  0  ] = p2d [...,  0, 0]
        p1d [..., -1  ] = p2d [..., -1, 0]

    # Adding metadata
    if math == xr :
        p1d = xr.DataArray (p1d)
        p1d.attrs.update ( p2d.attrs )
        if len(p2d.shape [0:-2]) > 0 : 
            for idim in np.arange ( len(p2d.shape [0:-2]) ):
                dim=p2d.dims[idim]
                p1d = p1d.rename        ( {p1d.dims[idim]:p2d.dims[idim]}   )
                p1d = p1d.assign_coords ( {p1d.dims[idim] :p2d.coords[dim].values} )
        p1d = p1d.rename ( {p1d.dims[-1]:dim1d} )

    pop_stack ( f'geo2point' )
    return p1d

def geo2en (pxx, pyy, pzz, glam, gphi) :
    '''
    Change vector from geocentric to east/north

    Inputs :
        pxx, pyy, pzz : components on the geocentric system
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( f'geo2en (pxx, pyy, pzz, glam, gphi)' )
    gsinlon = np.sin (np.deg2rad(glam))
    gcoslon = np.cos (np.deg2rad(glam))
    gsinlat = np.sin (np.deg2rad(gphi))
    gcoslat = np.cos (np.deg2rad(gphi))

    pte = - pxx * gsinlon            + pyy * gcoslon
    ptn = - pxx * gcoslon * gsinlat  - pyy * gsinlon * gsinlat + pzz * gcoslat

    pop_stack ( f'geo2en ')
    return pte, ptn

def en2geo (pte, ptn, glam, gphi) :
    '''
    Change vector from east/north to geocentric

    Inputs :
        pte, ptn : eastward/northward components
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( f'en2geo (pte, ptn, glam, gphi)' )
    gsinlon = np.sin (np.deg2rad(glam))
    gcoslon = np.cos (np.deg2rad(glam))
    gsinlat = np.sin (np.deg2rad(gphi))
    gcoslat = np.cos (np.deg2rad(gphi))

    pxx = - pte * gsinlon - ptn * gcoslon * gsinlat
    pyy =   pte * gcoslon - ptn * gsinlon * gsinlat
    pzz =   ptn * gcoslat

    pop_stack ( 'geo2en')
    return pxx, pyy, pzz

def limit_blon (blon, clon, lon_cen=0) :
    '''
    From mapper https://github.com/PBrockmann/VTK_Mapper
    needed to limit excursion from center of the cell to longitude boundaries
    '''
    push_stack (f'limit_blon (blon, clon, {lon_cen=})')
    lon_min = lon_cen-180. ; lon_max = lon_cen+180.
    
    clon  = (clon+360.*10.)%360
    clon  = np.where (np.greater (clon, lon_max), clon-360., clon)
    clon  = np.where (np.less    (clon, lon_min), clon+360., clon)
    clon1 = np.ones  (blon.shape, dtype=float) * clon[..., None]

    blon  = (blon+360.*10.)%360
    blon  = np.where (np.greater(blon, lon_max), blon-360., blon)
    blon  = np.where (np.less   (blon, lon_min), blon+360., blon)
    
    blon  = np.where (np.greater(abs(blon-clon1), abs(blon+360. -clon1)), blon+360., blon)
    blon  = np.where (np.greater(abs(blon-clon1), abs(blon-360. -clon1)), blon-360., blon)

    pop_stack ( 'limit_blon' )
    return blon, clon

def limit_lon (clon, lon_cen=0) :
    '''
    From mapper https://github.com/PBrockmann/VTK_Mapper
    needed to limit excursion from center of the cell to longitude boundaries
    '''
    push_stack ( f'limit_lon (clon, {lon_cen})' )
    lon_min = lon_cen-180. ; lon_max = lon_cen+180.
    
    clon  = (clon+360.*10.)%360
    clon  = np.where (np.greater (clon, lon_max), clon-360., clon)
    clon  = np.where (np.less    (clon, lon_min), clon+360.,clon)
    
    return clon

def direction (uu, vv, unit='deg') :
    '''
    Compute direction of a vector (angle with north)
    '''
    zd = np.atan2 (uu,vv)

## ===========================================================================
##                                                                            
##                               That's all folk's !!!                        
##                                                                            
## ===========================================================================
