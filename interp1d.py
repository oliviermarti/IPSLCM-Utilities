def interp1d (x, xp, yp, zdim) :
    '''
    One-dimensionnal interpolation of a multi-dimensionnal field

    Intended to interpolate on standard pressure level
    
    All inputs shoud be xarray data arrays

    Input : 
       x  : levels at wich we want to interpolat
       xp : position of the inpout points (i.e. pressure)
       yp : fields values at thes points (temperature, humidity, etc ..)
       zdim : name of the dimension that we want to interpolate
    '''
    import numpy as np, xarray as xr
    
    # Get the number of dimension with dim==zdim
    axis = list(xp.dims).index(zdim)
    
    # Get the number of levels in each arrays
    nk_in = xp.shape[axis]
    nk_ou = len (x)
    
    # Define the result array
    in_shape       = np.array (xp.shape)
    ou_shape       = np.array (in_shape)
    ou_shape[axis] = nk_ou
    
    in_dims        = list (yp.dims)
    ou_dims        = in_dims
    pdim           = x.dims[0]
    ou_dims[axis]  = pdim
    
    new_coords = []
    for coord in yp.dims :
        if coord == zdim : new_coords.append (x.coords[pdim].values)
        else             : new_coords.append (yp.coords[coord].values)
            
    ou_tab = xr.DataArray (np.empty (ou_shape), dims=ou_dims, coords=new_coords)
    
    # Interpolate
    for k in np.arange (nk_ou) :
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
        
        result = (dx1*y2 + dx2*y1) / ( dx1 + dx2 )
        
        # Put result in the final array
        ou_tab [{pdim:k}] = result

    return ou_tab.squeeze()
