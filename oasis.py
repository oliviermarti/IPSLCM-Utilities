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
A few fonctionnalities of the OASIS coupler in Python

olivier.marti@lsce.ipsl.fr
'''
import sys, numpy as np, inspect

try    : import xarray as xr
except ImportError : pass
    
try    : import numba
except ImportError : pass
    
import time

rpi = np.pi ; rad = np.deg2rad (1.0) ; dar = np.rad2deg (1.0)

@numba.jit(forceobj=True)
def compute_links (remap_matrix, src_address, dst_address, src_grid_size, dst_grid_size, num_links):
    src_grid_target     = np.zeros ((src_grid_size,), dtype=int)
    src_grid_weight     = np.zeros ((src_grid_size,))

    dst_grid_target     = np.zeros ((dst_grid_size,), dtype=int)
    dst_grid_weight     = np.zeros ((dst_grid_size,))
    for link in np.arange (num_links) :
        if link%1000 == 0 : print ( link, end=' ' )
        src_grid_target[src_address[link]] += 1
        src_grid_weight[src_address[link]] += remap_matrix [link]
        dst_grid_target[dst_address[link]] += 1
        dst_grid_weight[dst_address[link]] += remap_matrix [link]
    return src_grid_target, src_grid_weight, dst_grid_target, dst_grid_weight

    
@numba.jit(forceobj=True)
def rmp_remap (ptab, d_rmp, sval=np.nan, verbose=False ) :
    '''
    Remap a field using OASIS rmpfile

    Inputs :
      ptab  : field to interpolate. Should be an xarray Data Array
          ptab dimensions are [...., y, x]
          y, x are geographical positions

      d_rmp : an xarray dataset corresponding to a rmp file 
          Weight files are at OASIS-MCT format (matching ESMF or CDO weights files format)

      sval : value for destinations points with no value assigned by the interpolation
    '''

    print (__name__ + '.rmp_remap :  Read rmp file')
    num_links      = d_rmp.dims ['num_links']
    src_grid_size  = d_rmp.dims ['src_grid_size']
    dst_grid_size  = d_rmp.dims ['dst_grid_size']
    # address in rmp file are in Fortran convention : starting a 1
    # Here we shift to python/C convention : starting at 0
    src_address    = d_rmp ['src_address'].values - 1
    dst_address    = d_rmp ['dst_address'].values - 1
    remap_matrix   = d_rmp ['remap_matrix'][:,0].values

    # Get dimensions of source and destination field
    src_ny, src_nx = d_rmp ['src_grid_dims'].values
    dst_ny, dst_nx = d_rmp ['dst_grid_dims'].values

    if ptab.shape[-2:] != (src_ny, src_nx) :
        print ('ptab dimensions : ', ptab.shape[-2:])
        print ('expected source dimensions in rmp file : ', src_ny, src_ny)
        print ('Dimensions do not match')
        raise Exception ("Error in module: " + __name__ + ", file: " + __file__ + ", function: " + rmp_remap.__name__)
       
    if verbose : print ('grid sizes      : ', src_grid_size, dst_grid_size)
    if verbose : print ('num_links       : ', num_links)
    if verbose : print ('address sizes   : ', src_address.shape, dst_address.shape, remap_matrix.shape)
    if verbose : print ('src dimensions  : ', src_ny, src_nx)
    if verbose : print ('dst dimensions  : ', dst_ny, dst_nx)

    # Get information to create the destination field
    src_shape_2D   = list (ptab.shape)
    dst_shape_2D   = src_shape_2D[:-2] + [dst_ny, dst_nx]
    if verbose : print ('shapes  2D      : ', src_shape_2D, dst_shape_2D)   

    src_shape_1D = src_shape_2D[:-2] + [src_ny*src_nx]
    dst_shape_1D = dst_shape_2D[:-2] + [dst_ny*dst_nx]
    if verbose : print ('shapes  1D      : ', src_shape_1D, dst_shape_1D)   
    
    src_dims_2D = list (ptab.dims) ; 
    src_dims_1D = src_dims_2D[:-2] + ['xy']  
  
    dst_dims_2D = list (src_dims_2D[:-2])
    dst_dims_2D = dst_dims_2D + ['y', 'x']
    dst_dims_1D = dst_dims_2D[:-2] + ['xy']
    
    if verbose : print ('dims 2D         : ', src_dims_2D, dst_dims_2D)
    if verbose : print ('dims 1D         : ', src_dims_1D, dst_dims_1D)
        
    src_coords_2D = ptab.coords
    dst_coords_2D = []
    for dim in src_dims_2D[:-2] :
        dst_coords_2D.append (src_coords_2D[dim])
    dst_coords_2D = dst_coords_2D + [np.arange(dst_ny), np.arange(dst_nx)]
    
    src_field_1D = ptab.stack (xy=src_dims_2D[-2:]).values
    dst_field_1D = np.zeros (dst_shape_1D)

    ## Creates an array to mask destinations points with no value assigned by the interpolation
    dst_mask_1D = np.full (dst_shape_1D, np.nan)
    
    if verbose : print ("shape fields 1D : ", src_field_1D.shape, dst_field_1D.shape, dst_mask_1D.shape)
    if verbose : print ("shape fields 1D : ", np.prod(src_field_1D.shape), np.prod(dst_field_1D.shape), np.prod(dst_mask_1D.shape) )

    # Interpolate
    dst_field_1D = remap ( src_field_1D, src_grid_size, dst_grid_size, num_links, src_address, dst_address, remap_matrix, sval = np.nan, verbose = True )
        
    dst_field_2D = np.reshape   (dst_field_1D, dst_shape_2D)
    dst_field_2D = xr.DataArray (dst_field_2D, dims=dst_dims_2D, coords=dst_coords_2D)

    # Copy attributes from source field to destination
    for attr in ptab.attrs :
        dst_field_2D.attrs [attr] = ptab.attrs [attr]

    if verbose : print ("End of " + __name__ + ".rmp_remap")   
    return dst_field_2D

@numba.jit(forceobj=True)
def progress (percent=0, width=30) :
        left  = (width * percent) // 100
        right = width - left
        #print ('\r[', '#' * left, ' ' * right, ']', f' {percent:.0f}%',  sep='', end='', flush=True)
        print ( '\r[', '#' * left, ' ' * right, '] {:4d}%'.format(percent),  sep='', end='', flush=True)

@numba.jit(forceobj=True)
def remap ( src_field, src_grid_size, dst_grid_size, num_links, src_address, dst_address, remap_matrix, sval = np.nan, verbose = True ) :
    '''
    Remap a field using interpolation weights and addresses

    Inputs :
      src_field  : field to interpolate
          ptab dimensions are [...., x]
          x is the geographical positions

      src_grid_size : last dimension of src_field : input grid size
      dst_grid_size : output grid size
      num_links     : number of interpolation links
      src_address   : address of source point for each link
      dst_address   : address of destination point for each link
      remap_matrix  : interpolation weights
      sval          : value of non reached point on te destiantion grid
      verbose       : 

      All addresses should be in python/C convention : starting at 0

    '''
    width=80
    
    src_shape = src_field.shape
    dst_shape = ( *src_shape[:1], dst_grid_size)
    
    dst_field = np.zeros ( (dst_shape) )
    dst_mask  = np.full  ( (dst_shape), np.nan)
     
    if verbose :
        print ("\nStarting interpolation")
    t_start = time.time ()
    t_0 = t_start
   
    for link in np.arange (num_links) :
        if verbose :
            if link%(num_links//100) == 0 :
                t_1 = time.time ()
                if t_1 > t_0 + 0.6 :
                    progress ( percent = np.minimum ( 100, int(link/num_links*100) ), width=width)
                    t_0 = t_1
        dst_mask  [..., dst_address [link]] = 1.0
        dst_field [..., dst_address [link]] += remap_matrix[link] * src_field[..., src_address[link]]
    t_end = time.time ()
    if verbose : progress (percent=100, width=width)
    
    if verbose :
        print ("\nInterpolation time : {:5.3}s".format (t_end-t_start))
        print (" ")
        
    dst_field = np.where ( np.isnan(dst_mask), sval, dst_field)

    return dst_field

@numba.jit(forceobj=True)
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

@numba.jit(forceobj=True)
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

## Sommes des poids à l'arrivée
@numba.jit(forceobj=True)
def sum_matrix (rmp) :
    '''
    Computes sum of weights on souce and destination points

    rmp : an xarray dataset corresponding to a rmp file 
          Weight files are at OASIS-MCT format (matching ESMF or CDO weights files format)
    '''
    src_sum_matrix = np.zeros ( (rmp.dims['src_grid_size'],) )
    dst_sum_matrix = np.zeros ( (rmp.dims['dst_grid_size'],) )
    for n in rmp['num_links'].values :
        src_a = rmp['src_address'][n]
        dst_a = rmp['dst_address'][n]
        src_sum_matrix[src_a-1] += rmp['remap_matrix'][n]
        dst_sum_matrix[dst_a-1] += rmp['remap_matrix'][n]
    return src_sum_matrix, dst_sum_matrix

## ===========================================================================
##
##                               That's all folk's !!!
##
## ===========================================================================
