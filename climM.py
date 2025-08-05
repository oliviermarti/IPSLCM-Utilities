'''
Compute some climatologies

Olivier Marti - olivier.marti@lsce.ipsl.fr
2021 December

En gros inutile. Utiliser xcdat directement est plus simple

'''

import xarray as xr
import xcdat as xc

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
        #ztime_dim  = var[time_dim]
        ztime_name = time_dim
    else : 
        #ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    #month_length  = ztime_dim.dt.days_in_month # a remplacer par le nombre de pas de temps ...      
    var_yearmax = var.resample ({ztime_name:"1YE"})
    var_yearmax = var_yearmax.max ()

    if len ( var.attrs) > 0 :
        var_yearmax.attrs.update ( var.attrs)
    
    return var_yearmax

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
        #ztime_dim  = var[time_dim]
        ztime_name = time_dim
    else : 
        #ztime_dim  = time_dim
        ztime_name = time_dim.name
        
    #month_length  = ztime_dim.dt.days_in_month # a remplacer par le nombre de pas de temps ...      
    var_yearmin   = var.resample ({ztime_name:"1YE"})
    var_yearmin   = var_yearmin.min ()

    if len ( var.attrs) > 0 :
        var_yearmin.attrs.update ( var.attrs)
    
    return var_yearmin

def yseamean (dd: xr.Dataset, varname:str, season:str='JJAS', drop_incomplete_djf:bool=True, dec_mode:str='DJF') -> xr.DataArray :
    '''
    Compute seasonal mean
    dd      : an xcdat dataset
    varname : variable name in dd
    season  : 3 or 4 months seasons (i.e. 'JJA', 'JJAS', etc ...) 
       due to xcdat limitations, 4 months seasons that cross the year limits
    drop_incomplete_djf : only for 3 months means
    '''
    
    if season == 'JJAS' : 
        use_custom=True
        if xc.__version__ >= '0.8' :
            custom_seasons = [ ["Jun", "Jul", "Aug", "Sep"], ]
        else :
            nseason = 1
            custom_seasons = [ ["Jan", "Feb", "Mar", "Apr", "May"], ["Jun", "Jul", "Aug", "Sep"], ["Oct", "Nov", "Dec"] ]
    if season == 'MAMJ' :
        use_custom=True
        if xc.__version__ >= '0.8' :
            nseason = 1
            custom_seasons = [ ["Mar", "Apr", "May", "Jun"], ]
        else : 
            custom_seasons = [ ["Jan", "Feb"], ["Mar", "Apr", "May", "Jun"], ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] ]
    if season == 'DJFM' :
        use_custom=True
        custom_seasons = [ ["Dec", "Jan", "Feb", "Mar"], ["Apr", "May", "Jun"], ["Jul", "Aug", "Sep", "Oct", "Nov"] ]
        if xc.__version__ >= '0.8' :
            custom_seasons = [ ["Dec", "Jan", "Feb", "Mar"], ]
        else : 
            raise ValueError ( 'xcdat can not compute 4 months seasons that cross the year limits' )
    if season == 'NDJF' :
        use_custom=True
        custom_seasons = [ ["Nov", "Dec", "Jan", "Feb"], ["Mar", "Apr", "May", "Jun"], ["Jul", "Aug", "Sep", "Oct"] ]
        if xc.__version__ >= '0.8' :
            custom_seasons = [["Nov", "Dec", "Jan", "Feb"], ]
        else : 
            raise ValueError ( 'xcdat can not compute 4 months seasons that cross the year limits' )
    if season == 'SOND' :
        use_custom=True
        if xc.__version__ >= '0.8' :
            custom_seasons = [ ["Sep", "Oct", "Nov", "Dec"], ]
        else :
            nseason = 1
        custom_seasons = [ ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"], ["Sep", "Oct", "Nov", "Dec"] ]

    if season == 'DJF'  :
        use_custom = False
        nseason    = 0
    if season == 'MAM'  :
        use_custom = False
        nseason    = 1
    if season == 'JJA'  :
        use_custom = False
        nseason    = 2
    if season == 'SON'  :
        use_custom = False
        nseason    = 3
        
    if use_custom :
        if xc.__version__ > '0.8' :
            zz = dd.temporal.group_average ( varname, "season",
                                             season_config={"custom_seasons":custom_seasons} )[varname]
        else : 
            zz = dd.temporal.group_average ( varname, "season",
                                             season_config={"custom_seasons":custom_seasons} )[varname][nseason::len(custom_seasons)]
    else :
        zz = dd.temporal.group_average ( varname, "season",
                                             season_config={"drop_incomplete_djf":drop_incomplete_djf, 'dec_mode':dec_mode} )[varname][nseason::4]

    return zz

# def ymonthmean (var, time_dim, month=None) :
#     '''
#     Compute seasonal means for a specific month
 
#     Inputs :
#        var      : an xr.DataArray with a proper time dimension
#        time_dim : the time dimension
#        season   : 'DJF', 'MAM', 'JJA', 'SON' or None

#     Ouput :
#         A yearly time series of one specific season mean
#         A yearly time series of all season if season == None
#     '''
#     if isinstance (time_dim, str) :
#         ztime_dim = var[time_dim]
#         ztime_name = time_dim
#     else : 
#         ztime_dim  = time_dim
#         ztime_name = time_dim.name
        
#     SliceTS = { 'JAN':slice(0,None,12), 'FEB':slice(1,None,12), 'MAR':slice(2,None,12), 'APR':slice(3,None,12), 'MAY':slice( 4,None,12), 'JUN':slice( 5,None,12),
#                 'JUL':slice(6,None,12), 'AUG':slice(7,None,12), 'SEP':slice(8,None,12), 'OCT':slice(9,None,12), 'NOV':slice(10,None,12), 'DEC':slice(11,None,12)}
