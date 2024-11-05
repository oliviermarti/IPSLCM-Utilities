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

import time
import sys, numpy as np, xarray as xr

rpi = np.pi ; rad = np.deg2rad (1.0) ; dar = np.rad2deg (1.0)

class Container :
    ''' 
    Void class to act as a container
    Class members can be accessed either with dictionnary or namespace syntax
       i.e  <Container>['member'] or <Container>.member
    '''
    def update (self, dico=None, **kwargs):
        '''Use a dictionnary to update values'''
        if dico : 
            for attr in dico.keys () : super().__setattr__(attr, dico[attr])
        self.__dict__.update (kwargs)
    def keys    (self) : return self.__dict__.keys()
    def values  (self) : return self.__dict__.values()
    def items   (self) : return self.__dict__.items()
    def dict    (self) : return self.__dict__
    ## Hidden functions
    def __str__     (self) : return str  (self.__dict__)
    def __repr__    (self) : return repr (self.__dict__)
    def __name__    (self) : return self.__class__.__name__
    def __getitem__ (self, attr) : return getattr (self, attr)
    def __setitem__ (self, attr, value) : setattr (self, attr, value)
    def __iter__    (self) : return self.__dict__.__iter__()
    def __next__    (self) : return self.__dict__.__next__()
    def __len__     (self) : return len (self.__dict__)
    def __init__ (self, **kwargs) :
        for attr, value in kwargs.items () :
            super().__setattr__(attr, value)

# Variables exchanged between ocean and atmosphere in IPSL coupled model
o2a = [
    ['O_SSTSST' , 'SISUTESW'] ,
    ['OIceFrc'  , 'SIICECOV'] ,
    ['O_TepIce' , 'SIICTEMW'] ,
    ['O_AlbIce' , 'SIICEALW'] ,
    ['O_OCurx1' , 'CURRENTX'] ,
    ['O_OCury1' , 'CURRENTY'] ,
    ['O_OCurz1' , 'CURRENTZ'] ]
a2o = [
    ['COTAUXXU' , 'O_OTaux1'] ,
    ['COTAUYYU' , 'O_OTauy1'] ,
    ['COTAUZZU' , 'O_OTauz1'] ,
    ['COTAUXXV' , 'O_OTaux2'] ,
    ['COTAUYYV' , 'O_OTauy2'] ,
    ['COTAUZZV' , 'O_OTauz2'] ,
    ['COWINDSP' , 'O_Wind10'] ,
    ['COTOTRAI' , 'OTotRain'] ,
    ['COTOTSNO' , 'OTotSnow'] ,
    ['COTOTEVA' , 'OTotEvap'] ,
    ['COICEVAP' , 'OIceEvap'] ,
    ['COQSRMIX' , 'O_QsrMix'] ,
    ['COQNSMIX' , 'O_QnsMix'] ,
    ['COSHFICE' , 'O_QsrIce'] ,
    ['CONSFICE' , 'O_QnsIce'] ]

# Build dictionnaries for correspondance between ocean and atmosphere variables.
a2o_d = Container () ; a2o_r = Container ()
for avar, ovar in a2o :
    a2o_d.update ({avar:ovar})
    a2o_r.update ({ovar:avar})

o2a_d = {} ; o2a_r = {}
for ovar, avar in o2a :
    o2a_d.update ({ovar:avar})
    o2a_r.update ({avar:ovar})

# OASIS internal options
OPTIONS = { 'Debug':False, 'Trace':False, 'Timing':None, 't0':None, 'Depth':None, 'Stack':None }

class set_options :
    """
    Set options for oasis
    """
    def __init__ (self, **kwargs) :
        self.old = {}
        for k, v in kwargs.items() :
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update (self, options_dict) : OPTIONS.update (options_dict)
    def __enter__ (self) : return
    def __exit__ (self, type, value, traceback) : self._apply_update (self.old)

def get_options () -> dict :
    """
    Get options for oasis

    See Also
    ----------
    set_options

    """
    return OPTIONS

def return_stack () :
    return OPTIONS['Stack']

def push_stack (string:str) :
    if OPTIONS['Depth'] : OPTIONS['Depth'] += 1
    else                : OPTIONS['Depth'] = 1
    if OPTIONS['Trace'] : print ( '  '*(OPTIONS['Depth']-1), f'-->{__name__}.{string}' )
    #
    if OPTIONS['Stack'] : OPTIONS['Stack'].append (string)
    else                : OPTIONS['Stack'] = [string,]
    #
    if OPTIONS['Timing'] :
        if OPTIONS['t0'] :
            OPTIONS['t0'].append ( time.time() )
        else :
            OPTIONS['t0'] = [ time.time(), ]

def pop_stack (string:str) :
    if OPTIONS['Timing'] :
        dt = time.time() - OPTIONS['t0'][-1]
        OPTIONS['t0'].pop()
    else :
        dt = None
    if OPTIONS['Trace'] or dt :
        if dt : 
            if dt < 1e-3 : 
                print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string} : time: {dt*1e6:5.1f} micro s')
            if dt >= 1e-3 and dt < 1 : 
                print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string} : time: {dt*1e3:5.1f} milli s')
            if dt >= 1 : 
                print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string} : time: {dt*1:5.1f} second')
        else : 
            print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string}')
    #
    OPTIONS['Depth'] -= 1
    if OPTIONS['Depth'] == 0 : OPTIONS['Depth'] = None
    OPTIONS['Stack'].pop ()
    if OPTIONS['Stack'] == list () : OPTIONS['Stack'] = None
    #

## ===========================================================================
def compute_links (remap_matrix, src_address, dst_address, src_grid_size, dst_grid_size, num_links) :
    push_stack ( f'compute_links ( remap_matrix, src_address, dst_address, {src_grid_size=}, {dst_grid_size=}, {num_links=} )' )
    
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

    pop_stack ( 'compute_links')
    return src_grid_target, src_grid_weight, dst_grid_target, dst_grid_weight

def rmp_remap (ptab, d_rmp, sval=np.nan) :
    '''
    Remap a field using OASIS rmpfile

    Inputs :
      ptab  : field to interpolate. Should be an xarray Data Array
          ptab dimensions are [...., y, x]
          y, x are geographical positions

      d_rmp : an xarray dataset corresponding to a rmp file 
          Weight files are at OASIS-MCT format (matching ESMF or CDO weights files format)

      sval : value of destinations points with no value assigned by the interpolation
    '''

    push_stack ( f'rmp_remap :  Read rmp file')
    
    num_links      = d_rmp.sizes ['num_links']
    src_grid_size  = d_rmp.sizes ['src_grid_size']
    dst_grid_size  = d_rmp.sizes ['dst_grid_size']
    # Address in rmp file are in Fortran convention : starting a 1
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
       
    if OPTIONS['Debug'] : print ('grid sizes      : ', src_grid_size, dst_grid_size)
    if OPTIONS['Debug'] : print ('num_links       : ', num_links)
    if OPTIONS['Debug'] : print ('address sizes   : ', src_address.shape, dst_address.shape, remap_matrix.shape)
    if OPTIONS['Debug'] : print ('src dimensions  : ', src_ny, src_nx)
    if OPTIONS['Debug'] : print ('dst dimensions  : ', dst_ny, dst_nx)

    # Get information to create the destination field
    src_shape_2D   = list (ptab.shape)
    dst_shape_2D   = src_shape_2D[:-2] + [dst_ny, dst_nx]
    if OPTIONS['Debug'] : print ('shapes  2D      : ', src_shape_2D, dst_shape_2D)   

    src_shape_1D = src_shape_2D[:-2] + [src_ny*src_nx]
    dst_shape_1D = dst_shape_2D[:-2] + [dst_ny*dst_nx]
    if OPTIONS['Debug'] : print ('shapes  1D      : ', src_shape_1D, dst_shape_1D)   
    
    src_dims_2D = list (ptab.dims) ; 
    src_dims_1D = src_dims_2D[:-2] + ['xy']  
  
    dst_dims_2D = list (src_dims_2D[:-2])
    dst_dims_2D = dst_dims_2D + ['y', 'x']
    dst_dims_1D = dst_dims_2D[:-2] + ['xy']
    
    if OPTIONS['Debug'] : print ('dims 2D         : ', src_dims_2D, dst_dims_2D)
    if OPTIONS['Debug'] : print ('dims 1D         : ', src_dims_1D, dst_dims_1D)
        
    src_coords_2D = ptab.coords
    dst_coords_2D = []
    for dim in src_dims_2D[:-2] :
        dst_coords_2D.append (src_coords_2D[dim])
    dst_coords_2D = dst_coords_2D + [np.arange(dst_ny), np.arange(dst_nx)]
    
    src_field_1D = ptab.stack (xy=src_dims_2D[-2:]).values
    dst_field_1D = np.zeros (dst_shape_1D)

    ## Creates an array to mask destinations points with no value assigned by the interpolation
    dst_mask_1D = np.full (dst_shape_1D, np.nan)
    
    if OPTIONS['Debug'] : print ("shape fields 1D : ", src_field_1D.shape, dst_field_1D.shape, dst_mask_1D.shape)
    if OPTIONS['Debug'] : print ("shape fields 1D : ", np.prod(src_field_1D.shape), np.prod(dst_field_1D.shape), np.prod(dst_mask_1D.shape) )

    # Interpolate
    dst_field_1D = remap ( src_field_1D, src_grid_size, dst_grid_size, num_links, src_address, dst_address, remap_matrix, sval = np.nan )
        
    dst_field_2D = np.reshape   (dst_field_1D, dst_shape_2D)
    dst_field_2D = xr.DataArray (dst_field_2D, dims=dst_dims_2D, coords=dst_coords_2D)

    # Copy attributes from source field to destination
    for attr in ptab.attrs :
        dst_field_2D.attrs [attr] = ptab.attrs [attr]

    pop_stack ( "rmp_remap")   
    return dst_field_2D

def progress (percent=0, width=30) :
        left  = (width * percent) // 100
        right = width - left
        #print ('\r[', '#' * left, ' ' * right, ']', f' {percent:.0f}%',  sep='', end='', flush=True)
        print ( '\r[', '#' * left, ' ' * right, '] {:4d}%'.format(percent),  sep='', end='', flush=True)

def remap (src_field, src_grid_size, dst_grid_size, num_links, src_address, dst_address, remap_matrix, sval=np.nan) :
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

      All addresses should be in python/C convention : starting at 0

    '''
    push_stack ( f'remap ( src_field, {src_grid_size=}, {dst_grid_size=}, {num_links=}, src_address, dst_address, remap_matrix, {sval=}' )
    width=80
    
    src_shape = src_field.shape
    dst_shape = (*src_shape[:1], dst_grid_size)
    
    dst_field = np.zeros ( (dst_shape) )
    dst_mask  = np.full  ( (dst_shape), np.nan)
     
    if OPTIONS['Debug'] : print ("\nStarting interpolation")
    t_start = time.time ()
    t_0 = t_start
   
    for link in np.arange (num_links) :
        if OPTIONS['Debug'] :
            if link%(num_links//100) == 0 :
                t_1 = time.time ()
                if t_1 > t_0 + 0.6 :
                    progress ( percent = np.minimum ( 100, int(link/num_links*100) ), width=width)
                    t_0 = t_1
        dst_mask  [..., dst_address [link]] = 1.0
        dst_field [..., dst_address [link]] += remap_matrix[link] * src_field[..., src_address[link]]
    t_end = time.time ()
    if OPTIONS['Debug'] : progress (percent=100, width=width)
    
    if OPTIONS['Debug'] :
        print ("\nInterpolation time : {:5.3}s".format (t_end-t_start))
        print (" ")
        
    dst_field = np.where (np.isnan(dst_mask), sval, dst_field)

    pop_stack ( 'remap' )
    return dst_field

def geo2en (pxx, pyy, pzz, glam, gphi) : 
    '''
    Change vector from geocentric to east/north

    Inputs :
        pxx, pyy, pzz : components on the geocentric system
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( f'geo2en (pxx, pyy, pzz, glam, gphi)' )
    
    gsinlon = np.sin (rad * glam)
    gcoslon = np.cos (rad * glam)
    gsinlat = np.sin (rad * gphi)
    gcoslat = np.cos (rad * gphi)
          
    pte = - pxx * gsinlon            + pyy * gcoslon
    ptn = - pxx * gcoslon * gsinlat  - pyy * gsinlon * gsinlat + pzz * gcoslat

    pop_stack ( 'geo2en' )
    return pte, ptn

def en2geo (pte, ptn, glam, gphi) :
    '''
    Change vector from east/north to geocentric

    Inputs : 
        pte, ptn : eastward/northward components
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( f'en2geo (pte, ptn, glam, gphi)' )
    gsinlon = np.sin (rad * glam)
    gcoslon = np.cos (rad * glam)
    gsinlat = np.sin (rad * gphi)
    gcoslat = np.cos (rad * gphi)

    pxx = - pte * gsinlon - ptn * gcoslon * gsinlat
    pyy =   pte * gcoslon - ptn * gsinlon * gsinlat
    pzz =   ptn * gcoslat

    pop_stack ( 'en2geo' )
    return pxx, pyy, pzz

## Sommes des poids à l'arrivée
def sum_matrix (rmp) :
    '''
    Computes sum of weights on souce and destination points

    rmp : an xarray dataset corresponding to a rmp file 
          Weight files are at OASIS-MCT format (matching ESMF or CDO weights files format)
    '''
    push_stack ( f'sum_matrix (rmp)' )
    
    src_sum_matrix = np.zeros ( (rmp.dims['src_grid_size'],) )
    dst_sum_matrix = np.zeros ( (rmp.dims['dst_grid_size'],) )
    for n in rmp['num_links'].values :
        src_a = rmp['src_address'][n]
        dst_a = rmp['dst_address'][n]
        src_sum_matrix[src_a-1] += rmp['remap_matrix'][n]
        dst_sum_matrix[dst_a-1] += rmp['remap_matrix'][n]

    pop_stack ( 'sum_matrix' )
    return src_sum_matrix, dst_sum_matrix

## ===========================================================================
##
##                               That's all folk's !!!
##
## ===========================================================================
