#
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
Utilities to compute on the sphere

Author: olivier.marti@lsce.ipsl.fr

## SVN information
Author   = "$Author:  $"
Date     = "$Date: $"
Revision = "$Revision: $"
Id       = "$Id: $"
HeadURL  = "$HeadURL: $"
'''

import numpy as np
import xarray as xr
  
RPI   = np.pi
RAD   = np.deg2rad (1.0)
DAR   = np.rad2deg (1.0)
REPSI = np.finfo (1.0).eps

def distance (lat1:float, lon1:float, lat2:float, lon2:float, radius:float=1.0) -> float :
    '''
    Compute distance on the sphere
    '''
    arg      = ( np.sin (RAD*lat1) * np.sin (RAD*lat2)
               + np.cos (RAD*lat1) * np.cos (RAD*lat2) *
                 np.cos(RAD*(lon1-lon2)) )
    
    zdistance = np.arccos (arg) * radius
    
    return zdistance

def aire_triangle (lat0:float, lon0:float, lat1:float, lon1:float, lat2:float, lon2:float) -> float :
    '''
    Area of a triangle on the sphere
    Girard's formula
    '''
    
    a = distance (lat0 , lon0, lat1 , lon1)
    b = distance (lat1 , lon1, lat2 , lon2)
    c = distance (lat2 , lon2, lat0 , lon0)

    arg_alpha = (np.cos(a) - np.cos(b)*np.cos(c)) / ( np.sin(b)*np.sin(c) ) 
    arg_beta  = (np.cos(b) - np.cos(a)*np.cos(c)) / ( np.sin(a)*np.sin(c) ) 
    arg_gamma = (np.cos(c) - np.cos(a)*np.cos(b)) / ( np.sin(a)*np.sin(b) ) 

    alpha = np.arccos (arg_alpha) 
    beta  = np.arccos (arg_alpha) 
    gamma = np.arccos (arg_alpha)

    Saire = (alpha + beta + gamma - np.pi)

    return Saire

def aire_quadri (lat0:float, lon0:float, lat1:float, lon1:float, lat2:float, lon2:float, lat3:float, lon3:float) -> float :
    '''
    Area of a quadrilatere on the sphere
    Girard's formula
    '''
    
    Saire = aire_triangle (lat0, lon0, lat1, lon1, lat2, lon2 ) \
          + aire_triangle (lat2, lon2, lat3, lon3, lat0, lon0)
          
    return Saire
