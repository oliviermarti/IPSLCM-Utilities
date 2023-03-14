# -*- coding: utf-8 -*-
## ===========================================================================
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
## ===========================================================================
'''
Utilities to plot NEMO ORCA fields
Periodicity and other stuff

olivier.marti@lsce.ipsl.fr
'''

## SVN information
__Author__   = "$Author:  $"
__Date__     = "$Date: $"
__Revision__ = "$Revision:  $"
__Id__       = "$Id: $"
__HeadURL    = "$HeadURL: $"

import numpy as np
try    : import xarray as xr
except ImportError : pass

try    : import f90nml
except : pass

try : from sklearn.impute import SimpleImputer
except : pass

try    : import numba
except : pass

rpi = np.pi ; rad = np.deg2rad (1.0) ; dar = np.rad2deg (1.0)

nperio_valid_range = [0, 1, 4, 4.2, 5, 6, 6.2]

rday   = 24.*60.*60.     # Day length [s]
rsiyea = 365.25 * rday * 2. * rpi / 6.283076 # Sideral year length [s]
rsiday = rday / (1. + rday / rsiyea)
raamo  =  12.        # Number of months in one year
rjjhh  =  24.        # Number of hours in one day
rhhmm  =  60.        # Number of minutes in one hour
rmmss  =  60.        # Number of seconds in one minute
omega  = 2. * rpi / rsiday # Earth rotation parameter [s-1]
ra     = 6371229.    # Earth radius [m]
grav   = 9.80665     # Gravity [m/s2]
repsi  = np.finfo (1.0).eps

xList = [ 'x', 'X', 'lon'   , 'longitude' ]
yList = [ 'y', 'Y', 'lat'   , 'latitude'  ]
zList = [ 'z', 'Z', 'depth' , ]
tList = [ 't', 'T', 'time'  , ]

## ===========================================================================
def __mmath__ (tab, default=None) :
    mmath = default
    try    :
        if type (tab) == xr.core.dataarray.DataArray : mmath = xr
    except :
        pass

    try    :
        if type (tab) == np.ndarray : mmath = np
    except :
        pass
            
    return mmath


def __guessNperio__ (jpj, jpi, nperio=None, out='nperio') :
    '''
    Tries to guess the value of nperio (periodicity parameter. See NEMO documentation for details)
    
    Inputs
    jpj    : number of latitudes
    jpi    : number of longitudes
    nperio : periodicity parameter
    '''
    if nperio == None :
        nperio = __guessConfig__ (jpj, jpi, nperio=None, out='nperio')
    
    return nperio

def __guessConfig__ (jpj, jpi, nperio=None, config=None, out='nperio') :
    '''
    Tries to guess the value of nperio (periodicity parameter. See NEMO documentation for details)
    
    Inputs
    jpj    : number of latitudes
    jpi    : number of longitudes
    nperio : periodicity parameter
    '''
    if nperio == None :
        ## Values for NEMO version < 4.2
        if jpj ==  149 and jpi ==  182 :
            config = 'ORCA2.3'
            nperio = 4   # ORCA2. We choose legacy orca2.
            Iperio = 1 ; Jperio = 0 ; NFold = 1 ; NFtype = 'T'
        if jpj ==  332 and jpi ==  362 : # eORCA1.
            config = 'eORCA1.2'
            nperio = 6  
            Iperio = 1 ; Jperio = 0 ; NFold = 1 ; NFtype = 'F'
        if jpi == 1442 :  # ORCA025.
            config = 'ORCA025'
            nperio = 6 
            Iperio = 1 ; Jperio = 0 ; NFold = 1 ; NFtype = 'F'
        if jpj ==  294 : # ORCA1
            config = 'ORCA1'
            nperio = 6
            Iperio = 1 ; Jperio = 0 ; NFold = 1 ; NFtype = 'F'
            
        ## Values for NEMO version >= 4.2. No more halo points
        if jpj == 148 and jpi ==  180 :
            config = 'ORCA2.4'
            nperio = 4.2 # ORCA2. We choose legacy orca2.
            Iperio = 1 ; Jperio = 0 ; NFold = 1 ; NFtype = 'F'
        if jpj == 331  and jpi ==  360 : # eORCA1.
            config = 'eORCA1.4'
            nperio = 6.2
            Iperio = 1 ; Jperio = 0 ; NFold = 1 ; NFtype = 'F'
        if jpi == 1440 : # ORCA025.
            config = 'ORCA025'
            nperio = 6.2
            Iperio = 1 ; Jperio = 0 ; NFold = 1 ; NFtype = 'F'
            
        if nperio == None :
            raise Exception  ('in nemo module : nperio not found, and cannot by guessed')
        else :
            if nperio in nperio_valid_range :
                print ('nperio set as {:} (deduced from jpj={:d} jpi={:d})'.format (nperio, jpj, jpi))
            else : 
                raise ValueError ('nperio set as {:} (deduced from jpi={:d}) : nemo.py is not ready for this value'.format (nperio, jpi))

    if out == 'nperio' : return nperio
    if out == 'config' : return config
    if out == 'perio'  : return Iperio, Jperio, NFold, NFtype
    if out in ['full', 'all'] : return {'nperio':nperio, 'Iperio':Iperio, 'Jperio':Jperio, 'NFold':NFold, 'NFtype':NFtype}
        
def __guessPoint__ (ptab) :
    '''
    Tries to guess the grid point (periodicity parameter. See NEMO documentation for details)
    
    For array conforments with xgcm requirements

    Inputs
         ptab : xarray array

    Credits : who is the original author ?
    '''
    gP = None
    mmath = __mmath__ (ptab)
    if mmath == xr :
        if 'x_c' in ptab.dims and 'y_c' in ptab.dims                        : gP = 'T'
        if 'x_f' in ptab.dims and 'y_c' in ptab.dims                        : gP = 'U'
        if 'x_c' in ptab.dims and 'y_f' in ptab.dims                        : gP = 'V'
        if 'x_f' in ptab.dims and 'y_f' in ptab.dims                        : gP = 'F'
        if 'x_c' in ptab.dims and 'y_c' in ptab.dims and 'z_c' in ptab.dims : gP = 'T'
        if 'x_c' in ptab.dims and 'y_c' in ptab.dims and 'z_f' in ptab.dims : gP = 'W'
        if 'x_f' in ptab.dims and 'y_c' in ptab.dims and 'z_f' in ptab.dims : gP = 'U'
        if 'x_c' in ptab.dims and 'y_f' in ptab.dims and 'z_f' in ptab.dims : gP = 'V'
        if 'x_f' in ptab.dims and 'y_f' in ptab.dims and 'z_f' in ptab.dims : gP = 'F'
             
        if gP == None :
            raise Exception ('in nemo module : cd_type not found, and cannot by guessed')
        else :
            print ('Grid set as', gP, 'deduced from dims ', ptab.dims)
            return gP
    else :
         raise Exception  ('in nemo module : cd_type not found, input is not an xarray data')

def lbc_diag (nperio) :
    lperio = nperio ; aperio = False
    if nperio == 4.2 :
        lperio = 4 ; aperio = True
    if nperio == 6.2 :
        lperio = 6 ; aperio = True
        
    return lperio, aperio 

def __findAxis__ (tab, axis='z') :
    '''
    Find number and name of the requested axis
    '''
    mmath = __mmath__ (tab)
    ix = None ; ax = None

    if axis in xList :
        axList = [ 'x', 'X',
                   'lon', 'nav_lon', 'nav_lon_T', 'nav_lon_U', 'nav_lon_V', 'nav_lon_F', 'nav_lon_W',
                   'x_grid_T', 'x_grid_U', 'x_grid_V', 'x_grid_F', 'x_grid_W',
                   'glam', 'glamt', 'glamu', 'glamv', 'glamf', 'glamw' ]
        unList = [ 'degrees_east' ]
    if axis in yList :
        axList = [ 'y', 'Y', 'lat',
                   'nav_lat', 'nav_lat_T', 'nav_lat_U', 'nav_lat_V', 'nav_lat_F', 'nav_lat_W',
                   'y_grid_T', 'y_grid_U', 'y_grid_V', 'y_grid_F', 'y_grid_W',
                   'gphi', 'gphi', 'gphiu', 'gphiv', 'gphif', 'gphiw']
        unList = [ 'degrees_north' ]
    if axis in zList :
        axList = [ 'z', 'Z',
                   'depth', 'deptht', 'depthu', 'depthv', 'depthf', 'depthw',
                   'olevel' ]
        unList = [ 'm', 'meter' ]
    if axis in tList :
        axList = [ 't', 'T', 'time', 'time_counter' ]
        unList = [ 'second', 'minute', 'hour', 'day', 'month' ]
    
    if mmath == xr :
        for Name in axList :
            try    :
                ix = tab.dims.index (Name)
                ax = Name
            except : pass

        for i, dim in enumerate (tab.dims) :
            if 'units' in tab.coords[dim].attrs.keys() :
                for name in unList :
                    if name in tab.coords[dim].attrs['units'] :
                        ix = i
                        ax = dim
    else :
        if axis in xList : ix=-1
        if axis in yList :
            if len(tab.shape) >= 2 : ix=-2
        if axis in zList :
            if len(tab.shape) >= 3 : ix=-3
        if axis in tList :
            if len(tab.shape) >=3  : ix=-3
            if len(tab.shape) >=4  : ix=-4
       
    return ix, ax

#@numba.jit(forceobj=True)
def fixed_lon (lon, center_lon=0.0) :
    '''
    Returns corrected longitudes for nicer plots

    lon        : longitudes of the grid. At least 2D.
    center_lon : center longitude. Default=0.

    Designed by Phil Pelson. See https://gist.github.com/pelson/79cf31ef324774c97ae7
    '''
    mmath = __mmath__ (lon)
    
    fixed_lon = lon.copy ()
        
    fixed_lon = mmath.where (fixed_lon > center_lon+180., fixed_lon-360.0, fixed_lon)
    fixed_lon = mmath.where (fixed_lon < center_lon-180., fixed_lon+360.0, fixed_lon)
    
    for i, start in enumerate (np.argmax (np.abs (np.diff (fixed_lon, axis=-1)) > 180., axis=-1)) :
        fixed_lon [..., i, start+1:] += 360.

    # Special case for eORCA025
    if fixed_lon.shape [-1] == 1442 : fixed_lon [..., -2, :] = fixed_lon [..., -3, :]
    if fixed_lon.shape [-1] == 1440 : fixed_lon [..., -1, :] = fixed_lon [..., -2, :]

    if fixed_lon.min () > center_lon : fixed_lon += -360.0
    if fixed_lon.max () < center_lon : fixed_lon +=  360.0
        
    if fixed_lon.min () < center_lon-360.0 : fixed_lon +=  360.0
    if fixed_lon.max () > center_lon+360.0 : fixed_lon += -360.0
                
    return fixed_lon

#@numba.jit(forceobj=True)
def fill_empty (ztab, sval=np.nan, transpose=False) :
    '''
    Fill values

    Useful when NEMO has run with no wet points options : 
    some parts of the domain, with no ocean points, has no
    lon/lat values
    '''
    mmath = __mmath__ (ztab)

    imp = SimpleImputer (missing_values=sval, strategy='mean')
    if transpose :
        imp.fit (ztab.T)
        ptab = imp.transform (ztab.T).T
    else : 
        imp.fit (ztab)
        ptab = imp.transform (ztab)
   
    if mmath == xr :
        ptab = xr.DataArray (ptab, dims=ztab.dims, coords=ztab.coords)
        ptab.attrs = ztab.attrs
        
    return ptab

#@numba.jit(forceobj=True)
def fill_lonlat (lon, lat, sval=-1) :
    '''
    Fill longitude/latitude values

    Useful when NEMO has run with no wet points options : 
    some parts of the domain, with no ocean points, as no
    lon/lat values
    '''
    mmath = __mmath__ (lon)

    imp = SimpleImputer (missing_values=sval, strategy='mean')
    imp.fit (lon)
    plon = imp.transform (lon)
    imp.fit (lat.T)
    plat = imp.transform (lat.T).T

    if mmath == xr :
        plon = xr.DataArray (plon, dims=lon.dims, coords=lon.coords)
        plat = xr.DataArray (plat, dims=lat.dims, coords=lat.coords)
        plon.attrs = lon.attrs ; plat.attrs = lat.attrs
        
    plon = fixed_lon (plon)
    
    return plon, plat

#@numba.jit(forceobj=True)
def jeq (lat) :
    '''
    Returns j index of equator in the grid
    
    lat : latitudes of the grid. At least 2D.
    '''
    mmath = __mmath__ (lat)
    ix, ax = __findAxis__ (lat, 'x')
    iy, ay = __findAxis__ (lat, 'y')

    if mmath == xr :
        jeq = int ( np.mean ( np.argmin (np.abs (np.float64 (lat)), axis=iy) ) )
    else : 
        jeq = np.argmin (np.abs (np.float64 (lat[...,:, 0])))
    return jeq

#@numba.jit(forceobj=True)
def lon1D (lon, lat=None) :
    '''
    Returns 1D longitude for simple plots.
    
    lon : longitudes of the grid
    lat (optionnal) : latitudes of the grid
    '''
    mmath = __mmath__ (lon)
    jpj, jpi  = lon.shape [-2:]
    if np.max (lat) != None :
        je    = jeq (lat)
        #lon1D = lon.copy() [..., je, :]
        lon0 = lon [..., je, 0].copy()
        dlon = lon [..., je, 1].copy() - lon [..., je, 0].copy()
        lon1D = np.linspace ( start=lon0, stop=lon0+360.+2*dlon, num=jpi )
    else :
        lon0 = lon [..., jpj//3, 0].copy()
        dlon = lon [..., jpj//3, 1].copy() - lon [..., jpj//3, 0].copy()
        lon1D = np.linspace ( start=lon0, stop=lon0+360.+2*dlon, num=jpi )

    #start = np.argmax (np.abs (np.diff (lon1D, axis=-1)) > 180.0, axis=-1)
    #lon1D [..., start+1:] += 360

    if mmath == xr :
        lon1D = xr.DataArray( lon1D, dims=('lon',), coords=(lon1D,))
        lon1D.attrs = lon.attrs
        lon1D.attrs['units']         = 'degrees_east'
        lon1D.attrs['standard_name'] = 'longitude'
        lon1D.attrs['long_name :']   = 'Longitude'
        
    return lon1D

#@numba.jit(forceobj=True)
def latreg (lat, diff=0.1) :
    '''
    Returns maximum j index where gridlines are along latitudes in the northern hemisphere
    
    lat : latitudes of the grid (2D)
    diff [optional] : tolerance
    '''
    mmath = __mmath__ (lat)
    if diff == None :
        dy   = np.float64 (np.mean (np.abs (lat - np.roll (lat,shift=1,axis=-2, roll_coords=False))))
        diff = dy/100.
    
    je     = jeq (lat)
    jreg   = np.where (lat[...,je:,:].max(axis=-1) - lat[...,je:,:].min(axis=-1)< diff)[-1][-1] + je
    latreg = np.float64 (lat[...,jreg,:].mean(axis=-1))
    JREG   = jreg

    return jreg, latreg

#@numba.jit(forceobj=True)
def lat1D (lat) :
    '''
    Returns 1D latitudes for zonal means and simple plots.

    lat : latitudes of the grid (2D)
    '''
    mmath = __mmath__ (lat)
    jpj, jpi = lat.shape[-2:]

    dy     = np.float64 (np.mean (np.abs (lat - np.roll (lat, shift=1,axis=-2))))
    je     = jeq (lat)
    lat_eq = np.float64 (lat[...,je,:].mean(axis=-1))
      
    jreg, lat_reg = latreg (lat)
    lat_ave = np.mean (lat, axis=-1)

    if (np.abs (lat_eq) < dy/100.) : # T, U or W grid
        dys    = (90.-lat_reg) / (jpj-jreg-1)*0.5
        yrange = 90.-dys-lat_reg
    else                           :  # V or F grid
        yrange = 90.    -lat_reg
        
    lat1D = mmath.where (lat_ave<lat_reg, lat_ave, lat_reg + yrange * (np.arange(jpj)-jreg)/(jpj-jreg-1))   
        
    if mmath == xr :
        lat1D = xr.DataArray( lat1D.values, dims=('lat',), coords=(lat1D,))
        lat1D.attrs = lat.attrs
        lat1D.attrs['units']         = 'degrees_north'
        lat1D.attrs['standard_name'] = 'latitude'
        lat1D.attrs['long_name :']   = 'Latitude'
    return lat1D

#@numba.jit(forceobj=True)
def latlon1D (lat, lon) :
    '''
    Returns simple latitude and longitude (1D) for simple plots.

    lat, lon : latitudes and longitudes of the grid (2D)
    '''
    return lat1D (lat),  lon1D (lon, lat)

##@numba.jit(forceobj=True)
def mask_lonlat (ptab, x0, x1, y0, y1, lon, lat, sval=np.nan) :
    mmath = __mmath__ (ptab)
    try :
        lon = lon.copy().to_masked_array()
        lat = lat.copy().to_masked_array()
    except : pass
            
    mask = np.logical_and (np.logical_and(lat>y0, lat<y1), 
            np.logical_or (np.logical_or (np.logical_and(lon>x0, lon<x1), np.logical_and(lon+360>x0, lon+360<x1)),
                                      np.logical_and(lon-360>x0, lon-360<x1)))
    tab = mmath.where (mask, ptab, np.nan)
    
    return tab

#@numba.jit(forceobj=True)      
def extend (tab, Lon=False, jplus=25, jpi=None, nperio=4) :
    '''
    Returns extended field eastward to have better plots, and box average crossing the boundary
    Works only for xarray and numpy data (?)

    tab : field to extend.
    Lon : (optional, default=False) : if True, add 360 in the extended parts of the field
    jpi : normal longitude dimension of the field. exrtend does nothing it the actual
        size of the field != jpi (avoid to extend several times)
    jplus (optional, default=25) : number of points added on the east side of the field
    
    '''
    mmath = __mmath__ (tab)
    
    if tab.shape[-1] == 1 : extend = tab

    else :
        if jpi == None : jpi = tab.shape[-1]

        if Lon : xplus = -360.0
        else   : xplus =    0.0

        if tab.shape[-1] > jpi :
            extend = tab
        else :
            if nperio == 0 or nperio == 4.2 :
                istart = 0 ; le=jpi+1 ; la=0
            if nperio == 1 :
                istart = 0 ; le=jpi+1 ; la=0
            if nperio == 4 or nperio == 6 : # OPA case with two halo points for periodicity
                istart = 1 ; le=jpi-2 ; la=1  # Perfect, except at the pole that should be masked by lbc_plot
           
            if mmath == xr :
                extend = np.concatenate ((tab.values[..., istart   :istart+le+1    ] + xplus,
                                          tab.values[..., istart+la:istart+la+jplus]         ), axis=-1)
                lon    = tab.dims[-1]
                new_coords = []
                for coord in tab.dims :
                    if coord == lon : new_coords.append ( np.arange( extend.shape[-1]))
                    else            : new_coords.append ( tab.coords[coord].values)
                extend = xr.DataArray ( extend, dims=tab.dims, coords=new_coords )
            else : 
                extend = np.concatenate ((tab [..., istart   :istart+le+1    ] + xplus,
                                          tab [..., istart+la:istart+la+jplus]          ), axis=-1)
    return extend

def orca2reg (ff, lat_name='nav_lat', lon_name='nav_lon', y_name='y', x_name='x') :
    '''
    Assign an ORCA dataset on a regular grid.
    For use in the tropical region.
    
    Inputs : 
      ff : xarray dataset
      lat_name, lon_name : name of latitude and longitude 2D field in ff
      y_name, x_name     : namex of dimensions in ff
      
      Returns : xarray dataset with rectangular grid. Incorrect above 20°N
    '''
    # Compute 1D longitude and latitude
    (lat, lon) = latlon1D (ff[lat_name], ff[lon_name])

    # Assign lon and lat as dimensions of the dataset
    if y_name in ff.dims : 
        lat = xr.DataArray (lat, coords=[lat,], dims=['lat',])     
        ff  = ff.rename_dims ({y_name: "lat",}).assign_coords (lat=lat)
    if x_name in ff.dims :
        lon = xr.DataArray (lon, coords=[lon,], dims=['lon',])
        ff  = ff.rename_dims ({x_name: "lon",}).assign_coords (lon=lon)
    # Force dimensions to be in the right order
    coord_order = ['lat', 'lon']
    for dim in [ 'depthw', 'depthv', 'depthu', 'deptht', 'depth', 'z',
                 'time_counter', 'time', 'tbnds', 
                 'bnds', 'axis_nbounds', 'two2', 'two1', 'two', 'four',] :
        if dim in ff.dims : coord_order.insert (0, dim)
        
    ff = ff.transpose (*coord_order)
    return ff

def lbc_init (ptab, nperio=None) :
    '''
    Prepare for all lbc calls
    
    Set periodicity on input field
    nperio    : Type of periodicity
      0       : No periodicity
      1, 4, 6 : Cyclic on i dimension (generaly longitudes) with 2 points halo
      2       : Obsolete (was symmetric condition at southern boundary ?)
      3, 4    : North fold T-point pivot (legacy ORCA2)
      5, 6    : North fold F-point pivot (ORCA1, ORCA025, ORCA2 with new grid for paleo)
    cd_type   : Grid specification : T, U, V or F

    See NEMO documentation for further details
    '''
    jpj, jpi = ptab.shape[-2:]
    if nperio == None : nperio = __guessNperio__ (jpj, jpi, nperio)
    
    if nperio not in nperio_valid_range :
        raise Exception ('nperio=', nperio, ' is not in the valid range', nperio_valid_range)

    return jpj, jpi, nperio
        
#@numba.jit(forceobj=True)
def lbc (ptab, nperio=None, cd_type='T', psgn=1.0, nemo_4U_bug=False) :
    '''
    Set periodicity on input field
    ptab      : Input array (works for rank 2 at least : ptab[...., lat, lon])
    nperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F
    psgn      : For change of sign for vector components (1 for scalars, -1 for vector components)
    
    See NEMO documentation for further details
    '''
    jpj, jpi, nperio = lbc_init (ptab, nperio)
    psgn   = ptab.dtype.type (psgn)
    mmath = __mmath__ (ptab)
    
    if mmath == xr : ztab = ptab.values.copy ()
    else           : ztab = ptab.copy ()
        
    #
    #> East-West boundary conditions
    # ------------------------------
    if nperio in [1, 4, 6] :
        # ... cyclic
        ztab [..., :,  0] = ztab [..., :, -2]
        ztab [..., :, -1] = ztab [..., :,  1]
    #
    #> North-South boundary conditions
    # --------------------------------
    if nperio in [3, 4] :  # North fold T-point pivot
        if cd_type in [ 'T', 'W' ] : # T-, W-point
            ztab [..., -1, 1:       ] = psgn * ztab [..., -3, -1:0:-1      ]
            ztab [..., -1, 0        ] = psgn * ztab [..., -3, 2            ]
            ztab [..., -2, jpi//2:  ] = psgn * ztab [..., -2, jpi//2:0:-1  ]
                
        if cd_type == 'U' :
            ztab [..., -1, 0:-1     ] = psgn * ztab [..., -3, -1:0:-1      ]       
            ztab [..., -1,  0       ] = psgn * ztab [..., -3,  1           ]
            ztab [..., -1, -1       ] = psgn * ztab [..., -3, -2           ]
                
            if nemo_4U_bug :
                ztab [..., -2, jpi//2+1:-1] = psgn * ztab [..., -2, jpi//2-2:0:-1]
                ztab [..., -2, jpi//2-1   ] = psgn * ztab [..., -2, jpi//2       ]
            else :
                ztab [..., -2, jpi//2-1:-1] = psgn * ztab [..., -2, jpi//2:0:-1]
                
        if cd_type == 'V' : 
            ztab [..., -2, 1:       ] = psgn * ztab [..., -3, jpi-1:0:-1   ]
            ztab [..., -1, 1:       ] = psgn * ztab [..., -4, -1:0:-1      ]   
            ztab [..., -1, 0        ] = psgn * ztab [..., -4, 2            ]
                
        if cd_type == 'F' :
            ztab [..., -2, 0:-1     ] = psgn * ztab [..., -3, -1:0:-1      ]
            ztab [..., -1, 0:-1     ] = psgn * ztab [..., -4, -1:0:-1      ]
            ztab [..., -1,  0       ] = psgn * ztab [..., -4,  1           ]
            ztab [..., -1, -1       ] = psgn * ztab [..., -4, -2           ]

    if nperio in [4.2] :  # North fold T-point pivot
        if cd_type in [ 'T', 'W' ] : # T-, W-point
            ztab [..., -1, jpi//2:  ] = psgn * ztab [..., -1, jpi//2:0:-1  ]
                
        if cd_type == 'U' :
            ztab [..., -1, jpi//2-1:-1] = psgn * ztab [..., -1, jpi//2:0:-1]
                
        if cd_type == 'V' : 
            ztab [..., -1, 1:       ] = psgn * ztab [..., -2, jpi-1:0:-1   ]
                
        if cd_type == 'F' :
            ztab [..., -1, 0:-1     ] = psgn * ztab [..., -2, -1:0:-1      ]

    if nperio in [5, 6] :            #  North fold F-point pivot  
        if cd_type in ['T', 'W']  :
            ztab [..., -1, 0:       ] = psgn * ztab [..., -2, -1::-1       ]
                
        if cd_type == 'U' :
            ztab [..., -1, 0:-1     ] = psgn * ztab [..., -2, -2::-1       ]       
            ztab [..., -1, -1       ] = psgn * ztab [..., -2, 0            ] # Bug ?
                
        if cd_type == 'V' :
            ztab [..., -1, 0:       ] = psgn * ztab [..., -3, -1::-1       ]
            ztab [..., -2, jpi//2:  ] = psgn * ztab [..., -2, jpi//2-1::-1 ]
                
        if cd_type == 'F' :
            ztab [..., -1, 0:-1     ] = psgn * ztab [..., -3, -2::-1       ]
            ztab [..., -1, -1       ] = psgn * ztab [..., -3, 0            ]
            ztab [..., -2, jpi//2:-1] = psgn * ztab [..., -2, jpi//2-2::-1 ]

    #
    #> East-West boundary conditions
    # ------------------------------
    if nperio in [1, 4, 6] :
        # ... cyclic
        ztab [..., :,  0] = ztab [..., :, -2]
        ztab [..., :, -1] = ztab [..., :,  1]

    if mmath == xr :
        ztab = xr.DataArray ( ztab, dims=ptab.dims, coords=ptab.coords)
        ztab.attrs = ptab.attrs
        
    return ztab

#@numba.jit(forceobj=True)
def lbc_mask (ptab, nperio=None, cd_type='T', sval=np.nan) :
    #
    '''
    Mask fields on duplicated points
    ptab      : Input array. Rank 2 at least : ptab [...., lat, lon]
    nperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F
    
    See NEMO documentation for further details
    '''
    jpj, jpi, nperio = lbc_init (ptab, nperio)
    ztab = ptab.copy ()

    #
    #> East-West boundary conditions
    # ------------------------------
    if nperio in [1, 4, 6] :
        # ... cyclic
        ztab [..., :,  0] = sval
        ztab [..., :, -1] = sval

    #
    #> South (in which nperio cases ?)
    # --------------------------------
    if nperio in [1, 3, 4, 5, 6] :
        ztab [..., 0, :] = sval
        
    #
    #> North-South boundary conditions
    # --------------------------------
    if nperio in [3, 4] :  # North fold T-point pivot
        if cd_type in [ 'T', 'W' ] : # T-, W-point
            ztab [..., -1,  :         ] = sval
            ztab [..., -2, :jpi//2  ] = sval
                
        if cd_type == 'U' :
            ztab [..., -1,  :         ] = sval  
            ztab [..., -2, jpi//2+1:  ] = sval
                
        if cd_type == 'V' :
            ztab [..., -2, :       ] = sval
            ztab [..., -1, :       ] = sval   
                
        if cd_type == 'F' :
            ztab [..., -2, :       ] = sval
            ztab [..., -1, :       ] = sval

    if nperio in [4.2] :  # North fold T-point pivot
        if cd_type in [ 'T', 'W' ] : # T-, W-point
            ztab [..., -1, jpi//2  :  ] = sval
                
        if cd_type == 'U' :
            ztab [..., -1, jpi//2-1:-1] = sval
                
        if cd_type == 'V' : 
            ztab [..., -1, 1:       ] = sval
                
        if cd_type == 'F' :
            ztab [..., -1, 0:-1     ] = sval
    
    if nperio in [5, 6] :            #  North fold F-point pivot
        if cd_type in ['T', 'W']  :
            ztab [..., -1, 0:       ] = sval
                
        if cd_type == 'U' :
            ztab [..., -1, 0:-1     ] = sval       
            ztab [..., -1, -1       ] = sval
             
        if cd_type == 'V' :
            ztab [..., -1, 0:       ] = sval
            ztab [..., -2, jpi//2:  ] = sval
                             
        if cd_type == 'F' :
            ztab [..., -1, 0:-1       ] = sval
            ztab [..., -1, -1         ] = sval
            ztab [..., -2, jpi//2+1:-1] = sval

    return ztab

#@numba.jit(forceobj=True)
def lbc_plot (ptab, nperio=None, cd_type='T', psgn=1.0, sval=np.nan) :
    '''
    Set periodicity on input field, adapted for plotting for any cartopy projection
    ptab      : Input array. Rank 2 at least : ptab[...., lat, lon]
    nperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F
    psgn      : For change of sign for vector components (1 for scalars, -1 for vector components)
    
    See NEMO documentation for further details
    '''

    jpj, jpi, nperio = lbc_init (ptab, nperio)
    psgn   = ptab.dtype.type (psgn)
    ztab   = ptab.copy ()
    #
    #> East-West boundary conditions
    # ------------------------------
    if nperio in [1, 4, 6] :
        # ... cyclic
        ztab [..., :,  0] = ztab [..., :, -2]
        ztab [..., :, -1] = ztab [..., :,  1]

    #> Masks south
    # ------------
    if nperio in [4, 6] : ztab [..., 0, : ] = sval
        
    #
    #> North-South boundary conditions
    # --------------------------------
    if nperio in [3, 4] :  # North fold T-point pivot
        if cd_type in [ 'T', 'W' ] : # T-, W-point
            ztab [..., -1,  :      ] = sval
            #ztab [..., -2, jpi//2: ] = sval
            ztab [..., -2, :jpi//2 ] = sval # Give better plots than above
        if cd_type == 'U' :
            ztab [..., -1, : ] = sval

        if cd_type == 'V' : 
            ztab [..., -2, : ] = sval
            ztab [..., -1, : ] = sval
            
        if cd_type == 'F' :
            ztab [..., -2, : ] = sval
            ztab [..., -1, : ] = sval

    if nperio in [4.2] :  # North fold T-point pivot
        if cd_type in [ 'T', 'W' ] : # T-, W-point
            ztab [..., -1, jpi//2:  ] = sval
                
        if cd_type == 'U' :
            ztab [..., -1, jpi//2-1:-1] = sval
                
        if cd_type == 'V' : 
            ztab [..., -1, 1:       ] = sval
                
        if cd_type == 'F' :
            ztab [..., -1, 0:-1     ] = sval
      
    if nperio in [5, 6] :            #  North fold F-point pivot  
        if cd_type in ['T', 'W']  :
            ztab [..., -1, : ] = sval
                
        if cd_type == 'U' :
            ztab [..., -1, : ] = sval      
             
        if cd_type == 'V' :
            ztab [..., -1, :        ] = sval
            ztab [..., -2, jpi//2:  ] = sval
                             
        if cd_type == 'F' :
            ztab [..., -1, :          ] = sval
            ztab [..., -2, jpi//2+1:-1] = sval

    return ztab

#@numba.jit(forceobj=True)
def lbc_add (ptab, nperio=None, cd_type=None, psgn=1, sval=None) :
    '''
    Handle NEMO domain changes between NEMO 4.0 to NEMO 4.2
      Peridodicity halo has been removed
    This routine adds the halos if needed

    ptab      : Input array (works 
      rank 2 at least : ptab[...., lat, lon]
    nperio    : Type of periodicity
 
    See NEMO documentation for further details
    '''
    mmath = __mmath__ (ptab) 
    jpj, jpi, nperio = lbc_init (ptab, nperio)

    t_shape = np.array (ptab.shape)

    if nperio == 4.2 or nperio == 6.2 :
      
        ext_shape = t_shape
        ext_shape[-1] = ext_shape[-1] + 2
        ext_shape[-2] = ext_shape[-2] + 1

        if mmath == xr :
            ptab_ext = xr.DataArray (np.zeros (ext_shape), dims=ptab.dims) 
            ptab_ext.values[..., :-1, 1:-1] = ptab.values.copy ()
        else           :
            ptab_ext =               np.zeros (ext_shape)
            ptab_ext[..., :-1, 1:-1] = ptab.copy ()
            
        #if sval != None :  ptab_ext[..., 0, :] = sval
        
        if nperio == 4.2 : ptab_ext = lbc (ptab_ext, nperio=4, cd_type=cd_type, psgn=psgn)
        if nperio == 6.2 : ptab_ext = lbc (ptab_ext, nperio=6, cd_type=cd_type, psgn=psgn)
             
        if mmath == xr :
            ptab_ext.attrs = ptab.attrs

    else : ptab_ext = lbc (ptab, nperio=nperio, cd_type=cd_type, psgn=psgn)
        
    return ptab_ext

def lbc_del (ptab, nperio=None, cd_type='T', psgn=1) :
    '''
    Handle NEMO domain changes between NEMO 4.0 to NEMO 4.2
      Periodicity halo has been removed
    This routine removes the halos if needed

    ptab      : Input array (works 
      rank 2 at least : ptab[...., lat, lon]
    nperio    : Type of periodicity
 
    See NEMO documentation for further details
    '''

    jpj, jpi, nperio = lbc_init (ptab, nperio)

    if nperio == 4.2 or nperio == 6.2 :
        return lbc (ptab[..., :-1, 1:-1], nperio=nperio, cd_type=cd_type, psgn=psgn)
    else :
        return ptab

#@numba.jit(forceobj=True)
def lbc_index (jj, ii, jpj, jpi, nperio=None, cd_type='T') :
    '''
    For indexes of a NEMO point, give the corresponding point inside the util domain
    jj, ii    : indexes
    jpi, jpi  : size of domain
    nperio    : type of periodicity
    cd_type   : grid specification : T, U, V or F
    
    See NEMO documentation for further details
    '''

    if nperio == None : nperio = __guessNperio__ (jpj, jpi, nperio)
    
    ## For the sake of simplicity, switch to the convention of original lbc Fortran routine from NEMO
    ## : starts indexes at 1
    jy = jj + 1 ; ix = ii + 1

    mmath = __mmath__ (jj)
    if mmath == None : mmath=np

    #
    #> East-West boundary conditions
    # ------------------------------
    if nperio in [1, 4, 6] :
        #... cyclic
        ix = mmath.where (ix==jpi, 2   , ix)
        ix = mmath.where (ix== 1 ,jpi-1, ix)

    #
    def modIJ (cond, jy_new, ix_new) :
        jy_r = mmath.where (cond, jy_new, jy)
        ix_r = mmath.where (cond, ix_new, ix)
        return jy_r, ix_r
    #
    #> North-South boundary conditions
    # --------------------------------
    if nperio in [ 3 , 4 ]  :
        if cd_type in  [ 'T' , 'W' ] :
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix>=2       ), jpj-2, jpi-ix+2)
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix==1       ), jpj-1, 3       )   
            (jy, ix) = modIJ (np.logical_and (jy==jpj-1, ix>=jpi//2+1), jy   , jpi-ix+2) 

        if cd_type in [ 'U' ] :
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , np.logical_and (ix>=1, ix <= jpi-1)   ), jy   , jpi-ix+1)
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix==1  )                               , jpj-2, 2       )
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix==jpi)                               , jpj-2, jpi-1   )
            (jy, ix) = modIJ (np.logical_and (jy==jpj-1, np.logical_and (ix>=jpi//2, ix<=jpi-1)), jy   , jpi-ix+1)
          
        if cd_type in [ 'V' ] :
            (jy, ix) = modIJ (np.logical_and (jy==jpj-1, ix>=2  ), jpj-2, jpi-ix+2)
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix>=2  ), jpj-3, jpi-ix+2)
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix==1  ), jpj-3,  3      )
            
        if cd_type in [ 'F' ] :
            (jy, ix) = modIJ (np.logical_and (jy==jpj-1, ix<=jpi-1), jpj-2, jpi-ix+1)
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix<=jpi-1), jpj-3, jpi-ix+1)
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix==1    ), jpj-3, 2       )
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix==jpi  ), jpj-3, jpi-1   )

    if nperio in [ 5 , 6 ] :
        if cd_type in [ 'T' , 'W' ] :                        # T-, W-point
             (jy, ix) = modIJ (jy==jpj, jpj-1, jpi-ix+1)
 
        if cd_type in [ 'U' ] :                              # U-point
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix<=jpi-1   ), jpj-1, jpi-ix  )
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix==jpi     ), jpi-1, 1       )
            
        if cd_type in [ 'V' ] :    # V-point
            (jy, ix) = modIJ (jy==jpj                                 , jy   , jpi-ix+1)
            (jy, ix) = modIJ (np.logical_and (jy==jpj-1, ix>=jpi//2+1), jy   , jpi-ix+1)
            
        if cd_type in [ 'F' ] :                              # F-point
            (jy, ix) = modIJ (np.logical_and (jy==jpj  , ix<=jpi-1   ), jpj-2, jpi-ix  )
            (jy, ix) = modIJ (np.logical_and (ix==jpj  , ix==jpi     ), jpj-2, 1       )
            (jy, ix) = modIJ (np.logical_and (jy==jpj-1, ix>=jpi//2+1), jy   , jpi-ix  )

    ## Restore convention to Python/C : indexes start at 0
    jy += -1 ; ix += -1

    if isinstance (jj, int) : jy = jy.item ()
    if isinstance (ii, int) : ix = ix.item ()

    return jy, ix
    
def geo2en (pxx, pyy, pzz, glam, gphi) : 
    '''
    Change vector from geocentric to east/north

    Inputs :
        pxx, pyy, pzz : components on the geocentric system
        glam, gphi : longitude and latitude of the points
    '''

    gsinlon = np.sin (rad * glam)
    gcoslon = np.cos (rad * glam)
    gsinlat = np.sin (rad * gphi)
    gcoslat = np.cos (rad * gphi)
          
    pte = - pxx * gsinlon            + pyy * gcoslon
    ptn = - pxx * gcoslon * gsinlat  - pyy * gsinlon * gsinlat + pzz * gcoslat

    return pte, ptn

def en2geo (pte, ptn, glam, gphi) :
    '''
    Change vector from east/north to geocentric

    Inputs : 
        pte, ptn   : eastward/northward components
        glam, gphi : longitude and latitude of the points
    '''
    
    gsinlon = np.sin (rad * glam)
    gcoslon = np.cos (rad * glam)
    gsinlat = np.sin (rad * gphi)
    gcoslat = np.cos (rad * gphi)

    pxx = - pte * gsinlon - ptn * gcoslon * gsinlat
    pyy =   pte * gcoslon - ptn * gsinlon * gsinlat
    pzz =   ptn * gcoslat
    
    return pxx, pyy, pzz

def findJI (lat_data, lon_data, lat_grid, lon_grid, mask=1.0, verbose=False) :
    '''
    Description: seeks J,I indices of the grid point which is the closest of a given point 
    Usage: go FindJI  <data latitude> <data longitude> <grid latitudes> <grid longitudes> [mask]
    <longitude fields> <latitude field> are 2D fields on J/I (Y/X) dimensions
    mask : if given, seek only non masked grid points (i.e with mask=1)
    
    Example : findIJ (40, -20, nav_lat, nav_lon, mask=1.0)

    Note : all longitudes and latitudes in degrees
        
    Note : may work with 1D lon/lat (?)
    '''
    # Get grid dimensions
    if len (lon_grid.shape) == 2 : (jpj, jpi) = lon_grid.shape
    else                         : jpj = len(lat_grid) ; jpi=len(lon_grid)

    mmath = __mmath__ (lat_grid)
        
    # Compute distance from the point to all grid points (in radian)
    arg      = np.sin (rad*lat_data) * np.sin (rad*lat_grid) \
             + np.cos (rad*lat_data) * np.cos (rad*lat_grid) * np.cos(rad*(lon_data-lon_grid))
    distance = np.arccos (arg) + 4.0*rpi*(1.0-mask) # Send masked points to 'infinite' 

    # Truncates to alleviate some precision problem with some grids
    prec = int (1E7)
    distance = (distance*prec).astype(int) / prec

    # Compute minimum of distance, and index of minimum
    #
    distance_min = distance.min    ()
    jimin        = int (distance.argmin ())
    
    # Compute 2D indices 
    jmin = jimin // jpi ; imin = jimin - jmin*jpi

    # Compute distance achieved
    mindist = distance[jmin, imin]
    
    # Compute azimuth
    dlon = lon_data-lon_grid[jmin,imin]
    arg  = np.sin (rad*dlon) /  (np.cos(rad*lat_data)*np.tan(rad*lat_grid[jmin,imin]) - np.sin(rad*lat_data)*np.cos(rad*dlon))
    azimuth = dar*np.arctan (arg)
    
    # Result
    if verbose : 
        print ('I={:d} J={:d} - Data:{:5.1f}°N {:5.1f}°E - Grid:{:4.1f}°N {:4.1f}°E - Dist: {:6.1f}km {:5.2f}° - Azimuth: {:3.2f}rad - {:5.1f}°'
            .format (imin, jmin, lat_data, lon_data, lat_grid[jmin,imin], lon_grid[jmin,imin], ra*distance[jmin,imin], dar*distance[jmin,imin], rad*azimuth, azimuth))

    return jmin, imin

def clo_lon (lon, lon0=0., rad=False, deg=True) :
    '''Choose closest to lon0 longitude, adding or substacting 360° if needed'''
    mmath = __mmath__ (lon, np)
    if rad : lon_range = 2.*np.pi
    if deg : lon_range = 360.
    clo_lon = lon
    clo_lon = mmath.where (clo_lon > lon0 + lon_range*0.5, clo_lon-lon_range, clo_lon)
    clo_lon = mmath.where (clo_lon < lon0 - lon_range*0.5, clo_lon+lon_range, clo_lon)
    clo_lon = mmath.where (clo_lon > lon0 + lon_range*0.5, clo_lon-lon_range, clo_lon)
    clo_lon = mmath.where (clo_lon < lon0 - lon_range*0.5, clo_lon+lon_range, clo_lon)
    if clo_lon.shape == () : clo_lon = clo_lon.item ()
    if mmath == xr :
        try : 
            for attr in lon.attrs : clo_lon.attrs[attr] = lon.attrs[attr]
        except :
            pass
    return clo_lon

def angle_full (glamt, gphit, glamu, gphiu, glamv, gphiv, glamf, gphif, nperio=None) :
    '''Compute sinus and cosinus of model line direction with respect to east'''
    mmath = __mmath__ (glamt)

    zlamt = lbc_add (glamt, nperio, 'T', 1.)
    zphit = lbc_add (gphit, nperio, 'T', 1.)
    zlamu = lbc_add (glamu, nperio, 'U', 1.)
    zphiu = lbc_add (gphiu, nperio, 'U', 1.)
    zlamv = lbc_add (glamv, nperio, 'V', 1.)
    zphiv = lbc_add (gphiv, nperio, 'V', 1.)
    zlamf = lbc_add (glamf, nperio, 'F', 1.)
    zphif = lbc_add (gphif, nperio, 'F', 1.)
    
    # north pole direction & modulous (at T-point)
    zxnpt = 0. - 2.0 * np.cos (rad*zlamt) * np.tan (rpi/4.0 - rad*zphit/2.0)
    zynpt = 0. - 2.0 * np.sin (rad*zlamt) * np.tan (rpi/4.0 - rad*zphit/2.0)
    znnpt = zxnpt*zxnpt + zynpt*zynpt
    
    # north pole direction & modulous (at U-point)
    zxnpu = 0. - 2.0 * np.cos (rad*zlamu) * np.tan (rpi/4.0 - rad*zphiu/2.0)
    zynpu = 0. - 2.0 * np.sin (rad*zlamu) * np.tan (rpi/4.0 - rad*zphiu/2.0)
    znnpu = zxnpu*zxnpu + zynpu*zynpu
    
    # north pole direction & modulous (at V-point)
    zxnpv = 0. - 2.0 * np.cos (rad*zlamv) * np.tan (rpi/4.0 - rad*zphiv/2.0)
    zynpv = 0. - 2.0 * np.sin (rad*zlamv) * np.tan (rpi/4.0 - rad*zphiv/2.0)
    znnpv = zxnpv*zxnpv + zynpv*zynpv

    # north pole direction & modulous (at F-point)
    zxnpf = 0. - 2.0 * np.cos( rad*zlamf ) * np.tan ( rpi/4. - rad*zphif/2. )
    zynpf = 0. - 2.0 * np.sin( rad*zlamf ) * np.tan ( rpi/4. - rad*zphif/2. )
    znnpf = zxnpf*zxnpf + zynpf*zynpf

    # j-direction: v-point segment direction (around T-point)
    zlam = zlamv  
    zphi = zphiv
    zlan = np.roll ( zlamv, axis=-2, shift=1)  # glamv (ji,jj-1)
    zphh = np.roll ( zphiv, axis=-2, shift=1)  # gphiv (ji,jj-1)
    zxvvt =  2.0 * np.cos ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2.0 * np.cos ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    zyvvt =  2.0 * np.sin ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2.0 * np.sin ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    znvvt = np.sqrt ( znnpt * ( zxvvt*zxvvt + zyvvt*zyvvt )  )

    # j-direction: f-point segment direction (around u-point)
    zlam = zlamf
    zphi = zphif
    zlan = np.roll (zlamf, axis=-2, shift=1) # glamf (ji,jj-1)
    zphh = np.roll (zphif, axis=-2, shift=1) # gphif (ji,jj-1)
    zxffu =  2.0 * np.cos ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2.0 * np.cos ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    zyffu =  2.0 * np.sin ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2.0 * np.sin ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    znffu = np.sqrt ( znnpu * ( zxffu*zxffu + zyffu*zyffu )  )

    # i-direction: f-point segment direction (around v-point)
    zlam = zlamf  
    zphi = zphif
    zlan = np.roll (zlamf, axis=-1, shift=1) # glamf (ji-1,jj)
    zphh = np.roll (zphif, axis=-1, shift=1) # gphif (ji-1,jj)
    zxffv =  2.0 * np.cos ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2.0 * np.cos ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    zyffv =  2.0 * np.sin ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2.0 * np.sin ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    znffv = np.sqrt ( znnpv * ( zxffv*zxffv + zyffv*zyffv )  )

    # j-direction: u-point segment direction (around f-point)
    zlam = np.roll (zlamu, axis=-2, shift=-1) # glamu (ji,jj+1) 
    zphi = np.roll (zphiu, axis=-2, shift=-1) # gphiu (ji,jj+1)
    zlan = zlamu
    zphh = zphiu
    zxuuf =  2. * np.cos ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2. * np.cos ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    zyuuf =  2. * np.sin ( rad*zlam ) * np.tan ( rpi/4. - rad*zphi/2. )   \
          -  2. * np.sin ( rad*zlan ) * np.tan ( rpi/4. - rad*zphh/2. )
    znuuf = np.sqrt ( znnpf * ( zxuuf*zxuuf + zyuuf*zyuuf )  )

    
    # cosinus and sinus using scalar and vectorial products
    gsint = ( zxnpt*zyvvt - zynpt*zxvvt ) / znvvt
    gcost = ( zxnpt*zxvvt + zynpt*zyvvt ) / znvvt
    
    gsinu = ( zxnpu*zyffu - zynpu*zxffu ) / znffu
    gcosu = ( zxnpu*zxffu + zynpu*zyffu ) / znffu
    
    gsinf = ( zxnpf*zyuuf - zynpf*zxuuf ) / znuuf
    gcosf = ( zxnpf*zxuuf + zynpf*zyuuf ) / znuuf
    
    gsinv = ( zxnpv*zxffv + zynpv*zyffv ) / znffv
    gcosv =-( zxnpv*zyffv - zynpv*zxffv ) / znffv  # (caution, rotation of 90 degres)
    
    #gsint = lbc (gsint, cd_type='T', nperio=nperio, psgn=-1.)
    #gcost = lbc (gcost, cd_type='T', nperio=nperio, psgn=-1.)
    #gsinu = lbc (gsinu, cd_type='U', nperio=nperio, psgn=-1.)
    #gcosu = lbc (gcosu, cd_type='U', nperio=nperio, psgn=-1.)
    #gsinv = lbc (gsinv, cd_type='V', nperio=nperio, psgn=-1.)
    #gcosv = lbc (gcosv, cd_type='V', nperio=nperio, psgn=-1.)
    #gsinf = lbc (gsinf, cd_type='F', nperio=nperio, psgn=-1.)
    #gcosf = lbc (gcosf, cd_type='F', nperio=nperio, psgn=-1.)

    gsint = lbc_del (gsint, cd_type='T', nperio=nperio, psgn=-1.)
    gcost = lbc_del (gcost, cd_type='T', nperio=nperio, psgn=-1.)
    gsinu = lbc_del (gsinu, cd_type='U', nperio=nperio, psgn=-1.)
    gcosu = lbc_del (gcosu, cd_type='U', nperio=nperio, psgn=-1.)
    gsinv = lbc_del (gsinv, cd_type='V', nperio=nperio, psgn=-1.)
    gcosv = lbc_del (gcosv, cd_type='V', nperio=nperio, psgn=-1.)
    gsinf = lbc_del (gsinf, cd_type='F', nperio=nperio, psgn=-1.)
    gcosf = lbc_del (gcosf, cd_type='F', nperio=nperio, psgn=-1.)

    if mmath == xr :
        gsint = gsint.assign_coords ( glamt.coords )
        gcost = gcost.assign_coords ( glamt.coords )
        gsinu = gsinu.assign_coords ( glamu.coords )
        gcosu = gcosu.assign_coords ( glamu.coords )
        gsinv = gsinv.assign_coords ( glamv.coords )
        gcosv = gcosv.assign_coords ( glamv.coords )
        gsinf = gsinf.assign_coords ( glamf.coords )
        gcosf = gcosf.assign_coords ( glamf.coords )

    return gsint, gcost, gsinu, gcosu, gsinv, gcosv, gsinf, gcosf

def angle (glam, gphi, nperio, cd_type='T') :
    '''Compute sinus and cosinus of model line direction with respect to east'''
    mmath = __mmath__ (glam)

    zlam = lbc_add (glam, nperio, cd_type, 1.)
    zphi = lbc_add (gphi, nperio, cd_type, 1.)
    
    # north pole direction & modulous
    zxnp = 0. - 2.0 * np.cos (rad*zlam) * np.tan (rpi/4.0 - rad*zphi/2.0)
    zynp = 0. - 2.0 * np.sin (rad*zlam) * np.tan (rpi/4.0 - rad*zphi/2.0)
    znnp = zxnp*zxnp + zynp*zynp

    # j-direction: segment direction (around point)
    zlan_n = np.roll (zlam, axis=-2, shift=-1) # glam [jj+1, ji]
    zphh_n = np.roll (zphi, axis=-2, shift=-1) # gphi [jj+1, ji]
    zlan_s = np.roll (zlam, axis=-2, shift= 1) # glam [jj-1, ji]
    zphh_s = np.roll (zphi, axis=-2, shift= 1) # gphi [jj-1, ji]
    
    zxff = 2.0 * np.cos (rad*zlan_n) * np.tan (rpi/4.0 - rad*zphh_n/2.0) \
        -  2.0 * np.cos (rad*zlan_s) * np.tan (rpi/4.0 - rad*zphh_s/2.0)
    zyff = 2.0 * np.sin (rad*zlan_n) * np.tan (rpi/4.0 - rad*zphh_n/2.0) \
        -  2.0 * np.sin (rad*zlan_s) * np.tan (rpi/4.0 - rad*zphh_s/2.0)
    znff = np.sqrt (znnp * (zxff*zxff + zyff*zyff) )
 
    gsin = (zxnp*zyff - zynp*zxff) / znff
    gcos = (zxnp*zxff + zynp*zyff) / znff

    gsin = lbc_del (gsin, cd_type=cd_type, nperio=nperio, psgn=-1.)
    gcos = lbc_del (gcos, cd_type=cd_type, nperio=nperio, psgn=-1.)

    if mmath == xr :
        gsin = gsin.assign_coords ( glam.coords )
        gcos = gcos.assign_coords ( glam.coords )
        
    return gsin, gcos

def rot_en2ij ( u_e, v_n, gsin, gcos, nperio, cd_type ) :
    '''
    ** Purpose :   Rotate the Repere: Change vector componantes between
    geographic grid --> stretched coordinates grid.
    All components are on the same grid (T, U, V or F) 
    '''

    u_i = + u_e * gcos + v_n * gsin
    v_j = - u_e * gsin + v_n * gcos
    
    u_i = lbc (u_i, nperio=nperio, cd_type=cd_type, psgn=-1.0)
    v_j = lbc (v_j, nperio=nperio, cd_type=cd_type, psgn=-1.0)
    
    return u_i, v_j

def rot_ij2en ( u_i, v_j, gsin, gcos, nperio, cd_type='T' ) :
    '''
    ** Purpose :   Rotate the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid
    All components are on the same grid (T, U, V or F) 
    '''
    u_e = + u_i * gcos - v_j * gsin
    v_n = + u_i * gsin + v_j * gcos
    
    u_e = lbc (u_e, nperio=nperio, cd_type=cd_type, psgn= 1.0)
    v_n = lbc (v_n, nperio=nperio, cd_type=cd_type, psgn= 1.0)
    
    return u_e, v_n

def rot_uv2en ( uo, vo, gsint, gcost, nperio, zdim='deptht' ) :
    '''
    ** Purpose :   Rotate the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid
    uo is on the U grid point, vo is on the V grid point
    east-north components on the T grid point   
    '''
    mmath = __mmath__ (uo)

    ut = U2T (uo, nperio=nperio, psgn=-1.0, zdim=zdim)
    vt = V2T (vo, nperio=nperio, psgn=-1.0, zdim=zdim)
    
    u_e = + ut * gcost - vt * gsint
    v_n = + ut * gsint + vt * gcost

    u_e = lbc (u_e, nperio=nperio, cd_type='T', psgn=1.0)
    v_n = lbc (v_n, nperio=nperio, cd_type='T', psgn=1.0)
    
    return u_e, v_n

def rot_uv2enF ( uo, vo, gsinf, gcosf, nperio, zdim='deptht' ) :
    '''
    ** Purpose : Rotate the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid
    uo is on the U grid point, vo is on the V grid point
    east-north components on the T grid point   
    '''
    mmath = __mmath__ (uo)

    uf = U2F (uo, nperio=nperio, psgn=-1.0, zdim=zdim)
    vf = V2F (vo, nperio=nperio, psgn=-1.0, zdim=zdim)
    
    u_e = + uf * gcosf - vf * gsinf
    v_n = + uf * gsinf + vf * gcosf

    u_e = lbc (u_e, nperio=nperio, cd_type='F', psgn= 1.0)
    v_n = lbc (v_n, nperio=nperio, cd_type='F', psgn= 1.0)
    
    return u_e, v_n

#@numba.jit(forceobj=True)
def U2T (utab, nperio=None, psgn=-1.0, zdim='deptht', action='ave') :
    '''Interpolate an array from U grid to T grid i-mean)'''
    mmath = __mmath__ (utab)
    utab_0 = mmath.where ( np.isnan(utab), 0., utab)
    lperio, aperio = lbc_diag (nperio)
    utab_0 = lbc_add (utab_0, nperio=nperio, cd_type='U', psgn=psgn)
    ix, ax = __findAxis__ (utab_0, 'x')
    iz, az = __findAxis__ (utab_0, 'z')
    if action == 'ave'  : ttab = 0.5 *      (utab_0 + np.roll (utab_0, axis=ix, shift=1))
    if action == 'min'  : ttab = np.minimum (utab_0 , np.roll (utab_0, axis=ix, shift=1))
    if action == 'max'  : ttab = np.maximum (utab_0 , np.roll (utab_0, axis=ix, shift=1))
    if action == 'mult' : ttab =             utab_0 * np.roll (utab_0, axis=ix, shift=1)
    ttab = lbc_del (ttab, nperio=nperio, cd_type='T', psgn=psgn)
    
    if mmath == xr :
        if ax != None :
            ttab = ttab.assign_coords({ax:np.arange (ttab.shape[ix])+1.})
        if zdim != None and iz != None  and az != 'olevel' : 
            ttab = ttab.rename( {az:zdim}) 
    return ttab

#@numba.jit(forceobj=True)
def V2T (vtab, nperio=None, psgn=-1.0, zdim='deptht', action='ave') :
    '''Interpolate an array from V grid to T grid (j-mean)'''
    mmath = __mmath__ (vtab)
    lperio, aperio = lbc_diag (nperio)
    vtab_0 = mmath.where ( np.isnan(vtab), 0., vtab)
    vtab_0 = lbc_add (vtab_0, nperio=nperio, cd_type='V', psgn=psgn)
    iy, ay = __findAxis__ (vtab_0, 'y')
    iz, az = __findAxis__ (vtab_0, 'z')
    if action == 'ave'  : ttab = 0.5 *      (vtab_0 + np.roll (vtab_0, axis=iy, shift=1))
    if action == 'min'  : ttab = np.minimum (vtab_0 , np.roll (vtab_0, axis=iy, shift=1))
    if action == 'max'  : ttab = np.maximum (vtab_0 , np.roll (vtab_0, axis=iy, shift=1))
    if action == 'mult' : ttab =             vtab_0 * np.roll (vtab_0, axis=iy, shift=1)
    ttab = lbc_del (ttab, nperio=nperio, cd_type='T', psgn=psgn)
    if mmath == xr :
        if ay !=None : 
            ttab = ttab.assign_coords({ay:np.arange(ttab.shape[iy])+1.})
        if zdim != None and iz != None  and az != 'olevel' :
            ttab = ttab.rename( {az:zdim}) 
    return ttab

#@numba.jit(forceobj=True)
def F2T (ftab, nperio=None, psgn=1.0, zdim='depthf', action='ave') :
    '''Interpolate an array from F grid to T grid (i- and j- means)'''
    mmath = __mmath__ (ftab)
    ftab_0 = mmath.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , nperio=nperio, cd_type='F', psgn=psgn)
    ttab = V2T(F2V(ftab_0, nperio=nperio, psgn=psgn, zdim=zdim, action=action), nperio=nperio, psgn=psgn, zdim=zdim, action=action)
    return lbc_del (ttab, nperio=nperio, cd_type='T', psgn=psgn)

#@numba.jit(forceobj=True)
def T2U (ttab, nperio=None, psgn=1.0, zdim='depthu', action='ave') :
    '''Interpolate an array from T grid to U grid (i-mean)'''
    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 , nperio=nperio, cd_type='T', psgn=psgn)
    ix, ax = __findAxis__ (ttab_0, 'x')
    iz, az = __findAxis__ (ttab_0, 'z')
    if action == 'ave'  : utab = 0.5 *      (ttab_0 + np.roll (ttab_0, axis=ix, shift=-1))
    if action == 'min'  : utab = np.minimum (ttab_0 , np.roll (ttab_0, axis=ix, shift=-1))
    if action == 'max'  : utab = np.maximum (ttab_0 , np.roll (ttab_0, axis=ix, shift=-1))
    if action == 'mult' : utab =             ttab_0 * np.roll (ttab_0, axis=ix, shift=-1)
    utab = lbc_del (utab, nperio=nperio, cd_type='U', psgn=psgn)

    if mmath == xr :    
        if ax != None : 
            utab = ttab.assign_coords({ax:np.arange(utab.shape[ix])+1.})
        if zdim != None  and iz != None  and az != 'olevel' :
            utab = utab.rename( {az:zdim}) 
    return utab

#@numba.jit(forceobj=True)
def T2V (ttab, nperio=None, psgn=1.0, zdim='depthv', action='ave') :
    '''Interpolate an array from T grid to V grid (j-mean)'''
    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 , nperio=nperio, cd_type='T', psgn=psgn)
    iy, ay = __findAxis__ (ttab_0, 'y')
    iz, az = __findAxis__ (ttab_0, 'z')
    if action == 'ave'  : vtab = 0.5 *      (ttab_0 + np.roll (ttab_0, axis=iy, shift=-1))
    if action == 'min'  : vtab = np.minimum (ttab_0 , np.roll (ttab_0, axis=iy, shift=-1))
    if action == 'max'  : vtab = np.maximum (ttab_0 , np.roll (ttab_0, axis=iy, shift=-1))
    if action == 'mult' : vtab =             ttab_0 * np.roll (ttab_0, axis=iy, shift=-1)

    vtab = lbc_del (vtab, nperio=nperio, cd_type='V', psgn=psgn)
    if mmath == xr :
        if ay != None : 
            vtab = vtab.assign_coords({ay:np.arange(vtab.shape[iy])+1.})
        if zdim != None  and iz != None and az != 'olevel' :
            vtab = vtab.rename( {az:zdim}) 
    return vtab

#@numba.jit(forceobj=True)
def V2F (vtab, nperio=None, psgn=-1.0, zdim='depthf', action='ave') :
    '''Interpolate an array from V grid to F grid (i-mean)'''
    mmath = __mmath__ (vtab)
    vtab_0 = mmath.where ( np.isnan(vtab), 0., vtab)
    vtab_0 = lbc_add (vtab_0 , nperio=nperio, cd_type='V', psgn=psgn)
    ix, ax = __findAxis__ (vtab_0, 'x')
    iz, az = __findAxis__ (vtab_0, 'z')
    if action == 'ave'  : 0.5 *      (vtab_0 + np.roll (vtab_0, axis=ix, shift=-1))
    if action == 'min'  : np.minimum (vtab_0 , np.roll (vtab_0, axis=ix, shift=-1))
    if action == 'max'  : np.maximum (vtab_0 , np.roll (vtab_0, axis=ix, shift=-1))
    if action == 'mult' :             vtab_0 * np.roll (vtab_0, axis=ix, shift=-1)
    ftab = lbc_del (ftab, nperio=nperio, cd_type='F', psgn=psgn)
    
    if mmath == xr :
        if ax != None : 
            ftab = ftab.assign_coords({ax:np.arange(ftab.shape[ix])+1.})
        if zdim != None and iz != None and az != 'olevel' :
            ftab = ftab.rename( {az:zdim}) 
    return lbc_del (ftab, nperio=nperio, cd_type='F', psgn=psgn)

#@numba.jit(forceobj=True)
def U2F (utab, nperio=None, psgn=-1.0, zdim='depthf', action='ave') :
    '''Interpolate an array from U grid to F grid i-mean)'''
    mmath = __mmath__ (utab)
    utab_0 = mmath.where ( np.isnan(utab), 0., utab)
    utab_0 = lbc_add (utab_0 , nperio=nperio, cd_type='U', psgn=psgn)
    iy, ay = __findAxis__ (utab_0, 'y')
    iz, az = __findAxis__ (utab_0, 'z')
    if action == 'ave'  :    ftab = 0.5 *      (utab_0 + np.roll (utab_0, axis=iy, shift=-1))
    if action == 'min'  :    ftab = np.minimum (utab_0 , np.roll (utab_0, axis=iy, shift=-1))
    if action == 'max'  :    ftab = np.maximum (utab_0 , np.roll (utab_0, axis=iy, shift=-1))
    if action == 'mult' :    ftab =             utab_0 * np.roll (utab_0, axis=iy, shift=-1)
    ftab = lbc_del (ftab, nperio=nperio, cd_type='F', psgn=psgn)

    if mmath == xr :
        if ay != None : 
            ftab = ftab.assign_coords({'y':np.arange(ftab.shape[iy])+1.})
        if zdim != None and iz != None and az != 'olevel' :
            ftab = ftab.rename( {az:zdim}) 
    return ftab

#@numba.jit(forceobj=True)
def F2T (ftab, nperio=None, psgn=1.0, zdim='deptht', action='ave') :
    '''Interpolate an array on F grid to T grid (i- and j- means)'''
    mmath = __mmath__ (ftab)
    ftab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    ftab_0 = lbc_add (ftab_0 , nperio=nperio, cd_type='F', psgn=psgn)
    ttab = U2T(F2U(ftab_0, nperio=nperio, psgn=psgn, zdim=zdim, action=action), nperio=nperio, psgn=psgn, zdim=zdim, action=action)
    return lbc_del (ttab, nperio=nperio, cd_type='T', psgn=psgn)

#@numba.jit(forceobj=True)
def T2F (ttab, nperio=None, psgn=1.0, zdim='deptht', action='mean') :
    '''Interpolate an array on T grid to F grid (i- and j- means)'''
    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 , nperio=nperio, cd_type='T', psgn=psgn)
    ftab = T2U(U2F(ttab, nperio=nperio, psgn=psgn, zdim=zdim, action=action), nperio=nperio, psgn=psgn, zdim=zdim, action=action)
    
    return lbc_del (ftab, nperio=nperio, cd_type='F', psgn=psgn)

#@numba.jit(forceobj=True)
def F2U (ftab, nperio=None, psgn=1.0, zdim='depthu', action='ave') :
    '''Interpolate an array on F grid to FUgrid (i-mean)'''
    mmath = __mmath__ (ftab)
    ftab_0 = mmath.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , nperio=nperio, cd_type='F', psgn=psgn)
    iy, ay = __findAxis__ (ftab_0, 'y')
    iz, az = __findAxis__ (ftab_0, 'z')
    if action == 'ave'  : utab = 0.5 *      (ftab_0 + np.roll (ftab_0, axis=iy, shift=-1))
    if action == 'min'  : utab = np.minimum (ftab_0 , np.roll (ftab_0, axis=iy, shift=-1))
    if action == 'max'  : utab = np.maximum (ftab_0 , np.roll (ftab_0, axis=iy, shift=-1))
    if action == 'mult' : utab =             ftab_0 * np.roll (ftab_0, axis=iy, shift=-1)

    utab = lbc_del (utab, nperio=nperio, cd_type='U', psgn=psgn)
    
    if mmath == xr :
        utab = utab.assign_coords({ay:np.arange(ftab.shape[iy])+1.})
        if zdim != None and iz != None and az != 'olevel' :
            utab = utab.rename( {az:zdim}) 
    return utab

#@numba.jit(forceobj=True)
def F2V (ftab, nperio=None, psgn=1.0, zdim='depthv', action='ave') :
    '''Interpolate an array from F grid to V grid (i-mean)'''
    mmath = __mmath__ (ftab)
    ftab_0 = mmath.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , nperio=nperio, cd_type='F', psgn=psgn)
    ix, ax = __findAxis__ (ftab_0, 'x')
    iz, az = __findAxis__ (ftab_0, 'z')
    if action == 'ave'  : vtab = 0.5 *      (ftab_0 + np.roll (ftab_0, axis=ix, shift=-1))
    if action == 'min'  : vtab = np.minimum (ftab_0 , np.roll (ftab_0, axis=ix, shift=-1))
    if action == 'max'  : vtab = np.maximum (ftab_0 , np.roll (ftab_0, axis=ix, shift=-1))
    if action == 'mult' : vtab =             ftab_0 * np.roll (ftab_0, axis=ix, shift=-1)

    vtab = lbc_del (vtab, nperio=nperio, cd_type='V', psgn=psgn)
    if mmath == xr :
        vtab = vtab.assign_coords({ax:np.arange(ftab.shape[ix])+1.})
        if zdim != None and iz != None and az != 'olevel' :
            vtab = vtab.rename( {az:zdim}) 
    return vtab

##@numba.jit(forceobj=True)
def W2T (wtab, zcoord=None, zdim='deptht', sval=np.nan) :
    '''
    Interpolate an array on W grid to T grid (k-mean)
    sval is the bottom value
    '''
    mmath = __mmath__ (wtab)
    wtab_0 = mmath.where ( np.isnan(wtab), 0., wtab)

    iz, az = __findAxis__ (wtab_0, 'z')
       
    ttab = 0.5 * ( wtab_0 + np.roll (wtab_0, axis=iz, shift=-1) )
    
    if mmath == xr :
        ttab[{az:iz}] = sval
        if zdim != None and iz != None and az != 'olevel' :
            ttab = ttab.rename ( {az:zdim} )
        try    : ttab = ttab.assign_coords ( {zdim:zcoord} )
        except : pass
    else :
        ttab[..., -1, :, :] = sval

    return ttab

#@numba.jit(forceobj=True)
def T2W (ttab, zcoord=None, zdim='depthw', sval=np.nan, extrap_surf=False) :
    '''Interpolate an array from T grid to W grid (k-mean)
    sval is the surface value
    if extrap_surf==True, surface value is taken from 1st level value.
    '''
    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    iz, az = __findAxis__ (ttab_0, 'z')
    wtab = 0.5 * ( ttab_0 + np.roll (ttab_0, axis=iz, shift=1) )

    if mmath == xr :
        if extrap_surf : wtab[{az:0}] = ttabb[{az:0}]
        else           : wtab[{az:0}] = sval
    else : 
        if extrap_surf : wtab[..., 0, :, :] = ttab[..., 0, :, :]
        else           : wtab[..., 0, :, :] = sval

    if mmath == xr :
        if zdim != None and iz != None and az != 'olevel' :
                wtab = wtab.rename ( {az:zdim})
        if zcoord != None : wtab = wtab.assign_coords ( {zdim:zcoord})
        else              : ztab = wtab.assign_coords ( {zdim:np.arange(ttab.shape[iz])+1.} )
    return wtab

#@numba.jit(forceobj=True)
def fill (ptab, nperio, cd_type='T', npass=1, sval=0.) :
    '''
    Fill sval values with mean of neighbours
   
    Inputs :
       ptab : input field to fill
       nperio, cd_type : periodicity characteristics
    '''       

    mmath = __mmath__ (ptab)

    DoPerio = False ; lperio = nperio
    if nperio == 4.2 :
        DoPerio = True ; lperio = 4
    if nperio == 6.2 :
        DoPerio = True ; lperio = 6
        
    if DoPerio :
        ztab = lbc_add (ptab, nperio=nperio, sval=sval)
    else : 
        ztab = ptab
        
    if np.isnan (sval) : 
        ztab   = mmath.where (np.isnan(ztab), np.nan, ztab)
    else :
        ztab   = mmath.where (ztab==sval    , np.nan, ztab)
   
    for nn in np.arange (npass) : 
        zmask = mmath.where ( np.isnan(ztab), 0., 1.   )
        ztab0 = mmath.where ( np.isnan(ztab), 0., ztab )
        # Compte du nombre de voisins
        zcount = 1./6. * ( zmask \
          + np.roll(zmask, shift=1, axis=-1) + np.roll(zmask, shift=-1, axis=-1) \
          + np.roll(zmask, shift=1, axis=-2) + np.roll(zmask, shift=-1, axis=-2) \
          + 0.5 * ( \
                + np.roll(np.roll(zmask, shift= 1, axis=-2), shift= 1, axis=-1) \
                + np.roll(np.roll(zmask, shift=-1, axis=-2), shift= 1, axis=-1) \
                + np.roll(np.roll(zmask, shift= 1, axis=-2), shift=-1, axis=-1) \
                + np.roll(np.roll(zmask, shift=-1, axis=-2), shift=-1, axis=-1) ) )

        znew =1./6. * ( ztab0 \
           + np.roll(ztab0, shift=1, axis=-1) + np.roll(ztab0, shift=-1, axis=-1) \
           + np.roll(ztab0, shift=1, axis=-2) + np.roll(ztab0, shift=-1, axis=-2) \
           + 0.5 * ( \
                + np.roll(np.roll(ztab0 , shift= 1, axis=-2), shift= 1, axis=-1) \
                + np.roll(np.roll(ztab0 , shift=-1, axis=-2), shift= 1, axis=-1) \
                + np.roll(np.roll(ztab0 , shift= 1, axis=-2), shift=-1, axis=-1) \
                + np.roll(np.roll(ztab0 , shift=-1, axis=-2), shift=-1, axis=-1) ) )

        zcount = lbc (zcount, nperio=lperio, cd_type=cd_type)
        znew   = lbc (znew  , nperio=lperio, cd_type=cd_type)
        
        ztab = mmath.where (np.logical_and (zmask==0., zcount>0), znew/zcount, ztab)

    ztab = mmath.where (zcount==0, sval, ztab)
    if DoPerio : ztab = lbc_del (ztab, nperio=lperio)

    return ztab

#@numba.jit(forceobj=True)
def correct_uv (u, v, lat) :
    '''
    Correct a Cartopy bug in Orthographic projection

    See https://github.com/SciTools/cartopy/issues/1179

    The correction is needed with cartopy <= 0.20
    It seems that version 0.21 will correct the bug (https://github.com/SciTools/cartopy/pull/1926)

    Inputs :
       u, v : eastward/nothward components
       lat  : latitude of the point (degrees north)

    Outputs : 
       modified eastward/nothward components to have correct polar projections in cartopy
    '''
    uv = np.sqrt (u*u + v*v)           # Original modulus
    zu = u
    zv = v * np.cos (rad*lat)
    zz = np.sqrt ( zu*zu + zv*zv )     # Corrected modulus
    uc = zu*uv/zz ; vc = zv*uv/zz      # Final corrected values
    return uc, vc

def msf (v_e1v_e3v, lat1d, depthw) :
    '''
    Computes the meridonal stream function
    First input is meridional_velocity*e1v*e3v
    '''
    #@numba.jit(forceobj=True)
    def iin (tab, dim) :
        '''
        Integrate from the bottom
        '''
        result = tab * 0.0
        nlen = len(tab.coords[dim])
        for jn in np.arange (nlen-2, 0, -1) :
            result [{dim:jn}] = result [{dim:jn+1}] - tab [{dim:jn}]
        result = result.where (result !=0, np.nan)
        return result
    
    zomsf = iin ((v_e1v_e3v).sum (dim='x', keep_attrs=True)*1E-6, dim='depthv')
    zomsf = zomsf.assign_coords ( {'depthv':depthw.values, 'y':lat1d.values})
    zomsf = zomsf.rename ( {'depthv':'depthw', 'y':'lat'})
    zomsf.attrs['long_name'] = 'Meridional stream function'

    zomsf.attrs['units'] = 'Sv'
    zomsf.depthw.attrs=depthw.attrs
    zomsf.lat.attrs=lat1d.attrs
        
    return zomsf

def bsf (u_e2u_e3u, mask, nperio=None, bsf0=None ) :
    '''
    Computes the barotropic stream function
    First input is zonal_velocity*e2u*e3u
    bsf0 is the point with bsf=0 (ex: bsf0={'x':5, 'y':120} )
    '''
    #@numba.jit(forceobj=True)
    def iin (tab, dim) :
        '''
        Integrate from the south
        '''
        result = tab * 0.0
        nlen = len(tab.coords[dim])
        for jn in np.arange (3, nlen) :
            result [{dim:jn}] = result [{dim:jn-1}] + tab [{dim:jn}]
        return result
    
    bsf = iin ((u_e2u_e3u).sum(dim='depthu', keep_attrs=True)*1E-6, dim='y')
    bsf.attrs = u_e2u_e3u.attrs
    if bsf0 != None :
        bsf = bsf - bsf.isel (bsf0)
       
    bsf = bsf.where (mask !=0, np.nan)
    bsf.attrs['long_name'] = 'Barotropic stream function'
    bsf.attrs['units'] = 'Sv'
    bsf = lbc (bsf, nperio=nperio, cd_type='F')
       
    return bsf

def namelist_read (ref=None, cfg=None, out='dict', flat=False, verbose=False) :
    '''
    Read NEMO namelist(s) and return either a dictionnary or an xarray dataset

    ref : file with reference namelist, or a f90nml.namelist.Namelist object
    cfg : file with config namelist, or a f90nml.namelist.Namelist object
    At least one namelist neaded

    out: 
        'dict' to return a dictonnary
        'xr'   to return an xarray dataset
    flat : only for dict output. Output a flat dictionnary with all values.
    
    '''

    if ref != None :
        if isinstance (ref, str) : nml_ref = f90nml.read (ref)
        if isinstance (ref, f90nml.namelist.Namelist) : nml_ref = ref
        
    if cfg != None :
        if isinstance (cfg, str) : nml_cfg = f90nml.read (cfg)
        if isinstance (cfg, f90nml.namelist.Namelist) : nml_cfg = cfg
    
    if out == 'dict' : dict_namelist = {}
    if out == 'xr'   : xr_namelist = xr.Dataset ()

    list_nml = [] ; list_comment = []

    if ref != None :
        list_nml.append (nml_ref) ; list_comment.append ('ref')
    if cfg != None :
        list_nml.append (nml_cfg) ; list_comment.append ('cfg')

    for nml, comment in zip (list_nml, list_comment) :
        if verbose : print (comment)
        if flat and out =='dict' :
            for nam in nml.keys () :
                if verbose : print (nam)
                for value in nml[nam] :
                     if out == 'dict' : dict_namelist[value] = nml[nam][value]
                     if verbose : print (nam, ':', value, ':', nml[nam][value])
        else :
            for nam in nml.keys () :
                if verbose : print (nam)
                if out == 'dict' :
                    if nam not in dict_namelist.keys () : dict_namelist[nam] = {}
                for value in nml[nam] :
                    if out == 'dict' : dict_namelist[nam][value] = nml[nam][value]
                    if out == 'xr'   : xr_namelist[value] = nml[nam][value]
                    if verbose : print (nam, ':', value, ':', nml[nam][value])

    if out == 'dict' : return dict_namelist
    if out == 'xr'   : return xr_namelist


def fill_closed_seas (imask, nperio=None,  cd_type='T') :
    '''Fill closed seas with image processing library
    imask : mask, 1 on ocean, 0 on land
    '''
    from scipy import ndimage

    imask_filled = ndimage.binary_fill_holes ( lbc (imask, nperio=nperio, cd_type=cd_type))
    imask_filled = lbc ( imask_filled, nperio=nperio, cd_type=cd_type)

    return imask_filled

## ===========================================================================
##
##                               That's all folk's !!!
##
## ===========================================================================

def __is_orca_north_fold__ ( Xtest, cname_long='T' ) :
    '''
    Ported (pirated !!?) from Sosie

    Tell if there is a 2/point band overlaping folding at the north pole typical of the ORCA grid

    0 => not an orca grid (or unknown one)
    4 => North fold T-point pivot (ex: ORCA2)
    6 => North fold F-point pivot (ex: ORCA1)

    We need all this 'cname_long' stuff because with our method, there is a
    confusion between "Grid_U with T-fold" and "Grid_V with F-fold"
    => so knowing the name of the longitude array (as in namelist, and hence as
    in netcdf file) might help taking the righ decision !!! UGLY!!!
    => not implemented yet
    '''
    
    ifld_nord =  0 ; cgrd_type = 'X'
    ny, nx = Xtest.shape[-2:]

    if ny > 3 : # (case if called with a 1D array, ignoring...)
        if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-1:nx-nx//2+1:-1] ).sum() == 0. :
          ifld_nord = 4 ; cgrd_type = 'T' # T-pivot, grid_T      

        if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-2:nx-nx//2  :-1] ).sum() == 0. :
            if cnlon == 'U' : ifld_nord = 4 ;  cgrd_type = 'U' # T-pivot, grid_T
                ## LOLO: PROBLEM == 6, V !!!

        if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-1:nx-nx//2+1:-1] ).sum() == 0. :
            ifld_nord = 4 ; cgrd_type = 'V' # T-pivot, grid_V

        if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-2, nx-1-1:nx-nx//2:-1] ).sum() == 0. :
            ifld_nord = 6 ; cgrd_type = 'T'# F-pivot, grid_T

        if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-1, nx-1:nx-nx//2-1:-1] ).sum() == 0. :
            ifld_nord = 6 ;  cgrd_type = 'U' # F-pivot, grid_U

        if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-2:nx-nx//2  :-1] ).sum() == 0. :
            if cnlon == 'V' : ifld_nord = 6 ; cgrd_type = 'V' # F-pivot, grid_V
                ## LOLO: PROBLEM == 4, U !!!

    return ifld_nord, cgrd_type
