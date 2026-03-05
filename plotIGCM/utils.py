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
import os
from typing import Callable, Any, Self, Literal, _LiteralGenericAlias # pyright: ignore[reportAttributeAccessIssue]
import typing
import re
from urllib.request import urlretrieve
from pathlib import Path

import numpy as np
import xarray as xr
import shapely as shp

import cftime
import cartopy
import cartopy.crs as ccrs

from plotIGCM.options import OPTIONS
from plotIGCM.options import push_stack
from plotIGCM.options import pop_stack

class RegexEqual (str) :
    def __eq__(self:Self, pattern:str) -> bool :
        return bool (re.search(pattern, self))

Debug=True
Check=False

def GetFile (url:str, File=None, Debug=False) :
    '''
    Get a file from a web server
    '''
    if File : File = Path (File)
    else    : File = Path (os.path.basename(url))
    if not File.exists () :
        if OPTIONS['Debug'] or Debug :
            print ( f'Retrieving url={url}' )
        urlretrieve (url, File)
    return File

def build_feat (file, Debug=False, facecolor='none', edgecolor='k') :
    '''
    From a geojson file, build a cartopy feature
    '''
    if 'http' in file : zf = open (GetFile (file), 'r')
    else              : zf = open (file, 'r')
    if OPTIONS['Debug'] or Debug :
        print ( f'Reading shapefile in {file=}' )
    file_shp  = shp.from_geojson (zf.read())
    file_poly = cartopy.feature.ShapelyFeature (file_shp, crs=ccrs.PlateCarree(),# pyright: ignore[reportAttributeAccessIssue]
                                    facecolor=facecolor, edgecolor=edgecolor) # pyright: ignore[reportAttributeAccessIssue]
    zf.close()
    return file_poly, file_shp

def join_series (ptab1, ptab2, dim='time_counter', Debug=False) :
    '''
    Join two time series : first take ptab1, and ptab2 when possible
    '''
    Y1 = ptab1[dim][ 0].item().year
    Y3 = ptab2[dim][ 0].item().year
    Y4 = ptab2[dim][-1].item().year
    Y2 = Y3-1

    #print (Y1, Y2, Y3, Y4)

    print ( f'Start of simu1: {Y1=} | End of simu 1: {Y2=} | End of simu 1 {Y3=} | End of simus 2 : {Y4=}' )

    T1 = f"{Y1:04d}-01-01"
    T2 = f"{Y2:04d}-12-31"
    T3 = f"{Y3:04d}-01-01"
    T4 = f"{Y4:04d}-12-31"

    if OPTIONS['Debug'] or Debug :
        print ( f'Start of simu1: {T1=} | End of simu 1: {T2=} | End of simu 1 {T3=} | End of simus 2 : {T4=}' )

    ptab3 =  xr.concat ( [ ptab1.sel( {dim:slice(T1,T2)} ), ptab2.sel ( {dim:slice(T3,T4)} ) ], dim=dim )
    return ptab3

def add_year (ptime:xr.DataArray, year_shift:int=0, Debug=False) -> xr.DataArray :
    '''
    Add years to a time variable
    Time variable is an xarray of cftime values
    '''
    dates_elements   = [ (date.year+year_shift, date.month, date.day, date.hour,
                          date.minute, date.second, date.microsecond) for date in ptime.values]

    if isinstance (ptime[0].item(), cftime._cftime.DatetimeGregorian) :
        if Debug :
            print ( 'add_year: Gregorian calendar case' )
        time_new = [ cftime.DatetimeGregorian (*date_el, has_year_zero=False)\
                             for date_el in dates_elements ]
    else :
        if Debug :
            print ( 'add_year: standard calendar case' )
        time_new = [ cftime.datetime (*date_el, calendar='standard',
                              has_year_zero=False) for date_el in dates_elements ]

    time_counter = xr.DataArray (time_new, dims=(ptime.name,), coords=(time_new,))
    time_counter.attrs.update (ptime.attrs)

    return time_counter

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
                #if type(param_type) == typing._LiteralGenericAlias :
                if isinstance(param_type, _LiteralGenericAlias) :
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

def copy_attrs (ptab:xr.DataArray, pref:xr.DataArray, Debug:bool=False) -> xr.DataArray :
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

def unit2math (unit:str, Debug:bool=False) -> str :
    '''
    Return a nice unit for matplotlib
    '''
    zu = unit
        
    #match RegexEqual (unit) :
    #    case 'C'             : zu = '°C'
    #    #case 'deg.*C'        : zu = '°C'
    #    case _               : zu = unit

    zu = zu.replace ( '.', ' ')

    zu = re.sub ( 'deg.*C', '°C', zu)

    # Correct Orchidee Units
    zu = zu.replace ( 'Kg', 'kg' )

    zu = re.sub ( 'deg.*[E,east]' , '°E', zu)
    zu = re.sub ( 'deg.*[N,north]', '°N', zu)

    zu = zu.replace ('degree_celsius', '°C')
    zu = zu.replace ('degree_C2'     , '°C^{2}' )
    zu = zu.replace ('degree_C'      , '°C')
    zu = zu.replace ('deg'           , '°')

    # Multiplicator
    for nn in [1,2,3,4,5,6,7,8,9,20] :
        zu = zu.replace (f'10^(-{nn})', f'$10^{{-{nn}}}$')
        zu = zu.replace (f'10^-{nn}'  , f'$10^{{-{nn}}}$')
        zu = zu.replace (f'10^{nn}'   , f'$10^{{{nn}}}$' )
        zu = zu.replace (f'1e-{nn}'   , f'10^{{{-nn}}}$' )
        zu = zu.replace (f'1E-{nn}'   , f'10^{{{-nn}}}$' )
        zu = zu.replace (f'1e{nn}'    , f'10^{{{nn}}}$'  )
        zu = zu.replace (f'1E{nn}'    , f'10^{{{nn}}}$'  )

        zu = zu.replace (f'1.e-{nn}'  , f'10^{{{-nn}}}$' )
        zu = zu.replace (f'1.E-{nn}'  , f'10^{{{-nn}}}$' )
        zu = zu.replace (f'1.e{nn}'   , f'10^{{{nn}}}$' )
        zu = zu.replace (f'1.E{nn}'   , f'10^{{{nn}}}$' )

        zu = zu.replace ( 'Giga', '10^{9}' )
        zu = zu.replace ( 'Mega', '10^{6}' )
  
        zu = zu.replace ( 'mm/d'       , 'mm d$^{-1}$'         )
        zu = zu.replace ( 'J/m2'       , 'J m$^{-2}$'          )
        zu = zu.replace ( 'kg/(s*m2)'  , 'kg m$^{-2}$ s$^{-1}' )
        zu = zu.replace ( 'kg/m2/s'    , 'kg m$^{-2}$ s$^{-1}' )
        zu = zu.replace ( 'kg/m3'      , 'kg m$^{-3}$'         )  
        zu = zu.replace ( 'kg/s'       , 'kg s$^{-1}'          )
        zu = zu.replace ( 'm/s'        , 'm s$^{-1}$'          )
        zu = zu.replace ( 'W/m^2'      , 'W m$^{-2}$'          )
        
        zu = zu.replace ( 'm2'         , 'kg m$^3$'            )
        zu = zu.replace ( 'm3'         , 'kg m$^3$'            )

    # for zz in ['s', 'cm', 'mm', 'm', 'kgC', 'kg', 'N', 'ngN', 'Sv', 'gC', 'g', 'days', 'day', 'd',
    #            'yr', 'years', 'year', 'C', '°C', 'K', 'Pa', 'J', 'pft', 'PSU', 'PSS', 'psu', 'pss', 'W', 'PW' ] :

    #     if zz in zu : 
        
    #         if Debug or OPTIONS['Debug'] :
    #             print ( f"In : {zz=:5} -> {zu=:10}" )

    #             zu = zu.replace ( f'0.001*{zz}'  , f'10^{{-3}} {zz}' )
    #             zu = zu.replace ( f'0.01*{zz}'   , f'10^{{-2}} {zz}' )
    #             zu = zu.replace ( f'0.1*{zz}'    , f'10^{{-1}} {zz}' )
                
    #             zu = re.sub ( f'1/ *{zz}^3'      , f' {zz}^{{-3}}' , zu  )
    #             zu = re.sub ( f'1/ *{zz}^2'      , f' {zz}^{{-2}}' , zu  )
    #             zu = re.sub ( f'1/ *{zz}'        , f' {zz}^{{-1}}' , zu  )
                
    #             zu = zu.replace ( f'/{zz}3'      , f' {zz}$^{{-3}}$' )
    #             zu = zu.replace ( f'/{zz}2'      , f' {zz}$^{{-2}}$' )
    #             zu = zu.replace ( f'/{zz}'       , f' {zz}$^{{-1}}$' )
                
    #             zu = zu.replace ( f'{zz}^3'      , f' {zz}$^{{3}}$' )
    #             zu = zu.replace ( f'{zz}^2'      , f' {zz}$^{{2}}$' )

    #             # zu = zu.replace ( f'{zz}^{{3}}'  , f' {zz}$^{{3}}$' )
    #             # zu = zu.replace ( f'{zz}^{{2}}'  , f' {zz}$^{{2}}$' )

    #             # zu = zu.replace ( f'{zz}**-3'    , f' {zz}$^{-3}$' )
    #             # zu = zu.replace ( f'{zz}**-2'    , f' {zz}$^{-2}$' )
    #             # zu = zu.replace ( f'{zz}**-1'    , f' {zz}$^{-1}$' )

    #             # zu = zu.replace ( f'{zz}**3'     , f' {zz}$^{{3}}$' )
    #             # zu = zu.replace ( f'{zz}**2'     , f' {zz}$^{{2}}$' )

    #             # zu = zu.replace ( f'{zz}^-3'     , f' {zz}$^{{-3}}$' )
    #             # zu = zu.replace ( f'{zz}^-2'     , f' {zz}$^{{-2}}$' )
    #             # zu = zu.replace ( f'{zz}^-1'     , f' {zz}$^{{-1}}$' )
                
    #             # zu = zu.replace ( f'{zz}^{{-3}}' , f' {zz}$^{{-3}}$' )
    #             # zu = zu.replace ( f'{zz}^{{-2}}' , f' {zz}$^{{-2}}$' )
    #             # zu = zu.replace ( f'{zz}^{{-1}}' , f' {zz}$^{{-1}}$' )
                
    #             # zu = zu.replace ( f'{zz}3'       , f' {zz}$^{{3}}$' )
    #             # zu = zu.replace ( f'{zz}2'       , f' {zz}$^{{2}}$' )
                
    #             if Debug or OPTIONS['Debug'] :
    #                 print ( f"Out: {zz=:5} -> {zu=:10}" )
            
    # Simplifies

    zu = zu.replace ( f'0.001*'  , f'10^{{-3}}' )
    zu = zu.replace ( f'0.01*'   , f'10^{{-2}}' )
    zu = zu.replace ( f'0.0*'    , f'10^{{-1}}' )
    
    zu = zu.replace ( '$$' , '' )
    zu = zu.replace ( '$ $', '' )

    zu = zu.replace ( '( ', '(' )
    zu = zu.replace ( ' )', ')' )
    
    zu = re.sub ( '  *', ' ', zu)
    zu = zu.strip (' ')
    
    if Debug or OPTIONS['Debug'] :
        print ( f"{unit} -> {zu}" )

    return zu

def set_long_name (varName:str, long_name:str|None=None, Debug:bool=False) -> str :
    '''
    Return a full long_name of a Monitoring variable
    '''
    class RegexEqual (str) :
        def __eq__(self:Self, pattern:str) -> bool :
            return bool (re.search(pattern, self))
        
    match RegexEqual (varName) :
        case 'icevol_north'             : zname = 'Ice volume, northern hemisphere'
        case 'icevol_north_MAR'         : zname = 'Sea ice volume, northern hemisphere, March'
        case 'icevol_south'             : zname = 'Ice volume, southern hemisphere'
        case 'precip_global'            : zname = 'Global precipitation'
        case 'sosaline_north'           : zname = 'Salinity, northern hemisphere'
        case 't2m_global.*'             : zname = 'Global air surface temperature'

        case 'nadw_ocean.*'             : zname = 'AMOC index'
        case 'somxl010_Irminger'        : zname = 'MXL depth, Irminger sea'
        case 'somxl010_NordicSeas'      : zname = 'MXL depth, Nordic seas'
        case 'somxl010_Labrador'        : zname = 'MXL depth, Labrador sea'
        case 'sosaline_30N_50N'         : zname = 'Salinity, 30N-50N'
        case 'sosaline_50N_70N'         : zname = 'Salinity, 50N-70N'
        case 'sosaline_atl_30N_50N'     : zname = 'Salinity, Atlantic, 30N-50N'
        case 'sosaline_atl_50N_70N'     : zname = 'Salinity, Atlantic, 50N-70N'
        
        case _ :
            if long_name is not None :
                zname = long_name
            else :
                zname = varName

    if Debug or OPTIONS['Debug'] :
        print ( f"{varName=} : {zname=}")
                
    return zname

def get_comp (varName:str) -> Literal['OCE', 'ICE', 'ATM', 'SRF', 'SBG', 'CPL']|None :
    '''
    Return the component name of a monitoring variable
    '''
    match RegexEqual (varName) :

        case '.*10m.*'              : comp = 'ATM'
        case '.*nino.*'             : comp = 'ATM'
        case '^evap.*'              : comp = 'ATM'
        case '^fract_.*'            : comp = 'ATM'
        case 'lat_itcz.*'           : comp = 'ATM'
        case 'pourc_.*'             : comp = 'ATM'
        case 'precip.*'             : comp = 'ATM'
        case 'tsol.*'               : comp = 'ATM'
        case 't2m.*'                : comp = 'ATM'
        case 'net.*'                : comp = 'ATM'
        case 'top.*'                : comp = 'ATM'

        case 'aabw.*'               : comp = 'OCE'
        case 'deacon.*'             : comp = 'OCE'
        case 'friver.*'             : comp = 'OCE'
        case 'mld.*'                : comp = 'OCE'
        case 'nadw.*'               : comp = 'OCE'
        case 'npdw.*'               : comp = 'OCE'
        case '^so.*'                : comp = 'OCE'
        case 'sss.*'                : comp = 'OCE'
        case 'thetao.*'             : comp = 'OCE'
        case 'wfo.*'                : comp = 'OCE'
        case '^zos.*'               : comp = 'OCE'
        case '^hc.*'                : comp = 'OCE'
         
        case '^ii.*'                : comp = 'ICE'
        case '^si.*'                : comp = 'ICE'
        case '^ic.*'                : comp = 'ICE'

   
        case '.*harvest.*'          : comp='SBG'

        case 'delta_water_stock'    : comp='SRF'
        case 'water_budget_closure' : comp='SRF'
        case 'surface_.*'           : comp='SRF'
        case '.*_lands   '          : comp='SRF'
        case 'maxveget.*'           : comp='SRF'

        case _ : comp = None

    return comp
