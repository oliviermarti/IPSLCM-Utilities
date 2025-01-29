# -*- coding: utf-8 -*-
'''
Utilities 1D vertical interpolation

authoir: olivier.marti@lsce.ipsl.fr

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

import time
import numpy as np, xarray as xr
from libIGCM.utils import Container, OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack
#from numba import jit

def interp1d (x:float, xp:float, yp:float, zdim:str, name=None) :
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

    # Get the number of dimension with dim==zdim
    axis           = list (xp.dims).index (zdim)

    # Get the number of levels in each arrays
    nk_in          = xp.shape[axis]
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
        raise Exception( 'interp1d : Coordinate not monotonic')
    else : 
        if ( dx.min() > 0. and dx.max()> 0. ) : or_up=True
        if ( dx.min() < 0. and dx.max()< 0. ) : or_up=False

    if or_up :
        x  = -x ; xp = -xp
        
    # Define the result array 
    new_coords = []
    for coord in yp.dims :
        if coord == zdim : new_coords.append (x.coords [pdim] .values)
        else             : new_coords.append (yp.coords[coord].values)


    ou_tab = xr.DataArray (np.empty (ou_shape), dims=ou_dims, coords=new_coords)

    # Interpolate
    for k in np.arange (nk_ou) :
        t0 = time.time ()
        # Find index of just above level
        idk1   = np.minimum ( (x[k]-xp), 0.).argmax (dim=zdim)
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
