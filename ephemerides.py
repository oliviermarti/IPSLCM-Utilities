'''
Compute time of sun rise and sun set, given a day and a geographical position

(http://www.softrun.fr/index.php/bases-scientifiques/heure-de-lever-et-de-coucher-du-soleil)

All computation are approximate, with an error of a few minutes

More details here : http://jean-paul.cornec.pagesperso-orange.fr/heures_lc.htm

Details for exact computation : https://www.imcce.fr/en/grandpublic/systeme/promenade/pages3/367.html

'''

import numpy as np, xarray as xr
import cftime

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

def time2BP (time, unit='year', year0=7999, month0=7, day0=0, hour0=0) :
    '''
    Convert a cftime time variable in to Year before present values
    unit  : year or month
    year0 : year corresponding to 0k BP
    month0, day0, hour0 : month, day, hour corresponding to 0 ka BP

    Approximate calculation for plots
    '''
    try    : ty    = isinstance (time, xr.core.dataarray.DataArray)
    except : ty    = None
    if ty  : ztime = time.values
    else   : ztime = time
    result = np.empty_like (time)
    for ii, tt in enumerate (ztime) :
        (year, month, day, hour, mn, sec, ms) = cftime.to_tuple (tt)
        result [ii] = (year0-year) - (month-month0)/12 - (day-day0)/365.25 - (hour-hour0)/(365.25*24) - mn/(365.25*24*60) - sec/(365.25*24*60+60)
    if unit in ['month', 'Month', 'months', 'Months', 'M', 'm' ] :
        result = result*12

    if ty : 
        result = xr.DataArray (result, dims=('YearBP',), coords=(result,))
        if unit in ['month', 'Month', 'months', 'Months', 'M', 'm' ] :
            result.attrs.update ({'unit':'Month BP', 'Comment':'Month before 1950'})
        else : 
            result.attrs.update ({'unit':'Year BP' , 'Comment':'Year before 1950' })
    return result

def mthday2day (month, day) :
    '''
    From month and day, compute day of year
    '''
    days = np.sum ( mth_length[:np.mod (month-1, 12)] ) + day
    return days

def declinaison (day) :
    '''
    Computes declinaison of the Sun (deg)
    
    Input : 
    day : number of the day of the year. May be > 366
    '''
    M = np.mod (357.0 + day2deg*day, 360)
    C = 1.914 * np.sin (np.deg2rad(M)) + 0.02 * np.sin (2.0 * deg2rad*M)
    L = np.mod (280.0 + C + day2deg*day , 360)
    declinaison = np.arcsin (0.3978 * np.sin (deg2rad*L) ) * rad2deg
    
    if isinstance (day, xr.core.dataarray.DataArray) :
        declinaison.attrs.update ({'units':'degrees_north', 'standard_name':'declinaison', 'long_name':'Sun declinaison',} )
    return declinaison

def equation_temps (day) :
    '''
    Computes equation of time (minutes)
    Time between 12:00 GMT and the passage of the Sun at the Greenwich meridian

    Input : 
    day : number of the day of the year. Maybe > 366
    '''
    M = np.mod (357.0 + day2deg*day, 360.)
    C = 1.914 * np.sin (deg2rad*M) + 0.02 * np.sin (2.0 * deg2rad*M)
    L = np.mod (280.0 + C + day2deg*day, 360.)
    R = -2.466 * np.sin (2.0 * deg2rad*L) + 0.053 * np.sin (4.0 * deg2rad*L)
    equation_temps = (C + R) * 4.0
        
    if isinstance (equation_temps, xr.core.dataarray.DataArray) :
        equation_temps.attrs.update ( {'units':'minutes', 'standard_name':'equation_du_temps', 'long_name':'Equation du temps',
                                          'comment':'Time between 12:00 GMT and the passage of the Sun at the Greenwich meridian'} )
    return equation_temps

def H0 (day, lat) :
    '''
    Computes H0 : maximum height of the Sun above horizon for a given day (passage at the local meridian)

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    '''
    dec = declinaison (day)
    arg = (-0.01454 - np.sin (deg2rad*dec) * np.sin (deg2rad*lat)) / (np.cos (deg2rad*dec) * np.cos (deg2rad*lat) )
    H0  = xr.where ( np.abs(arg) <= 1.0,  rad2deg*np.arccos ( np.clip( arg, -1, 1.)), np.nan )
    if isinstance (H0, xr.core.dataarray.DataArray) :
        H0.attrs.update ({'units':'degrees', 'comment':'maximum height of the Sun above horizon for a given day (passage at the local meridian)'})
    return H0

def argH0 (day, lat) :
    dec = declinaison (day)
    arg = (-0.01454 - np.sin (deg2rad*dec) * np.sin (deg2rad*lat)) / (np.cos (deg2rad*dec) * np.cos (deg2rad*lat) )
    return arg

def hour_angle (H) :
    '''
    omega : hour angle, second equatorial coordinate of the Sun, defined here as the angle, 
    counted positively towards the east, between the current position of the local meridian plane and the position
    of this same meridian at true noon (or between the local meridian plane and the meridian plane
    which contains the centre of the Sun).

    $\omega = \frac{ \pi \cdot (12-H)}{12} = \pi \cdot (1-\frac{H}{12})$

    H is true time, local

    hour_angle is computed in degrees
    '''
    omega = 180.0 * (1 - H/12.)
    if isinstance (omega, xr.core.dataarray.DataArray) :
        omega.attrs.update ( {'units':'degrees_east', 'long_name':'angle horaire'} )

    return omega

def sun_height (delta, lat, omega) :
    '''
    Height of the sun above the horizon
    The following angles are defined for the orientation of the surface receiving the solar flux:
      delta  : declinaison
      lambda : latitude 
      omega  : hour angle
    '''

    sin_h = np.sin(deg2rad*delta)*np.sin(deg2rad*lat) + np.cos(deg2rad*delta)*np.cos(deg2rad*lat)*np.cos(deg2rad*omega)
    sun_height = rad2deg * np.arcsin(sin_h)

    if isinstance (sun_height, xr.core.dataarray.DataArray) :
        sun_height.attrs.update ( {'units':'degrees', 'long_name':'sun_height',
                                           'comment':'Sun height above horizon'} )
    return sun_height

def insol (delta, lat, omega) :
    '''
    Solar radiation 
    The following angles are defined for the orientation of the surface receiving the solar flux 
      delta  : declinaison
      lambda : latitude 
      omega  : hour angle
    '''

    sin_h = np.sin(deg2rad*delta)*np.sin(deg2rad*lat) + np.cos(deg2rad*delta)*np.cos(deg2rad*lat)*np.cos(deg2rad*omega)

    insol = SOLAR * np.maximum(0., sin_h)
    if isinstance (insol, xr.core.dataarray.DataArray) :
        insol.attrs.update ( {'units':'W m^-2', 'standard_name':'tops', 'comment':'Insolation at top of atm'} )
    return insol
        
def SunRiseGMT (day, lat, lon) :
    '''
    Hour of the Sun rise : in fraction of GMT hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    lon : longitude in degrees
    '''
    h0 = H0 (day, lat)
    eq = equation_temps (day)
    h1 = 12. - h0/15. + eq/60. - lon/15.  
    SunRise = np.fix (h1) + np.fix ( (h1 - np.fix (h1)) * 60. ) / 60.
    if isinstance (day, xr.core.dataarray.DataArray) :
        SunRise.attrs.update ( {'units':'hours', 'comment':'Hour of the Sun rise in fraction of GMT hour'})
    return SunRise 

def SunSetGMT (day, lat, lon) :
    '''
    Hour of the Sun set : in fraction of GMT hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    lon : longitude in degrees
    '''
    h0 = H0 (day, lat)
    eq = equation_temps (day)
    h1 = 12. + h0/15. + eq/60. - lon/15.
    SunSet = np.fix (h1) + np.fix ( (h1 - np.fix (h1)) * 60. ) / 60.
    if isinstance (day, xr.core.dataarray.DataArray) :
        SunSet.attrs.update ( {'units':'hours', 'comment':'Hour of the Sun set in fraction of GMT hour'})
    return SunSet

def DayLength (day, lat) :
    '''
    Hour of the Sun rise : in fraction of GMT hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    lon : longitude in degrees
    '''
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
        
    return DayLength 


def SunRiseLocal (day, lat) :
    '''
    Hour of the Sun rise : in fraction of local hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    '''
    return SunRiseGMT (day, lat, lon=0)

def SunSetLocal (day, lat) :
    '''
    Hour of the Sun set : in fraction of local hour

    Input : 
    day : number of the day of the year. May be > 366
    lat ; latitude in degrees
    '''
    return SunSetGMT (day, lat, lon=0)

def date2day (pdate, t0) :
    '''
    Gives day from a date in np.datetime64 format : integer

    Input
    pdate : date in np.datetime64
    t0    : reference date in np.datetime64 01-JAN of any year, time 00:00
    '''
    ts = (pdate - t0) / np.timedelta64 (1, 'h')
    day = np.fix ( np.mod (ts/24, 365) ) + 1
    if isinstance (pdate, xr.core.dataarray.DataArray) :
        day.attrs.update ( {'units':'days'} )
    return day

def date2hour (pdate, t0) :
    '''
    Gives hour from a date in np.datetime64, format : integer

    Input
    pdate : date in np.datetime64
    t0    : reference date in np.datetime64 01-JAN of any year, time 00:00
    '''
    ts   = (pdate - t0) / np.timedelta64 (1, 'h')
    hour = np.fix ( np.mod (ts, 24))
    if isinstance (pdate, xr.core.dataarray.DataArray) :
        hour.attrs.update ( {'units':'hours' } )
    return hour

def date2hourdec (pdate, t0) :
    '''
    Gives day from a date in np.datetime64 format : hour and fraction of hour

    Input
    pdate : date in np.datetime64
    t0    : reference date in np.datetime64 01-JAN of any year, time 00:00
    '''
    ts = (pdate - t0) / np.timedelta64 (1, 'h')
    hourdec = np.mod (ts, 24)
    if isinstance (pdate, xr.core.dataarray.DataArray) :
        hourdec.attrs.update ( {'units':'hours'} )
    return hourdec

def pseudo_local_time (ptime, lat=0, lon=0, t0=np.datetime64 ('1955-01-01T00:00:00')) :
    '''
    Converts time to local Roman time
    Stretch & compress local time to have 6h=SunRise/18h=SunSet
    '''
  
    day       = date2day     (ptime, t0)
    hourGMT   = date2hourdec (ptime, t0)
    hour      = np.mod (hourGMT + lon/15.0, 24.0)

    if isinstance (ptime, xr.core.dataarray.DataArray) : math = xr
    else : math = np
    
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
        hourdec.attrs.update ( {'units':'hours', 'comment':'pseudo local time, roman definition',
                                'reference':'Marti, O., S. Nguyen, P. Braconnot, S. Valcke, F. Lemarié, and E. Blayo, 2021: A Schwarz iterative method to evaluate ocean–atmosphere coupling schemes: implementation and diagnostics in IPSL-CM6-SW-VLR. Geosci. Model Dev., 14, 2959–2975, https://doi.org/10.5194/gmd-14-2959-2021.'} )
    
    return pseudo_local_time
