# -*- coding: utf-8 -*-
'''
Utilities 1D vertical interpolation

author: olivier.marti@lsce.ipsl.fr

GitHub : https://github.com/oliviermarti/IPSLCM-Utilities

Design to interpolatte on pressure levels

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

import numpy as np
import xarray as xr
from plotIGCM.options import OPTIONS
from plotIGCM.options import push_stack
from plotIGCM.options import pop_stack

#from numba import jit

def interp1d (x:np.ndarray|xr.DataArray, xp:xr.DataArray,
              yp:xr.DataArray,
              zdim:str,
              name:str|None=None) :
    '''
    One-dimensionnal interpolation of a multi-dimensionnal field

    Intended to interpolate on standard pressure level
    
    All inputs shoud be xarray data arrays

    Input : 
       x    : levels at wich we want to interpolat
       xp   : position of the input points (i.e. pressure)
       yp   : fields values at these points (temperature, humidity, etc ..)
       zdim : name of the dimension that we want to interpolate
       name : set the name of new dimension
    '''
    push_stack ( f'interp1d (x, xp, yp, {zdim=} {name=}')

    if isinstance (x, np.ndarray) :
        x = xr.DataArray (x, coords=(x,), dims=(zdim,))
    if isinstance (x, float) :
        x = xr.DataArray (x, coords=(np.array(x),), dims=(zdim,))

    # Get the number of dimension with dim==zdim
    axis           = list (xp.dims).index (zdim)

    # Get the number of levels in each arrays
    nk_ou          = len (x)

    in_dims        = list (yp.dims)
    ou_dims        = in_dims

    in_shape       = np.array (xp.shape)
    ou_shape       = np.array (in_shape)
    ou_shape[axis] = nk_ou

    pdim           = x.dims[0]
    ou_dims[axis]  = pdim

    # Determines orientation of x
    dx = x.differentiate (coord=zdim)
    if dx.min()*dx.max() < 0. :
        raise ValueError ( 'interp1d : Coordinate not monotonic')
    else :
        if   ( dx.min() > 0. and dx.max()> 0. ) : or_up=True
        elif ( dx.min() < 0. and dx.max()< 0. ) : or_up=False
        else : raise ValueError ( 'interp1d : Coordinate not monotonic')

    if or_up :
        x  = -x ; xp = -xp

    # Define the result array
    new_coords = []
    for coord in yp.dims :
        if coord == zdim : new_coords.append (x.coords [pdim] .values)
        else             : new_coords.append (yp.coords[coord].values)

    ou_tab = xr.DataArray (np.empty (ou_shape), dims=ou_dims, coords=new_coords)

    # Interpolate
    for k in range (nk_ou) :
        # Find index of just above level
        idk1   = np.minimum ( (x[k]-xp), 0.).argmax (dim=zdim) # type: ignore
        idk2   = idk1 - 1
        idk2   = np.maximum (idk2, 0)

        x1     = xp[{zdim:idk1}]
        x2     = xp[{zdim:idk2}]

        dx1    = x[k] - x1
        dx2    = x2   - x[k]
        dx     = x2   - x1

        y1     = yp[{zdim:idk1}]
        y2     = yp[{zdim:idk2}]

        ou_tab [{pdim:k}] = (dx1*y2 + dx2*y1) / (dx1 + dx2)

    if name : ou_tab = ou_tab.rename ( {pdim:name} )

    pop_stack ( 'interp1d' )

    return ou_tab.squeeze()

def find_roots_np (x:np.ndarray, y:np.ndarray, Debug=True) -> float|np.ndarray :
    '''https://stackoverflow.com/questions/46909373/
    how-to-find-the-exact-intersection-of-a-curve-as-np-array-with-y-0'''
    s = np.abs(np.diff(np.sign(y))).astype(bool)

    z0_1 = x[:-1][s]
    z0_2 = np.diff(x)[s]
    z0_3 = y[1:][s]
    z0_4 = y[:-1][s]

    z0 = z0_1 + z0_2 / ( np.abs(z0_3/z0_4) + 1 )

    if OPTIONS['Debug'] or Debug :
        print ( 's   :', s    )
        print ( 'z0_1:', z0_1 )
        print ( 'z0_2:', z0_2 )
        print ( 'z0_3:', z0_3 )
        print ( 'z0_4:', z0_4 )

    return z0
    #return x[:-1][s] + np.diff(x)[s]/ ( np.abs(y[1:][s]/y[:-1][s]) + 1 )


def find_root (xc:xr.DataArray, ytab:xr.DataArray, y0:float|xr.DataArray=0.,
                dim:str|None=None, direction:str='forward', Debug=False) -> xr.DataArray :
    '''
    Find the x-coordinate where a tabulated function crosses a given y-value.
    
    This function identifies the point where ytab(x) = y0 by finding a sign change
    in (ytab - y0) along a specified dimension and performs linear interpolation
    between the bracketing points.

    Parameters
    ----------
    xc        : The x-coordinates corresponding to the tabulated function 
    ytab      : The tabulated function values y = f(x)
    y0        : The y-value for which to find the root. Default is 0.
                If xr.DataArray, must be broadcastable with ytab.
    dim       : The dimension along which to search for the root.
                If None, uses the first dimension of xc.
                Must be present in both xc and ytab.
                if None, use first dimension of xc
    direction search direction: 'forward' for the first root from the start,
                'backward' for the last root from the end. Default is 'forward'.
    Debug     : bool, optional
                If True, prints debug information about intermediate calculations.

    Adapted from 'https://stackoverflow.com/questions/46909373/
    how-to-find-the-exact-intersection-of-a-curve-as-np-array-with-y-0'
    to multidimenson xarrays.

    Return
    ------
    The interpolated x-coordinate where ytab crosses y0.
        Contains np.nan where no root is found.
        The dimension specified by `dim` is dropped from the result.

    Raises
    ------
    ValueError
        If dim is not found in ytab dimensions.
        If direction is not 'forward' or 'backward'.

    Notes
    -----
    - The function uses linear interpolation between adjacent points.
    - If y0_bef == y0_aft (flat region), x0_bef is returned without interpolation.
    - Results are set to NaN if no sign change is detected along the dimension.
       
    '''

    # Validate and set the dimension if not provided
    if dim is None :
        dim = xc.dims[0] # pyright: ignore[reportAssignmentType]
        if dim not in ytab.dims :
            raise ValueError ( f'{dim=} (first dim of xc) not found in ytab dimensions = {ytab.dims}' )
    else :
        if dim not in xc.dims :
            raise ValueError ( f'{dim=} not found in xc dimensions = {xc.dims}' )

        if dim not in ytab.dims :
            raise ValueError ( f'{dim=} not found in ytab dimensions = {ytab.dims}' )


    # Detect sign changes in (ytab - y0) along the specified dimension.
    # sc will be 1 where a sign change occurs, 0 elsewhere.
    sc = np.abs ( (np.sign(ytab-y0)).diff(dim=dim)).astype(int)

    if   'back' in  direction :
        # Search backward: find the LAST sign change
        # Fill non-sign-change positions with max+10 to push them to the end
        # Select last value of xc
        sb = sc.where (sc, sc[dim].max()+10) # filling
        first_pos = sb.argmin(dim=dim)
    elif 'forw' in  direction :
        # Search forward: find the FIRST sign change
        # Fill non-sign-change positions with min-10 to push them to the start
        sb = sc.where (sc, sc[dim].min()-10) # filling
        first_pos = sb.argmax(dim=dim)
    else :
        raise ValueError ( f'direction parameter should be "forward|backward". You give {direction=}' )

    # Extract the bracketing points (before and after the sign change)
    x0_bef = xc.isel   ({dim:first_pos})   # x-coordinate before the root
    x0_aft = xc.isel   ({dim:first_pos+1}) # x-coordinate after the root
    y0_bef = ytab.isel ({dim:first_pos})   # y-value before the root
    y0_aft = ytab.isel ({dim:first_pos+1}) # y-value after the root

    # Linear interpolation: x0 = x0_bef + (x0_aft - x0_bef) * (y0_bef - y0) / (y0_bef - y0_aft)
    # If the function is flat (y0_bef == y0_aft), use x0_bef directly
    x0 = xr.where (y0_bef==y0_aft, x0_bef, x0_bef + (x0_aft-x0_bef)*np.abs ( (y0_bef-y0)/(y0_bef-y0_aft) ) )

    # Set result to NaN where no sign change was detected
    x0 = x0.where ( sb.any(dim=dim), np.nan ) # Set to nan if no root is found

    # Remove the dimension coordinate from the result since it's no longer needed
    if dim in x0.coords :
        x0 = x0.drop_vars (dim)

    # Print debug information if requested
    if OPTIONS['Debug'] or Debug:
        print('sc        :', sc.values)          # Sign change indicator
        print('sb        :', sb.values)          # Filled sign change array
        print('first_pos :', first_pos.values)   # Index of the bracketing point
        print('x0_bef    :', x0_bef.values)      # x before root
        print('x0_aft    :', x0_aft.values)      # x after root
        print('y0_bef    :', y0_bef.values)      # y before root
        print('y0_aft    :', y0_aft.values)      # y after root

    return x0
