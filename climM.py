'''
Compute some climatologies

Olivier Marti - olivier.marti@lsce.ipsl.fr
2021 December
'''

import numpy as np, xarray as xr

try    : import numba
except ImportError : pass

@numba.jit(forceobj=True)
def seamean (var, time_dim) :
    '''
    Compute climatological seasonal means
    Correct for any start time of data, for any frequency (?)

    Inputs :
       var      : an xr.DataArray with a proper time dimension
       time_dim : the time dimension

    Ouput :
       seasonal means
       season order is 'DJF', 'JJA', 'MAM', 'SON'
    '''
    if isinstance (time_dim, str) :
        ztime_dim = var[time_dim]
        ztime_name = time_dim
    else : 
        ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    season_group = ztime_name + ".season"
    
    month_length = ztime_dim.dt.days_in_month
    weights_sea  = month_length.groupby (season_group) / month_length.groupby(season_group).sum()
    var_sea = (var * weights_sea).groupby(season_group).sum(dim=ztime_name)

    if len ( var.attrs) > 0 :
        var_sea.attrs.update ( var.attrs)

    return var_sea

@numba.jit(forceobj=True)
def monthmean (var, time_dim) :
    '''
    Compute climatological monthly means
    Correct for any start time of data, for any frequency (?)

    Inputs :
       var      : an xr.DataArray with a proper time dimension
       time_dim : the time dimension

    Ouput :
       climatological monthly means
    '''
    if isinstance (time_dim, str) :
        ztime_dim  = var[time_dim]
        ztime_name = time_dim
    else : 
        ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    month_group = ztime_name + ".month"
    
    month_length  = ztime_dim.dt.days_in_month
    weights_month = month_length.groupby(month_group) / month_length.groupby(month_group).sum()
    var_mth = (var * weights_month).groupby(month_group).sum(dim=ztime_name)
    
    if len ( var.attrs) > 0 :
        var_mth.attrs.update (var.attrs)
  
    return var_mth

@numba.jit(forceobj=True)
def yearmean (var, time_dim) :
    '''
    Compute yearly means
    Correct for any start time of data, for monthly inputs only

    Inputs :
       var      : an xr.DataArray with a proper time dimension
       time_dim : the time dimension

    Ouput :
       A yearly time series
    '''
    if isinstance (time_dim, str) :
        ztime_dim  = var[time_dim]
        ztime_name = time_dim
    else : 
        ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    month_length  = ztime_dim.dt.days_in_month # a remplacer par le nombre de pas de temps ...
    year_length   = month_length.resample({ztime_name:"1YE"}).sum()
        
    var_year = (var*month_length).resample ({ztime_name:"1YE"})
    var_year = var_year.sum () / year_length

    if len (var.attrs) > 0 :
        var_year.attrs.update (var.attrs)
        
    return var_year

@numba.jit(forceobj=True)
def yearmax (var, time_dim) :
    '''
    Compute yearly max
    Correct for any start time of data, for monthly inputs only

    Inputs :
       var      : an xr.DataArray with a proper time dimension
       time_dim : the time dimension

    Ouput :        A yearly time series
    '''
    if isinstance (time_dim, str) :
        ztime_dim  = var[time_dim]
        ztime_name = time_dim
    else : 
        ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    month_length  = ztime_dim.dt.days_in_month # a remplacer par le nombre de pas de temps ...      
    var_yearmax = var.resample ({ztime_name:"1YE"})
    var_yearmax = var_yearmax.max ()

    if len ( var.attrs) > 0 :
        var_yearmax.attrs.update ( var.attrs)
    
    return var_yearmax

@numba.jit(forceobj=True)
def yearmin (var, time_dim) :
    '''
    Compute yearly min
    Correct for any start time of data, for monthly inputs only

    Inputs :
       var      : an xr.DataArray with a proper time dimension
       time_dim : the time dimension

    Ouput :
       A yearly time series
    '''
    if isinstance (time_dim, str) :
        ztime_dim  = var[time_dim]
        ztime_name = time_dim
    else : 
        ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    month_length  = ztime_dim.dt.days_in_month # a remplacer par le nombre de pas de temps ...      
    var_yearmin = var.resample ({ztime_name:"1YE"})
    var_yearmin = var_yearmin.min ()

    if len ( var.attrs) > 0 :
        var_yearmin.attrs.update ( var.attrs)
    
    return var_yearmin

@numba.jit(forceobj=True)
def yseamean (var, time_dim, season='All', drop_incomplete=False) :
    '''
    Compute seasonal means for a specific season, or all seasons
    Correct for any start time of data, for monthly means

    Inputs :
       var      : an xr.DataArray with a proper time dimension
       time_dim : the time dimension (name of dimension object)
       season   : 'DJF', 'MAM', 'JJA', 'SON', 'JJAS, 'DJFM', 'SOND', 'MJJA', 'NDJF' or None

    Ouput :
        A yearly time series of one specific season mean
        A yearly time series of all season if season == None
    '''
    if isinstance (time_dim, str) :
        ztime_dim = var[time_dim]
        ztime_name = time_dim
    else : 
        ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    if not season or season.upper() == 'ALL' :
        season = 'ALL'
        month_length = ztime_dim.dt.days_in_month
        var_yseamean = (var * month_length).resample ({ztime_name:'QS-DEC'}).sum() / month_length.resample ({ztime_name:'QS-DEC'}).sum()
        
    else : 
        if season.upper () == 'ANNUAL' : 
            var_yseamean = yearmean (var, time_dim)
       
        if season.upper () in  ['DJF', 'MAM', 'JJA', 'SON' ] :
            month_length  = ztime_dim.dt.days_in_month
            var_yseamean = (var * month_length).resample ({ztime_name:'QS-DEC'}).sum() / month_length.resample({ztime_name:'QS-DEC'}).sum()
            if season.upper() == 'DJF' : var_yseamean = var_yseamean[0::4]
            if season.upper() == 'MAM' : var_yseamean = var_yseamean[1::4]
            if season.upper() == 'JJA' : var_yseamean = var_yseamean[2::4]
            if season.upper() == 'SON' : var_yseamean = var_yseamean[3::4]
         

        if season.upper () in ['DJFM', 'JJAS', 'MAMJ', 'SOND', 'MJJA'] :          
            if season == 'JJAS' : lm = [ 6,  7,  8,  9]
            if season == 'DJFM' : lm = [11, 12,  2,  3]
            if season == 'MAMJ' : lm = [ 3,  4,  5,  6]
            if season == 'SOND' : lm = [ 9, 10, 11, 12]
            if season == 'MJJA' : lm = [ 5,  6,  7,  8]
            if season == 'NDJF' : lm = [11, 12,  1,  2]

            ll = ztime_dim.dt.month.isin (lm)
            month_length  = ztime_dim.dt.days_in_month
            season_length = month_length[ll].resample ({ztime_name:"1YE"}).sum ()
            var_yseamean  = var*month_length.where (ll)
            var_yseamean  = var_yseamean.resample ({ztime_name:"1YE"})
            var_yseamean  = var_yseamean.sum () / season_length

    #print ( f'{season=}')
    print ( season )
    
    if drop_incomplete and season.upper() in ['DJF', 'ALL'] :
        print ( '--' )
        if ztime_dim.dt.month[ 0] == 2  : var_yseamean = var_yseamean[1:]
        if ztime_dim.dt.month[ 0] == 1  : var_yseamean = var_yseamean[1:]
        if ztime_dim.dt.month[-1] == 12 : var_yseamean = var_yseamean[:-1]
                    
    if len (var.attrs) > 0 : 
        var_yseamean.attrs.update (var.attrs)

    return var_yseamean

@numba.jit(forceobj=True)
def ymonthmean (var, time_dim, month=None) :
    '''
    Compute seasonal means for a specific month
 
    Inputs :
       var      : an xr.DataArray with a proper time dimension
       time_dim : the time dimension
       season   : 'DJF', 'MAM', 'JJA', 'SON' or None

    Ouput :
        A yearly time series of one specific season mean
        A yearly time series of all season if season == None
    '''
    if isinstance (time_dim, str) :
        ztime_dim = var[time_dim]
        ztime_name = time_dim
    else : 
        ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    SliceTS = { 'JAN':slice(0,None,12), 'FEB':slice(1,None,12), 'MAR':slice(2,None,12), 'APR':slice(3,None,12), 'MAY':slice( 4,None,12), 'JUN':slice( 5,None,12),
                'JUL':slice(6,None,12), 'AUG':slice(7,None,12), 'SEP':slice(8,None,12), 'OCT':slice(9,None,12), 'NOV':slice(10,None,12), 'DEC':slice(11,None,12)}
