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

import copy
import time
import numpy as np
import xarray as xr

from libIGCM.utils import OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack

full_name = {'tos':{'standard_name':'sea_surface_temperature', 'Title':'Sea surface temperature'},
     'sos':{'standard_name':'sea_surface_salinity'   , 'Title':'Sea surface salinity'   }
     }

def distance (lat1:float, lon1:float, lat2:float, lon2:float, radius:float=1.0, Debug=False) -> float :
    '''
    Compute distance on the sphere
    '''
    arg      = ( np.sin (np.deg2rad(lat1)) * np.sin (np.deg2rad(lat2))
               + np.cos (np.deg2rad(lat1)) * np.cos (np.deg2rad(lat2)) *
                 np.cos (np.deg2rad(lon1-lon2)) ) 
    
    zdistance = np.arccos (arg) * radius
    if OPTIONS['Debug'] or Debug :
        print ( f'1 - {zdistance.values = }' )

    if OPTIONS['Debug'] or Debug :
        print ( f'2 - {zdistance.values = }' )

    if OPTIONS['Debug'] or Debug :
        print ( f'3 - {zdistance.values = }' )

    return zdistance

def aire_triangle (lat0: float, lon0: float, lat1: float, lon1: float, lat2: float, lon2: float, 
                   radius:float=1.0, Debug:bool=False) -> float :
    '''
    Area of a triangle on the sphere
    Girard's formula
    '''
    
    a = distance (lat0 , lon0, lat1 , lon1)
    b = distance (lat1 , lon1, lat2 , lon2)
    c = distance (lat2 , lon2, lat0 , lon0)

    if OPTIONS['Debug'] or Debug :
        print ( f'{a=}, {b=}, {c=}' )

    arg_alpha = (np.cos(a) - np.cos(b)*np.cos(c)) / (np.sin(b)*np.sin(c)) 
    arg_beta  = (np.cos(b) - np.cos(a)*np.cos(c)) / (np.sin(a)*np.sin(c)) 
    arg_gamma = (np.cos(c) - np.cos(a)*np.cos(b)) / (np.sin(a)*np.sin(b))

    if OPTIONS['Debug'] or Debug :
        print ( f'{arg_alpha=}, {arg_beta=}, {arg_gamma=}' )
    
    alpha = np.arccos (arg_alpha) 
    beta  = np.arccos (arg_beta ) 
    gamma = np.arccos (arg_gamma)

    if OPTIONS['Debug'] or Debug :
        print ( f'{alpha=}, {beta=}, {gamma=} {radius=}' )

    Saire = (alpha + beta + gamma - np.pi) * radius * radius

    return Saire

def aire_quadri (lat0:float, lon0:float, lat1:float, lon1:float, lat2:float, lon2:float, lat3:float, lon3:float, radius:float=1.0) -> float :
    '''
    Area of a quadrilatere on the sphere
    Girard's formula
    '''
    
    Saire = aire_triangle (lat0, lon0, lat1, lon1, lat2, lon2, radius ) \
          + aire_triangle (lat2, lon2, lat3, lon3, lat0, lon0, radius )
          
    return Saire

