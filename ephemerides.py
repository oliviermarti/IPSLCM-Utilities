'''
Compute time of sun rise and sun set, given a day and a geographical position

(http://www.softrun.fr/index.php/bases-scientifiques/heure-de-lever-et-de-coucher-du-soleil)

All computation are approximate, with an error of a few minutes

More details here : http://jean-paul.cornec.pagesperso-orange.fr/heures_lc.htm

Details for exact computation : https://www.imcce.fr/en/grandpublic/systeme/promenade/pages3/367.html

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
import copy
import numpy as np
import xarray as xr
import cftime
from libIGCM_utils import Container

deg2rad = np.deg2rad (1.0)
rad2deg = np.rad2deg (1.0)

day2deg  = 360.0/365.25
min2hour = 1./60.
lon2hour = 24./360.

mth_length = np.array ( [31, 28, 31,  30,  31,  30,  31,  31,  30,  31,  30,  31] )
mth_start  = np.array ( [ 0, 31, 59,  90, 120, 151, 181, 212, 243, 273, 304, 334] )
mth_end = mth_start + mth_length + 1 # A cause des bornes superieures de Python

month_names = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
month_Names = list (map (lambda x: x.capitalize(), month_names))
month_NAMES = list (map (lambda x: x.upper     (), month_names))

mth_names   = list (map (lambda x: x[0:3], month_names))
mth_Names   = list (map (lambda x: x.capitalize(), mth_names))
mth_NAMES   = list (map (lambda x: x.upper     (), mth_names))

month_noms  = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
month_Noms  = list (map (lambda x: x.capitalize(), month_noms ))
month_NOMS  = list (map (lambda x: x.upper     (), month_noms ))

mth_noms  = list (map (lambda x: x[0:3], month_noms))
mth_Noms  = list (map (lambda x: x.capitalize(), mth_noms ))
mth_NOMS  = list (map (lambda x: x.upper     (), mth_noms ))

month_Ini = list (map (lambda x: x[0], month_NOMS )) # Juste les initiales
month_ini = list (map (lambda x: x[0], month_noms ))

SliceSE = { 'Annual':slice(0,12),
            'DJF' :slice(11,14), 'MAM' :slice(2,5), 'JJA' :slice(5,8), 'SON' :slice(8,11), 
            'DJFM':slice(11,15), 'MAMJ':slice(2,6), 'JJAS':slice(5,9), 'SOND':slice(8,12),
            'JAN':slice(0), 'FEB':slice(1), 'MAR':slice(2), 'APR':slice(3), 'MAY':slice( 4), 'JUN':slice( 5),
            'JUL':slice(6), 'AUG':slice(7), 'SEP':slice(8), 'OCT':slice(9), 'NOV':slice(10), 'DEC':slice(11)}

SliceTS = { 'JAN':slice(0,None,12), 'FEB':slice(1,None,12), 'MAR':slice(2,None,12), 'APR':slice(3,None,12), 'MAY':slice( 4,None,12), 'JUN':slice( 5,None,12),
            'JUL':slice(6,None,12), 'AUG':slice(7,None,12), 'SEP':slice(8,None,12), 'OCT':slice(9,None,12), 'NOV':slice(10,None,12), 'DEC':slice(11,None,12)}

SOLAR = 1365.0          # Solar constant (W/m^2)   

# Ephemerides internal options
DEFAULT_OPTIONS = Container (Debug  = False,
                             Trace  = False,
                             Timing = None,
                             t0     = None,
                             Depth  = None,
                             Stack  = None)
OPTIONS = copy.deepcopy (DEFAULT_OPTIONS)

class set_options :
    """
    Set options for Ephemerides
    """
    def __init__ (self, **kwargs):
        self.old = Container ()
        for k, v in kwargs.items():
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
    Get options for Ephemerides

    See Also
    ----------
    set_options

    """
    return OPTIONS

def reset_options():
    return set_options (**DEFAULT_OPTIONS)

def return_stack () :
    return OPTIONS['Stack']

def push_stack (string:str) :
    if OPTIONS['Depth'] :
        OPTIONS['Depth'] += 1
    else                :
        OPTIONS['Depth'] = 1
    if OPTIONS['Trace'] :
        print ( '  '*(OPTIONS['Depth']-1), f'-->{__name__}.{string}' )
    #
    if OPTIONS['Stack'] :
        OPTIONS['Stack'].append (string)
    else                :
        OPTIONS['Stack'] = [string,]
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
    if OPTIONS['Depth'] == 0 :
        OPTIONS['Depth'] = None
    OPTIONS['Stack'].pop ()
    if OPTIONS['Stack'] == list () :
        OPTIONS['Stack'] = None
    #

## ============================================================================
def time2BP (time, unit='year', year0=7999, month0=7, day0=0, hour0=0) :
    '''
    Convert a cftime time variable in to Year before present values
    unit  : year or month
    year0 : year corresponding to 0k BP
    month0, day0, hour0 : month, day, hour corresponding to 0 ka BP

    Approximate calculation for plots
    '''
    push_stack ( f'time2BP (time, {unit=}, {year0=}, {month0=}, {day0=}, {hour0=})' )
    
    ty = isinstance (time, xr.core.dataarray.DataArray)
        
    if OPTIONS['Debug'] :
        print ( f'{ty=}')
    if ty  :
        ztime = time.values
    else   :
        ztime = time
    result = np.empty_like (time)
    if OPTIONS['Debug'] :
        print ( f'{type (ztime)=}')
        
    for ii, tt in enumerate (ztime) :
        #if OPTIONS['Debug'] : print ( f'{tt=}')
        (year, month, day, hour, mn, sec, ms) = cftime.to_tuple (tt)
        result [ii] = (year0-year) - (month-month0)/12 - (day-day0)/365.25 - (hour-hour0)/(365.25*24) - mn/(365.25*24*60) - sec/(365.25*24*60+60)
    if unit in ['month', 'Month', 'months', 'Months', 'M', 'm' ] :
        result = result*12
    result = result.astype(float)

    if ty : 
        result = xr.DataArray (result, dims=('YearBP',), coords=(result,))
        if unit in ['month', 'Month', 'months', 'Months', 'M', 'm' ] :
            result.attrs.update ({'unit':'Month BP', 'Comment':'Month before 1950'})
        else : 
            result.attrs.update ({'unit':'Year BP' , 'Comment':'Year before 1950' })

    pop_stack ( 'time2BP' )        
    return result

def mthday2day (month, day) :
    '''
    From month and day, compute day of year
    '''
    push_stack ( 'mthday2day (month, day)' )
    days = np.sum ( mth_length[:np.mod (month-1, 12)] ) + day
    pop_stack ( 'mthday2day' )
    return days

def declinaison (day) :
    '''
    Computes declinaison of the Sun (deg)
    
    Input : 
    day : number of the day of the year. May be > 366
    '''
    push_stack ( 'declinaison (day)' )
    M = np.mod (357.0 + day2deg*day, 360)
    C = 1.914 * np.sin (np.deg2rad(M)) + 0.02 * np.sin (2.0 * deg2rad*M)
    L = np.mod (280.0 + C + day2deg*day , 360)
    declinaison = np.arcsin (0.3978 * np.sin (deg2rad*L) ) * rad2deg
    
    if isinstance (day, xr.core.dataarray.DataArray) :
        declinaison.attrs.update ({'units':'degrees_north', 'standard_name':'declinaison', 'long_name':'Sun declinaison',} )

    pop_stack (declinaison)
    return declinaison

def equation_temps (day) :
    '''
    Computes equation of time (minutes)
    Time between 12:00 GMT and the passage of the Sun at the Greenwich meridian

    Input : 
    day : number of the day of the year. Maybe > 366
    '''
    push_stack ( 'equation_temps (day)' )
    M = np.mod (357.0 + day2deg*day, 360.)
    C = 1.914 * np.sin (deg2rad*M) + 0.02 * np.sin (2.0 * deg2rad*M)
    L = np.mod (280.0 + C + day2deg*day, 360.)
    R = -2.466 * np.sin (2.0 * deg2rad*L) + 0.053 * np.sin (4.0 * deg2rad*L)
    equation_temps = (C + R) * 4.0
        
    if isinstance (equation_temps, xr.core.dataarray.DataArray) :
        equation_temps.attrs.update ( {'units':'minutes', 'standard_name':'equation_du_temps', 'long_name':'Equation du temps',
                                          'comment':'Time between 12:00 GMT and the passage of the Sun at the Greenwich meridian'} )
    push_stack ( 'equation_temps' )
    return equation_temps

def equation_temps_smooth (day) :
    '''
    Computes equation of time (minutes)
    Time between 12:00 GMT and the passage of the Sun at the Greenwich meridian

    Input : 
    day : number of the day of the year. Maybe > 366

    This version takes a real version of day 1.0 is day 1, 0h, 1.5 is day 1, 12h, etc ....
    '''
    push_stack ( 'equation_temps (day)' )
    M = np.mod (357.0 + day2deg*(day-0.5), 360.)
    C = 1.914 * np.sin (deg2rad*M) + 0.02 * np.sin (2.0 * deg2rad*M)
    L = np.mod (280.0 + C + day2deg*day, 360.)
    R = -2.466 * np.sin (2.0 * deg2rad*L) + 0.053 * np.sin (4.0 * deg2rad*L)
    equation_temps = (C + R) * 4.0
        
    if isinstance (equation_temps, xr.core.dataarray.DataArray) :
        equation_temps.attrs.update ( {'units':'minutes', 'standard_name':'equation_du_temps', 'long_name':'Equation du temps',
                                          'comment':'Time between 12:00 GMT and the passage of the Sun at the Greenwich meridian'} )
    push_stack ( 'equation_temps' )
    return equation_temps

def H0 (day, lat) :
    '''
    Computes H0 : maximum height of the Sun above horizon for a given day (passage at the local meridian)

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    '''
    push_stack ( 'H0(day, lat)' )
    dec = declinaison (day)
    arg = (-0.01454 - np.sin (deg2rad*dec) * np.sin (deg2rad*lat)) / (np.cos (deg2rad*dec) * np.cos (deg2rad*lat) )
    H0  = xr.where ( np.abs(arg) <= 1.0,  rad2deg*np.arccos ( np.clip( arg, -1, 1.)), np.nan )
    if isinstance (H0, xr.core.dataarray.DataArray) :
        H0.attrs.update ({'units':'degrees', 'comment':'maximum height of the Sun above horizon for a given day (passage at the local meridian)'})

    pop_stack ('H0')
    return H0

def argH0 (day, lat) :
    push_stack ( 'argH0(day, lat)' )
    dec = declinaison (day)
    arg = (-0.01454 - np.sin (deg2rad*dec) * np.sin (deg2rad*lat)) / (np.cos (deg2rad*dec) * np.cos (deg2rad*lat) )
    pop_stack ('argH0')
    return arg

def hour_angle (H) :
    '''
    omega : hour angle, second equatorial coordinate of the Sun, defined here as the angle, 
    counted positively towards the east, between the current position of the local meridian plane and the position
    of this same meridian at true noon (or between the local meridian plane and the meridian plane
    which contains the centre of the Sun).

    $\\omega = \\frac{ \\pi \\cdot (12-H)}{12} = \\pi \\cdot (1-\\frac{H}{12})$

    H is true time, local

    hour_angle is computed in degrees
    '''
    push_stack ( 'hour_angle(H0)' )
    omega = 180.0 * (1 - H/12.)
    if isinstance (omega, xr.core.dataarray.DataArray) :
        omega.attrs.update ( {'units':'degrees_east', 'long_name':'angle horaire'} )

    pop_stack ( 'hour_angle')
    return omega

def sun_height (delta, lat, omega) :
    '''
    Height of the sun above the horizon
    The following angles are defined for the orientation of the surface receiving the solar flux:
      delta  : declinaison
      lambda : latitude 
      omega  : hour angle
    '''
    push_stack ('sun_height (delta, lat, omega)')
    sin_h = np.sin(deg2rad*delta)*np.sin(deg2rad*lat) + np.cos(deg2rad*delta)*np.cos(deg2rad*lat)*np.cos(deg2rad*omega)
    sun_height = rad2deg * np.arcsin(sin_h)

    if isinstance (sun_height, xr.core.dataarray.DataArray) :
        sun_height.attrs.update ( {'units':'degrees', 'long_name':'sun_height',
                                           'comment':'Sun height above horizon'} )
    pop_stack ( 'sun_height' )
    return sun_height

def insol (delta, lat, omega) :
    '''
    Solar radiation 
    The following angles are defined for the orientation of the surface receiving the solar flux 
      delta  : declinaison
      lambda : latitude 
      omega  : hour angle
    '''
    push_stack ( 'insol (delta, lat, omega)')
    sin_h = np.sin(deg2rad*delta)*np.sin(deg2rad*lat) + np.cos(deg2rad*delta)*np.cos(deg2rad*lat)*np.cos(deg2rad*omega)

    insol = SOLAR * np.maximum(0., sin_h)
    if isinstance (insol, xr.core.dataarray.DataArray) :
        insol.attrs.update ( {'units':'W m^-2', 'standard_name':'tops', 'comment':'Insolation at top of atm'} )
    pop_stack (insol)
    return insol
        
def SunRiseGMT (day, lat, lon) :
    '''
    Hour of the Sun rise : in fraction of GMT hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    lon : longitude in degrees
    '''
    push_stack ( 'SunRiseGMT (day, lat, lon) ')
    h0 = H0 (day, lat)
    eq = equation_temps (day)
    h1 = 12. - h0/15. + eq/60. - lon/15.  
    SunRise = np.fix (h1) + np.fix ( (h1 - np.fix (h1)) * 60. ) / 60.
    if isinstance (day, xr.core.dataarray.DataArray) :
        SunRise.attrs.update ( {'units':'hours', 'comment':'Hour of the Sun rise in fraction of GMT hour'})
    pop_stack ( 'SunRiseGMT' )
    return SunRise 

def SunSetGMT (day, lat, lon) :
    '''
    Hour of the Sun set : in fraction of GMT hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    lon : longitude in degrees
    '''
    push_stack ('SunSetGMT (day, lat, lon)')
    h0 = H0 (day, lat)
    eq = equation_temps (day)
    h1 = 12. + h0/15. + eq/60. - lon/15.
    SunSet = np.fix (h1) + np.fix ( (h1 - np.fix (h1)) * 60. ) / 60.
    if isinstance (day, xr.core.dataarray.DataArray) :
        SunSet.attrs.update ( {'units':'hours', 'comment':'Hour of the Sun set in fraction of GMT hour'})
    pop_stack ( 'SunSetGMT' )
    return SunSet

def DayLength (day, lat) :
    '''
    Hour of the Sun rise : in fraction of GMT hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    lon : longitude in degrees
    '''
    push_stack ( 'DayLength (day, lat)' )
    h0  = H0    (day, lat)
    arg = argH0 (day, lat)
    h0  = xr.where ( arg < -1.,  180., h0)
    h0  = xr.where ( arg >  1., -180., h0)

    eq = equation_temps (day)
  
    h1 = 12. - h0/15. + eq/60.
    h2 = 12. + h0/15. + eq/60.

    dimz   = []
    coordz = []
            
    if isinstance (day, xr.core.dataarray.DataArray) :
            coordz.append (day.coords[day.dims[0]])
            dimz.append   (day.dims[0])
    if isinstance (lat, xr.core.dataarray.DataArray) :
            coordz.append (lat.coords[lat.dims[0]])
            dimz.append   (lat.dims[0])
    
    if isinstance (day, xr.core.dataarray.DataArray) or isinstance (lat, xr.core.dataarray.DataArray) :      
        h1 = xr.DataArray ( h1, coords=coordz, dims=dimz)
        h2 = xr.DataArray ( h2, coords=coordz, dims=dimz)
            
    DayLength = h2 - h1
    DayLength = xr.where ( arg>=1,   0, DayLength )
    DayLength = xr.where ( arg<=-1, 24, DayLength )
    
    if isinstance (DayLength, xr.core.dataarray.DataArray) :
        DayLength.attrs.update ( {'units':'hours', 'comment':'Length of the day, from sun rise to sun set'})

    pop_stack ( 'DayLength' )
    return DayLength 

def SunRiseLocal (day, lat) :
    '''
    Hour of the Sun rise : in fraction of local hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    '''
    push_stack ( 'SunRiseLocal (day, lat)')
    zval =  SunRiseGMT (day, lat, lon=0)
    pop_stack ( 'SunRiseLocal' )
    return zval

def SunSetLocal (day, lat) :
    '''
    Hour of the Sun set : in fraction of local hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    '''
    push_stack ( 'SunSetLocal (day, lat)' )
    zval =  SunSetGMT (day, lat, lon=0)
    pop_stack ( 'SunSetLocal' )
    return zval

def date2day (pdate, t0=np.datetime64 ('1955-01-01T00:00:00')) :
    '''
    Gives day from a date in np.datetime64 format : integer

    Input
    pdate : date in np.datetime64, or string
    t0    : reference date in np.datetime64 01-JAN of any year, time 00:00
    '''
    push_stack ( f'date2day (pdate, {t0=})' )

    if isinstance (t0, str) :
        zdate = np.datetime64 (pdate)
    else :
        zdate = pdate

    ts = (zdate - t0) / np.timedelta64 (1, 'D')
    day = np.floor (ts%365) + 1
    
    if isinstance (pdate, xr.core.dataarray.DataArray) :
        day.attrs.update ( {'units':'days'} )
    pop_stack ( 'date2day' )
    return day

def date2daydec (pdate, t0=np.datetime64 ('1955-01-01T00:00:00'), out_int=True) :
    '''
    Gives day from a date in np.datetime64 format : day and  fraction of day

    Input
    pdate : date in np.datetime64
    t0    : reference date in np.datetime64 01-JAN of any year, time 00:00
    '''
    push_stack ( f'date2day (pdate, {t0=})' )

    ts = (pdate - t0) / np.timedelta64 (1, 'D')
    day = ts%365 + 1
    
    if isinstance (pdate, xr.core.dataarray.DataArray) :
        day.attrs.update ( {'units':'days'} )
    pop_stack ( 'date2day' )
    return day

def date2hour (pdate, t0=np.datetime64 ('1955-01-01T00:00:00'), out='int') :
    '''
    Gives hour from a date in np.datetime64, format : integer

    Input
    pdate : date in np.datetime64
    t0    : reference date in np.datetime64 01-JAN of any year, time 00:00
    '''
    push_stack ( f'date2hour (pdate, {t0=})' )
    ts   = (pdate - t0) / np.timedelta64 (1, 'h')
    hour = np.floor (ts%24)
    if isinstance (pdate, xr.core.dataarray.DataArray) :
        hour.attrs.update ( {'units':'hours' } )
    pop_stack (date2hour)
    return hour

def date2hourdec (pdate, t0) :
    '''
    Gives day from a date in np.datetime64 format : hour and fraction of hour

    Input
    pdate : date in np.datetime64
    t0    : reference date in np.datetime64 01-JAN of any year, time 00:00
    '''
    push_stack ( f'date2hourdec (pdate, {t0=})' )
    ts = (pdate - t0) / np.timedelta64 (1, 'h')
    hourdec = ts%24
    if isinstance (pdate, xr.core.dataarray.DataArray) :
        hourdec.attrs.update ( {'units':'hours'} )
    pop_stack ( 'date2hourdec' )
    return hourdec

def pseudo_local_time (ptime, lat=0, lon=0, t0=np.datetime64 ('1955-01-01T00:00:00')) :
    '''
    Converts time to local Roman time
    Stretch & compress local time to have 6h=SunRise/18h=SunSet
    '''
    push_stack ( f'pseudo_local_time (ptime, {lat=}, {lon=}, {t0=})' )
    day       = date2day     (ptime, t0)
    hourGMT   = date2hourdec (ptime, t0)
    hour      = np.mod (hourGMT + lon/15.0, 24.0)

    if OPTIONS.Debug :
        print ( f'{day=}' )

    if isinstance (ptime, xr.core.dataarray.DataArray) :
        math = xr
    else :
        math = np
    
    # Ephemerides of the Sun in local time
    zeroh    = 0.0
    SunRise  = SunRiseLocal (day=day, lat=lat)
    Noon     = 12.0
    SunSet   = SunSetLocal  (day=day, lat=lat)
    Midnight = 24.0
    
    h1 = math.where ( hour<SunRise  ,  
                   0.0 + (hour - zeroh)/(SunRise - zeroh)*6.0, 0.)
    h2 = math.where ( np.logical_and(SunRise <= hour, hour <= Noon),
                   6.0 + (hour - SunRise)/(Noon - SunRise) * 6.0, 0.)
    h3 = math.where ( np.logical_and(Noon < hour, hour <= SunSet),
                  12.0 + (hour -Noon)/(SunSet - Noon)*6.0, 0.)  
    h4 = math.where ( hour>SunSet, 
                  18.0 + (hour - SunSet)/(Midnight-SunSet)*6.0, 0.)
    
    pseudo_local_time = math.where ( SunSet>SunRise, h1 + h2 + h3 + h4, np.nan)

    if isinstance (pseudo_local_time, xr.core.dataarray.DataArray) :
        pseudo_local_time.attrs.update ( {'units':'hours', 'comment':'pseudo local time, roman definition',
                                'reference':'Marti, O., S. Nguyen, P. Braconnot, S. Valcke, F. Lemarié, and E. Blayo, 2021: A Schwarz iterative method to evaluate ocean–atmosphere coupling schemes: implementation and diagnostics in IPSL-CM6-SW-VLR. Geosci. Model Dev., 14, 2959–2975, https://doi.org/10.5194/gmd-14-2959-2021.'} )

        
    pop_stack ( 'pseudo_local_time' )    
    return pseudo_local_time
