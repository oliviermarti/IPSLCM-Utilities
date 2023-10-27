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
Utilities for LMDZ grid

- Lots of tests for xarray object
- Not much tested for numpy objects

Author: olivier.marti@lsce.ipsl.fr

## SVN information
__Author__   = "$Author: omamce $"
__Date__     = "$Date: 2023-10-10 12:58:04 +0200 (Tue, 10 Oct 2023) $"
__Revision__ = "$Revision: 6647 $"
__Id__       = "$Id: $"
__HeadURL    = "$HeadURL: svn+ssh://omamce@forge.ipsl.jussieu.fr/ipsl/forge/projets/igcmg/svn/TOOLS/WATER_BUDGET/lmdz.py $"
'''

import numpy as np
import xarray as xr

RPI   = np.pi
RAD   = np.deg2rad (1.0)
DAR   = np.rad2deg (1.0)
REPSI = np.finfo (1.0).eps

RAAMO    =      12          # Number of months in one year
RJJHH    =      24          # Number of hours in one day
RHHMM    =      60          # Number of minutes in one hour
RMMSS    =      60          # Number of seconds in one minute
RA       = 6371229.0        # Earth radius                                  [m]
GRAV     =       9.80665    # Gravity                                       [m/s2]
RT0      =     273.15       # Freezing point of fresh water                 [Kelvin]
RAU0     =    1026.0        # Volumic mass of sea water                     [kg/m3]
RLEVAP   =       2.5e+6     # Latent heat of evaporation (water)            [J/K]
VKARMN   =       0.4        # Von Karman constant
STEFAN   =       5.67e-8    # Stefan-Boltzmann constant                     [W/m2/K4]
#RHOS     =     330.         # Volumic mass of snow                          [kg/m3]

RDAY     = RJJHH * RHHMM * RMMSS                # Day length               [s]
RSIYEA   = 365.25 * RDAY * 2. * RPI / 6.283076  # Sideral year length      [s]
RSIDAY   = RDAY / (1. + RDAY / RSIYEA)          # Sideral day length       [s]
ROMEGA   = 2. * RPI / RSIDAY                    # Earth rotation parameter [s-1]

def __mmath__ (ptab, default=None) :
    '''Determines the type of tab : xarray, numpy or numpy.ma object ?

    Returns type
    '''
    mmath = default
    if isinstance (ptab, xr.core.dataarray.DataArray) :
        mmath = xr
    if isinstance (ptab, np.ndarray) :
        mmath = np
    if isinstance (ptab, np.ma.MaskType) :
        mmath = np.ma

    return mmath

#
def extend (tab, Lon=False, jplus=25, jpi=None, lonplus=360.0) :
    '''Returns extended field eastward to have better plots, and box average crossing the boundary

    Works only for xarray and numpy data (?)

    tab : field to extend.
    Lon : (optional, default=False) : if True, add 360 in the extended parts of the field
    jpi : normal longitude dimension of the field. exrtend does nothing it the actual
        size of the field != jpi (avoid to extend several times)
    jplus (optional, default=25) : number of points added on the east side of the field
    '''
    
    math = __mmath__ (tab)
    if tab.shape[-1] == 1 :
        ztab = tab

    else :
        if jpi is None :
            jpi = tab.shape[-1]

        if Lon :
            xplus =  lonplus
        else   :
            xplus =    0.0

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
                #except :
                #    pass
            if math == np :
                ztab = np.concatenate ((tab    [..., istart:istart+le],
                                        tab    [..., istart+la:jplus]+xplus  ), axis=-1)

    return ztab

def interp1d (x, xp, yp, zdim='presnivs', units=None, verbose=False, method='linear') :
    '''One-dimensionnal interpolation of a multi-dimensionnal field

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
    # Get the number of dimension with dim==zdim
    axis = list(xp.dims).index(zdim)

    # Get the number of levels in each arrays
    nk_ou = len (x)

    # Define the result array
    in_shape       = np.array (xp.shape)
    if verbose :
        print ( f'{in_shape=}' )
    ou_shape       = np.array (in_shape)
    if verbose :
        print ( f'{ou_shape=}' )
    ou_shape[axis] = nk_ou

    in_dims        = list (yp.dims)
    if verbose :
        print ( f'{in_dims=}' )
    ou_dims        = in_dims

    pdim           = x.dims[0]
    ou_dims[axis]  = pdim

    new_coords = []
    for i, dim in enumerate (yp.dims) :
        if dim == zdim :
            ou_dims[i] = x.dims[0]
            if units is not None :
                yp[dim].attrs['units'] = units
            new_coords.append (x             .values)
        else :
            new_coords.append (yp.coords[dim].values)

    if verbose :
        print ( f'{ou_dims   =}' )
        print ( f'{new_coords=}' )

    ou_tab = xr.DataArray (np.empty (ou_shape), dims=ou_dims, coords=new_coords)

    if 'log' in method :
        yp_min = yp.min()
        yp_max = yp.max()
        indic  = yp_min * yp_max
        if indic <= 0. :
            print ( 'Input data have a change of sign')
            print ( 'Error: logarithmic method is available only for')
            print ( 'positive or negative input values. ')
            raise ValueError

    # Optimized (pre-compiled) interpolation loop
    #@numba.jit (nopython=True)
    def __interp (x, xp, yp) :
        # Interpolate
        # Find index of the just above level
        idk1 = np.minimum ( (x-xp), 0.).argmax (dim=zdim)
        idk2 = idk1 - 1
        idk2 = np.maximum (idk2, 0)

        x1   = xp[{zdim:idk1}]
        x2   = xp[{zdim:idk2}]

        dx1  = x  - x1
        dx2  = x2 - x
        dx   = x2 - x1
        dx1  = dx1/dx
        dx2  = dx2/dx

        y1   = yp[{zdim:idk1}]
        y2   = yp[{zdim:idk2}]

        if 'linear'  in method :
            result = dx1*y2 + dx2*y1
        if 'log'     in method :
            if yp_min > 0. :
                result = np.power(y2, dx1) * np.power(y1, dx2)
            if yp_max < 0. :
                result = -np.power(-y2, dx1) * np.power(-y1, dx2)
        if 'nearest' in method :
            result = xr.where ( dx2>=dx1, y1, y2)

        return result

    for k in np.arange (nk_ou) :
        result = __interp  (x[{pdim:k}], xp, yp)

        # Put result in the final array
        ou_tab [{pdim:k}] = result

    return ou_tab.squeeze()

def fixed_lon (lon, center_lon=0.0) :
    '''Returns corrected longitudes for nicer plots

    lon        : longitudes of the grid. At least 1D.
    center_lon : center longitude. Default=0.

    Designed by Phil Pelson. See https://gist.github.com/pelson/79cf31ef324774c97ae7
    '''
    mmath = __mmath__ (lon)

    zfixed_lon = lon.copy ()

    zfixed_lon = mmath.where (zfixed_lon > center_lon+180., zfixed_lon-360.0, fixed_lon)
    zfixed_lon = mmath.where (zfixed_lon < center_lon-180., zfixed_lon+360.0, fixed_lon)

    start = np.argmax (np.abs (np.diff (zfixed_lon, axis=-1)) > 180., axis=-1)
    zfixed_lon [start+1:] += 360.

    return zfixed_lon

def nord2sud (p2d) :
    '''Swap north to south a 2D field
    '''
    pout = p2d [..., -1::-1, : ]

    return pout

def point2geo (p1d) :
    '''From 1D (restart type) to 2D
    '''
    math = __mmath__ (p1d)

    # Get the dimensions
    jpn = p1d.shape[-1]

    if len (p1d.shape) > 1 :
        jpt = p1d.shape[0]
    else :
        jpt = 0

    if jpn ==  9026 :
        jpi, jpj =  96,  96
    if jpn == 17858 :
        jpi, jpj = 144, 144
    if jpn == 20306 :
        jpi, jpj = 144, 143

    if jpt > 0 :
        p2d = np.zeros ( (jpt, jpj, jpi) )
        p2d [:, 1:jpj-1, :] = np.reshape (p1d [:,1:jpn-1], (jpt, jpj-2, jpi) )
        p2d [:, 0    , : ] = p1d[:,   0  ]
        p2d [:, jpj-1, : ] = p1d[:, jpn-1]
    else :
        p2d = np.zeros ( (jpj, jpi) )
        p2d [1:jpj-1, :] = np.reshape (np.float64 (p1d [1:jpn-1]), (jpj-2, jpi) )
        p2d [0    , : ] = p1d[   0 ]
        p2d [jpj-1, : ] = p1d[jpn-1]

    if math == xr :
        p2d = xr.DataArray (p2d)
        p2d.attrs.update ( p1d.attrs )
        p2d = p2d.rename ( {p2d.dims[0]:p1d.dims[0], p2d.dims[-1]:'x', p2d.dims[-2]:'y'} )

    return p2d

def geo2point ( p2d, cumul_poles=False, dim1d='points_physiques' ) :
    '''From 2D (lat, lon) to 1D (points_phyiques)
    '''
    math = __mmath__ (p2d)
    #
    # Get the dimension

    (jpj, jpi) = p2d.shape[-2:]

    if len (p2d.shape) > 2 :
        jpt = p2d.shape[0]
    else :
        jpt = -1

    jpn = jpi*(jpj-2) + 2

    if jpt == -1 :
        p1d = np.zeros ( (jpn,) )
        p1d[1:-1] = np.float64(p2d[1:-1, :]).ravel()
        p1d[ 0]   = p2d[ 0, 0]
        p1d[-1]   = p2d[-1, 0]

    else :
        p1d = np.zeros ( (jpt, jpn) )
        if math == xr :
            p1d[:, 1:-1] = np.reshape ( np.float64 (p2d[:, 1:-1, :].values).ravel(), (jpt, jpn-2) )
        else :
            p1d[:, 1:-1] = np.reshape ( np.float64 (p2d[:, 1:-1, :]       ).ravel(), (jpt, jpn-2) )
        p1d[:,  0  ] = p2d[:,  0, 0]
        p1d[:, -1  ] = p2d[:, -1, 0]

    if math == xr :
        p1d = xr.DataArray (p1d)
        p1d.attrs.update ( p2d.attrs )
        p1d = p1d.rename ( {p1d.dims[0]:p2d.dims[0], p1d.dims[-1]:dim1d} )

    if cumul_poles :
        p1d[...,  0] = np.sum ( p2d[...,  0, :] )
        p1d[..., -1] = np.sum ( p2d[..., -1, :] )

    return p1d

def geo3point ( p3d, cumul_poles=False, dim1d='points_physiques' ) :
    '''From 3D (lev, lat, lon) to 2D (lev, points_phyiques)
    '''
    math = __mmath__ (p3d)
    #
    # Get the dimensions

    (jpk, jpj, jpi) = p3d.shape[-3:]

    if len (p3d.shape) > 3 :
        jpt = p3d.shape[0]
    else :
        jpt = -1

    jpn = jpi*(jpj-2) + 2

    if jpt == -1 :
        p2d = np.zeros ( (jpk, jpn,) )
        for jk in np.arange (jpk) :
            p2d [jk, :] = geo2point ( p3d [jk,:,:], cumul_poles, dim1d )
    else :
        p2d = np.zeros ( (jpt, jpk, jpn) )
        for jk in np.arange (jpk) :
            p2d [:, jk, :] = geo2point ( p3d [:, jk,:,:], cumul_poles, dim1d  )

    if math == xr :
        p2d       = xr.DataArray (p2d)
        p2d.attrs.update ( p3d.attrs )
        p2d       = p2d.rename ( {p2d.dims[-1]:dim1d, p2d.dims[-2]:p3d.dims[-3]} )

    return p2d

def geo2en (pxx, pyy, pzz, glam, gphi) :
    '''Change vector from geocentric to east/north

    Inputs :
        pxx, pyy, pzz : components on the geocentric system
        glam, gphi : longitude and latitude of the points
    '''

    gsinlon = np.sin (RAD * glam)
    gcoslon = np.cos (RAD * glam)
    gsinlat = np.sin (RAD * gphi)
    gcoslat = np.cos (RAD * gphi)

    pte = - pxx * gsinlon            + pyy * gcoslon
    ptn = - pxx * gcoslon * gsinlat  - pyy * gsinlon * gsinlat + pzz * gcoslat

    return pte, ptn

def en2geo (pte, ptn, glam, gphi) :
    '''Change vector from east/north to geocentric

    Inputs :
        pte, ptn : eastward/northward components
        glam, gphi : longitude and latitude of the points
    '''

    gsinlon = np.sin (RAD * glam)
    gcoslon = np.cos (RAD * glam)
    gsinlat = np.sin (RAD * gphi)
    gcoslat = np.cos (RAD * gphi)

    pxx = - pte * gsinlon - ptn * gcoslon * gsinlat
    pyy =   pte * gcoslon - ptn * gsinlon * gsinlat
    pzz =   ptn * gcoslat

    return pxx, pyy, pzz

## ===========================================================================
##
##                               That's all folk's !!!
##
## ===========================================================================
