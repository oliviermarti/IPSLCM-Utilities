# -*- coding: utf-8 -*-
'''
Utilities for LMDZ grid

- Lots of tests for xarray object
- Not much tested for numpy objects

Author: olivier.marti@lsce.ipsl.fr

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
personal.
'''

from typing import Literal, Union, Optional
import numpy as np
import xarray as xr
import cartopy
    
if cartopy.__version__ > '0.20' :
    import cartopy.util as cutil
else :
    import my_cyclic as cutil

from plotIGCM.options import OPTIONS, push_stack, pop_stack

lon_per = xr.DataArray (360.0    , name='lon_per', attrs={'units':"degrees_east"  , 'long_name':"Longitude range" })
RAAMO   = xr.DataArray (12       , name='RAAMO'  , attrs={'units':"month"  , 'long_name':"Number of months in one year" })
RJJHH   = xr.DataArray (24       , name='RJJHH'  , attrs={'units':"hour"   , 'long_name':"Number of hours in one day"} )
RHHMM   = xr.DataArray (60       , name='RHHMM'  , attrs={'units':"min"    , 'long_name':"Number of minutes in one hour"} )
RMMSS   = xr.DataArray (60       , name='RMMSS'  , attrs={'units':"second" , 'long_name':"Number of seconds in one minute"} )
RA      = xr.DataArray (6371229.0, name='RA'     , attrs={'units':"meter"  , 'long_name':"Earth radius"} )
GRAV    = xr.DataArray (9.80665  , name='GRAV'   , attrs={'units':"m/s2"   , 'long_name':"Gravity"} )
RT0     = xr.DataArray (273.15   , name='RT0'    , attrs={'units':"K"      , 'long_name':"Freezing point of fresh water"} )
RAU0    = xr.DataArray (1026.0   , name='RAU0'   , attrs={'units':"kg/m3"  , 'long_name':"Volumic mass of sea water"} )
SICE    = xr.DataArray (6.0      , name='SICE'   , attrs={'units':"psu"    , 'long_name':"Salinity of ice (for pisces)"} )
SOCE    = xr.DataArray (34.7     , name='SOCE'   , attrs={'units':"psu"    , 'long_name':"Salinity of sea (for pisces and isf)"} )
RLEVAP  = xr.DataArray (2.5e+6   , name='RLEVAP' , attrs={'units':"J/K"    , 'long_name':"Latent heat of evaporation (water)"} )
VKARMN  = xr.DataArray (0.4      , name='VKARMN' , attrs={                   'long_name':"Von Karman constant"} )
STEFAN  = xr.DataArray (5.67e-8  , name='STEFAN' , attrs={'units':"W/m2/K4", 'long_name':"Stefan-Boltzmann constant"} )

RDAY    = xr.DataArray (RJJHH*RHHMM*RMMSS           , name='RDAY'  , attrs={'units':"second", 'long_name':"Day length"})
RSIYEA  = xr.DataArray (365.25*RDAY*2*np.pi/6.283076, name='RSIYEA', attrs={'units':"second", 'long_name':"Sideral year length"})
RSIDAY  = xr.DataArray (RDAY/(1+RDAY/ RSIYEA)       , name='RSIDAY', attrs={'units':"second", 'long_name':"Sideral day length"})
ROMEGA  = xr.DataArray (2*np.pi/RSIDAY              , name='ROMEGA', attrs={'units':"s-1"   , 'long_name':"Earth rotation parameter"})

## Default names of dimensions                                                 
UDIMS:dict[str,str] = {'x':'lon', 'y':'lat', 'z':'presnivs', 't':'time_counter'}

## All possible names of dimensions in LMDZ files                              
XNAME:list[str] = [ 'x', 'X', 'lon', ]
YNAME:list[str] = [ 'y', 'Y', 'lat', ]
CNAME:list[str] = [ 'c', 'cell', ]
ZNAME:list[str] = [ 'z', 'Z', 'presnivs', ]
TNAME:list[str] = [ 't', 'T', 'tt', 'TT', 'time', 'time_counter', 'time_centered', 'TIME', 'TIME_COUNTER', 'TIME_CENTERED', ]
BNAME:list[str] = [ 'bnd', 'bnds', 'bound', 'bounds', 'vertex', 'nvertex', 'two', 'two1', 'two2', 'four' ]

## All possibles name of units of dimensions in LMDZ files                     
XUNIT:list[str] = [ 'degrees_east', ]
YUNIT:list[str] = [ 'degrees_north', ]
CUNIT:list[str] = [ 'cell', ]
ZUNIT:list[str] = [ 'Pa', 'm', 'meter']
TUNIT:list[str] = [ 'second', 'minute', 'hour', 'day', 'month', 'year', ]

## All possibles size of dimensions in LMDZ files                              
XLENGTH :list[int]  = [ 96, 144, 180, 360, ]
YLENGTH :list[int] = [ 95, 96, 143, 144, 180, 360, ]
XYLENGTH:list[list[int]] = [ [96,95], [144, 143], [180, 180], [360, 360]]
CLENGTH :list[int] = [ 16002, ]
ZLENGTH :list[int] = [ 39, 59, 79, ]


## ============================================================================

def __find_axis__ (ptab:xr.DataArray|xr.Dataset, axis:Literal['x', 'y', 'z', 't', 'b', 'c']='z', back:bool=True, Debug:bool=False) -> tuple[Optional[str], Optional[int]] :
    '''
    Returns name and name of the requested axis
    '''
    push_stack ( f'__find_axis__ ( ptab, {axis=} {back=} )' )

    ax        :Optional[str]       = None
    ix        :Optional[int]       = None
    ax_name   :Optional[list[str]] = None
    unit_list :Optional[list[str]] = None
    length    :Optional[list[int]] = None 
  
    if axis in XNAME :
        ax_name   = XNAME
        unit_list = XUNIT
        length    = XLENGTH
        if OPTIONS['Debug'] or Debug :
            print ( f'Working on xaxis found by name : {axis=} : {XNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in YNAME :
        ax_name, unit_list, length = YNAME, YUNIT, YLENGTH
        if OPTIONS['Debug'] or Debug :
            print ( f'Working on yaxis found by name : {axis=} : {YNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in CNAME :
        ax_name, unit_list, length = CNAME, CUNIT, CLENGTH
        if OPTIONS['Debug'] or Debug :
            print ( f'Working on caxis found by name : {axis=} : {CNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in ZNAME :
        ax_name, unit_list, length = ZNAME, ZUNIT, ZLENGTH
        if OPTIONS['Debug'] or Debug :
            print ( f'Working on zaxis found by name : {axis=} : {ZNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in TNAME :
        ax_name, unit_list, length = TNAME, TUNIT, None
        if OPTIONS['Debug'] or Debug :
            print ( f'Working on taxis found by name : {axis=} : {TNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in BNAME :
        ax_name, unit_list, length = BNAME, None, None
        if OPTIONS['Debug'] or Debug :
            print ( f'Working on taxis found by name : {axis=} : {BNAME=} {ax_name=} {unit_list=} {length=}' )

    # Try by name
    if ax_name is not None :
        for dim in ax_name :
            if dim in ptab.dims :
                if OPTIONS['Debug'] or Debug :
                    print ( f'Rule 2 : {ax_name=} axis found by unit : {axis=} : {XNAME=}' )
                ix=ptab.dims.index(dim) ;  ax=dim # type: ignore

    # If not found, try by 'axis' attribute
    if not ix :
        for ii, dim in enumerate (ptab.dims) :
            if 'axis' in ptab.coords[dim].attrs.keys() :
                l_axis = ptab.coords[dim].attrs['axis']
                if OPTIONS['Debug'] or Debug :
                    print ( f'Rule 3 : Trying {ii=} {dim=} {l_axis=}' )
                if l_axis in ax_name and l_axis == str('X') :
                        if OPTIONS['Debug'] or Debug :
                            print ( f'Rule 3 : xaxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                        ix=ii ; ax=str(dim)
                if l_axis in ax_name and l_axis == str('Y') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 3 : yaxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix=ii ; ax=str(dim)
                if l_axis in ax_name and l_axis == str('C') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 3 : caxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix=ii ; ax=str(dim)
                if l_axis in ax_name and l_axis == str('Z') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 3 : zaxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix=ii ; ax=str(dim)
                if l_axis in ax_name and l_axis == str('T') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 3 : taxis found by name : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix=ii ; ax=str(dim)

        # If not found, try by units
        if not ix and unit_list is not None :
            for ii, dim in enumerate (ptab.dims) :
                if 'units' in ptab.coords[dim].attrs.keys() :
                    for name in unit_list :
                        if name in ptab.coords[dim].attrs['units'] :
                            if OPTIONS['Debug'] or Debug :
                                print ( f'Rule 4 : axis found by unit {name} : {unit_list=} {ii=} {dim=}' )
                            ix=ii ; ax=str(dim)

    # If dimension not found, try by length
    if not ix :
        if length is not None :
            l_shape = ptab.shape
            for nn in range ( len(l_shape) ) :
                if l_shape[nn] in length :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 5 : axis found by length : {axis=} : {XNAME=} {nn=} {dim=}' )
                    ix = nn

    if ix and back :
        ix -= len(ptab.shape)

    pop_stack ( f'__find_axis__ ( {ax=} {ix=} )' )
    return ax, ix # type: ignore

def find_axis ( ptab:Union[xr.DataArray,xr.Dataset], axis:Literal['x', 'y', 'z', 't', 'b', 'c']='z', back:bool=True, Debug:bool=False ) -> tuple[Union[str,None], Union[int,None]] :
    '''
    Version of find_axis with no __'''
    push_stack ( f'find_axis__ ( ptab {axis=} {back=} )' )
    xx, ix = __find_axis__ (ptab, axis, back)
    pop_stack ( f'find_axis ( {xx=} {ix=} )' )
    return xx, ix

def get_shape ( ptab:xr.DataArray ) -> str :
    '''
    Get shape of ptab return a string with axes names

    shape may contain X, Y, C, Z or T
    Y is missing for a latitudinal slice
    X is missing for on longitudinal slice
    etc ...
    '''
    push_stack ( 'get_shape ( ptab) ' )

    g_shape = ''
    if __find_axis__ (ptab, 'x')[0] :
        g_shape = 'X'
    if __find_axis__ (ptab, 'y')[0] :
        g_shape = 'Y' + g_shape
    if __find_axis__ (ptab, 'c')[0] :
        g_shape = 'C' + g_shape
    if __find_axis__ (ptab, 'z')[0] :
        g_shape = 'Z' + g_shape
    if __find_axis__ (ptab, 't')[0] :
        g_shape = 'T' + g_shape

    push_stack ( f'get_shape : {g_shape=} ' )
    return g_shape

def extend (tab:xr.DataArray, Lon:bool=False, jplus:int=25, jpi:Union[int,None]=None, lonplus:Union[float,xr.DataArray]=lon_per, Debug:bool=False) -> xr.DataArray :
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
    if tab.shape[-1] == 1 :
        ztab = tab

    else :
        if jpi is None :
            jpi = tab.shape[-1]

        if Lon :
            xplus = lonplus
        else   :
            xplus = 0.0

        if tab.shape[-1] > jpi :
            ztab = tab
        else :
            istart = 0
            le     = jpi+1
            la     = 0
            lon = tab.dims[-1]
            ztab         = xr.concat      ((
                tab.isel (lon=slice(istart   ,istart+le      )),
                tab.isel (lon=slice(istart+la,istart+la+jplus))+xplus  ), dim=lon)
            if 'lon' in tab.dims :
                extend_lon = xr.concat      ((
                    tab.coords[lon].isel(lon=slice(istart   ,istart+le      )),
                    tab.coords[lon].isel(lon=slice(istart+la,istart+la+jplus))+lonplus), dim=lon)
                ztab = ztab.assign_coords ( {tab.dims[-1]:extend_lon} )

    pop_stack ( 'extend ' )
    return ztab

def interp1d (x:xr.DataArray, xp:xr.DataArray, yp:xr.DataArray, zdim:str='presnivs', units:Union[str,None]=None, method:str='linear', Debug:bool=False) -> xr.DataArray :
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

    # Get the number of levels in each arrays
    nk_ou = len (x)

    # Define the result array
    in_shape       = np.array (yp.shape)
    if OPTIONS['Debug'] or Debug :
        print ( f'{in_shape=}' )
    ou_shape       = np.array (in_shape)
    if OPTIONS['Debug'] or Debug :
        print ( f'{ou_shape=}' )
    ou_shape[axis] = nk_ou

    in_dims        = list (yp.dims)
    if OPTIONS['Debug'] or Debug :
        print ( f'{in_dims=}' )
    ou_dims        = in_dims

    pdim           = x.dims[0]
    ou_dims[axis]  = pdim

    if OPTIONS['Debug'] or Debug :
        print ( f'{pdim=}' )

    new_coords = []
    for i, dim in enumerate (yp.dims) :
        if dim == zdim :
            ou_dims[i] = x.dims[0]
            if units is not None :
                yp[dim].attrs['units'] = units
            if OPTIONS['Debug'] or Debug :
                print ( f'append new coord for {dim=} {x.shape=}' )
            new_coords.append (x             .values)
        else :
            if OPTIONS['Debug'] or Debug :
                print ( f'append coord for {dim=} {yp.coords[dim].shape=}' )
            new_coords.append (yp.coords[dim].values)

    #if OPTIONS['Debug'] or Debug :
    #    print ( f'{ou_dims   =}' )
    #    print ( f'{new_coords=}' )

    ou_tab = xr.DataArray (np.empty (ou_shape), dims=ou_dims, coords=new_coords)

    if OPTIONS['Debug'] or Debug :
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

    def __interp (x:xr.DataArray, xp:xr.DataArray, yp:xr.DataArray, pdim:str='presnivs', Debug:bool=Debug) -> xr.DataArray :
        # Interpolate
        # Find index of the just above level
        push_stack ( f'interp1d.__interp (x, xp, yp, {pdim=})' )

        #if OPTIONS['Debug'] or Debug :
        #    print ( f'{x.shape=} {x.dims=} {xp.shape=} {yp.shape=}' )
        #    print ( f'{pdim=}' )
        idk1 = np.minimum ((x-xp), 0.).argmax (dim=pdim) # type: ignore
        idk2 = idk1 - 1
        idk2 = np.maximum (idk2, 0)

        #if OPTIONS['Debug'] or Debug :
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
            if yp_min > 0. :
                result = np.power(y2, dx1) * np.power(y1, dx2)
            if yp_max < 0. :
                result = -np.power(-y2, dx1) * np.power(-y1, dx2)
        if 'nearest' in method :
            result = xr.where ( dx2>=dx1, y1, y2)

        pop_stack ( 'interp1d.__interp' )
        return result # type: ignore

    for k in range (nk_ou) :
        zlev = x[{pdim:k}]
        result = __interp  (zlev, xp, yp)

        # Put result in the final array
        ou_tab [{pdim:k}] = result

    pop_stack ( 'interp1d' )
    return ou_tab.squeeze()

def correct_uv (u:xr.DataArray, v:xr.DataArray, 
                lon:xr.DataArray, lat:xr.DataArray, Debug:bool=False) :
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
    push_stack ( 'correct_uv (u, v, lon, lat)' )
    
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

    pop_stack ( 'correct_uv' )
    return uc, vc

def fixed_lon (lon:xr.DataArray, center_lon:float=0.0, Debug:bool=False) -> xr.DataArray :
    '''Returns corrected longitudes for nicer plots

    lon        : longitudes of the grid. At least 1D.
    center_lon : center longitude. Default=0.

    Designed by Phil Pelson. See https://gist.github.com/pelson/79cf31ef324774c97ae7
    '''
    push_stack ( f'fixed_lon (lon {center_lon=})' )

    zfixed_lon = lon.copy ()

    zfixed_lon = xr.where (zfixed_lon > center_lon+180., zfixed_lon-lon_per, fixed_lon)
    zfixed_lon = xr.where (zfixed_lon < center_lon-180., zfixed_lon+lon_per, fixed_lon)

    start = np.argmax (np.abs (np.diff (zfixed_lon, axis=-1)) > 180., axis=-1)
    zfixed_lon [start+1:] += lon_per

    pop_stack ( 'fixed_lon' )
    return zfixed_lon

def nord2sud (p2d:xr.DataArray) -> xr.DataArray :
    '''
    Swap north to south a 2D field
    '''
    pop_stack ( 'nord2sud (p2d)' )
    z2d_inv = p2d[..., -1::-1, : ]
    pop_stack ( 'nord2sud' )
    return z2d_inv 

def unify_dims (dd:Union[xr.DataArray,xr.Dataset], x:str='x', y:str='y', z:str='olevel', t:str='time_counter', c:str='cell', Debug:bool=False ) -> Union[xr.DataArray,xr.Dataset] :
    '''
    Rename dimensions to unify them between LMDZ versions
    '''
    push_stack ( f'unify_dims ( dd, {x=}, {y=}, {z=}, {t=}, {c=} )' )

    for xx in XNAME :
        if xx in dd.dims and xx != x :
            if OPTIONS['Debug'] or Debug :
                print ( f"{xx} renamed to {x}" )
            dd = dd.rename ( {xx:x})

    for yy in YNAME :
        if yy in dd.dims and yy != y  :
            if OPTIONS['Debug'] or Debug :
                print ( f"{yy} renamed to {y}" )
            dd = dd.rename ( {yy:y} )

    for cc in CNAME :
        if cc in dd.dims and cc != c  :
            if OPTIONS['Debug'] or Debug :
                print ( f"{cc} renamed to {c}" )
            dd = dd.rename ( {cc:c} )

    for zz in ZNAME :
        if zz in dd.dims and zz != z :
            if OPTIONS['Debug'] or Debug :
                print ( f"{zz} renamed to {z}" )
            dd = dd.rename ( {zz:z} )

    for tt in TNAME  :
        if tt in dd.dims and tt != t :
            if OPTIONS['Debug'] or Debug :
                print ( f"{tt} renamed to {t}" )
            dd = dd.rename ( {tt:t} )

    pop_stack ( 'unify_dims' )
    return dd

def add_cyclic (ptab:xr.DataArray, x:xr.DataArray, y:xr.DataArray, axis:int=-1, 
                cyclic:float|xr.DataArray=lon_per, precision:float=0.0001, Debug:bool=False) -> tuple[xr.DataArray, xr.DataArray, xr.DataArray] :
    '''
    Add a cyclic point to an array and optionally corresponding x/longitude and y/latitude coordinates.
    
    Same as cartopy.util.add_cyclic, but returns xarray instead of numy arrays.

    Use cartopy.util.add_cyclic
    '''
    push_stack ( f'add_cyclic ({ptab.shape=} {axis=} {cyclic=} {precision=} )' )

    xx1=x
    yy1=y
    ztab, xx, yy = cutil.add_cyclic (data   = ptab, # type: ignore
                                     x      = xx1,
                                     y      = yy1,
                                     axis   = axis,
                                     cyclic = lon_per.item(),
                                     precision=0.0001)
    #xx = xr.DataArray (xx, dims=(y.dims[0], x.dims[0]), coords=(yy[:,0].squeeze(), xx[0,:].squeeze()) )
    #yy = xr.DataArray (yy, dims=(y.dims[0], x.dims[0]), coords=(yy[:,0].squeeze(), xx[0,:].squeeze()) )
    xx = xr.DataArray (xx, dims=(x.dims[0],), coords=(xx.squeeze(),) )
    yy = xr.DataArray (yy, dims=(y.dims[0],), coords=(yy.squeeze(),) )

    new_coords = []
    for i, dim in enumerate (ptab.dims) :
        if dim == ptab.dims[axis] :
            new_coords.append (xx)
        else                      :
            new_coords.append (ptab.coords[dim].values)

    ztab = xr.DataArray (ztab, dims=ptab.dims, coords=new_coords)

    pop_stack ( 'add_cyclic' )
    return ztab, xx, yy

def point2geo (p1d:xr.DataArray, lon:bool|str=False, lat:bool|str=False, jpi:int|None=None, jpj:int|None=None, 
               share_pole:bool=False, lon_name:str|None=None, lat_name:str|None=None, Debug:bool=False) -> xr.DataArray :
    '''
    From 1D [..., points_physiques] (restart type) to 2D [..., lat, lon]

    if jpi/jpj are not set, try to guess them from the number of points

    if lon/lat is True, add longitude/latitude values (regular grid), with name lon_name (or 'lon' if lon_name not defined)
    if lon/lat is a string, add longitude/latitude values (regular grid), with name lon/lat
    '''
    push_stack (f'point2geo (p1d, {lon=}, {lat=}, {jpi=}, {jpj=}, {share_pole=}, {lon_name=}, {lat_name=})')
    
    # Get the horizontal dimension
    jpn = p1d.shape[-1]
    # Get other dimension(s)
    form1 = list (p1d.shape [0:-1])

    if not jpi :
        jpi=0
    if not jpj :
        jpj=0

    # Check or compute 2D horizontal dimensions
    if jpi != 0 and jpj != 0 :
        if jpi*(jpj-2) + 2 != jpn :
            raise ValueError (f'{jpn=} {jpi=}, {jpj}, {jpi*(jpj-2)+2=} does match rule jpi·(jpj-2)+2==p1d.shape[-1]')
    if jpi==0 and jpj>0    :
        jpi = (jpn-2)//(jpj-2)
    if jpi>0  and jpj == 0 :
        jpj = (jpn-2)//jpi +2            
    if jpi==0 and jpi==0 :
        for [jj, ji] in [ [36,45], [72,96], [95,96], [96,96], [143,144], [144,144], [180,180] ] :
            if ji*(jj-2) + 2 == jpn :
                jpj = jj
                jpi = ji
        if jpi==0 and jpi==0 :
            raise ValueError (f'1D horizontal dimension {jpn=} not known. Cannot not guess horizontal dimensions jpj, jpi')
                
    form_all   = form1 + [jpj  , jpi]
    form_shape = form1 + [jpj-2, jpi]

    p2d = np.empty (form_all)
    p2d [..., 1:-1, :] = np.reshape (p1d [..., 1:-1], form_shape )
    if OPTIONS['Debug'] or Debug :
        print (f'{jpn=} {jpi=} {jpi=} {form1=} {form_all=} {form_shape=} {p2d.shape=}')

    if share_pole :
        p2d [...,  0 , :].flat = p1d [...,  0] / float (jpi) # type: ignore
        p2d [..., -1 , :].flat = p1d [..., -1] / float (jpi) # type: ignore
    else :
        p2d [...,  0 , :].flat = p1d [...,  0] # type: ignore
        p2d [..., -1 , :].flat = p1d [..., -1] # type: ignore
        
    # Adding metadata, coordinates, etc ...
    p2d = xr.DataArray (p2d)
    p2d.attrs.update ( p1d.attrs )
    for idim in range ( len(p1d.shape [0:-1]) ):
        dim = p1d.dims[idim]
        p2d = p2d.rename        ({p2d.dims[idim]:p1d.dims[idim]} )
        p2d = p2d.assign_coords ({p2d.dims[idim]:p1d.coords[dim]})

    if isinstance (lon, str) :
        if not lon_name :
            lon_name = lon
        zlon = np.linspace ( -180, 180, jpi, endpoint=False)
    if isinstance (lat, str) :
        if not lat_name :
            lat_name = lat
        zlat = np.linspace ( 90, -90, jpj, endpoint=True) 
    if isinstance (lon, bool) :
        if lon :
            if not lon_name :
                lon_name = 'lon'
            zlon = np.linspace ( -180, 180, jpi, endpoint=False)
    if isinstance (lat, bool) :
        if lat :
            if not lat_name :
                lat_name = 'lat'
            zlat = np.linspace ( 90, -90, jpj, endpoint=True)
    if OPTIONS['Debug'] or Debug :
        print ( f'{lon_name=} {type(zlon)=}' )

    if isinstance(zlon, np.ndarray) == np :
        if not lon_name :
            lon_name = 'lon'
        zlon = xr.DataArray ( zlon, dims=(lon_name,), coords=(zlon,) )
        for aa in { 'units':'degrees_east', 'long_name':'Longitude', 'standard_name':'longitude', 'axis':'X' }.items() :
            if aa[0] not in lon.attrs : # type: ignore
                zlon.attrs.update ( { aa[0]:aa[1] } )
    if isinstance (zlat, np.ndarray) :
        if not lat_name :
            lat_name = 'lat'
        zlat = xr.DataArray ( zlat, dims=(lat_name,), coords=(zlat,) )
        for aa in  { 'units':'degrees_north', 'long_name':'Latitude' , 'standard_name':'latitude' , 'axis':'Y' }.items () :
            if aa[0] not in lat.attrs : # type: ignore
                zlat.attrs.update ( { aa[0]:aa[1] } )
    if not isinstance (lat, xr.DataArray) :
        if not lat_name : 
            lat_name = lat.name if isinstance (zlat, xr.DataArray) else 'lat'
    if not isinstance (lon, xr.DataArray) :
        if not lon_name :
            lon_name = lon.name if isinstance (zlon, xr.DataArray) else 'lon'

    if not lon_name :
        lon_name = 'x'
    if not lat_name :
        lat_name = 'y'

    if OPTIONS['Debug'] or Debug :
        print ( f'{lon_name=}' )

    if lon_name != p2d.dims[-1] :
        p2d = p2d.rename ( {p2d.dims[-1]:lon_name} ) 
    if lat_name != p2d.dims[-2] :
        p2d = p2d.rename ( {p2d.dims[-2]:lat_name} )
    
    p2d = p2d.assign_coords ( {lon_name:zlon} )
    p2d[lon_name].attrs.update ( lon.attrs ) # type: ignore
    p2d = p2d.assign_coords ( {lat_name:zlat} )
    p2d[lon_name].attrs.update ( lat.attrs ) # type: ignore

    pop_stack ('point2geo')
    return p2d

def point3geo (p1d:xr.DataArray, lon:Union[bool,str]=False, lat:Union[bool,str]=False, lev:bool=False, jpi:Union[int,None]=None, jpj:Union[int,None]=None, jpk:Union[int,None]=None, 
               share_pole:bool=False, lon_name:Union[str,None]=None, lat_name:Union[str,None]=None, lev_name:Union[str,None]=None, Debug:Union[bool,None]=None) -> xr.DataArray :
    '''
    From 2D [..., horizon_vertical] (restart type) to 3D [..., lev, lat, lon]

    if jpi/jpj/jpk are not set, try to guess them from the number of points

    if lon/lat is True, add longitude/latitude values (regular grid), with name lon_name (or 'lon' if lon_name not defined)
    if lon/lat is a string, add longitude/latitude values (regular grid), with name lon/lat
    '''
    push_stack ( f'point3geo (p1d, {lon=}, {lat=}, {lev=}, {jpi=}, {jpj=}, {jpk=}, {share_pole=}, {lon_name=}, {lat_name=}, {lev_name=}) ' )

    # Get the horizontal dimension
    jpn = p1d.shape[-1]
    # Get other dimension(s)
    form1 = list (p1d.shape [0:-2])

    if not jpi :
        jpi=0
    if not jpj :
        jpj=0
    if not jpk :
        jpk=0
    
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
                if jk*(ji*(jj-2) + 2) == jpn :
                    ( jpk, jpj, jpk) = (jk, jj, ji)
        jpij = jpn / jpk
    else :
        jpij = jpn / jpk
        if jpi*jpj !=0 : 
            if jpk * ( jpi*(jpj-2) + 2 ) != jpn :
                raise ValueError (f'{jpn=}, {jpij=} {jpi=}, {jpj}, {jpk=}, {jpi*(jpj-2)+2=} does match rule jpi·(jpj-2)+2==p1d.shape[-1]')
        if jpi==0 and jpj>0    :
            jpi = (jpi*jpj-2)//(jpj-2)
        if jpi>0  and jpj == 0 :
            jpj = (jpi*jpj-2)//jpi +2            
        if jpi==0 and jpi==0 :
            for [jj, ji] in [ [36,45], [72,96], [95,96], [96,96], [143,144], [144,144], [180,180] ] :
                if ji*(jj-2) + 2 == jpi*jpj :
                    jpj = jj
                    jpi = ji

    form_2D = form1 + list ( (jpk, jpi*(jpj-2) + 2, ) )

    if OPTIONS['Debug'] or Debug :
        print ( f'{jpn=}, {jpij=} {jpi=}, {jpj=}, {jpk=}' )
        print ( f'{form1=}, {form_2D=}' )
    p2d = np.reshape ( p1d.values, form_2D )
        
    if OPTIONS['Debug'] or Debug :
        print ( f'{p2d.shape=}' )
    
    p2d = xr.DataArray (p2d)
    p2d.attrs.update ( p1d.attrs )
    for idim in range ( len(p1d.shape [0:-1]) ):
        dim = p1d.dims[idim]
        p2d = p2d.rename        ( {p2d.dims[idim]:p1d.dims[idim]}  )
        p2d = p2d.assign_coords ( {p2d.dims[idim]:p1d.coords[dim]} )
            
    p3d = point2geo (p2d, lon=lon, lat=lat, jpi=jpi, jpj=jpj, share_pole=share_pole, lon_name=lon_name, lat_name=lat_name )

    if lev_name != p3d.dims[-3] :
        p3d = p3d.rename ( {p3d.dims[-3]:lev_name} ) 
    p2d = p2d.assign_coords ( {lev_name:lev} )
    p2d[lon_name].attrs.update (lon.attrs) # type: ignore

    push_stack ( 'point3geo')
    return p3d

def geo2point (p2d:xr.DataArray, cumul_poles:bool=False, dim1d:str='points_physiques', Debug:bool=False ) -> xr.DataArray :
    '''
    From 2D [..., lat, lon] to 1D [..., points_phyiques]
    '''
    push_stack ( f'geo2point ( p2d, {cumul_poles=}, {dim1d=} )' )
    #
    # Get the horizontal dimensions
    (jpj, jpi) = p2d.shape[-2:]
    jpn = jpi*(jpj-2) + 2

    # Get other dimensions
    form1   = list(p2d.shape [0:-2]) 
    form_2D = form1 + [jpn,]
        
    p1d     = np.empty (form_2D)
    form_1D = form1 + [jpn-2,]
    
    p1d [..., 1:-1] = np.reshape ( p2d[..., 1:-1, :].values.ravel(), form_1D )
    if cumul_poles :
        p1d [...,  0] = np.sum ( p2d[...,  0, :], axis=-1 )
        p1d [..., -1] = np.sum ( p2d[..., -1, :], axis=-1 )
    else :
        p1d [...,  0  ] = p2d [...,  0, 0]
        p1d [..., -1  ] = p2d [..., -1, 0]

    # Adding metadata
    p1d = xr.DataArray (p1d)
    p1d.attrs.update ( p2d.attrs )
    if len(p2d.shape [0:-2]) > 0 : 
        for idim in range ( len(p2d.shape [0:-2]) ):
            dim=p2d.dims[idim]
            p1d = p1d.rename        ( {p1d.dims[idim]:p2d.dims[idim]}   )
            p1d = p1d.assign_coords ( {p1d.dims[idim] :p2d.coords[dim].values} )
    p1d = p1d.rename ( {p1d.dims[-1]:dim1d} )

    pop_stack ( 'geo2point' )
    return p1d

def geo2en (pxx:xr.DataArray, pyy:xr.DataArray, pzz:xr.DataArray, glam:xr.DataArray, gphi:xr.DataArray, Debug:bool=False) -> tuple[xr.DataArray, xr.DataArray] :
    '''
    Change vector from geocentric to east/north

    Inputs :
        pxx, pyy, pzz : components on the geocentric system
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( 'geo2en (pxx, pyy, pzz, glam, gphi)' )
    gsinlon = np.sin (np.deg2rad(glam))
    gcoslon = np.cos (np.deg2rad(glam))
    gsinlat = np.sin (np.deg2rad(gphi))
    gcoslat = np.cos (np.deg2rad(gphi))

    pte = - pxx * gsinlon            + pyy * gcoslon
    ptn = - pxx * gcoslon * gsinlat  - pyy * gsinlon * gsinlat + pzz * gcoslat

    pop_stack ( 'geo2en ')
    return pte, ptn

def en2geo (pte:xr.DataArray, ptn:xr.DataArray, glam:xr.DataArray, gphi:xr.DataArray, Debug:bool=False) -> tuple[xr.DataArray, xr.DataArray, xr.DataArray] :
    '''
    Change vector from east/north to geocentric

    Inputs :
        pte, ptn : eastward/northward components
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( 'en2geo (pte, ptn, glam, gphi)' )
    gsinlon = np.sin (np.deg2rad(glam))
    gcoslon = np.cos (np.deg2rad(glam))
    gsinlat = np.sin (np.deg2rad(gphi))
    gcoslat = np.cos (np.deg2rad(gphi))

    pxx = - pte * gsinlon - ptn * gcoslon * gsinlat
    pyy =   pte * gcoslon - ptn * gsinlon * gsinlat
    pzz =   ptn * gcoslat

    pop_stack ( 'geo2en')
    return pxx, pyy, pzz

def limit_blon (blon:xr.DataArray, clon:xr.DataArray, lon_cen:float=0, Debug:bool=False) -> tuple[xr.DataArray, xr.DataArray] :
    '''
    From mapper https://github.com/PBrockmann/VTK_Mapper
    needed to limit excursion from center of the cell to longitude boundaries
    '''
    push_stack (f'limit_blon (blon, clon, {lon_cen=})')
    lon_min = lon_cen-180.
    lon_max = lon_cen+180.
    
    clon  = (clon+lon_per*10.)%360
    clon  = xr.where (np.greater (clon, lon_max), clon-lon_per, clon)
    clon  = xr.where (np.less    (clon, lon_min), clon+lon_per, clon)
    clon1 = np.ones  (blon.shape, dtype=float) * clon[..., None]

    blon  = (blon+lon_per*10.)%360
    blon  = xr.where (np.greater(blon, lon_max), blon-lon_per, blon)
    blon  = xr.where (np.less   (blon, lon_min), blon+lon_per, blon)
    
    blon  = xr.where (np.greater(abs(blon-clon1), abs(blon+lon_per -clon1)), blon+lon_per, blon)
    blon  = xr.where (np.greater(abs(blon-clon1), abs(blon-lon_per -clon1)), blon-lon_per, blon)

    pop_stack ( 'limit_blon' )
    return blon, clon

def limit_lon (clon:xr.DataArray, lon_cen:float=0, Debug:bool=False) -> xr.DataArray :
    '''
    From mapper https://github.com/PBrockmann/VTK_Mapper
    needed to limit excursion from center of the cell to longitude boundaries
    '''
    push_stack ( f'limit_lon (clon, {lon_cen})' )
    lon_min = lon_cen-180.
    lon_max = lon_cen+180.
    
    clon  = (clon+lon_per*10.)%360
    clon  = xr.where (np.greater (clon, lon_max), clon-lon_per, clon)
    clon  = xr.where (np.less    (clon, lon_min), clon+lon_per,clon)
    
    return clon

def direction (uu:xr.DataArray, vv:xr.DataArray, unit:str='deg', Debug:bool=False) -> xr.DataArray :
    '''
    Compute direction of a vector (angle with north)
    '''
    zd = np.atan2 (uu,vv)
    if unit in ['deg', 'degree', 'degrees'] :
        zd = np.rad2deg(zd)
    return zd # type: ignore

## ===========================================================================
##                                                                            
##                               That's all folk's !!!                        
##                                                                            
## ===========================================================================
