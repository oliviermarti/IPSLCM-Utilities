# -*- coding: utf-8 -*-
# pylint: disable=too-many-positional-arguments, too-many-locals, too-many-arguments, invalid-name
"""
Compute daily insolation

Created on Thu Jun 17 15:20:13 2021
@Author: Didier Paillard. Adapted by Olivier Marti
"""

import copy
import time
from typing import Any, Self, Type
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
DEFAULT_OPTIONS = { 'Debug':False, 'Trace':False, 'Timing':False, 't0':None, 'Depth':0, 'Stack':[] }

OPTIONS: dict[str, Any] = copy.deepcopy(DEFAULT_OPTIONS)

class set_options :
    '''
    Set OPTIONS for libIGCM

    See Also :
    ----------
    reset_options, get_options

    '''
    def __init__ (self:Self, **kwargs) -> None :
        self.old = {}
        for k in kwargs :
            if k not in OPTIONS :
                raise ValueError ( f"argument name {k!r}"\
                                   f"is not in the set of valid OPTIONS {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update (kwargs)

    def _apply_update (self:Self, options_dict:dict) -> None :
        OPTIONS.update (options_dict)

    def __enter__(self: Self) -> None:
        return None

    def __exit__(self: Self, ztype: Type[BaseException]|None,
                 zvalue: BaseException|None,
                 ztraceback: Any|None) -> None:
        self._apply_update(self.old)

def get_options() -> dict[str, Any]:
    '''
    Get OPTIONS for libIGCM

    See Also :
    ----------
    set_options, reset_options
    '''
    return OPTIONS

def reset_options () :
    '''
    Reset OPTIONS to DEFAULT_OPTIONS for libIGCM

    See Also :
    ----------
    set_options, get_options

    '''
    return set_options (**DEFAULT_OPTIONS)

def return_stack() -> list[str]|str|int|bool|None:
    '''Return the current stack of function calls for libIGCM
    See Also :
    ----------
    set_options, get_options, reset_options, push_stack, pop_stack
    '''
    return OPTIONS['Stack']

def push_stack (string:str) -> None :
    '''Push a string on the stack of function calls for libIGCM
    See Also :
    ----------
    set_options, get_options, reset_options, return_stack, pop_stack
    '''
    OPTIONS['Depth'] += 1
    if OPTIONS['Trace'] :
        print ( '  '*(OPTIONS['Depth']-1), f'-->{__name__}.{string}' )
    #
    OPTIONS['Stack'].append (string)
    #
    if OPTIONS['Timing'] :
        if OPTIONS['t0'] :
            OPTIONS['t0'].append (time.time())
        else :
            OPTIONS['t0'] = [time.time(),]

def pop_stack (string:str) -> None :
    '''
    Pop a string from the stack of function calls for libIGCM
    See Also :
    ----------
    set_options, get_options, reset_options, return_stack, push_stack
    '''
    if OPTIONS['Timing'] :
        dt = time.time() - OPTIONS['t0'][-1]
        OPTIONS['t0'].pop()
    else :
        dt = None
    if OPTIONS['Trace'] or dt :
        if dt :
            if dt < 1e-3 :
                print ( '  '*(OPTIONS['Depth']-1), \
                        f'<--{__name__}.{string} : time: {dt*1e6:5.1f} micro s')
            else :
                if dt < 1 :
                    print ( '  '*(OPTIONS['Depth']-1), \
                        f'<--{__name__}.{string} : time: {dt*1e3:5.1f} milli s')
                else :
                    print ( '  '*(OPTIONS['Depth']-1), \
                        f'<--{__name__}.{string} : time: {dt*1:5.1f} second')
        else :
            print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string}')
    #
    OPTIONS['Depth'] -= 1
    OPTIONS['Stack'].pop ()
    #

# Astronomical functions
def daily_inso_longitude (lat:float|xr.DataArray, lon:float|xr.DataArray,
                          ecc:float=ECC, obl:float=OBL,
                          pre:float=PRE, solar:float=SOLAR) -> float|xr.DataArray :
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
    # True anomaly in radian (angle from perihelion)
    v_r = lon_r - np.pi - np.deg2rad (pre)
    # (a/r) = inverse of the distance to Sun (=focus) in astronomical units U.A.
    ar  = (1.0+ecc*np.cos(v_r))/(1.0-ecc*ecc)
    ar2 = ar*ar

    daily_inso = solar * ar2 * g/np.pi

    if isinstance (daily_inso, xr.DataArray) :
        daily_inso.attrs.update (
            {'units':'W.m-2', 'standard_name':'daily_insolation', 'long_name':'Daily insolation',} )

    return daily_inso

def solve_kepler_iter (m:float|np.ndarray|xr.DataArray,
                       ecc:float|np.ndarray|xr.DataArray=ECC, niter:int=NITER) :
    '''
    Solve Kepler equation : E - e sinE = m
    Use a fixed number of iterations
    '''
    ze = m
    # For a weak eccentricity (like for the Earth, <0.06) a few iterations are enough
    # (error < 5.10e-11 for 7 iterations; <10e-14 for 10 iterations)
    for _ in range (niter) :
        ze = m + ecc * np.sin (ze)

    return ze

def solve_kepler_prec (m:float|np.ndarray|xr.DataArray,
                       ecc:float|np.ndarray|xr.DataArray=ECC,
                       prec:float=PREC) -> float|np.ndarray|xr.DataArray :
    '''
    Solve Kepler equation : E - e sinE = m
    Iterate until error < prec
    '''
    ze = m
    error = 1.0
    while error > prec :
        ze     = m + ecc * np.sin (ze)
        error = np.max ( np.abs (m - (ze - ecc*np.sin(ze))) )
    return ze

def solve_kepler (m, ecc:float|np.ndarray|xr.DataArray=ECC, niter:None|int=None,
                  prec:None|float=None ) -> float|np.ndarray|xr.DataArray :
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
        print ( 'Error in solve_kepler' )
        print ( 'Only one of the two parameters niter and prec is allowed' )
        raise ValueError ( 'Only one of the two parameters niter and prec is allowed' )

    if niter is None and prec is None :
        niter = NITER

    if niter is None and prec is not None :
        zsolve_kepler = solve_kepler_prec (m, ecc=ecc, prec=prec  )
    else :
        zsolve_kepler = solve_kepler_iter (m, ecc=ecc,
                                           niter=niter) # pyright: ignore[reportArgumentType]

    return zsolve_kepler

def daily_inso_time (lat, t, ecc=ECC, obl=OBL, pre=PRE, solar=SOLAR):
    '''
    Daily insolation for a given latitute as the fraction
    of the year t, counted from the March equinox
    All angles in degrees

    Input :
    lat : latitude
    t   : time in fraction of year (in [0,1])
    '''

    # t in [0, 1] (t_r in [0, 2pi]).
    # For instance t = (day-80)/365 for a 365 day calendar, with equinox at day "80"
    t_r   = t*2.0*np.pi
    v0_r  = -np.pi - np.deg2rad (pre)       # true anomaly for longitude 0 (March equinox)
    a     = np.sqrt ((1.0-ecc)/(1.0+ecc))
    ze0   = 2.*np.arctan (a*np.tan(v0_r/2)) # eccentric anomaly for lon=0
    t0    = ze0 - ecc*np.sin (ze0)            # mean anomaly (time from perihelion) for lon=0
    ze     = solve_kepler (t_r + t0)         # eccentric anomaly at time t
    v_r   = 2.*np.arctan (np.tan(ze/2.0)/a)  # true anomaly
    lon_r = v_r + np.pi + np.deg2rad (pre)  # true longitude
    lon   = np.rad2deg (lon_r)

    zdaily_inso_time = daily_inso_longitude (lat, lon, ecc=ecc, obl=obl, pre=pre, solar=solar)

    if isinstance (zdaily_inso_time, xr.DataArray) :
        zdaily_inso_time.attrs.update (
            {'units':'W.m-2', 'standard_name':'daily_insolation', 'long_name':'Daily insolation',} )

    return zdaily_inso_time

def simple_calendar (day, equinox=EQUINOX, year_length=YEAR_LENGTH) :
    '''
    365 day calendar, with equinox at day "80"

    Input
    day : day of year (in [0,YEAR])
    '''
    return (day-equinox)/year_length
