# -*- coding: utf-8 -*-
"""
Compute daily insolation

Created on Thu Jun 17 15:20:13 2021
@Author: Didier Paillard. Adapted by Olivier Marti
"""

import time
import numpy as np
import xarray as xr

## Astronomical parameters
ECC     =   0.0167024   # Excentricity 0kBP (1950 CE)
OBL     =  23.4393      # Obliquity 0kBP (degrees)
PRE     = 102.918       # Climatic precession (degrees)
EQUINOX =  80.          # Day of March equinox

## Deliberate difference with Berger et al. (2010), who consider the SIDERAL_YEAR
YEAR_SIDERAL  = 365.25636
YEAR_TROPICAL = 365.24219876
YEAR_365      = 365.0
YEAR_366      = 366.0

YEAR_LENGTH   = YEAR_365

SOLAR = 1365.0          # Solar constant (W/m^2)

mth_length = np.array ( [31, 28, 31,  30,  31,  30,  31,  31,  30,  31,  30,  31] )
mth_start  = np.array ( [ 0, 31, 59,  90, 120, 151, 181, 212, 243, 273, 304, 334] )
#mth_end    = np.array ( [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365] ) 

# Internal parameters for solving the Kepler equation
NITER = 7
PREC  = 1.0E-7

# daily inso internal options
OPTIONS = dict (Debug=False, Trace=False, Timing=False, t0=None, Depth=0, Stack=[])

class set_options :
    """
    Set options for daily inso
    """
    def __init__ (self, **kwargs) :
        self.old = dict ()
        for k, v in kwargs.items() :
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update (self, options_dict) :
        OPTIONS.update (options_dict)
    def __enter__ (self) :
        return
    def __exit__ (self, type, value, traceback) :
        self._apply_update (self.old)

def get_options () -> dict :
    """
    Get options for nemo

    See Also
    ----------
    set_options

    """
    return OPTIONS

def return_stack () :
    return OPTIONS['Stack']

def push_stack (string:str) :
    OPTIONS['Depth'] += 1
    if OPTIONS['Trace'] :
        print ( '  '*(OPTIONS['Depth']-1), f'-->{__name__}.{string}' )
    #
    OPTIONS['Stack'].append (string)
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
            print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string}') # type: ignore
    #
    OPTIONS['Depth'] -= 1
    OPTIONS['Stack'].pop () # type: ignore
    #

# Astronomical functions
def daily_inso_longitude (lat, lon, ecc=ECC, obl=OBL, pre=PRE, solar=SOLAR) :
    '''
    Daily insolation for a given latitude and for true solar longitude 
    All angles in degrees

    Input : 
    lat : latitude
    lon : true longitude of the Sun (orbital position)
    '''
    
    lat_r   = np.deg2rad (lat)
    lon_r   = np.deg2rad (lon)
    
    obl_r   = np.deg2rad (obl)
    sin_lat = np.sin (lat_r)
    sin_lon = np.sin (lon_r)
    sin_obl = np.sin (obl_r)
    p = sin_lat*sin_lon*sin_obl
    s = np.maximum (0., 1. - sin_lat*sin_lat - sin_lon*sin_lon*sin_obl*sin_obl)
    d = np.sqrt (s+p*p)
    # d>0 in almost all cases. If d=0 then p = s = 0 et g = 0
    g   = np.where (d>0.0, p * np.arccos (-p/np.maximum (d, 1.E-99)) + np.sqrt (s), 0.0)
    v_r = lon_r - np.pi - np.deg2rad (pre)        # True anomaly in radian (angle from perihelion)
    ar  = (1.0+ecc*np.cos(v_r))/(1.0-ecc*ecc)  # (a/r) = inverse of the distance to Sun (=focus) in astronomical units U.A.
    ar2 = ar*ar

    daily_inso = solar * ar2 * g/np.pi

    if isinstance (daily_inso, xr.DataArray) :
        daily_inso.attrs.update ({'units':'W.m-2', 'standard_name':'daily_insolation', 'long_name':'Daily insolation',} )
    
    return daily_inso

def solve_Kepler_iter (m:float|np.ndarray|xr.DataArray, ecc:float|np.ndarray|xr.DataArray=ECC, niter:int=NITER) :
    '''
    Solve Kepler equation : E - e sinE = m
    Use a fixed number of iterations
    '''
    E = m
    for i in range (niter) :       # For a weak eccentricity (like for the Earth, <0.06) a few iterations are enough (error < 5.10e-11 for 7 iterations; <10e-14 for 10 iterations)
        E = m + ecc * np.sin (E)

    return E

def solve_Kepler_prec (m:float|np.ndarray|xr.DataArray, ecc:float|np.ndarray|xr.DataArray=ECC, prec:float=PREC) -> float|np.ndarray|xr.DataArray :
    '''
    Solve Kepler equation : E - e sinE = m
    Iterate until error < prec
    '''
    E = m
    error = 1.0
    while error > prec :
        E     = m + ecc * np.sin (E)
        error = np.max ( np.abs (m - (E - ecc*np.sin(E))) )
    return E

def solve_Kepler (m, ecc=ECC, niter:int|None=None, prec:float|None=None) :
    '''
    Solve Kepler equation : E - e sinE = m
    input :
       m
       ecc   : ecccentricity. Default=ECC
       niter : number of iterations (default value: NITER)
       prec  : absolute precision
       niter and prec are mutually exclusive. If none is given, niter=NITER is used
    '''
    
    if niter is not None and prec is not None :
        print ( 'Error in solve_Kepler' )
        print ( 'Only one of the two parameters niter and prec is allowed' )
        return None
    else :
        if niter is None and prec is None :
            niter = NITER
        if niter is None :
            solver_Kepler = solve_Kepler_prec (m, ecc=ECC, prec=prec  )
        if prec is None :
            solver_Kepler = solve_Kepler_iter (m, ecc=ECC, niter=niter)

        return solver_Kepler

def daily_inso_time (lat, t, ecc=ECC, obl=OBL, pre=PRE, solar=SOLAR):
    '''
    Daily insolation for a given latitute as the fraction of the year t, counted from the March equinox
    All angles in degrees

    Input : 
    lat : latitude
    t   : time in fraction of year (in [0,1])
    '''
    t_r   = t*2.0*np.pi                     # t in [0, 1] (t_r in [0, 2pi]). For instance t = (day-80)/365 for a 365 day calendar, with equinox at day "80"
    v0_r  = -np.pi - np.deg2rad (pre)       # true anomaly for longitude 0 (March equinox)
    a     = np.sqrt ((1.0-ecc)/(1.0+ecc))
    E0    = 2.*np.arctan (a*np.tan(v0_r/2)) # eccentric anomaly for lon=0
    t0    = E0 - ecc*np.sin (E0)            # mean anomaly (time from perihelion) for lon=0
    E     = solve_Kepler (t_r + t0)         # eccentric anomaly at time t
    v_r   = 2.*np.arctan (np.tan(E/2.0)/a)  # true anomaly
    lon_r = v_r + np.pi + np.deg2rad (pre)  # true longitude
    lon   = np.rad2deg (lon_r)

    daily_inso_time = daily_inso_longitude (lat, lon, ecc=ecc, obl=obl, pre=pre, solar=solar)

    if isinstance (daily_inso_time, xr.DataArray) :
        daily_inso_time.attrs.update ({'units':'W.m-2', 'standard_name':'daily_insolation', 'long_name':'Daily insolation',} )
    
    return daily_inso_time

def simple_calendar (day, equinox=EQUINOX, year_length=YEAR_LENGTH) :
    '''
    365 day calendar, with equinox at day "80"

    Input
    day : day of year (in [0,YEAR])
    '''
    
    simple_calendar = (day-equinox)/year_length
    return simple_calendar
