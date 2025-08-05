# -*- coding: utf-8 -*-
'''
plotIGCM : a few utilities for post processing

Author : olivier.marti@lsce.ipsl.fr

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
personal. Be warned that the author himself may not respect the
prerequisites.                                                                 
'''

from typing import Union

import numpy as np
import xarray as xr

from plotIGCM.options import OPTIONS
from plotIGCM.options import push_stack
from plotIGCM.options import pop_stack

rad = np.deg2rad(1.0)

full_name = {'tos':{'standard_name':'sea_surface_temperature', 'Title':'Sea surface temperature'},
     'sos':{'standard_name':'sea_surface_salinity'   , 'Title':'Sea surface salinity'   }
     }

def distance (lat1:Union[float,np.ndarray,xr.DataArray], lon1:Union[float,np.ndarray,xr.DataArray],
              lat2:Union[float,np.ndarray,xr.DataArray], lon2:Union[float,np.ndarray,xr.DataArray],
              radius:float=1.0, Debug:bool=False) -> Union[float,np.ndarray,xr.DataArray] :
    '''
    Compute distance on the sphere
    '''
    push_stack ( 'distance' )
    zlat1 = lat1.values if isinstance(lat1, xr.DataArray) else lat1
    zlon1 = lon1.values if isinstance(lon1, xr.DataArray) else lon1
    zlat2 = lat2.values if isinstance(lat2, xr.DataArray) else lat2
    zlon2 = lon2.values if isinstance(lon2, xr.DataArray) else lon2
    
    arg      = ( np.sin (np.deg2rad(zlat1)) * np.sin (np.deg2rad(zlat2))
               + np.cos (np.deg2rad(zlat1)) * np.cos (np.deg2rad(zlat2)) *
                 np.cos (np.deg2rad(zlon1-zlon2)) ) 
    
    zdistance = np.arccos (arg) * radius
    if OPTIONS['Debug'] or Debug :
        print ( f'1 - {zdistance = }' )

    if OPTIONS['Debug'] or Debug :
        print ( f'2 - {zdistance = }' )

    if OPTIONS['Debug'] or Debug :
        print ( f'3 - {zdistance = }' )

    if isinstance(lat1, xr.DataArray) :
        zdistance = xr.DataArray (zdistance, dims=lat1.dims, coords=lat1.coords)

    pop_stack ('distance')
    return zdistance

def aire_triangle (lat0: float|np.ndarray|xr.DataArray, lon0: float|np.ndarray|xr.DataArray,
                   lat1: float|np.ndarray|xr.DataArray, lon1: float|np.ndarray|xr.DataArray,
                   lat2: float|np.ndarray|xr.DataArray, lon2: float|np.ndarray|xr.DataArray, 
                   radius:float=1.0, Debug:bool=False) -> float|np.ndarray|xr.DataArray :
    '''
    Area of a triangle on the sphere
    Girard's formula
    '''
    push_stack ('aire_triangle')

    zlat0 = lat0.values if isinstance(lat0, xr.DataArray) else lat0
    zlon0 = lon0.values if isinstance(lon0, xr.DataArray) else lon0
    zlat1 = lat1.values if isinstance(lat1, xr.DataArray) else lat1
    zlon1 = lon1.values if isinstance(lon1, xr.DataArray) else lon1
    zlat2 = lat2.values if isinstance(lat2, xr.DataArray) else lat2
    zlon2 = lon2.values if isinstance(lon2, xr.DataArray) else lon2
    
    za = distance (zlat0 , zlon0, zlat1 , zlon1)
    zb = distance (zlat1 , zlon1, zlat2 , zlon2)
    zc = distance (zlat2 , zlon2, zlat0 , zlon0)

    if OPTIONS['Debug'] or Debug :
        print ( f'{za=}, {zb=}, {zc=}' )

    arg_alpha = (np.cos(za) - np.cos(zb)*np.cos(zc)) / (np.sin(zb)*np.sin(zc)) 
    arg_beta  = (np.cos(zb) - np.cos(za)*np.cos(zc)) / (np.sin(za)*np.sin(zc)) 
    arg_gamma = (np.cos(zc) - np.cos(za)*np.cos(zb)) / (np.sin(za)*np.sin(zb))

    if OPTIONS['Debug'] or Debug :
        print ( f'{arg_alpha=}, {arg_beta=}, {arg_gamma=}' )
    
    alpha = np.arccos (arg_alpha) 
    beta  = np.arccos (arg_beta ) 
    gamma = np.arccos (arg_gamma)

    if OPTIONS['Debug'] or Debug :
        print ( f'{alpha=}, {beta=}, {gamma=} {radius=}' )

    Saire = (alpha + beta + gamma - np.pi) * radius * radius

    if isinstance(lat1, xr.DataArray) :
        Saire = xr.DataArray (Saire, dims=lat1.dims, coords=lat1.coords)

    pop_stack ('aire_triangle')
    return Saire

def aire_quadri (lat0:float|np.ndarray|xr.DataArray, lon0:float|np.ndarray|xr.DataArray,
                 lat1:float|np.ndarray|xr.DataArray, lon1:float|np.ndarray|xr.DataArray,
                 lat2:float|np.ndarray|xr.DataArray, lon2:float|np.ndarray|xr.DataArray,
                 lat3:float|np.ndarray|xr.DataArray, lon3:float|np.ndarray|xr.DataArray,
                 radius:float=1.0) -> float|np.ndarray|xr.DataArray :
    '''
    Area of a quadrilatere on the sphere
    Girard's formula
    '''
    push_stack ('aire_quadri')
    Saire = aire_triangle (lat0, lon0, lat1, lon1, lat2, lon2, radius ) \
         + aire_triangle (lat2, lon2, lat3, lon3, lat0, lon0, radius )

    pop_stack ( 'aire_quadri')
    return Saire

def angle (latA:float|np.ndarray|xr.DataArray, lonA:float|np.ndarray|xr.DataArray,
           latB:float|np.ndarray|xr.DataArray, lonB:float|np.ndarray|xr.DataArray,
           latC:float|np.ndarray|xr.DataArray, lonC:float|np.ndarray|xr.DataArray,
           Debug:bool=False) -> float|np.ndarray|xr.DataArray :
    '''
    Angle between AB and AC
    
    '''
    push_stack ('angle')
    
    zlatA = latA.values if isinstance(latA, xr.DataArray) else latA
    zlonA = lonA.values if isinstance(lonA, xr.DataArray) else lonA
    zlatB = latB.values if isinstance(latB, xr.DataArray) else latB
    zlonB = lonB.values if isinstance(lonB, xr.DataArray) else lonB
    zlatC = latC.values if isinstance(latC, xr.DataArray) else latC
    zlonC = lonC.values if isinstance(lonC, xr.DataArray) else lonC
    
    za = distance (zlatB, zlonB, zlatC, zlonC)
    zb = distance (zlatA, zlonA, zlatC, zlonC)
    zc = distance (zlatA, zlonA, zlatB, zlonB)

    zarg1 = np.cos(za) - np.cos(zb)*np.cos(zc)
    zarg2 = np.sin(zb)*np.sin(zc)
    zarg2 = np.where ( zarg2 != 0, zarg2, np.nan)
    zarg = np.clip (zarg1 / zarg2, -1, 1)

    zA = np.arccos (zarg)
    
    if isinstance (latA, xr.DataArray) :
        zA = xr.DataArray (zA, dims=latA.dims, coords=latA.coords)

    pop_stack ('angle')
    return zA

def somme_4angles (lat0:float|np.ndarray|xr.DataArray, lon0:float|np.ndarray|xr.DataArray,
                   latA:float|np.ndarray|xr.DataArray, lonA:float|np.ndarray|xr.DataArray,
                   latB:float|np.ndarray|xr.DataArray, lonB:float|np.ndarray|xr.DataArray,
                   latC:float|np.ndarray|xr.DataArray, lonC:float|np.ndarray|xr.DataArray,
                   latD:float|np.ndarray|xr.DataArray, lonD:float|np.ndarray|xr.DataArray ) -> float|np.ndarray|xr.DataArray :
    '''
    Sum of angles from point 0 to all others in order : angle(0A,0B)+angle(0B,0C)+angle(0C,0D)+angle(0D,0A)
    Note : if 0 is inside the polygon (A,B,C,D), angle is close to 2*pi (slightly less on the sphere)
           if 0 is outside, it is close to 0.
    '''
    push_stack ( 'somme_4angles')
    zA = angle (lat0, lon0, latA, lonA, latB, lonB)
    zB = angle (lat0, lon0, latB, lonB, latC, lonC)
    zC = angle (lat0, lon0, latC, lonC, latD, lonD)
    zD = angle (lat0, lon0, latD, lonD, latA, lonA)

    zz = zA + zB + zC + zD

    pop_stack ('somme_4angles')
    return zz
    
def somme_angles (lat0:float|xr.DataArray, lon0:float|xr.DataArray,
                  lat:xr.DataArray, lon:xr.DataArray, Debug:bool=False, dim:str|None=None) -> xr.DataArray :
    '''
    Sum of angles from point 0 to all others in order : angle(0A,0B)+angle(0B,0C)+ ...
    Note : if 0 is inside the polygon (A,B,C,...), angle is close to 2*pi (slightly less on the sphere)
               if 0 is outside, it is close to 0.
    '''
    if dim is not None :
        edim = dim
    else : 
        if isinstance (lat0, xr.DataArray) :
            edim  = list(set(lat.dims) - set(lat0.dims))[0]
        else : 
            edim  = lat.dims
    nd    = lat.sizes[edim]
    
    zz = lat*0
    
    for nn in range (nd) :
        zz[{edim:nn}] = angle (lat0, lon0, lat.isel({edim:nn}), lon.isel({edim:nn}), lat.isel({edim:(nn+1)%nd}), lon.isel({edim:(nn+1)%nd}))
    
    zn = zz.sum(dim=edim) # type: ignore

    return zn
    
