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

try    : import numba
except ImportError : pass

rpi = np.pi ; rad = np.deg2rad (1.0) ; dar = np.rad2deg (1.0)


def __math__ (tab) :
    '''
    Determines the type of tab : i.e. numpy or xarray
    '''
    math = None
    try : 
        if type (tab) == xr.core.dataarray.DataArray : math = xr
    except :
        pass

    try :
        if type (tab) == np.ndarray : math = np
    except :
        pass
            
    return math
#
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
    math = __math__ (tab)
    if tab.shape[-1] == 1 : extend = tab

    else :
        if jpi == None : jpi = tab.shape[-1]

        if Lon : xplus =  lonplus
        else   : xplus =    0.0

        if tab.shape[-1] > jpi :
            extend = tab
        else :
            istart = 0 ; le=jpi+1 ; la=0
            if math == xr :
                lon = tab.dims[-1]
                extend         = xr.concat      ((tab.isel(lon=slice(istart   ,istart+le      )),
                                                  tab.isel(lon=slice(istart+la,istart+la+jplus))+xplus  ), dim=lon)
                try :
                    extend_lon = xr.concat      ((tab.coords[lon].isel(lon=slice(istart   ,istart+le      )),
                                                  tab.coords[lon].isel(lon=slice(istart+la,istart+la+jplus))+lonplus), dim=lon)
                    extend = extend.assign_coords ( {tab.dims[-1]:extend_lon} )   
                except :
                    pass
            if math == np :
                extend = np.concatenate ((tab    [..., istart:istart+le], tab    [..., istart+la:jplus]+xplus  ), axis=-1)
                
    return extend

def interp1d (x, xp, yp, zdim='presnivs', units=None, verbose=False, method='linear') :
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

       \!/ xp should be decreasing values along zdim axis \!/
    '''
    # Get the number of dimension with dim==zdim
    axis = list(xp.dims).index(zdim)
    
    # Get the number of levels in each arrays
    nk_in = xp.shape[axis]
    nk_ou = len (x)
    
    # Define the result array
    in_shape       = np.array (xp.shape)
    if verbose : print ( 'in_shape    : ', in_shape   )
    ou_shape       = np.array (in_shape)
    if verbose : print ( 'ou_shape    : ', ou_shape   )
    ou_shape[axis] = nk_ou
    
    in_dims        = list (yp.dims)
    if verbose : print ( 'in_dims     : ', in_dims    )
    ou_dims        = in_dims
  
    pdim           = x.dims[0]
    ou_dims[axis]  = pdim

    new_coords = []
    for i, dim in enumerate (yp.dims) :
        if dim == zdim :
            ou_dims[i] = x.dims[0]
            if units != None : yp[dim].attrs['units'] = units
            new_coords.append (x             .values)
        else :
            new_coords.append (yp.coords[dim].values)
   
    if verbose :
        print ( 'ou_dims     : ', ou_dims    )
        print ( 'new_coords  : ', new_coords )
        
    ou_tab = xr.DataArray (np.empty (ou_shape), dims=ou_dims, coords=new_coords)

    if 'log' in method :
        yp_min = yp.min() ; yp_max = yp.max()
        indic = yp_min * yp_max
        if indic <= 0. :
            print ('Input data have a change of sign')
            print ('Error : logarithmic method is available only for')
            print ('positive or negative input values. ')
            raise Exception

    # Optimized (pre-compiled) interpolation loop
    #@numba.jit (nopython=True)
    def __interp (nk_ou, x, xp, yp) :
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
        dx1  = dx1/dx ; dx2 = dx2/dx
        
        y1   = yp[{zdim:idk1}]
        y2   = yp[{zdim:idk2}]
        
        #print ( k, idk1, idk2, x1, x2, dx1, dx2, y1, y2 )
        
        if 'linear'  in method : 
            result = (dx1*y2 + dx2*y1)
        if 'log'     in method :
            if yp_min > 0. : 
                result = np.power(y2, dx1) * np.power(y1, dx2)
            if yp_max < 0. :
                result = -np.power(-y2, dx1) * np.power(-y1, dx2)
        if 'nearest' in method :
            result = xr.where ( dx2>=dx1, y1, y2)
                
        return result

    for k in np.arange (nk_ou) :
        result = __interp  (nk_ou, x[{pdim:k}], xp, yp)
           
        # Put result in the final array
        ou_tab [{pdim:k}] = result

    return ou_tab.squeeze()

def nord2sud (p2D) :
    '''
    Swap north to south a 2D field
    '''
    pout = p2D [..., -1::-1, : ]

    return pout

def point2geo (p1D) :
    '''
    From 1D (restart type) to 2D
    '''
    math = __math__ (p1D)

    # Get the dimensions
    jpn = p1D.shape[-1]
    
    if len (p1D.shape) > 1 :
        jpt = p1D.shape[0]
    else :
        jpt = 0
        
    if jpn ==  9026 : jpi =  96 ; jpj =  96
    if jpn == 17858 : jpi = 144 ; jpj = 144
    if jpn == 20306 : jpi = 144 ; jpj = 143

    if jpt > 0 :
        p2D = np.zeros ( (jpt, jpj, jpi) )
        p2D [:, 1:jpj-1, :] = np.reshape (p1D [:,1:jpn-1], (jpt, jpj-2, jpi) )
        p2D [:, 0    , : ] = p1D[:,   0  ]
        p2D [:, jpj-1, : ] = p1D[:, jpn-1]

    else :
        p2D = np.zeros ( (jpj, jpi) )
        p2D [1:jpj-1, :] = np.reshape (np.float64 (p1D [1:jpn-1]), (jpj-2, jpi) )
        p2D [0    , : ] = p1D[   0 ]
        p2D [jpj-1, : ] = p1D[jpn-1]

    if math == xr :
        p2D = xr.DataArray (p2D)
        for attr in p1D.attrs : 
            p2D.attrs[attr] = p1D.attrs[attr]
        p2D = p2D.rename ( {p2D.dims[0]:p1D.dims[0], p2D.dims[-1]:'x', p2D.dims[-2]:'y'} )
        
    return p2D

def geo2point ( p2D, cumulPoles=False, dim1D='points_physiques' ) : 
    '''
    From 2D (lat, lon) to 1D (points_phyiques)
    '''
    math = __math__ (p2D)
    #
    # Get the dimension
    
    (jpj, jpi) = p2D.shape[-2:]
     
    if len (p2D.shape) > 2 :
        jpt = p2D.shape[0]
    else : 
        jpt = -1

    jpn = jpi*(jpj-2) + 2

    if jpt == -1 :
        p1D = np.zeros ( (jpn,) )
        p1D[1:-1] = np.float64(p2D[1:-1, :]).ravel()
        p1D[ 0]   = p2D[ 0, 0]
        p1D[-1]   = p2D[-1, 0]

    else : 
        p1D = np.zeros ( (jpt, jpn) )
        if math == xr :
            p1D[:, 1:-1] = np.reshape ( np.float64 (p2D[:, 1:-1, :].values).ravel(), (jpt, jpn-2) )
        else :
            p1D[:, 1:-1] = np.reshape ( np.float64 (p2D[:, 1:-1, :]       ).ravel(), (jpt, jpn-2) )
        p1D[:,  0  ] = p2D[:,  0, 0]
        p1D[:, -1  ] = p2D[:, -1, 0]
     
    if math == xr :
        p1D       = xr.DataArray (p1D)
        for attr in p2D.attrs : 
            p1D.attrs[attr] = p2D.attrs[attr]
        p1D       = p1D.rename ( {p1D.dims[0]:p2D.dims[0], p1D.dims[-1]:dim1D} )

    if cumulPoles :
        p1D[...,  0] = np.sum ( p2D[...,  0, :] )
        p1D[..., -1] = np.sum ( p2D[..., -1, :] )
        
    return p1D

def geo3point ( p3D, cumulPoles=False, dim1D='points_physiques' ) : 
    '''
    From 3D (lev, lat, lon) to 2D (lev, points_phyiques)
    '''
    math = __math__ (p3D)
    #
    # Get the dimensions
    
    (jpk, jpj, jpi) = p3D.shape[-3:]
     
    if len (p3D.shape) > 3 :
        jpt = p3D.shape[0]
    else : 
        jpt = -1

    jpn = jpi*(jpj-2) + 2

    if jpt == -1 :
        p2D = np.zeros ( (jpk, jpn,) )
        for jk in np.arange (jpk) :
            p2D [jk, :] = geo2point ( p3D [jk,:,:], cumulPoles, dim1D )
    else :
        p2D = np.zeros ( (jpt, jpk, jpn) )
        for jk in np.arange (jpk) :
            p2D [:, jk, :] = geo2point ( p3D [:, jk,:,:], cumulPoles, dim1D  )

    if math == xr :
        p2D       = xr.DataArray (p2D)
        for attr in p2D.attrs : 
            p2D.attrs[attr] = p3D.attrs[attr]
        p2D       = p2D.rename ( {p2D.dims[-1]:dim1D, p2D.dims[-2]:p3D.dims[-3]} )
        
    return p2D  

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
        pte, ptn : eastward/northward components
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

## ===========================================================================
##
##                               That's all folk's !!!
##
## ===========================================================================
