# -*- coding: utf-8 -*-
## ============================================================================
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
## ============================================================================
'''
Utilities to plot NEMO ORCA fields,

Handles periodicity and other stuff

- Lots of tests for xarray object
- Not much tested for numpy objects

Author: olivier.marti@lsce.ipsl.fr

## SVN information                                                             
Author   = "$Author:  $"
Date     = "$Date: $"
Revision = "$Revision: $"
Id       = "$Id: $"
HeadURL  = "$HeadURL: $"
'''

## Modules                                                                     
import time
import numpy as np
import xarray as xr
#import pint
#ureg = pint.UnitRegistry()
import cf_xarray.units 
import pint_xarray
from pint_xarray import unit_registry as ureg

try :
    import xcdat as xc
except :
    xc = None

try :
    from sklearn.impute import SimpleImputer
except ImportError as err :
    print (f'===> Warning : Module nemo : Import error of sklearn.impute.SimpleImputer : {err}')
    SimpleImputer = None

try :
    import f90nml
except ImportError as err :
    print (f'===> Warning : Module nemo : Import error of f90nml : {err}')
    f90nml = None

from Utils import Container

## SVN information                                                             
__SVN__ = ({
    'Author'   : '$Author: $',
    'Date'     : '$Date: $',
    'Revision' : '$Revision:  $',
    'Id'       : '$Id:  $',
    'HeadURL'  : '$HeadURL: $',
    'SVN_Date' : '$SVN_Date: $',
    })
## Useful constants and parameters                                             
    
REPSI = np.finfo (1.0).eps

RAAMO  = xr.DataArray (12)        ; RAAMO .name='RAAMO'  ; RAAMO.attrs.update  ({'units':"mth"    , 'long_name':"Number of months in one year" })
RJJHH  = xr.DataArray (24)        ; RJJHH .name='RJJHH'  ; RJJHH.attrs.update  ({'units':"h"      , 'long_name':"Number of hours in one day"} )
RHHMM  = xr.DataArray (60)        ; RHHMM .name='RHHMM'  ; RHHMM.attrs.update  ({'units':"min"    , 'long_name':"Number of minutes in one hour"} )
RMMSS  = xr.DataArray (60)        ; RMMSS .name='RMMSS'  ; RMMSS.attrs.update  ({'units':"s"      , 'long_name':"Number of seconds in one minute"} )
RA     = xr.DataArray (6371229.0) ; RA    .name='RA'     ; RA.attrs.update     ({'units':"m"      , 'long_name':"Earth radius"} )
GRAV   = xr.DataArray (9.80665)   ; GRAV  .name='GRAV'   ; GRAV.attrs.update   ({'units':"m/s2"   , 'long_name':"Gravity"} )
RT0    = xr.DataArray (273.15)    ; RT0   .name='RT0'    ; RT0.attrs.update    ({'units':"K"      , 'long_name':"Freezing point of fresh water"} )
RAU0   = xr.DataArray (1026.0)    ; RAU0  .name='RAU0'   ; RAU0.attrs.update   ({'units':"kg/m3"  , 'long_name':"Volumic mass of sea water"} )
SICE   = xr.DataArray (6.0)       ; SICE  .name='SICE'   ; SICE.attrs.update   ({'units':"psu"    , 'long_name':"Salinity of ice (for pisces)"} )
SOCE   = xr.DataArray (34.7)      ; SOCE  .name='SOCE'   ; SOCE.attrs.update   ({'units':"psu"    , 'long_name':"Salinity of sea (for pisces and isf)"} )
RLEVAP = xr.DataArray (2.5e+6)    ; RLEVAP.name='RLEVAP' ; RLEVAP.attrs.update ({'units':"J/K"    , 'long_name':"Latent heat of evaporation (water)"} )
VKARMN = xr.DataArray (0.4)       ; VKARMN.name='VKARMN' ; VKARMN.attrs.update ({'units':"-"      , 'long_name':"Von Karman constant"} )
STEFAN = xr.DataArray (5.67e-8)   ; STEFAN.name='STEFAN' ; STEFAN.attrs.update ({'units':"W/m2/K4", 'long_name':"Stefan-Boltzmann constant"} )
RHOS   = xr.DataArray (330.)      ; RHOS  .name='RHOS'   ; RHOS.attrs.update   ({'units':"kg/m3"  , 'long_name':"Volumic mass of snow"} )
RHOI   = xr.DataArray (917.)      ; RHOI  .name='RHOI'   ; RHOI.attrs.update   ({'units':"kg/m3"  , 'long_name':"Volumic mass of sea ice"} )
RHOW   = xr.DataArray (1000.)     ; RHOW  .name='RHOW'   ; RHOW.attrs.update   ({'units':"kg/m3"  , 'long_name':"Volumic mass of freshwater in melt ponds"} )
RCND_I = xr.DataArray (2.034396)  ; RCND_I.name='RCND_I' ; RCND_I.attrs.update ({'units':"W/m/J"  , 'long_name':"Thermal conductivity of fresh ice"} )
RCPI   = xr.DataArray (2067.0)    ; RCPI  .name='RCPI'   ; RCPI.attrs.update   ({'units':"J/kg/K" , 'long_name':"Specific heat of fresh ice"} )
RLSUB  = xr.DataArray (2.834e+6)  ; RLSUB .name='RLSUB'  ; RLSUB.attrs.update  ({'units':"J/kg"   , 'long_name':"Pure ice latent heat of sublimation"} )
RLFUS  = xr.DataArray (0.334e+6)  ; RLFUS .name='RLFUS'  ; RLFUS.attrs.update  ({'units':"J/kg"   , 'long_name':"Latent heat of fusion of fresh ice"} )
RTMLT  = xr.DataArray (0.054)     ; RTMLT .name='RTMLT'  ; RTMLT.attrs.update  ({'units':"C/PSU"  , 'long_name':"Decrease of seawater meltpoint with salinity"} )

RDAY     = RJJHH * RHHMM * RMMSS                 ; RDAY  .name='RDAY'   ; RDAY.attrs.update   ({'units':"s"  , 'long_name':"Day length"} )
RSIYEA   = 365.25 * RDAY * 2. * np.pi / 6.283076 ; RSIYEA.name='RSIYEA' ; RSIYEA.attrs.update ({'units':"s"  , 'long_name':"Sideral year length"} )
RSIDAY   = RDAY / (1. + RDAY / RSIYEA)           ; RSIDAY.name='RSIDAY' ; RSIDAY.attrs.update ({'units':"s"  , 'long_name':"Sideral day length"} )
ROMEGA   = 2. * np.pi / RSIDAY                   ; ROMEGA.name='ROMEGA' ; ROMEGA.attrs.update ({'units':"s-1", 'long_name':"Earth rotation parameter"} )

NPERIO_VALID_RANGE = [0, 1, 4, 4.2, 5, 6, 6.2]

## Default names of dimensions                                                 
UDIMS = {'x':'x', 'y':'y', 'z':'olevel', 't':'time_counter'}

## All possible names of lon/lat variables in Nemo files                       
LONNAME=['nav_lon', 'nav_lon_T', 'nav_lon_U', 'nav_lon_V', 'nav_lon_F', 'nav_lon_W',
             'nav_lon_grid_T', 'nav_lon_grid_U', 'nav_lon_grid_V', 'nav_lon_grid_F', 'nav_lon_grid_W']
LATNAME=['nav_lat', 'nav_lat_T', 'nav_lat_U', 'nav_lat_V', 'nav_lat_F', 'nav_lat_W',
             'nav_lat_grid_T', 'nav_lat_grid_U', 'nav_lat_grid_V', 'nav_lat_grid_F', 'nav_lat_grid_W']

## All possibles names of dimensions in Nemo files                             
XNAME = [ 'x_grid_W', 'x_grid_T', 'x_grid_U', 'x_grid_V', 'x_grid_F',
          'lon', 'nav_lon', 'longitude', 'X1', 'x_c', 'x_f', 'x', 'X', 'X1', 'xx', 'XX',]
YNAME = [ 'y_grid_W', 'y_grid_T', 'y_grid_U', 'y_grid_V', 'y_grid_F',
          'lat', 'nav_lat', 'latitude' , 'Y1', 'y_c', 'y_f', 'y', 'Y', 'Y1', 'yy', 'YY',]
ZNAME = [ 'z', 'Z', 'Z1', 'zz', 'ZZ', 'depth', 'tdepth', 'udepth',
          'vdepth', 'wdepth', 'fdepth', 'deptht', 'depthu',
          'depthv', 'depthw', 'depthf', 'olevel', 'z_c', 'z_f',
          'rho', 'rhop', 'Rho', 'Rhop', 'RHO', 'RHOP', 'sigma', 'Sigma', 'SIGMA']
TNAME = [ 't', 'T', 'tt', 'TT', 'time', 'time_counter', 'time_centered', 'time', 'TIME', 'TIME_COUNTER', 'TIME_CENTERED', ]

BNAME = [ 'bnd', 'bnds', 'bound', 'bounds' ]

## All possibles name of units of dimensions in NEMO files                     
XUNIT = [ 'degrees_east', ]
YUNIT = [ 'degrees_north', ]
ZUNIT = [ 'm', 'meter', ]
TUNIT = [ 'second', 'minute', 'hour', 'day', 'month', 'year', ]

## All possibles size of dimensions in Orca files                              
XLENGTH   = [ 180, 182, 360, 362, 1440, 1442 ]
YLENGTH   = [ 148, 149, 331, 332 ]
ZLENGTH   = [ 31, 75]
XYZLENGTH = [ [180,148,31], [182,149,31], [360,331,75], [362,332,75] ]

## T, S arrays to plot TS diagrams                                             
Ttab = np.linspace (-2, 40, 100) * ureg.celsius
Stab = np.linspace ( 0, 40, 100) * ureg.psu

Ttab = xr.DataArray (Ttab, dims=('Temperature',), coords=(Ttab,))
Stab = xr.DataArray (Stab, dims=('Salinity'   ,), coords=(Stab,))

Ttab.attrs.update ( {'unit':'degrees_celcius', 'long_name':'Temperature'} )
Stab.attrs.update ( {'unit':'PSU',             'long_name':'Salinity'} )

## Units not recognized by pint                                                
ureg.define ('degree_C = degC')
ureg.define ('DU = 10^-5 * m = du')

pint_dict = {
    'thetao':'degC',
    'so':'psu',
    'sos':'psu',
    'sssdcymax':'psu',
    'sssdcymin':'psu',
    'sssdcy':'psu',
    'sozosatr':'g/s',
    'somesatr':'g/s',
    }

## nemo module internal options                                                
OPTIONS = Container (Debug=False, Trace=False, Timing=None, t0=None, Depth=None, Stack=None)

class set_options :
    '''
    Set options for nemo
    '''
    def __init__ (self, **kwargs) :
        self.old = Container ()
        for k, v in kwargs.items() :
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update (self, options_dict) : OPTIONS.update (options_dict)
    def __enter__ (self) : return
    def __exit__ (self, type, value, traceback) : self._apply_update (self.old)

def get_options () -> dict :
    '''
    Get options for nemo

    See Also
    ----------
    set_options

    '''
    return OPTIONS

def return_stack () :
    return OPTIONS.Stack

def push_stack (string:str) :
    if OPTIONS.Depth : OPTIONS.Depth += 1
    else             : OPTIONS.Depth = 1
    if OPTIONS.Trace : print ( '  '*(OPTIONS.Depth-1), f'-->{__name__}.{string}' )
    #
    if OPTIONS.Stack : OPTIONS.Stack.append (string)
    else             : OPTIONS.Stack = [string,]
    #
    if OPTIONS.Timing :
        if OPTIONS.t0 :
            OPTIONS.t0.append ( time.time() )
        else :
            OPTIONS.t0 = [ time.time(), ]

def pop_stack (string:str) :
    if OPTIONS.Timing :
        dt = time.time() - OPTIONS.t0[-1]
        OPTIONS.t0.pop()
    else :
        dt = None
    if OPTIONS.Trace or dt :
        if dt :
            if dt < 1e-3 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1e6:5.1f} micro s')
            if dt >= 1e-3 and dt < 1 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1e3:5.1f} milli s')
            if dt >= 1 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1:5.1f} second')
        else : 
            print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string}')
    #
    OPTIONS.Depth -= 1
    if OPTIONS.Depth == 0 : OPTIONS.Depth = None
    OPTIONS.Stack.pop ()
    if OPTIONS.Stack == list () : OPTIONS.Stack = None
    #

##                                                                             

Regions = Container ()

Regions.regions = Container (
    NorthAtlantic    = Container (Basin="North Atlantic"         , ColorLine=np.array ([  0, 255,   0])/255, Marker='1' ),
    SubpolarNorthAtl = Container (Basin="Subpolar North Atlantic", ColorLine=np.array ([  0,   0,   0])/255, Marker='p' ),
    Labrador         = Container (Basin="Labrador Sea"           , ColorLine=np.array ([112, 160, 205])/255, Marker='s' ),
    Barents          = Container (Basin="Barents Sea"            , ColorLine=np.array ([196, 121,   0])/255, Marker='^' ),
    Irminger         = Container (Basin="Irminger Sea"           , ColorLine=np.array ([178, 178, 178])/255, Marker='v' ),
    NordicSeas       = Container (Basin="Nordic Seas"            , ColorLine=np.array ([  0,  52, 102])/255, Marker='<' ),     
    Rockal           = Container (Basin="Rockal"                 , ColorLine=np.array ([  0,  79,   0])/255, Marker='>' ),
    MedWest          = Container (Basin="Mediterranean (west)"   , ColorLine=np.array ([255,   0,   0])/255, Marker='P' ),        
    MedEast          = Container (Basin="Mediterranean (east)"   , ColorLine=np.array ([0  ,   0, 255])/255, Marker='x' ),     
    Wedell           = Container (Basin="Wedell Sea"             , ColorLine=np.array ([0  ,   0, 255])/255, Marker='x' ),     
    Davis            = Container (Basin="Davis Sector"           , ColorLine=np.array ([255,   0,   0])/255, Marker='p' ),
    Circum           = Container (Basin="Circum Polar"           , ColorLine=np.array ([0  , 255,   0])/255, Marker='p' ),  
    )

Regions.eORCA1 = Container (
    NorthAtlantic    = Container (index={'x':slice(226,299), 'y':slice(259,313)} ),
    SubpolarNorthAtl = Container (index={'x':slice(226,299), 'y':slice(259,281)} ),
    Labrador         = Container (index={'x':slice(226,249), 'y':slice(260,288)} ),
    Barents          = Container (index={'x':slice(270,304), 'y':slice(312,330)} ),
    Irminger         = Container (index={'x':slice(246,267), 'y':slice(260,285)} ),
    NordicSeas       = Container (index={'x':slice(260,299), 'y':slice(283,313)} ),
    Rockal           = Container (index={'x':slice(265,290), 'y':slice(263,283)} ),
    MedWest          = Container (index={'x':slice(285,303), 'y':slice(235,253)} ),
    MedEast          = Container (index={'x':slice(302,325), 'y':slice(233,253)} ),
    Wedell           = Container (index={'x':slice(228,300), 'y':slice( 10,93)} ),
    Davis            = Container (index={'x':slice(  1, 20), 'y':slice( 60,93)} ),
    Circum           = Container (index={'x':slice(  1, -1), 'y':slice( 10,93)} ),
    )

Regions.ORCA2 = Container (
    NorthAtlantic    = Container (index={'x':slice(111,146), 'y':slice(109,135)} ),
    SubpolarNorthAtl = Container (index={'x':slice(111,146), 'y':slice(109,123)} ),
    Labrador         = Container (index={'x':slice(111,122), 'y':slice(112,127)} ),
    Barents          = Container (index={'x':slice(133,149), 'y':slice(134,160)} ),
    Irminger         = Container (index={'x':slice(121,131), 'y':slice(112,122)} ),
    NordicSeas       = Container (index={'x':slice(130,150), 'y':slice(119,135)} ),
    Rockal           = Container (index={'x':slice(130,143), 'y':slice(111,121)} ),
    MedWest          = Container (index={'x':slice(141,153), 'y':slice(100,108)} ),
    MedEast          = Container (index={'x':slice(153,179), 'y':slice( 95,105)} ),
    Wedell           = Container (index={'x':slice(112,149), 'y':slice(  2, 25)} ),
    Davis            = Container (index={'x':slice(  1, 10), 'y':slice( 10, 25)} ),
    Circum           = Container (index={'x':slice(  1, -1), 'y':slice(  2, 25)} ),)
        
# Regions.eORCA1 = Container (
#     SubpolarNorthAtl = Container (index={'x':slice(260,299), 'y':slice(259,281)}, Basin="Subpolar North Atlantic", ColorLine=np.array ([  0,   0,   0])/255, Marker='p' ),
#     Labrador         = Container (index={'x':slice(226,249), 'y':slice(264,288)}, Basin="Labrador Sea"           , ColorLine=np.array ([112, 160, 205])/255, Marker='s' ),
#     Barents          = Container (index={'x':slice(270,294), 'y':slice(312,330)}, Basin="Barents Sea"            , ColorLine=np.array ([196, 121,   0])/255, Marker='^' ),
#     Irminger         = Container (index={'x':slice(246,267), 'y':slice(271,285)}, Basin="Irminger Sea"           , ColorLine=np.array ([178, 178, 178])/255, Marker='v' ),
#     NordicSeas       = Container (index={'x':slice(260,299), 'y':slice(283,313)}, Basin="Nordic Seas"            , ColorLine=np.array ([  0,  52, 102])/255, Marker='<' ),      
#     Rockal           = Container (index={'x':slice(260,299), 'y':slice(283,313)}, Basin="Rockal"                 , ColorLine=np.array ([  0,  79,   0])/255, Marker='>' ), )

# Regions.ORCA2 = Container (
#     SubpolarNorthAtl = Container (index={'x':slice(130,150), 'y':slice(130,140)}, Basin="Subpolar North Atlantic", ColorLine=np.array ([  0,   0,   0])/255, Marker='p' ),
#     Labrador         = Container (index={'x':slice(113,125), 'y':slice(132,144)}, Basin="Labrador Sea"           , ColorLine=np.array ([112, 160, 205])/255, Marker='s' ),
#     Barents          = Container (index={'x':slice(135,149), 'y':slice(161,165)}, Basin="Barents Sea"            , ColorLine=np.array ([196, 121,   0])/255, Marker='^' ),
#     Irminger         = Container (index={'x':slice(123,214), 'y':slice(135,142)}, Basin="Irminger Sea"           , ColorLine=np.array ([178, 178, 178])/255, Marker='v' ),
#     NordicSeas       = Container (index={'x':slice(130,150), 'y':slice(141,156)}, Basin="Nordic Seas"            , ColorLine=np.array ([  0,  52, 102])/255, Marker='<' ),      
#     Rockal           = Container (index={'x':slice(130,150), 'y':slice(141,158)}, Basin="Rockal"                 , ColorLine=np.array ([  0,  79,   0])/255, Marker='>' ), )  
        
def __mmath__ (ptab, default=None) :
    '''Determines the type of tab : xarray, numpy or numpy.ma object ?

    Returns type
    '''
    push_stack ( f'__mmath__ ( ptab, {default=} )' )
    
    mmath = default
    if isinstance (ptab, xr.core.dataset.Dataset)     : mmath = 'dataset'
    if isinstance (ptab, xr.core.dataarray.DataArray) : mmath = xr
    if isinstance (ptab, np.ndarray)                  : mmath = np
    if isinstance (ptab, np.ma.MaskType)              : mmath = np.ma

    pop_stack ( f'__math_ : {mmath}' )
    return mmath

def __guess_nperio__ (jpj:int, jpi:int, nperio=None, out:str='nperio') :
    '''Tries to guess the value of nperio (periodicity parameter.

    See NEMO documentation for details)
    Inputs
    jpj    : number of latitudes
    jpi    : number of longitudes
    nperio : periodicity parameter
    '''
    push_stack ( f'__guess_nperio__ ( {jpj=} {jpi=} {nperio=}, {out=} )' )
    if nperio is None :
        nperio = __guess_config__ (jpj, jpi, nperio=None, out=out)
    pop_stack (  f'__guess_nperio__ : {nperio}' )
    return nperio

def __guess_config__ (jpj:int, jpi:int, nperio:bool=None, config=None, out='nperio') :
    '''Tries to guess the value of nperio (periodicity parameter).

    See NEMO documentation for details)
    Inputs
    jpj    : number of latitudes
    jpi    : number of longitudes
    nperio : periodicity parameter
    '''
    push_stack ( f'__guessConfig__ ( {jpj=}, {jpi=}, {nperio=}, {config=}, {out=}')
    
    #if OPTIONS.Debug : print ( f'__guess_config__ : {jpi=}, {jpj=}' )
    if nperio is None :
        ## Values for NEMO version < 4.2
        if ( (jpj == 149 and jpi == 182) or (jpj is None and jpi == 182) or
             (jpj == 149 or jpi is None) ) :
            # ORCA2. We choose legacy orca2.
            config, nperio, iperio, jperio, nfold, nftype = 'ORCA2.3' , 4, 1, 0, 1, 'T'
        if ((jpj == 332 and jpi == 362) or (jpj is None and jpi == 362) or
            (jpj ==  332 and jpi is None) ) : # eORCA1.
            config, nperio, iperio, jperio, nfold, nftype = 'eORCA1.2', 6, 1, 0, 1, 'F'
        if jpi == 1442 :  # ORCA025.
            config, nperio, iperio, jperio, nfold, nftype = 'ORCA025' , 6, 1, 0, 1, 'F'
        if jpj ==  294 : # ORCA1
            config, nperio, iperio, jperio, nfold, nftype = 'ORCA1'   , 6, 1, 0, 1, 'F'

        ## Values for NEMO version >= 4.2. No more halo points
        if  (jpj == 148 and jpi == 180) or (jpj is None and jpi == 180) or \
            (jpj == 148 and jpi is None) :  # ORCA2. We choose legacy orca2.
            config, nperio, iperio, jperio, nfold, nftype = 'ORCA2.4' , 4.2, 1, 0, 1, 'F'
        if  (jpj == 331 and jpi == 360) or (jpj is None and jpi == 360) or \
            (jpj == 331 and jpi is None) : # eORCA1.
            config, nperio, iperio, jperio, nfold, nftype = 'eORCA1.4', 6.2, 1, 0, 1, 'F'
        if jpi == 1440 : # ORCA025.
            config, nperio, iperio, jperio, nfold, nftype = 'ORCA025' , 6.2, 1, 0, 1, 'F'

        if nperio is None :
            raise ValueError ('in nemo module : nperio not found, and cannot by guessed')

        if nperio in NPERIO_VALID_RANGE :
            if OPTIONS['Debug'] :
                print ( f'nperio set as {nperio} (deduced from {jpj=} and {jpi=})' )
        else :
            raise ValueError ( f'nperio set as {nperio} (deduced from {jpi=} and {jpj=}) : \n'+
                                'nemo.py is not ready for this value' )

    if out == 'nperio'        :
        pop_stack ( f'__guessConfig__ : {nperio=}' )
        return nperio
    if out == 'config'        :
        return config
        pop_stack ( f'__guessConfig__ : {config=}' )
    if out == 'perio'         :
        return iperio, jperio, nfold, nftype
        pop_stack ( f'__guessConfig__ : {iperio=}, {jperio=}, {nfold=}, {nftype=}' )
    if out in ['full', 'all'] :
        zdict = {'nperio':nperio, 'iperio':iperio, 'jperio':jperio, 'nfold':nfold, 'nftype':nftype}
        pop_stack ( f'__guessConfig__ : {zdict}' )
        return zdict

def __guess_point__ (ptab) :
    '''Tries to guess the grid point (periodicity parameter.

    See NEMO documentation for details)
    For array conforments with xgcm requirements

    Inputs
         ptab : xarray array

    Credits : who is the original author ?
    '''
    push_stack ( f'__guess_point__ ( ptab )')

    gp = None
    mmath = __mmath__ (ptab)
    if mmath == xr :
        if ('x_c' in ptab.dims and 'y_c' in ptab.dims )                        : gp = 'T'
        if ('x_f' in ptab.dims and 'y_c' in ptab.dims )                        : gp = 'U'
        if ('x_c' in ptab.dims and 'y_f' in ptab.dims )                        : gp = 'V'
        if ('x_f' in ptab.dims and 'y_f' in ptab.dims )                        : gp = 'F'
        if ('x_c' in ptab.dims and 'y_c' in ptab.dims and 'z_c' in ptab.dims ) : gp = 'T'
        if ('x_c' in ptab.dims and 'y_c' in ptab.dims and 'z_f' in ptab.dims ) : gp = 'W'
        if ('x_f' in ptab.dims and 'y_c' in ptab.dims and 'z_f' in ptab.dims ) : gp = 'U'
        if ('x_c' in ptab.dims and 'y_f' in ptab.dims and 'z_f' in ptab.dims ) : gp = 'V'
        if ('x_f' in ptab.dims and 'y_f' in ptab.dims and 'z_f' in ptab.dims ) : gp = 'F'

        if gp is None :
            raise AttributeError ('in nemo module : cd_type not found, and cannot by guessed')
        if OPTIONS.Debug : print ( f'Grid set as {gp} deduced from dims {ptab.dims}' )

        pop_stack ( f'__guess_point__ : {gp}' )
        return gp
    else :
        pop_stack ( f'__guess_point__ : cd_type not found, input is not an xarray data' )
        raise AttributeError  ('in nemo module : cd_type not found, input is not an xarray data')

def get_shape (ptab) :
    '''Get shape of ptab return a string with axes names

    shape may contain X, Y, Z or T
    Y is missing for a latitudinal slice
    X is missing for on longitudinal slice
    etc ...
    '''
    push_stack ( f'get_shape ( ptab )' )
    g_shape = ''
    if find_axis (ptab, 'x')[0] : g_shape = 'X'
    if find_axis (ptab, 'y')[0] : g_shape = 'Y' + g_shape
    if find_axis (ptab, 'z')[0] : g_shape = 'Z' + g_shape
    if find_axis (ptab, 't')[0] : g_shape = 'T' + g_shape
        
    pop_stack ( f'get_shape : {g_shape}' )
    return g_shape

def lbc_diag (nperio:int) :
    '''Useful to switch between field with and without halo'''
    push_stack ( f'lbc_diag ( {nperio=}' )
    lperio, aperio = nperio, False
    if nperio == 4.2 : lperio, aperio = 4, True
    if nperio == 6.2 : lperio, aperio = 6, True

    pop_stack ( f'lbc_diag : {lperio}, {aperio}' )
    return lperio, aperio

def find_axis (ptab, axis='z', back:bool=True) :
    '''Returns name and name of the requested axis'''
    push_stack ( f'find_axis ( ptab, {axis=}, {back=}' )
    
    mmath = __mmath__ (ptab)
    ax, ix = None, None

    ax_name   = axis
    unit_list = None
    length    = None
    
    if axis in XNAME :
        ax_name   = XNAME
        unit_list = XUNIT
        length    = XLENGTH
        if OPTIONS.Debug : print ( f'Working on xaxis found by name : {axis=} : {XNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in YNAME :
        ax_name   = YNAME
        unit_list = YUNIT
        length    = YLENGTH
        if OPTIONS.Debug : print ( f'Working on yaxis found by name : {axis=} : {YNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in ZNAME :
        ax_name   = ZNAME
        unit_list = ZUNIT
        length    = ZLENGTH
        if OPTIONS.Debug : print ( f'Working on zaxis found by name : {axis=} : {ZNAME=} {ax_name=} {unit_list=} {length=}' )
    if axis in TNAME :
        ax_name   = TNAME
        unit_list = TUNIT
        length    = None
        ax_name, unit_list, length = TNAME, TUNIT, None
        if OPTIONS.Debug : print ( f'Working on taxis found by name : {axis=} : {TNAME=} {ax_name=} {unit_list=} {length=}' )

    if OPTIONS.Debug :
        print ( f'{ax_name=}')
        print ( f'{unit_list=}')
        print ( f'{length=}' )
            
    if mmath in [xr, 'dataset'] :
        # Try by axis attributes
        if ix is None :
            if OPTIONS.Debug : print ( 'ix not found - 1' )
            for ii, dim in enumerate (ptab.dims) :
                if OPTIONS.Debug : print ( f'{ii=} {dim=}' )
                if 'axis' in ptab.coords[dim].attrs.keys() :
                    l_axis = ptab.coords[dim].attrs['axis']
                    if OPTIONS.Debug : print ( f'Rule 1 : Trying {ii=} {dim=} {l_axis=}' )
                    if l_axis in ax_name and l_axis == 'X' :
                        if OPTIONS.Debug : print ( f'Rule 1 : xaxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                        ix, ax = (ii, dim)
                    if l_axis in ax_name and l_axis == 'Y' :
                        if OPTIONS.Debug : print ( f'Rule 1 : yaxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                        ix, ax = (ii, dim)
                    if l_axis in ax_name and l_axis == 'Z' :
                        if OPTIONS.Debug : print ( f'Rule 1 : zaxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                        ix, ax = (ii, dim)
                    if l_axis in ax_name and l_axis == 'T' :
                        if OPTIONS.Debug : print ( f'Rule 1 : taxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                        ix, ax = (ii, dim)

        # Try by name
        if ix is None :
            for ii, dim in enumerate (ptab.dims) :
                if OPTIONS['Debug'] : print ( f'{ii=} {dim=}' )
                if dim in ax_name :
                    if OPTIONS.Debug : print ( f'Rule 2 : {dim=} axis found by name in : {ax_name=}' )
                    ix, ax = ii, dim

 
        # If not found, try by units
        if ix is None :
            for ii, dim in enumerate (ptab.dims) :
                if 'units' in ptab.coords[dim].attrs.keys() and unit_list :
                    for name in unit_list :
                        if name in ptab.coords[dim].attrs['units'] :
                            if OPTIONS.Debug : print ( f'Rule 3 : {name=} found by unit : {axis=} : {unit_list=} {ii=} {dim=}' )
                            ix, ax = ii, dim

    # If numpy array or dimension not found, try by length
    if mmath not in [xr, 'dataset'] or not ix :
        if length :
            if mmath in [xr, 'dataset'] :
                l_shape =[ len (x) for x in ptab.dims ]
            else :
                l_shape = ptab.shape
            for nn in np.arange ( len(l_shape) ) :
                if l_shape[nn] in length :
                    ix = nn ; ax = None
                    if OPTIONS.Debug : print ( f'Rule 4 : {ax_name=} axis found by length : {axis=} : {XNAME=} {ix=} {ax=}' )

    if ix and back :
        if mmath in [xr, 'dataset'] :
            ix -= len (ptab.dims)
        else :
            ix -= len (ptab.shape)

    pop_stack ( f'find_axis : {ax}, {ix}' )
    return ax, ix

def find_axis_bounds (ds, axis='z') :
    '''
    Find axis and associated bounds
    '''
    push_stack ( f'find_axis_bounds ( ds, {axis=}' )

    ax, ix = find_axis (ds, axis)
    if OPTIONS.Debug : print ( f'{ax=} {ix=}' )

    ab    = None
    bdim = None
    for bname in BNAME :
        zname = f'{ax}_{bname}'
        if OPTIONS.Debug : print ( f'{zname=}' )
        for ii, var in enumerate (ds.variables) :
            if zname == var :
                ab = zname
                ib = ii

    if ab :
        for dim in ds[ab].dims :
            if dim != ax :               
                bdim = dim
                
    pop_stack ( f'find_axis_bounds : {ax=}, {ab=} {bdim=}' )

    return ax, ab, bdim

def build_bounds1d (ds, axis='z') :
    '''
    Build bounds variable at the XGCM format
    '''
    push_stack ( f'build_bounds ( ds, {axis=}' )

    depth_bnds1d = None
    
    var, var_bnds1d, bdim = find_axis_bounds (ds, axis)
    if bdim : 
        az, kz = find_axis ( ds[var], axis)
        ab, kb = find_axis ( ds[var_bnds1d], bdim)
        
        if OPTIONS.Debug : print (var, var_bnds1d, bdim, az, kz, ab, kb )
        
        lshape = list(ds[var].shape)
        lshape[kz] = lshape[kz]+1
        ldims=list(ds[var].dims)
        ldims[kz] = ldims[kz] + '_bnds1d'
        
        depth_bnds1d = xr.DataArray (np.empty (lshape), dims=ldims)
        depth_bnds1d[{ldims[kz]:slice(0,-1)}] = ds[var_bnds1d].isel({bdim:0}).values
        depth_bnds1d[{ldims[kz]:-1}]          = ds[var_bnds1d].isel({az:-1, bdim:1}).values

    pop_stack ( 'build_bounds1d' )

    return depth_bnds1d

def add_bounds1d (ds) :
    '''
    Add bounds variable for T and Z axis, at the XGCM format
    '''
    push_stack ( f'add_bounds1d ( ds )' )

    az, ik = find_axis (ds, 'z')
    at, il = find_axis (ds, 't')
    z_bnds = build_bounds1d (ds, 'z')
    t_bnds = build_bounds1d (ds, 't')

    if OPTIONS.Debug :
        print ( f'{az=} {ik=} {at=} {il=}' )
    
    if not z_bnds is None : ds = ds.merge ({f'{az}_bnds1d':z_bnds})
    if not t_bnds is None : ds = ds.merge ({f'{at}_bnds1d':t_bnds})

    pop_stack ('add_bounds1d : ds')
    return ds

# if xc : 
#     def grid (ds:
#         ds = add_bounds1d (ds)
#         az, kz = find_axis (ds, 'z')
#         at, kt = find_axis (ds, 't')
#         grid = xc.regridder.xgcm.Grid (ds, coords={az:{'center':az,'outer':f'{az}_bnds1d'},
#                                                    at:{'center':at, 'outer':f'{at}_bnds1d'}},
#                                        periodic=False)
        
#         return grid

def fixed_lon (plon, center_lon:float=0.0) :
    '''
    Returns corrected longitudes for nicer plots

    lon        : longitudes of the grid. At least 2D.
    center_lon : center longitude. Default=0.

    Designed by Phil Pelson.
    See https://gist.github.com/pelson/79cf31ef324774c97ae7
    '''
    push_stack ( f'fixed_lon ( plon, {center_lon=}' )
    mmath = __mmath__ (plon)
    ax, ix = find_axis (plon, axis='x', back=True)
    
    f_lon = plon.copy ()

    f_lon = mmath.where (f_lon > center_lon+180., f_lon-360.0, f_lon)
    f_lon = mmath.where (f_lon < center_lon-180., f_lon+360.0, f_lon)

    for i, start in enumerate (np.argmax (np.abs (np.diff (f_lon, axis=ix)) > 180., axis=ix)) :
        f_lon [..., i, start+1:] += 360.

    # Special case for eORCA025
    if f_lon.shape [ix] == 1442 : f_lon [..., -2, :] = f_lon [..., -3, :]
    if f_lon.shape [ix] == 1440 : f_lon [..., -1, :] = f_lon [..., -2, :]

    if f_lon.min () > center_lon       : f_lon += -360.0
    if f_lon.max () < center_lon       : f_lon +=  360.0

    if f_lon.min () < center_lon-360.0 : f_lon +=  360.0
    if f_lon.max () > center_lon+360.0 : f_lon += -360.0

    pop_stack ( f'fixed_lon : f_lon' )
    return f_lon

def bounds_clolon (pbounds_lon, plon, rad:bool=False, deg:bool=True) :
    '''
    Choose closest to lon0 longitude, adding/substacting 360° if needed
    '''
    push_stack ( f'bounds_clolon (pbounds_lon, plon, {rad=}, {deg=})' )
    #if rad and deg :
        
    if rad : lon_range = 2.0*np.pi
    if deg : lon_range = 360.0
    b_clolon = pbounds_lon.copy ()

    b_clolon = xr.where ( b_clolon < plon-lon_range/2., b_clolon+lon_range, b_clolon )
    b_clolon = xr.where ( b_clolon > plon+lon_range/2., b_clolon-lon_range, b_clolon )

    pop_stack ( f'bounds_clolon : b_clolon' )
    return b_clolon

def unify_dims (dd: "DataArray or Dataset", x=None, y=None, z=None, t=None, xgrid=None, xgcm=None ) -> "DataArray or Dataset" :
    '''
    Rename dimensions to unify them between NEMO versions
    If grid is set, force to xgcm standard
    '''
    push_stack ( f'unify_dims (dd, {x=}, {y=}, {z=}, {t=})' )

    if xgrid :
        match xgrid.upper() :
            case 'T' :
                x='x_c' ; y='y_c'; z='z_c'
            case 'U' :
                x='x_f' ; y='y_c'; z='z_c'
            case 'V' :
                x='x_c' ; y='y_f'; z='z_c'
            case 'F' :
                x='x_f' ; y='y_f'; z='z_c'
            case 'W' :
                x='x_c' ; y='y_c'; z='z_f'

    if xgcm :
        if 'x_grid_T' in dd.dims :
            dd = dd.rename ({'x_grid_T':'x_c'})
            if 'x_c' not in dd.coords :
                dd['x_c'] = np.arange (len(dd['x_c'])) + 1
                x = None
        if 'x_grid_U' in dd.dims :
            dd = dd.rename ({'x_grid_U':'x_f'})
            if 'x_c' not in dd.coords :
                dd['x_c']  = np.arange (len(dd['x_f'])) + 0.5
                dd.x_f.attrs.update({'c_grid_axis_shift':0.5})
                x = None
        if 'x_grid_V' in dd.dims :
            dd = dd.rename ({'x_grid_V':'x_c'})
            if 'x_c' not in dd.coords :
                dd['x_c'] = np.arange (len(dd['x_c'])) + 1
                x = None
        if 'x_grid_F' in dd.dims :
            dd = dd.rename ({'x_grid_F':'x_f'})
            if 'x_c' not in dd.coords :
                dd['x_c'] = np.arange (len(dd['x_f'])) + 0.5
                x = None
        if 'x_grid_W' in dd.dims :
            dd = dd.rename ({'x_grid_W':'x_c'})
            if 'x_c' not in dd.coords :
                dd['x_c'] = np.arange (len(dd['x_c'])) + 1
                x = None
        if 'y_grid_T' in dd.dims :
            dd = dd.rename ({'y_grid_T':'y_c'})
            if 'y_c' not in dd.coords :
                dd['y_c'] = np.arange (len(dd['y_c'])) + 1
                y = None
        if 'y_grid_U' in dd.dims :
            dd = dd.rename ({'y_grid_U':'y_f'})
            if 'y_c' not in dd.coords :
                dd['y_c'] = np.arange (len(dd['y_f'])) + 0.5
                dd.y_f.attrs.update({'c_grid_axis_shift':0.5})
                y = None
        if 'y_grid_V' in dd.dims :
            dd = dd.rename ({'y_grid_V':'y_c'})
            if 'y_c' not in dd.coords :
                dd['y_c'] = np.arange (len(dd['y_c'])) + 1
                y = None
        if 'y_grid_F' in dd.dims :
            dd = dd.rename ({'y_grid_F':'y_f'})
            if 'y_c' not in dd.coords :
                dd['y_c'] = np.arange (len(dd['y_f'])) + 0.5
                y = None
        if 'y_grid_W' in dd.dims :
            dd = dd.rename ({'y_grid_W':'y_c'})
            if 'y_c' not in dd.coords :
                dd['y_c'] = np.arange (len(dd['y_c'])) + 1
                y = None
         
    if x :
        if OPTIONS.Debug : print ( f"unify_dims : working on {x=}" )

        xx, ii = find_axis (dd, 'x')
        if xx and xx != x :
            if OPTIONS.Debug : print ( f"unify_dims : {xx} renamed to {x}" )
            dd = dd.rename ({xx:x})
            dd[x].attrs.update ({'axis':'X', 'name':x})
            if x == 'x_f' : dd.x_f.attrs.update({'c_grid_axis_shift':0.5})
        if xgrid :
            if x == 'x_c' and 'x_c' in dd.dims and 'x_c' not in dd.coords :
                dd['x_c'] = np.arange (len(dd[x])) + 1
            if x == 'x_f' and 'x_f' in dd.dims and 'x_f' not in dd.coords :
                dd['x_f'] = np.arange (len(dd[x])) + 0.5

    if y :                    
        yy, jj = find_axis (dd, 'y')
        if yy and yy != y  :
            if OPTIONS.Debug : print ( f"unify_dims : {yy} renamed to {y}" )
            dd = dd.rename ( {yy:y} )
            dd[y].attrs.update ({'axis':'Y', 'name':y})
            if y == 'y_f' : dd.y_f.attrs.update ({'c_grid_axis_shift':0.5})
        if xgrid :
            if y == 'y_c' and 'y_c' in dd.dims and 'y_c' not in dd.coords :
                dd['y_c'] = np.arange (len(dd[y])) + 1
            if y == 'y_f' and 'y_f' in dd.dims and 'y_f' not in dd.coords :
                dd['y_f'] = np.arange (len(dd[y])) + 0.5

    if z : 
        zz, kk = find_axis (dd, 'z')
        if zz and zz != z :
            if OPTIONS.Debug : print ( f"unify_dims : {zz} renamed to {z}" )
            dd = dd.rename ({zz:z})
            dd[z].attrs.update ({'axis':'Z', 'name':z})
            if z == 'z_f' : dd.z_f.attrs.update ({'c_grid_axis_shift':0.5})
        if isinstance (dd, xr.core.dataset.Dataset) and z in dd.variables and 'bounds' in dd[z].attrs :
            bound_var =  dd[z].attrs['bounds']
            if bound_var in dd.variables :
                new_bv = bound_var.replace (zz, z)
                if new_bv != bound_var : 
                    dd = dd.rename ({bound_var:new_bv})
                    dd[z].attrs['bounds'] = new_bv

    if t : 
        tt, ll = find_axis (dd, 't')
        if tt and tt != t :
            if OPTIONS.Debug : print ( f"unify_dims : {tt} renamed to {t}" )
            dd = dd.rename ({tt:t})
            dd[t].attrs.update ({'axis':'T', 'name':t})
        if isinstance (dd, xr.core.dataset.Dataset) and t in dd.variables and 'bounds' in dd[t].attrs :
            bound_var =  dd[t].attrs['bounds']
            if bound_var in dd.variables :
                new_bv = bound_var.replace (tt, t)
                if new_bv != bound_var : 
                    dd = dd.rename ({bound_var:new_bv})
                    dd[t].attrs['bounds'] = new_bv
            
    pop_stack ( f'unify_dims : dd' )
    return dd

if SimpleImputer : 
    def fill_empty (ptab, sval:float=np.nan, transpose:bool=False) :
        '''
        Fill empty values

        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, have no
        values
        '''
        push_stack ( f'fill_empty ( ptab, {sval=} {transpose=}' )
        mmath = __mmath__ (ptab)

        imp = SimpleImputer (missing_values=sval, strategy='mean')
        if transpose :
            imp.fit (ptab.T)
            ztab = imp.transform (ptab.T).T
        else :
            imp.fit (ptab)
            ztab = imp.transform (ptab)

        if mmath == xr :
            ztab = xr.DataArray (ztab, dims=ztab.dims, coords=ztab.coords)
            ztab.attrs.update (ptab.attrs)

        pop_stack ( f'fill_empty : ztab' )
        return ztab

    def fill_latlon (plat, plon, sval=-1) :
        '''
        Fill latitude/longitude values

        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, have no
        lon/lat values
        '''
        push_stack ( f'fill_latlon ( plat, plon {sval=}' )

        from sklearn.impute import SimpleImputer
        mmath = __mmath__ (plon)
        
        imp = SimpleImputer (missing_values=sval, strategy='mean')
        imp.fit (plon)
        zlon = imp.transform (plon)
        imp.fit (plat.T)
        zlat = imp.transform (plat.T).T
        
        if mmath == xr :
            zlon = xr.DataArray (zlon, dims=plon.dims, coords=plon.coords)
            zlat = xr.DataArray (zlat, dims=plat.dims, coords=plat.coords)
            zlon.attrs.update (plon.attrs)
            zlat.attrs.update (plat.attrs)
            
        zlon = fixed_lon (zlon)

        pop_stack ( f'fixed_lon')
        return zlat, zlon
    
    def fill_lonlat (plon, plat, sval=-1) :
        '''
        Fill longitude/latitude values
        
        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, have no
        lon/lat values
        '''
        push_stack ( f'fill_lonlat ( plon, plat {sval=}' )
        from sklearn.impute import SimpleImputer
        mmath = __mmath__ (plon)
        
        imp = SimpleImputer (missing_values=sval, strategy='mean')
        imp.fit (plon)
        zlon = imp.transform (plon)
        imp.fit (plat.T)
        zlat = imp.transform (plat.T).T
        
        if mmath == xr :
            zlon = xr.DataArray (zlon, dims=plon.dims, coords=plon.coords)
            zlat = xr.DataArray (zlat, dims=plat.dims, coords=plat.coords)
            zlon.attrs.update (plon.attrs)
            zlat.attrs.update (plat.attrs)
            
        zlon = fixed_lon (zlon)

        pop_stack ( f'fill_lonlat' )
        return zlon, zlat

    def fill_bounds_lonlat (pbounds_lon, pbounds_lat, sval=-1) :
        '''
        Fill longitude/latitude bounds values
        
        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, as no
        lon/lat values
        '''
        push_stack ( f'fill_bounds_lonlat (pbounds_lon, pbounds_lat, {sval=}' )
        mmath = __mmath__ (pbounds_lon)
        
        z_bounds_lon = np.empty_like (pbounds_lon)
        z_bounds_lat = np.empty_like (pbounds_lat)
        
        imp = SimpleImputer (missing_values=sval, strategy='mean')
        
        for n in np.arange (4) :
            imp.fit (pbounds_lon[:,:,n])
            z_bounds_lon[:,:,n] = imp.transform (pbounds_lon[:,:,n])
            imp.fit (pbounds_lat[:,:,n].T)
            z_bounds_lat[:,:,n] = imp.transform (pbounds_lat[:,:,n].T).T
            
        if mmath == xr :
            z_bounds_lon = xr.DataArray (pbounds_lon, dims=pbounds_lon.dims,
                                            coords=pbounds_lon.coords)
            z_bounds_lat = xr.DataArray (pbounds_lat, dims=pbounds_lat.dims,
                                            coords=pbounds_lat.coords)
            z_bounds_lon.attrs.update (pbounds_lat.attrs)
            z_bounds_lat.attrs.update (pbounds_lat.attrs)

        pop_stack ( 'fill_bounds_lonlat' )
        return z_bounds_lon, z_bounds_lat
    
else : 
    print ("Import error of sklearn.impute.SimpleImputer")
    def fill_empty (ptab, sval=np.nan, transpose=False) :
        '''
        Void version of fill_empy, because module sklearn.impute.SimpleImputer is not available

        fill_empty : 
          Fill values

          Useful when NEMO has run with no wet points options :
          some parts of the domain, with no ocean points, have no
          values
        '''
        push_stack ( f'fill_empty [void version] ( ptab, {sval=} {transpose=}' )

        print ( 'Error : module sklearn.impute.SimpleImputer not found' )
        print ( 'Can not call fill_empty' )
        print ( 'Call arguments where : ' )
        print ( f'{ptab.shape=} {sval=} {transpose=}' )
        pop_stack ( f'fill_empty [void version]' )
        return ptab

    def fill_latlon (plat, plon, sval=-1) :
        '''
        Void version of fill_latlon, because module sklearn.impute.SimpleImputer is not available

        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, have no
        lon/lat values
        '''
        push_stack ( f'fill_latlon [void_version] ( plat, plon {sval=}' )

        print ( 'Error : module sklearn.impute.SimpleImputer not found' )
        print ( 'Can not call fill_empty' )
        print ( 'Call arguments where : ' )
        print ( f'{plat.shape=} {sval=}' )

        pop_stack ( f'fixed_lon [void version]')
        return plat, plon
        
    def fill_lonlat (plon, plat, sval=-1) :
        ''''
        Void version of fill_lonlat, because module sklearn.impute.SimpleImputer is not available
        
        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, have no
        lon/lat values
        '''
        push_stack ( f'fill_lonlat [void Version] ( plon, plat {sval=}' )

        print ( 'Error : module sklearn.impute.SimpleImputer not found' )
        print ( 'Can not call fill_empty' )
        print ( 'Call arguments where : ' )
        print ( f'{plat.shape=} {sval=}' )

        pop_stack ( f'fill_lonlat [void version]' )
        return plon, plat
    
    def fill_bounds_lonlat (pbounds_lon, pbounds_lat, sval=-1) :
        ''''
        Void version of fill_bounds_lonlat, because module sklearn.impute.SimpleImputer is not available
        
        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, as no
        lon/lat values
        '''
        push_stack ( f'fill_bounds_lonlat [void version] (pbounds_lon, pbounds_lat, {sval=}' )

        print ( 'Error : module sklearn.impute.SimpleImputer not found' )
        print ( 'Can not call fill_empty' )
        print ( 'Call arguments where : ' )
        print ( f'{pbounds_lat.shape=} {sval=}' )

        pop_stack ( 'fill_bounds_lonlat [void version]' )
        return pbounds_lon, pbounds_lat

def jeq (plat) :
    '''
    Returns j index of equator in the grid

    lat : latitudes of the grid. At least 2D.
    '''
    push_stack ( f'jeq (plat) ' )
    mmath = __mmath__ (plat)
    ay, jy = find_axis (plat, 'y')

    if mmath == xr : jj = int (np.mean (np.argmin (np.abs (np.float64 (plat)), axis=jy)))
    else           : jj = np.argmin (np.abs (np.float64 (plat[...,:, 0])))

    pop_stack ( f'jeq : {jj}' )
    return jj

def lon1d (plon, plat=None) :
    '''
    Returns 1D longitude for simple plots.

    plon : longitudes of the grid
    plat (optionnal) : latitudes of the grid
    '''
    push_stack ( f'lon1d (plon, plat) ' ) 
    mmath = __mmath__ (plon)
    jpj, jpi  = plon.shape [-2:]
    if np.max (plat) :
        je     = jeq (plat)
        lon0   = plon [..., je, 0].copy().item()
        dlon   = (plon [..., je, 1].copy() - plon [..., je, 0].copy()).item()
        lon_1d = np.linspace (start=lon0, stop=lon0+360.+2*dlon, num=jpi)
    else :
        lon0   = plon [..., jpj//3, 0].copy().item()
        dlon   = (plon [..., jpj//3, 1].copy() - plon [..., jpj//3, 0].copy()).item()
        lon_1d = np.linspace ( start=lon0, stop=lon0+360.+2*dlon, num=jpi )

    if mmath == xr :
        lon_1d = xr.DataArray( lon_1d, dims=('lon',), coords=(lon_1d,))
        lon_1d.attrs.update (plon.attrs)
        lon_1d.attrs['units']         = 'degrees_east'
        lon_1d.attrs['standard_name'] = 'longitude'
        lon_1d.attrs['long_name :']   = 'Longitude'

    pop_stack ( 'lon_1d' )
    return lon_1d

def latreg (plat, diff=0.1) :
    '''
    Returns maximum j index where gridlines are along latitudes
    in the northern hemisphere

    lat : latitudes of the grid (2D)
    diff [optional] : tolerance
    '''
    push_stack ( f'latreg ( plat, {diff=}' )
    #mmath = __mmath__ (plat)
    ax, ix = find_axis (plat, 'x')
    ay, iy = find_axis (plat, 'y')
    if OPTIONS.Debug : print ( f'Found axis : {ax=} {ix=} {ay=} {iy=}' )

    if diff is None :
        dy = np.float64 (np.mean (np.abs (plat -
                        np.roll (plat,shift=1,axis=iy, roll_coords=False))))
        if OPTIONS.Debug : print ( f'latreg : {dy=}' )
        diff = dy/100.

    je = jeq (plat)
    if OPTIONS.Debug : print ( f'{je=}')
    if ix : 
        #jreg   = np.where (plat[...,je:,:].max(axis=ix) -
        #                   plat[...,je:,:].min(axis=ix)  < diff)[-1][-1] + je
        #lareg  = np.float64 (plat[...,jreg,:].mean(axis=ix))
        jreg   = np.count_nonzero  (plat.isel({ay:slice(je,None)}).max(dim=ax) -
                           plat.isel({ay:slice(je,None)}).min(dim=ax)  < diff) + je
        lareg  = np.float64 (plat.isel({ay:jreg}).mean(dim=ax))
    else : 
        jreg  = len (plat)
        lareg = np.max (plat)
        
    pop_stack ( f'latreg : {jreg=}, {lareg=}' )
    return jreg, lareg

def lat1d (plat) :
    '''
    Returns 1D latitudes for zonal means and simple plots.

    plat : latitudes of the grid (2D)
    '''
    push_stack ( f'lat1d ( plat )' )
    mmath = __mmath__ (plat)
    ax, ix = find_axis (plat, 'x')
    ay, iy = find_axis (plat, 'y')
    jpj = plat.shape[iy]

    dy     = np.float64 (np.mean (np.abs (plat - np.roll (plat, shift=1, axis=iy))))
    je     = jeq (plat)
    if ix : 
        lat_eq = np.float64 (plat[...,je,:].mean(axis=ix))
    else : 
        lat_eq = np.float64 (plat[...,je])
                                  
    jreg, lat_reg = latreg (plat)
    if ix : 
        lat_ave = np.mean (plat, axis=ix)
    else :
        lat_ave = plat
        
    if np.abs (lat_eq) < dy/100. : # T, U or W grid
        if jpj-1 > jreg : dys = (90.-lat_reg) / (jpj-jreg-1)*0.5
        else            : dys = (90.-lat_reg) / 2.0
        yrange = 90.-dys-lat_reg
    else :  yrange = 90.-lat_reg # V or F grid

    if jpj-1 > jreg :
        lat_1d = mmath.where (lat_ave<lat_reg,
                 lat_ave,
                 lat_reg + yrange * (np.arange(jpj)-jreg)/(jpj-jreg-1) )
    else :
        lat_1d = lat_ave
    lat_1d[-1] = 90.0

    if mmath == xr :
        lat_1d = xr.DataArray( lat_1d.values, dims=('lat',), coords=(lat_1d,))
        lat_1d.attrs.update (plat.attrs)
        lat_1d.attrs ['units']         = 'degrees_north'
        lat_1d.attrs ['standard_name'] = 'latitude'
        lat_1d.attrs ['long_name :']   = 'Latitude'

    pop_stack ( f'lat1d' )
    return lat_1d

def latlon1d (plat, plon) :
    '''
    Returns simple latitude and longitude (1D) for simple plots.

    plat, plon : latitudes and longitudes of the grid (2D)
    '''
    push_stack ( f'latlon1d ( plat, plon) ' )
    zla = lat1d (plat)
    zlo = lon1d (plon, plat)

    pop_stack ( f'latlon1d' )
    return zla, zlo

def ff (plat) :
    '''
    Returns Coriolis factor
    '''
    push_stack ( 'ff ( plat )' )
    zff   = np.sin (np.deg2rad(plat)) * ROMEGA
    pop_stack ( 'ff' )
    return zff

def beta (plat) :
    '''
    Return Beta factor (derivative of Coriolis factor)
    '''
    push_stack ( 'beta ( plat )' )
    zbeta = np.cos (np.deg2rad(plat)) * ROMEGA / RA
    pop_stack ( 'beta' )
    return zbeta

def mask_lonlat (ptab, x0, x1, y0, y1, lon, lat, sval=np.nan) :
    '''
    Returns masked values outside a lat/lon box
    '''
    push_stack ( f'mask_lonlat  (ptab, {x0=}, {x1=}, {y0=}, {y1=}, lon, lat, {sval=}' )
    mmath = __mmath__ (ptab)
    if mmath == xr :
        lon = lon.copy().to_masked_array()
        lat = lat.copy().to_masked_array()

    mask = np.logical_and (np.logical_and(lat>y0, lat<y1),
            np.logical_or (np.logical_or (
                np.logical_and (lon>x0, lon<x1),
                np.logical_and (lon+360>x0, lon+360<x1)),
                np.logical_and (lon-360>x0, lon-360<x1)))
    tab = mmath.where (mask, ptab, sval)

    pop_stack ( 'mask_lonlat' )
    return tab

def extend (ptab, blon=False, jplus=25, jpi=None, nperio=4) :
    '''
    Returns extended field eastward to have better plots,
    and box average crossing the boundary

    Works only for xarray and numpy data (?)
    Useful for plotting vertical sections in OCE and ATM.

    ptab : field to extend.
    blon  : (optional, default=False) : if True, add 360 in the extended
          parts of the field
    jpi   : normal longitude dimension of the field. extend does nothing
          if the actual size of the field != jpi
          (avoid to extend several times in notebooks)
    jplus (optional, default=25) : number of points added on
          the east side of the field

    '''
    push_stack ( f'extend ( ptab, {blon=}, {jplus=}, {jpi=}, {nperio=}' )
    mmath = __mmath__ (ptab)
    ix, ax = find_axis (ptab, axis, back)
    
    if ptab.shape[-1] == 1 : tabex = ptab

    else :
        if not jpi : jpi = ptab.shape[-1]

        if blon : xplus = -360.0
        else    : xplus =    0.0

        if ptab.shape[-1] > jpi :
            tabex = ptab
        else :
            if nperio in [ 0, 4.2 ] : istart, le, la = 0, jpi+1, 0
            if nperio == 1          : istart, le, la = 0, jpi+1, 0
            if nperio in [4, 6] : # OPA case with two halo points for periodicity
                # Perfect, except at the pole that should be masked by lbc_plot
                istart, le, la = 1, jpi-2, 1
            if mmath == xr :
                tabex = np.concatenate (
                     (ptab.values[..., istart   :istart+le+1    ] + xplus,
                      ptab.values[..., istart+la:istart+la+jplus]         ),
                      axis=ix)
                lon    = ptab.dims[-1]
                new_coords = []
                for coord in ptab.dims :
                    if coord == lon : new_coords.append ( np.arange( tabex.shape[-1]))
                    else            : new_coords.append ( ptab.coords[coord].values)
                tabex = xr.DataArray ( tabex, dims=ptab.dims,
                                           coords=new_coords )
            else :
                tabex = np.concatenate (
                    (ptab [..., istart   :istart+le+1    ] + xplus,
                     ptab [..., istart+la:istart+la+jplus]          ),
                     axis=ix)

    pop_stack ( 'extend' )
    return tabex

def orca2reg (dd, lat_name=None, lon_name=None, y_name=None, x_name=None) :
    '''
    Assign an ORCA dataset on a regular grid.

    For use in the tropical region.
    Inputs :
      ff : xarray dataset
      lat_name, lon_name : name of latitude and longitude 2D field in ff
      y_name, x_name     : namex of dimensions in ff

      Returns : xarray dataset with rectangular grid. Incorrect above 20°N
    '''
    push_stack ( f'orca2reg ( dd, {lat_name=}, {lon_name=}, {y_name=}, {x_name=}' )
    if not x_name : x_name, ix = find_axis (dd, axis='x')
    if not y_name : y_name, jy = find_axis (dd, axis='y')

    if not lon_name :
        for xn in LONNAME :
            if xn in dd.variables : lon_name = xn
    if not lat_name :
        for yn in LATNAME :
            if yn in dd.variables : lat_name = yn

    if OPTIONS.Debug :
        print ( 'orga2reg : ' )
        print ( f'{dd.dims=}'   )
        print ( f'{x_name=} {y_name=}' )
    
    # Compute 1D longitude and latitude
    ylat, xlon = fill_latlon (dd[lat_name], dd[lon_name], sval=-1)
    (zlat, zlon) = latlon1d (ylat, xlon)
    zdd = dd
    
    # Assign lon and lat as dimensions of the dataset
    if y_name in zdd.dims :
        zlat = xr.DataArray (zlat, coords=[zlat,], dims=['lat',])
        zdd  = zdd.rename_dims ({y_name: "lat",}).assign_coords (lat=zlat)
    if x_name in zdd.dims :
        zlon = xr.DataArray (zlon, coords=[zlon,], dims=['lon',])
        zdd  = zdd.rename_dims ({x_name: "lon",}).assign_coords (lon=zlon)
    # Force dimensions to be in the right order
    coord_order = ['lat', 'lon']
    for dim in [ 'olevel', 'depthw', 'depthv', 'depthu', 'deptht', 'depth', 'z',
                 'time_counter', 'time', 'tbnds',
                 'bnds', 'axis_nbounds', 'nvertex', 'two2', 'two1', 'two', 'four',] :
        if dim in zdd.dims : coord_order.insert (0, dim)

    zdd = zdd.transpose (*coord_order)

    pop_stack ( 'orca2reg' )
    return zdd

def lbc_init (ptab, nperio=None) :
    '''
    Prepare for all lbc calls

    Set periodicity on input field
    nperio    : Type of periodicity
      0       : No periodicity
      1, 4, 6 : Cyclic on i dimension (generaly longitudes) with 2 points halo
      2       : Obsolete (was symmetric condition at southern boundary ?)
      3, 4    : North fold T-point pivot (legacy ORCA2)
      5, 6    : North fold F-point pivot (ORCA1, ORCA025, ORCA2 with new grid for paleo)
    cd_type   : Grid specification : T, U, V or F

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_init ( ptab, {nperio=}' )
    jpi, jpj = None, None
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    if ax : jpi = ptab.shape[ix]
    if ay : jpj = ptab.shape[jy]

    if nperio is None : nperio = __guess_nperio__ (jpj, jpi, nperio)

    if nperio not in NPERIO_VALID_RANGE :
        raise AttributeError ( f'{nperio=} is not in the valid range {NPERIO_VALID_RANGE}' )

    pop_stack ( f'lbc_init : {jpj}, {jpi}, {nperio}' )
    return jpj, jpi, nperio

def lbc (ptab, nperio=None, cd_type='T', psgn=1.0, nemo_4U_bug=False) :
    '''
    Set periodicity on input field

    ptab      : Input array (works for rank 2 at least : ptab[...., lat, lon])
    nperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F
    psgn      : For change of sign for vector components (1 for scalars, -1 for vector components)

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_init ( ptab, {nperio=}, {cd_type=}, {psgn=}, {nemo_4U_bug=}' )

    jpi, nperio = lbc_init (ptab, nperio)[1:]
    ax     = find_axis (ptab, 'x')[0]
    ay     = find_axis (ptab, 'y')[0]
    psgn   = ptab.dtype.type (psgn)
    mmath  = __mmath__ (ptab)

    if mmath == xr : ztab = ptab.values.copy ()
    else           : ztab = ptab.copy ()

    if ax :
        #
        #> East-West boundary conditions
        # ------------------------------
        if nperio in [1, 4, 6] :
        # ... cyclic
            ztab [...,  0] = ztab [..., -2]
            ztab [..., -1] = ztab [...,  1]

        if ay :
            #
            #> North-South boundary conditions
            # --------------------------------
            if nperio in [3, 4] :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [..., -1, 1:       ] = psgn * ztab [..., -3, -1:0:-1      ]
                    ztab [..., -1, 0        ] = psgn * ztab [..., -3, 2            ]
                    ztab [..., -2, jpi//2:  ] = psgn * ztab [..., -2, jpi//2:0:-1  ]

                if cd_type == 'U' :
                    ztab [..., -1, 0:-1     ] = psgn * ztab [..., -3, -1:0:-1      ]
                    ztab [..., -1,  0       ] = psgn * ztab [..., -3,  1           ]
                    ztab [..., -1, -1       ] = psgn * ztab [..., -3, -2           ]

                    if nemo_4U_bug :
                        ztab [..., -2, jpi//2+1:-1] = psgn * ztab [..., -2, jpi//2-2:0:-1]
                        ztab [..., -2, jpi//2-1   ] = psgn * ztab [..., -2, jpi//2       ]
                    else :
                        ztab [..., -2, jpi//2-1:-1] = psgn * ztab [..., -2, jpi//2:0:-1]

                if cd_type == 'V' :
                    ztab [..., -2, 1:       ] = psgn * ztab [..., -3, jpi-1:0:-1   ]
                    ztab [..., -1, 1:       ] = psgn * ztab [..., -4, -1:0:-1      ]
                    ztab [..., -1, 0        ] = psgn * ztab [..., -4, 2            ]

                if cd_type == 'F' :
                    ztab [..., -2, 0:-1     ] = psgn * ztab [..., -3, -1:0:-1      ]
                    ztab [..., -1, 0:-1     ] = psgn * ztab [..., -4, -1:0:-1      ]
                    ztab [..., -1,  0       ] = psgn * ztab [..., -4,  1           ]
                    ztab [..., -1, -1       ] = psgn * ztab [..., -4, -2           ]

            if nperio in [4.2] :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [..., -1, jpi//2:  ] = psgn * ztab [..., -1, jpi//2:0:-1  ]
                if cd_type == 'U' : ztab [..., -1, jpi//2-1:-1] = psgn * ztab [..., -1, jpi//2:0:-1]
                if cd_type == 'V' : ztab [..., -1, 1:       ] = psgn * ztab [..., -2, jpi-1:0:-1   ]
                if cd_type == 'F' : ztab [..., -1, 0:-1     ] = psgn * ztab [..., -2, -1:0:-1      ]

            if nperio in [5, 6] :            #  North fold F-point pivot
                if cd_type in ['T', 'W']  :
                    ztab [..., -1, 0:       ] = psgn * ztab [..., -2, -1::-1       ]

                if cd_type == 'U' :
                    ztab [..., -1, 0:-1     ] = psgn * ztab [..., -2, -2::-1       ]
                    ztab [..., -1, -1       ] = psgn * ztab [..., -2, 0            ] # Bug ?

                if cd_type == 'V' :
                    ztab [..., -1, 0:       ] = psgn * ztab [..., -3, -1::-1       ]
                    ztab [..., -2, jpi//2:  ] = psgn * ztab [..., -2, jpi//2-1::-1 ]

                if cd_type == 'F' :
                    ztab [..., -1, 0:-1     ] = psgn * ztab [..., -3, -2::-1       ]
                    ztab [..., -1, -1       ] = psgn * ztab [..., -3, 0            ]
                    ztab [..., -2, jpi//2:-1] = psgn * ztab [..., -2, jpi//2-2::-1 ]

            #
            #> East-West boundary conditions
            # ------------------------------
            if nperio in [1, 4, 6] :
                # ... cyclic
                ztab [...,  0] = ztab [..., -2]
                ztab [..., -1] = ztab [...,  1]

    if mmath == xr :
        ztab = xr.DataArray ( ztab, dims=ptab.dims, coords=ptab.coords )
        ztab.attrs = ptab.attrs

    pop_stack ( 'lbc' )
    return ztab

def lbc_mask (ptab, nperio=None, cd_type='T', sval=np.nan) :
    '''
    Mask fields on duplicated points

    ptab      : Input array. Rank 2 at least : ptab [...., lat, lon]
    nperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_mask (ptab, {nperio=}, {cd_type=}, {sval=}' )
    jpi, nperio = lbc_init (ptab, nperio)[1:]
    ax = find_axis (ptab, 'x')[0]
    ay = find_axis (ptab, 'y')[0]
    ztab = ptab.copy ()

    if ax :
        #
        #> East-West boundary conditions
        # ------------------------------
        if nperio in [1, 4, 6] :
        # ... cyclic
            ztab [...,  0] = sval
            ztab [..., -1] = sval

        if ay :
            #
            #> South (in which nperio cases ?)
            # --------------------------------
            if nperio in [1, 3, 4, 5, 6] : ztab [..., 0, :] = sval

            #
            #> North-South boundary conditions
            # --------------------------------
            if nperio in [3, 4] :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [..., -1,  :         ] = sval
                    ztab [..., -2, :jpi//2  ] = sval

                if cd_type == 'U' :
                    ztab [..., -1,  :         ] = sval
                    ztab [..., -2, jpi//2+1:  ] = sval

                if cd_type == 'V' :
                    ztab [..., -2, :       ] = sval
                    ztab [..., -1, :       ] = sval

                if cd_type == 'F' :
                    ztab [..., -2, :       ] = sval
                    ztab [..., -1, :       ] = sval

            if nperio in [4.2] :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [..., -1, jpi//2  :  ] = sval
                if cd_type == 'U' : ztab [..., -1, jpi//2-1:-1] = sval
                if cd_type == 'V' : ztab [..., -1, 1:         ] = sval
                if cd_type == 'F' : ztab [..., -1, 0:-1       ] = sval

            if nperio in [5, 6] :            #  North fold F-point pivot
                if cd_type in ['T', 'W']  :
                    ztab [..., -1, 0:       ] = sval

                if cd_type == 'U' :
                    ztab [..., -1, 0:-1     ] = sval
                    ztab [..., -1, -1       ] = sval

                if cd_type == 'V' :
                    ztab [..., -1, 0:       ] = sval
                    ztab [..., -2, jpi//2:  ] = sval

                if cd_type == 'F' :
                    ztab [..., -1, 0:-1       ] = sval
                    ztab [..., -1, -1         ] = sval
                    ztab [..., -2, jpi//2+1:-1] = sval

    pop_stack ( 'lbc_mask' )
    return ztab

def lbc_plot (ptab, nperio=None, cd_type='T', psgn=1.0, sval=np.nan) :
    '''
    Set periodicity on input field, for plotting for any cartopy projection

      Points at the north fold are masked
      Points for zonal periodicity are kept
    ptab      : Input array. Rank 2 at least : ptab[...., lat, lon]
    nperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F
    psgn      : For change of sign for vector components
           (1 for scalars, -1 for vector components)

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_plot (ptab, {nperio=}, {cd_type=}, {psgn=}, {sval=}' )
    jpi, nperio = lbc_init (ptab, nperio)[1:]
    ax = find_axis (ptab, 'x')[0]
    ay = find_axis (ptab, 'y')[0]
    psgn   = ptab.dtype.type (psgn)
    ztab   = ptab.copy ()

    if ax :
        #
        #> East-West boundary conditions
        # ------------------------------
        if nperio in [1, 4, 6] :
            # ... cyclic
            ztab [..., :,  0] = ztab [..., :, -2]
            ztab [..., :, -1] = ztab [..., :,  1]

        if ay :
            #> Masks south
            # ------------
            if nperio in [4, 6] : ztab [..., 0, : ] = sval

            #
            #> North-South boundary conditions
            # --------------------------------
            if nperio in [3, 4] :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [..., -1,  :      ] = sval
                    #ztab [..., -2, jpi//2: ] = sval
                    ztab [..., -2, :jpi//2 ] = sval # Give better plots than above
                if cd_type == 'U' :
                    ztab [..., -1, : ] = sval

                if cd_type == 'V' :
                    ztab [..., -2, : ] = sval
                    ztab [..., -1, : ] = sval

                if cd_type == 'F' :
                    ztab [..., -2, : ] = sval
                    ztab [..., -1, : ] = sval

            if nperio in [4.2] :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [..., -1, jpi//2:  ] = sval
                if cd_type == 'U' : ztab [..., -1, jpi//2-1:-1] = sval
                if cd_type == 'V' : ztab [..., -1, 1:       ] = sval
                if cd_type == 'F' : ztab [..., -1, 0:-1     ] = sval

            if nperio in [5, 6] :            #  North fold F-point pivot
                if cd_type in ['T', 'W']  :
                    ztab [..., -1, : ] = sval

                if cd_type == 'U' :
                    ztab [..., -1, : ] = sval

                if cd_type == 'V' :
                    ztab [..., -1, :        ] = sval
                    ztab [..., -2, jpi//2:  ] = sval

                if cd_type == 'F' :
                    ztab [..., -1, :          ] = sval
                    ztab [..., -2, jpi//2+1:-1] = sval

    pop_stack ( 'lbc_plot' )
    return ztab

def lbc_add (ptab, nperio=None, cd_type=None, psgn=1) :
    '''
    Handles NEMO domain changes between NEMO 4.0 to NEMO 4.2

    Periodicity and north fold halos has been removed in NEMO 4.2
    This routine adds the halos if needed

    ptab      : Input array (works
      rank 2 at least : ptab[...., lat, lon]
    nperio    : Type of periodicity

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_add ( ptab, {nperio=}, {cd_type=}, {psgn=} )' )
    mmath = __mmath__ (ptab)
    nperio = lbc_init (ptab, nperio)[-1]
    lshape = get_shape (ptab)
    ix = find_axis (ptab, 'x')[-1]
    jy = find_axis (ptab, 'y')[-1]

    t_shape = np.array (ptab.shape)

    if nperio in [4.2, 6.2] :

        ext_shape = t_shape.copy()
        if 'X' in lshape :
            ext_shape[ix] = ext_shape[ix] + 2
        if 'Y' in lshape :
            ext_shape[jy] = ext_shape[jy] + 1

        if mmath == xr :
            ptab_ext = xr.DataArray (np.zeros (ext_shape), dims=ptab.dims)
            if 'X' in lshape and 'Y' in lshape :
                ptab_ext.values[..., :-1, 1:-1] = ptab.values.copy ()
            else :
                if 'X' in lshape : ptab_ext.values[...,      1:-1] = ptab.values.copy ()
                if 'Y' in lshape : ptab_ext.values[..., :-1      ] = ptab.values.copy ()
        else           :
            ptab_ext =               np.zeros (ext_shape)
            if 'X' in lshape and 'Y' in lshape :
                ptab_ext       [..., :-1, 1:-1] = ptab.copy ()
            else :
                if 'X' in lshape : ptab_ext [...,      1:-1] = ptab.copy ()
                if 'Y' in lshape : ptab_ext [..., :-1      ] = ptab.copy ()

        if nperio == 4.2 :
            ptab_ext = lbc (ptab_ext, nperio=4, cd_type=cd_type, psgn=psgn)
        if nperio == 6.2 :
            ptab_ext = lbc (ptab_ext, nperio=6, cd_type=cd_type, psgn=psgn)

        if mmath == xr :
            ptab_ext.attrs = ptab.attrs
            az = find_axis (ptab, 'z')[0]
            at = find_axis (ptab, 't')[0]
            if az : ptab_ext = ptab_ext.assign_coords ( {az:ptab.coords[az]} )
            if at : ptab_ext = ptab_ext.assign_coords ( {at:ptab.coords[at]} )

    else : ptab_ext = lbc (ptab, nperio=nperio, cd_type=cd_type, psgn=psgn)

    pop_stack ( 'lbc_add' )
    return ptab_ext

def lbc_del (ptab, nperio=None, cd_type='T', psgn=1) :
    '''
    Handles NEMO domain changes between NEMO 4.0 to NEMO 4.2

    Periodicity and north fold halos has been removed in NEMO 4.2
    This routine removes the halos if needed

    ptab      : Input array (works
      rank 2 at least : ptab[...., lat, lon]
    nperio    : Type of periodicity

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_del (ptab, {nperio=}, {cd_type=}, {psgn=}' )
    nperio = lbc_init (ptab, nperio)[-1]
    #lshape = get_shape (ptab)
    ax = find_axis (ptab, 'x')[0]
    ay = find_axis (ptab, 'y')[0]

    if nperio in [4.2, 6.2] :
        if ax or ay :
            if ax and ay : ztab = lbc (ptab[..., :-1, 1:-1], nperio=nperio, cd_type=cd_type, psgn=psgn)
            else :
                if ax    : ztab = lbc (ptab[...,      1:-1], nperio=nperio, cd_type=cd_type, psgn=psgn)
                if ay    : ztab = lbc (ptab[..., -1]       , nperio=nperio, cd_type=cd_type, psgn=psgn)
        else : ztab = ptab
    else : ztab = ptab

    pop_stack ( 'lbc_del' )
    return ztab

def lbc_index (jj, ii, jpj, jpi, nperio=None, cd_type='T') :
    '''
    For indexes of a NEMO point, give the corresponding point
        inside the domain (i.e. not in the halo)

    jj, ii    : indexes
    jpi, jpi  : size of domain
    nperio    : type of periodicity
    cd_type   : grid specification : T, U, V or F

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_index ( {jj=}, {ii=}, {jpj=}, {jpi=}, {nperio=}, {cd_type=} )' )
    if nperio is None :
        nperio = __guess_nperio__ (jpj, jpi, nperio)

    ## For the sake of simplicity, switch to the convention of original
    ## lbc Fortran routine from NEMO : starts indexes at 1
    jy = jj + 1
    ix = ii + 1

    mmath = __mmath__ (jj)
    if not mmath : mmath=np

    #
    #> East-West boundary conditions
    # ------------------------------
    if nperio in [1, 4, 6] :
        #... cyclic
        ix = mmath.where (ix==jpi, 2   , ix)
        ix = mmath.where (ix== 1 ,jpi-1, ix)

    #
    def mod_ij (cond, jy_new, ix_new) :
        push_stack ( f'mod_ij (cond, jy_new, ix_new)' )
        jy_r = mmath.where (cond, jy_new, jy)
        ix_r = mmath.where (cond, ix_new, ix)
        pop_stack ( 'mod_ij' )
        return jy_r, ix_r
    #
    #> North-South boundary conditions
    # --------------------------------
    if nperio in [ 3 , 4 ]  :
        if cd_type in  [ 'T' , 'W' ] :
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix>=2       ), jpj-2, jpi-ix+2)
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix==1       ), jpj-1, 3       )
            jy, ix = mod_ij (np.logical_and (jy==jpj-1, ix>=jpi//2+1),
                                  jy , jpi-ix+2)

        if cd_type in [ 'U' ] :
            jy, ix = mod_ij (np.logical_and (
                      jy==jpj  ,
                      np.logical_and (ix>=1, ix <= jpi-1)   ),
                                         jy   , jpi-ix+1)
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix==1  ) , jpj-2, 2       )
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix==jpi) , jpj-2, jpi-1   )
            jy, ix = mod_ij (np.logical_and (jy==jpj-1,
                            np.logical_and (ix>=jpi//2, ix<=jpi-1)), jy   , jpi-ix+1)

        if cd_type in [ 'V' ] :
            jy, ix = mod_ij (np.logical_and (jy==jpj-1, ix>=2  ), jpj-2, jpi-ix+2)
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix>=2  ), jpj-3, jpi-ix+2)
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix==1  ), jpj-3,  3      )

        if cd_type in [ 'F' ] :
            jy, ix = mod_ij (np.logical_and (jy==jpj-1, ix<=jpi-1), jpj-2, jpi-ix+1)
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix<=jpi-1), jpj-3, jpi-ix+1)
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix==1    ), jpj-3, 2       )
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix==jpi  ), jpj-3, jpi-1   )

    if nperio in [ 5 , 6 ] :
        if cd_type in [ 'T' , 'W' ] :                        # T-, W-point
            jy, ix = mod_ij (jy==jpj, jpj-1, jpi-ix+1)

        if cd_type in [ 'U' ] :                              # U-point
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix<=jpi-1   ), jpj-1, jpi-ix  )
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix==jpi     ), jpi-1, 1       )

        if cd_type in [ 'V' ] :    # V-point
            jy, ix = mod_ij (jy==jpj                                 , jy   , jpi-ix+1)
            jy, ix = mod_ij (np.logical_and (jy==jpj-1, ix>=jpi//2+1), jy   , jpi-ix+1)

        if cd_type in [ 'F' ] :                              # F-point
            jy, ix = mod_ij (np.logical_and (jy==jpj  , ix<=jpi-1   ), jpj-2, jpi-ix  )
            jy, ix = mod_ij (np.logical_and (ix==jpj  , ix==jpi     ), jpj-2, 1       )
            jy, ix = mod_ij (np.logical_and (jy==jpj-1, ix>=jpi//2+1), jy   , jpi-ix  )

    ## Restore convention to Python/C : indexes start at 0
    jy += -1 ; ix += -1

    if isinstance (jj, int) : jy = jy.item ()
    if isinstance (ii, int) : ix = ix.item ()

    pop_stack ( f'lbc_index = {jy}, {ix}' )
    return jy, ix

def find_ji (lat_data, lon_data, lat_grid, lon_grid, mask=1.0, drop_duplicates=False, out=None) :
    '''
    Description: seeks J,I indices of the grid point which is the closest
       of a given point

    Usage: go find_ji  <data latitude> <data longitude> <grid latitudes> <grid longitudes> [mask]
    <grid latitudes><grid longitudes> are 2D fields on J/I (Y/X) dimensions
    mask : if given, seek only non masked grid points (i.e with mask=1)

    Example : find_ji (40., -20., nav_lat, nav_lon, mask=1.0)

    Note : all longitudes and latitudes in degrees

    Note : may work with 1D lon_data/lat_data (?)
    '''
    push_stack ( f'find_ji ( lat_data, lon_data, lat_grid, lon_grid, mask, {drop_duplicates=}, {out=} ) ')
    # Get grid dimensions
    if len (lon_grid.shape) == 2 : jpi = lon_grid.shape[-1]
    else                         : jpi = len(lon_grid)

    #mmath = __mmath__ (lat_grid)

    if OPTIONS.Debug :
        print ( 'find_ij' )
        print ( f'{lat_data=}' )
        print ( f'{lon_data=}' )

    # Compute distance from the point to all grid points (in RADian)

    arg      = ( np.sin (np.deg2rad(lat_data)) * np.sin (np.deg2rad(lat_grid))
               + np.cos (np.deg2rad(lat_data)) * np.cos (np.deg2rad(lat_grid)) *
                 np.cos (np.deg2rad((lon_data-lon_grid))) )

    
    if OPTIONS.Debug : print ( f'{type(arg)=} {arg.shape=}' )
    
    # Send masked points to 'infinite'
    distance = np.arccos (arg) + 4.0*np.pi*(1.0-mask)

    if OPTIONS.Debug : print ( f'{type(distance)=} {distance.shape=}' )

    # Truncates to alleviate precision problem encountered with some grids
    prec = int (1E7)
    distance = (distance*prec).astype(int) / prec
    if OPTIONS.Debug : print ( f'{type(distance)=} {distance.shape=}' )
        
    # Compute index minimum of distance
    try :
        nn = len (lat_data)
    except : 
        nn = 0
        jimin = distance.argmin ().astype(int)
    else : 
        jimin   = np.empty (nn, dtype=int )
        for ji in np.arange (nn) :
            jimin[ji] = distance[ji].argmin()
    finally : 
        if OPTIONS.Debug :
            print ( f'{type(jimin)=} {jimin.shape}' )
            print ( f'{jimin=}' )

    # Compute 2D indices (Python/C flavor : starting at 0)
    jmin = jimin // jpi
    imin = jimin - jmin*jpi

    if OPTIONS.Debug :
        print ( f'{jmin=}' )
        print ( f'{imin=}' )
        
    if drop_duplicates :
        zz = np.vstack ( (np.array (jmin), np.array (imin)) )
        zz = np.swapaxes (zz , 0, 1)
        zz = np.unique ( zz, axis=0)
        jmin = zz[:,-2]
        imin = zz[:,-1]

    pop_stack ( 'find_ji' )
    if   out=='dict'                     :
        zdict = {UDIMS['y']:jmin, UDIMS['x']:imin}
        return zdict
    elif out in ['array', 'numpy', 'np'] :
        return np.array (jmin), np.array (imin)
    elif out in ['xarray', 'xr']         :
        jmin = xr.DataArray (jmin, dims=('Num',))
        imin = xr.DataArray (imin, dims=('Num',))
        jmin.attrs.update ( {'long_name':'j-index' } )
        imin.attrs.update ( {'long_name':'i-index' } )
        jmin.name = 'j_index'
        imin.name = 'j_index'
        return jmin, imin
    elif out=='list'                     :
        return [jmin, imin]
    elif out=='tuple'                    :
        return jmin, imin
    else                                 :
        return jmin, imin

def curl (tx, ty, e1f, e2f, nperio=None) :
    '''
    Returns curl of a horizontal vector field defined on the C-grid
    '''
    push_stack ( f'curl ( tx, ty, e1u, e2v, e1f, e2f, {nperio=} )' )
    ax = find_axis (tx, 'x')[0]
    ay = find_axis (ty, 'y')[0]

    tx_0    = lbc_add (tx*e1u , nperio=nperio, cd_type='U', psgn=-1)
    ty_0    = lbc_add (ty*e2v , nperio=nperio, cd_type='V', psgn=-1)
    e1e2f_0 = lbc_add (e1f*e2f, nperio=nperio, cd_type='F', psgn= 1)

    tx_1  = tx_0.roll ({ay:-1})
    ty_1  = ty_0.roll ({ax:-1})
    tx_1  = lbc (tx_1, nperio=nperio, cd_type='U', psgn=-1)
    ty_1  = lbc (ty_1, nperio=nperio, cd_type='V', psgn=-1)

    zcurl = ((ty_1 - ty_0) - (tx_1 - tx_0))/e1e2f_0

    mask = np.logical_or (
             np.logical_or (np.isnan(tx_0), np.isnan(tx_1)),
             np.logical_or (np.isnan(ty_0), np.isnan(ty_1)) )

    zcurl = zcurl.where (np.logical_not (mask), np.nan)

    zcurl = lbc_del (zcurl, nperio=nperio, cd_type='F', psgn=1)
    zcurl = lbc (zcurl, nperio=nperio, cd_type='F', psgn=1)

    pop_stack ( 'curl' )
    return zcurl

def div (ux, uy, e1t, e2t, e1u, e2u, nperio=None) :
    '''
    Returns divergence of a horizontal vector field defined on the C-grid
    '''
    push_stack ( f'div  (ux, uy, e1t, e2t, e1v, e2u, {nperio=}' )
    ax = find_axis (ux, 'x')[0]
    ay = find_axis (ux, 'y')[0]

    ux_0_e  = lbc_add (ux*e2u , nperio=nperio, cd_type='U', psgn=-1)
    uy_0_e  = lbc_add (uy*e1v , nperio=nperio, cd_type='V', psgn=-1)
    e1e2t_0 = lbc_add (e1t*e2t, nperio=nperio, cd_type='T', psgn= 1)

    ux_1 = ux_0.roll ({ay:1})
    uy_1 = uy_0.roll ({ax:1})
    ux_1 = lbc (ux_1, nperio=nperio, cd_type='U', psgn=-1)
    uy_1 = lbc (uy_1, nperio=nperio, cd_type='V', psgn=-1)

    zdiv = ((ux_0 - ux_1) + (uy_0 - uy_1))/e1e2t_0

    mask = np.logical_or (
             np.logical_or ( np.isnan(ux_0), np.isnan(ux_1)),
             np.logical_or ( np.isnan(uy_0), np.isnan(uy_1)) )

    zdiv = zdiv.where (np.logical_not (mask), np.nan)

    zdiv = lbc_del (zdiv, nperio=nperio, cd_type='T', psgn=1)
    zdiv = lbc (zdiv, nperio=nperio, cd_type='T', psgn=1)

    pop_stack ( 'zdiv' )
    return zdiv

def geo2en (pxx, pyy, pzz, glam, gphi) :
    '''
    Change vector from geocentric to east/north

    Inputs :
        pxx, pyy, pzz : components on the geocentric system
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( 'geo2en (pxx, pyy, pzz, glam, gphi)' )
    gsinlon = np.sin (np.deg2rad(glam))
    gcoslon = np.cos (np.deg2rad(glam))
    gsinlat = np.sin (np.deg2rad(gphi))
    gcoslat = np.cos (np.deg2rad(gphi))

    pte = - pxx * gsinlon            + pyy * gcoslon
    ptn = - pxx * gcoslon * gsinlat  - pyy * gsinlon * gsinlat + pzz * gcoslat

    pop_stack ( geo2en )
    return pte, ptn

def en2geo (pte, ptn, glam, gphi) :
    '''
    Change vector from east/north to geocentric

    Inputs :
        pte, ptn   : eastward/northward components
        glam, gphi : longitude and latitude of the points
    '''
    push_stack ( 'en2geo ( pte, ptn, glam, gphi )' )
    
    gsinlon = np.sin (np.deg2rad(glam))
    gcoslon = np.cos (np.deg2rad(glam))
    gsinlat = np.sin (np.deg2rad(gphi))
    gcoslat = np.cos (np.deg2rad(gphi))

    pxx = - pte * gsinlon - ptn * gcoslon * gsinlat
    pyy =   pte * gcoslon - ptn * gsinlon * gsinlat
    pzz =   ptn * gcoslat

    pop_stack ( 'en2geo' )
    return pxx, pyy, pzz


def clo_lon (lon, lon0=0., rad=False, deg=True) :
    '''
    Choose closest to lon0 longitude, adding/substacting 360°
    if needed
    '''
    push_stack ( f'clo_lon (lon, {lon0=}, {rad=}, {deg=} )' )
    if rad and deg :
        raise 
    mmath = __mmath__ (lon, np)
    if rad : lon_range = 2.*np.pi
    if deg : lon_range = 360.
    c_lon = lon
    c_lon = mmath.where (c_lon > lon0 + lon_range*0.5, c_lon-lon_range, c_lon)
    c_lon = mmath.where (c_lon < lon0 - lon_range*0.5, c_lon+lon_range, c_lon)
    c_lon = mmath.where (c_lon > lon0 + lon_range*0.5, c_lon-lon_range, c_lon)
    c_lon = mmath.where (c_lon < lon0 - lon_range*0.5, c_lon+lon_range, c_lon)
    if c_lon.shape == () : c_lon = c_lon.item ()
    if mmath == xr :
        if lon.attrs : c_lon.attrs.update (lon.attrs)

    pop_stack ( 'clo_lon' )
    return c_lon

def index2depth (pk, gdept_0) :
    '''
    From index (real, continuous), get depth

    Needed to use transforms in Matplotlib
    '''
    # No stack, debug or timing here, to avoid problem in Matplotlib
    jpk = gdept_0.shape[0]
    kk = xr.DataArray(pk)
    k  = np.maximum (0, np.minimum (jpk-1, kk    ))
    k0 = np.floor (k).astype (int)
    k1 = np.maximum (0, np.minimum (jpk-1,  k0+1))
    zz = k - k0
    gz = (1.0-zz)*gdept_0[k0]+ zz*gdept_0[k1]
    return gz.values

def depth2index (pz, gdept_0) :
    '''
    From depth, get index (real, continuous)

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpk  = gdept_0.shape[0]
    if   isinstance (pz, xr.core.dataarray.DataArray ) :
        zz   = xr.DataArray (pz.values , dims=('zz',))
    elif isinstance (pz,  np.ndarray) :
        zz   = xr.DataArray (pz.ravel(), dims=('zz',))
    else :
        zz   = xr.DataArray (np.array([pz]).ravel(), dims=('zz',))
    zz   = np.minimum (gdept_0[-1], np.maximum (0, zz))

    idk1 = np.minimum ( (gdept_0-zz), 0.).argmax (axis=0).astype(int)
    idk1 = np.maximum (0, np.minimum (jpk-1,  idk1  ))
    idk2 = np.maximum (0, np.minimum (jpk-1,  idk1-1))

    zff = (zz - gdept_0[idk2])/(gdept_0[idk1]-gdept_0[idk2])
    idk = zff*idk1 + (1.0-zff)*idk2
    idk = xr.where ( np.isnan(idk), idk1, idk)
    return idk.values

def index2depth_panels (pk, gdept_0, depth0, fact) :
    '''
    From  index (real, continuous), get depth, with bottom part compressed

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpk = gdept_0.shape[0]
    kk = xr.DataArray (pk)
    k  = np.maximum (0, np.minimum (jpk-1, kk    ))
    k0 = np.floor (k).astype (int)
    k1 = np.maximum (0, np.minimum (jpk-1,  k0+1))
    zz = k - k0
    gz = (1.0-zz)*gdept_0[k0]+ zz*gdept_0[k1]
    gz = xr.where ( gz<depth0, gz, depth0 + (gz-depth0)*fact)
    return gz.values

def depth2index_panels (pz, gdept_0, depth0, fact) :
    '''
    From  index (real, continuous), get depth, with bottom part compressed

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpk = gdept_0.shape[0]
    if isinstance (pz, xr.core.dataarray.DataArray) :
        zz   = xr.DataArray (pz.values , dims=('zz',))
    elif isinstance (pz, np.ndarray) :
        zz   = xr.DataArray (pz.ravel(), dims=('zz',))
    else :
        zz   = xr.DataArray (np.array([pz]).ravel(), dims=('zz',))
    zz         = np.minimum (gdept_0[-1], np.maximum (0, zz))
    gdept_comp = xr.where ( gdept_0>depth0,
                                (gdept_0-depth0)*fact+depth0, gdept_0)
    zz_comp    = xr.where ( zz     >depth0, (zz     -depth0)*fact+depth0,
                                zz     )
    zz_comp    = np.minimum (gdept_comp[-1], np.maximum (0, zz_comp))

    idk1 = np.minimum ( (gdept_0-zz_comp), 0.).argmax (axis=0).astype(int)
    idk1 = np.maximum (0, np.minimum (jpk-1,  idk1  ))
    idk2 = np.maximum (0, np.minimum (jpk-1,  idk1-1))

    zff = (zz_comp - gdept_0[idk2])/(gdept_0[idk1]-gdept_0[idk2])
    idk = zff*idk1 + (1.0-zff)*idk2
    idk = xr.where ( np.isnan(idk), idk1, idk)
    return idk.values

def depth2comp (pz, depth0, fact ) :
    '''
    Form depth, get compressed depth, with bottom part compressed

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    #print ('start depth2comp')
    if isinstance (pz, xr.core.dataarray.DataArray) :
        zz   = pz.values
    elif isinstance(pz, list) :
        zz = np.array (pz)
    else :
        zz   = pz
    gz = np.where ( zz>depth0, (zz-depth0)*fact+depth0, zz)
    if OPTIONS.Debug : print ( f'depth2comp : {gz=}' )
    if type (pz) in [int, float] : return gz.item()
    else                         : return gz

def comp2depth (pz, depth0, fact ) :
    '''
    Form compressed depth, get depth, with bottom part compressed

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    if isinstance (pz, xr.core.dataarray.DataArray) :
        zz   = pz.values
    elif isinstance (pz, list) :
        zz = np.array (pz)
    else :
        zz   = pz
    gz = np.where ( zz>depth0, (zz-depth0)/fact+depth0, zz)
    if type (pz) in [int, float] :
        gz = gz.item()

    return gz

def index2lon (pi, plon_1d) :
    '''
    From index (real, continuous), get longitude

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpi = plon_1d.shape[0]
    ii  = xr.DataArray (pi)
    i   =  np.maximum (0, np.minimum (jpi-1, ii    ))
    i0  = np.floor (i).astype (int)
    i1  = np.maximum (0, np.minimum (jpi-1,  i0+1))
    xx  = i - i0
    gx  = (1.0-xx)*plon_1d[i0]+ xx*plon_1d[i1]
    return gx.values

def lon2index (px, plon_1d) :
    '''
    From longitude, get index (real, continuous)

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpi  = plon_1d.shape[0]
    if isinstance (px, xr.core.dataarray.DataArray) :
        xx   = xr.DataArray (px.values , dims=('xx',))
    elif isinstance (px, np.ndarray) :
        xx   = xr.DataArray (px.ravel(), dims=('xx',))
    else :
        xx   = xr.DataArray (np.array([px]).ravel(), dims=('xx',))
    xx   = xr.where ( xx>plon_1d.max(), xx-360.0, xx)
    xx   = xr.where ( xx<plon_1d.min(), xx+360.0, xx)
    xx   = np.minimum (plon_1d.max(), np.maximum(xx, plon_1d.min() ))
    idi1 = np.minimum ( (plon_1d-xx), 0.).argmax (axis=0).astype(int)
    idi1 = np.maximum (0, np.minimum (jpi-1,  idi1  ))
    idi2 = np.maximum (0, np.minimum (jpi-1,  idi1-1))

    zff = (xx - plon_1d[idi2])/(plon_1d[idi1]-plon_1d[idi2])
    idi = zff*idi1 + (1.0-zff)*idi2
    idi = xr.where ( np.isnan(idi), idi1, idi)
    return idi.values

def index2lat (pj, plat_1d) :
    '''
    From index (real, continuous), get latitude

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpj = plat_1d.shape[0]
    jj  = xr.DataArray (pj)
    j   = np.maximum (0, np.minimum (jpj-1, jj    ))
    j0  = np.floor (j).astype (int)
    j1  = np.maximum (0, np.minimum (jpj-1,  j0+1))
    yy  = j - j0
    gy  = (1.0-yy)*plat_1d[j0]+ yy*plat_1d[j1]
    return gy.values

def lat2index (py, plat_1d) :
    '''
    From latitude, get index (real, continuous)

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpj = plat_1d.shape[0]
    if isinstance (py, xr.core.dataarray.DataArray) :
        yy   = xr.DataArray (py.values , dims=('yy',))
    elif isinstance (py, np.ndarray) :
        yy   = xr.DataArray (py.ravel(), dims=('yy',))
    else :
        yy   = xr.DataArray (np.array([py]).ravel(), dims=('yy',))
    yy   = np.minimum (plat_1d.max(), np.minimum(yy, plat_1d.max() ))
    idj1 = np.minimum ( (plat_1d-yy), 0.).argmax (axis=0).astype(int)
    idj1 = np.maximum (0, np.minimum (jpj-1,  idj1  ))
    idj2 = np.maximum (0, np.minimum (jpj-1,  idj1-1))

    zff = (yy - plat_1d[idj2])/(plat_1d[idj1]-plat_1d[idj2])
    idj = zff*idj1 + (1.0-zff)*idj2
    idj = xr.where ( np.isnan(idj), idj1, idj)
    return idj.values

def angle_full (glamt, gphit, glamu, gphiu, glamv, gphiv,
                glamf, gphif, nperio=None) :
    '''
    Computes sinus and cosinus of model line direction with
    respect to east
    '''
    push_stack ( f'angle_full ( glamt, gphit, glamu, gphiu, glamv, gphiv, glamf, gphif, {nperio=} )') 
    mmath = __mmath__ (glamt)
    ax, ix = find_axis (glamt, 'x')
    ay, iy = find_axis (glamt, 'y')

    zlamt = lbc_add (glamt, nperio, 'T', 1.)
    zphit = lbc_add (gphit, nperio, 'T', 1.)
    zlamu = lbc_add (glamu, nperio, 'U', 1.)
    zphiu = lbc_add (gphiu, nperio, 'U', 1.)
    zlamv = lbc_add (glamv, nperio, 'V', 1.)
    zphiv = lbc_add (gphiv, nperio, 'V', 1.)
    zlamf = lbc_add (glamf, nperio, 'F', 1.)
    zphif = lbc_add (gphif, nperio, 'F', 1.)

    # north pole direction & modulous (at T-point)
    zxnpt = 0. - 2.0 * np.cos (np.deg2rad(zlamt)) * np.tan (np.pi/4.0 - np.deg2rad(zphit/2.0))
    zynpt = 0. - 2.0 * np.sin (np.deg2rad(zlamt)) * np.tan (np.pi/4.0 - np.deg2rad(zphit/2.0))
    znnpt = zxnpt*zxnpt + zynpt*zynpt

    # north pole direction & modulous (at U-point)
    zxnpu = 0. - 2.0 * np.cos (np.deg2rad(zlamu)) * np.tan (np.pi/4.0 - np.deg2rad(zphiu/2.0))
    zynpu = 0. - 2.0 * np.sin (np.deg2rad(zlamu)) * np.tan (np.pi/4.0 - np.deg2rad(zphiu/2.0))
    znnpu = zxnpu*zxnpu + zynpu*zynpu

    # north pole direction & modulous (at V-point)
    zxnpv = 0. - 2.0 * np.cos (np.deg2rad(zlamv)) * np.tan (np.pi/4.0 - np.deg2rad(zphiv/2.0))
    zynpv = 0. - 2.0 * np.sin (np.deg2rad(zlamv)) * np.tan (np.pi/4.0 - np.deg2rad(zphiv/2.0))
    znnpv = zxnpv*zxnpv + zynpv*zynpv

    # north pole direction & modulous (at F-point)
    zxnpf = 0. - 2.0 * np.cos (np.deg2rad(zlamf)) * np.tan (np.pi/4. - np.deg2rad(zphif/2.))
    zynpf = 0. - 2.0 * np.sin (np.deg2rad(zlamf)) * np.tan (np.pi/4. - np.deg2rad(zphif/2.))
    znnpf = zxnpf*zxnpf + zynpf*zynpf

    # j-direction: v-point segment direction (around T-point)
    zlam = zlamv
    zphi = zphiv
    zlan = np.roll ( zlamv, axis=iy, shift=1)  # glamv (ji,jj-1)
    zphh = np.roll ( zphiv, axis=iy, shift=1)  # gphiv (ji,jj-1)
    zxvvt =  2.0 * np.cos (np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2.0 * np.cos (np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    zyvvt =  2.0 * np.sin (np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2.0 * np.sin (np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    znvvt = np.sqrt ( znnpt * ( zxvvt*zxvvt + zyvvt*zyvvt )  )

    # j-direction: f-point segment direction (around u-point)
    zlam = zlamf
    zphi = zphif
    zlan = np.roll (zlamf, axis=iy, shift=1) # glamf (ji,jj-1)
    zphh = np.roll (zphif, axis=iy, shift=1) # gphif (ji,jj-1)
    zxffu =  2.0 * np.cos (np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2.0 * np.cos (np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    zyffu =  2.0 * np.sin (np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2.0 * np.sin (np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    znffu = np.sqrt ( znnpu * ( zxffu*zxffu + zyffu*zyffu )  )

    # i-direction: f-point segment direction (around v-point)
    zlam = zlamf
    zphi = zphif
    zlan = np.roll (zlamf, axis=ix, shift=1) # glamf (ji-1,jj)
    zphh = np.roll (zphif, axis=ix, shift=1) # gphif (ji-1,jj)
    zxffv =  2.0 * np.cos (np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2.0 * np.cos (np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    zyffv =  2.0 * np.sin (np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2.0 * np.sin (np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    znffv = np.sqrt ( znnpv * ( zxffv*zxffv + zyffv*zyffv )  )

    # j-direction: u-point segment direction (around f-point)
    zlam = np.roll (zlamu, axis=ix, shift=-1) # glamu (ji,jj+1)
    zphi = np.roll (zphiu, axis=ix, shift=-1) # gphiu (ji,jj+1)
    zlan = zlamu
    zphh = zphiu
    zxuuf =  2. * np.cos ( np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2. * np.cos ( np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    zyuuf =  2. * np.sin ( np.deg2rad(zlam)) * np.tan (np.pi/4. - np.deg2rad(zphi/2.)) \
          -  2. * np.sin ( np.deg2rad(zlan)) * np.tan (np.pi/4. - np.deg2rad(zphh/2.))
    znuuf = np.sqrt ( znnpf * ( zxuuf*zxuuf + zyuuf*zyuuf )  )


    # cosinus and sinus using scalar and vectorial products
    gsint = ( zxnpt*zyvvt - zynpt*zxvvt ) / znvvt
    gcost = ( zxnpt*zxvvt + zynpt*zyvvt ) / znvvt

    gsinu = ( zxnpu*zyffu - zynpu*zxffu ) / znffu
    gcosu = ( zxnpu*zxffu + zynpu*zyffu ) / znffu

    gsinf = ( zxnpf*zyuuf - zynpf*zxuuf ) / znuuf
    gcosf = ( zxnpf*zxuuf + zynpf*zyuuf ) / znuuf

    gsinv = ( zxnpv*zxffv + zynpv*zyffv ) / znffv
    # (caution, rotation of 90 degres)
    gcosv =-( zxnpv*zyffv - zynpv*zxffv ) / znffv

    gsint = lbc_del (gsint, cd_type='T', nperio=nperio, psgn=-1.)
    gcost = lbc_del (gcost, cd_type='T', nperio=nperio, psgn=-1.)
    gsinu = lbc_del (gsinu, cd_type='U', nperio=nperio, psgn=-1.)
    gcosu = lbc_del (gcosu, cd_type='U', nperio=nperio, psgn=-1.)
    gsinv = lbc_del (gsinv, cd_type='V', nperio=nperio, psgn=-1.)
    gcosv = lbc_del (gcosv, cd_type='V', nperio=nperio, psgn=-1.)
    gsinf = lbc_del (gsinf, cd_type='F', nperio=nperio, psgn=-1.)
    gcosf = lbc_del (gcosf, cd_type='F', nperio=nperio, psgn=-1.)

    if mmath == xr :
        gsint = gsint.assign_coords (glamt.coords)
        gcost = gcost.assign_coords (glamt.coords)
        gsinu = gsinu.assign_coords (glamu.coords)
        gcosu = gcosu.assign_coords (glamu.coords)
        gsinv = gsinv.assign_coords (glamv.coords)
        gcosv = gcosv.assign_coords (glamv.coords)
        gsinf = gsinf.assign_coords (glamf.coords)
        gcosf = gcosf.assign_coords (glamf.coords)

    pop_stack ( 'angle_full' )
    return gsint, gcost, gsinu, gcosu, gsinv, gcosv, gsinf, gcosf

def angle (glam, gphi, nperio, cd_type='T') :
    '''
    Computes sinus and cosinus of model line direction with
    respect to east
    '''
    push_stack ( f'angle (glam, gphi, {nperio=}, {cd_type=} ) ')
    mmath = __mmath__ (glam)
    ax, ix = find_axis (glam, 'x')
    ay, iy = find_axis (glam, 'y')
    
    zlam = lbc_add (glam, nperio, cd_type, 1.)
    zphi = lbc_add (gphi, nperio, cd_type, 1.)

    # north pole direction & modulus
    zxnp = 0. - 2.0 * np.cos (np.deg2rad(zlam)) * np.tan (np.pi/4.0 - np.deg2rad(zphi/2.0))
    zynp = 0. - 2.0 * np.sin (np.deg2rad(zlam)) * np.tan (np.pi/4.0 - np.deg2rad(zphi/2.0))
    znnp = zxnp*zxnp + zynp*zynp

    # j-direction: segment direction (around point)
    zlan_n = np.roll (zlam, axis=iy, shift=-1) # glam [jj+1, ji]
    zphh_n = np.roll (zphi, axis=iy, shift=-1) # gphi [jj+1, ji]
    zlan_s = np.roll (zlam, axis=iy, shift= 1) # glam [jj-1, ji]
    zphh_s = np.roll (zphi, axis=iy, shift= 1) # gphi [jj-1, ji]

    zxff = 2.0 * np.cos (np.deg2rad(zlan_n)) * np.tan (np.pi/4.0 - np.deg2rad(zphh_n/2.0)) \
        -  2.0 * np.cos (np.deg2rad(zlan_s)) * np.tan (np.pi/4.0 - np.deg2rad(zphh_s/2.0))
    zyff = 2.0 * np.sin (np.deg2rad(zlan_n)) * np.tan (np.pi/4.0 - np.deg2rad(zphh_n/2.0)) \
        -  2.0 * np.sin (np.deg2rad(zlan_s)) * np.tan (np.pi/4.0 - np.deg2rad(zphh_s/2.0))
    znff = np.sqrt (znnp * (zxff*zxff + zyff*zyff) )

    gsin = (zxnp*zyff - zynp*zxff) / znff
    gcos = (zxnp*zxff + zynp*zyff) / znff

    gsin = lbc_del (gsin, cd_type=cd_type, nperio=nperio, psgn=-1.)
    gcos = lbc_del (gcos, cd_type=cd_type, nperio=nperio, psgn=-1.)

    if mmath == xr :
        gsin = gsin.assign_coords ( glam.coords )
        gcos = gcos.assign_coords ( glam.coords )

        #gsin = unify_dims (glam, **gsin.dims)

    pop_stack ( 'angle' )
    return gsin, gcos

def rot_en2ij ( u_e, v_n, gsin, gcos, nperio, cd_type='T' ) :
    '''
    Rotates the Repere: Change vector componantes between
    geographic grid --> stretched coordinates grid.

    All components are on the same grid (T, U, V or F)
    '''
    push_stack ( f'rot_en2ij ( u_e, v_n, gsin, gcos, nperio, {cd_type=} )' )
    u_i = + u_e * gcos + v_n * gsin
    v_j = - u_e * gsin + v_n * gcos

    u_i = lbc (u_i, nperio=nperio, cd_type=cd_type, psgn=-1.0)
    v_j = lbc (v_j, nperio=nperio, cd_type=cd_type, psgn=-1.0)

    pop_stack ( 'rot_en2ij' )
    return u_i, v_j

def rot_ij2en ( u_i, v_j, gsin, gcos, nperio, cd_type='T' ) :
    '''
    Rotates the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid

    All components are on the same grid (T, U, V or F)
    '''
    push_stack ( f'rot_ij2en ( u_i, v_j, gsin, gcos, {nperio=}, {cd_type=} )' )
    u_e = + u_i * gcos - v_j * gsin
    v_n = + u_i * gsin + v_j * gcos

    u_e = lbc (u_e, nperio=nperio, cd_type=cd_type, psgn=1.0)
    v_n = lbc (v_n, nperio=nperio, cd_type=cd_type, psgn=1.0)

    pop_stack ( 'rot_ij2en' )
    return u_e, v_n

def rot_uv2en ( uo, vo, gsint, gcost, nperio, zdim=None ) :
    '''
    Rotate the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid

    uo : velocity along i at the U grid point
    vo : valocity along j at the V grid point
    
    Returns east-north components on the T grid point
    '''
    push_stack ( f'rot_uv2en ( uo, vo, gsint, gcost, {nperio=}, {zdim=} )' )
    ut = u2t (uo, nperio=nperio, psgn=-1.0, zdim=zdim)
    vt = v2t (vo, nperio=nperio, psgn=-1.0, zdim=zdim)

    u_e = + ut * gcost - vt * gsint
    v_n = + ut * gsint + vt * gcost

    u_e = lbc (u_e, nperio=nperio, cd_type='T', psgn=1.0)
    v_n = lbc (v_n, nperio=nperio, cd_type='T', psgn=1.0)

    pop_stack ( 'rot_uv2en' )
    return u_e, v_n

def rot_uv2enf ( uo, vo, gsinf, gcosf, nperio, zdim=None ) :
    '''
    Rotates the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid

    uo : velocity along i at the U grid point
    vo : valocity along j at the V grid point
    
    Returns east-north components on the F grid point
    '''
    push_stack ( f'rot_uv2enf ( uo, vo, gsint, gcost, {nperio=}, {zdim=} )' )
    uf = u2f (uo, nperio=nperio, psgn=-1.0, zdim=zdim)
    vf = v2f (vo, nperio=nperio, psgn=-1.0, zdim=zdim)

    u_e = + uf * gcosf - vf * gsinf
    v_n = + uf * gsinf + vf * gcosf

    u_e = lbc (u_e, nperio=nperio, cd_type='F', psgn= 1.0)
    v_n = lbc (v_n, nperio=nperio, cd_type='F', psgn= 1.0)

    pop_stack ( 'rot_uv2enf' )
    return u_e, v_n

def u2t (utab, nperio=None, psgn=-1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from U grid to T grid (i-mean)
    '''
    push_stack ( f'u2t (utab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (utab)
    utab_0 = mmath.where ( np.isnan(utab), 0., utab)
    #lperio, aperio = lbc_diag (nperio)
    utab_0 = lbc_add (utab_0, nperio=nperio, cd_type='U', psgn=psgn)
    ax, ix = find_axis (utab_0, 'x')
    az, iz = find_axis (utab_0, 'z')

    if ax :
        if action == 'ave' :
            ttab = 0.5 *      (utab_0 + np.roll (utab_0, axis=ix, shift=1))
        if action == 'min' :
            ttab = np.minimum (utab_0 , np.roll (utab_0, axis=ix, shift=1))
        if action == 'max' :
            ttab = np.maximum (utab_0 , np.roll (utab_0, axis=ix, shift=1))
        if action == 'mult':
            ttab =             utab_0 * np.roll (utab_0, axis=ix, shift=1)
        ttab = lbc_del (ttab  , nperio=nperio, cd_type='T', psgn=psgn)
    else :
        ttab = lbc_del (utab_0, nperio=nperio, cd_type='T', psgn=psgn)

    if mmath == xr :
        if ax :
            ttab = ttab.assign_coords({ax:np.arange (ttab.shape[ix])+1.})
        if zdim and az :
            if az != zdim :
                ttab = ttab.rename( {az:zdim})
                
    pop_stack ( 'u2t' )
    return ttab

def v2t (vtab, nperio=None, psgn=-1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from V grid to T grid (j-mean)
    '''
    push_stack ( f'v2t (vtab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (vtab)
    #lperio, aperio = lbc_diag (nperio)
    vtab_0 = mmath.where ( np.isnan(vtab), 0., vtab)
    vtab_0 = lbc_add (vtab_0, nperio=nperio, cd_type='V', psgn=psgn)
    ay, jy = find_axis (vtab_0, 'y')
    az, iz = find_axis (vtab_0, 'z')
    if ay :
        if action == 'ave'  :
            ttab = 0.5 *      (vtab_0 + np.roll (vtab_0, axis=jy, shift=1))
        if action == 'min'  :
            ttab = np.minimum (vtab_0 , np.roll (vtab_0, axis=jy, shift=1))
        if action == 'max'  :
            ttab = np.maximum (vtab_0 , np.roll (vtab_0, axis=jy, shift=1))
        if action == 'mult' :
            ttab =             vtab_0 * np.roll (vtab_0, axis=jy, shift=1)
        ttab = lbc_del (ttab  , nperio=nperio, cd_type='T', psgn=psgn)
    else :
        ttab = lbc_del (vtab_0, nperio=nperio, cd_type='T', psgn=psgn)

    if mmath == xr :
        if ay :
            ttab = ttab.assign_coords({ay:np.arange(ttab.shape[jy])+1.})
        if zdim and az :
            if az != zdim :
                ttab = ttab.rename( {az:zdim})
                
    pop_stack ( 'v2t' )
    return ttab

def f2t (ftab, nperio=None, psgn=1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from F grid to T grid (i- and j- means)
    '''
    push_stack ( f'f2t (ftab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (ftab)
    ftab_0 = mmath.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , nperio=nperio, cd_type='F', psgn=psgn)
    ttab = v2t (f2v (ftab_0, nperio=nperio, psgn=psgn, zdim=zdim, action=action),
                     nperio=nperio, psgn=psgn, zdim=zdim, action=action)

    ttab = lbc_del (ttab, nperio=nperio, cd_type='T', psgn=psgn)
    
    pop_stack ( 'f2t' )
    return ttab

def t2u (ttab, nperio=None, psgn=1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from T grid to U grid (i-mean)
    '''
    push_stack ( f't2u (ttab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )

    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 , nperio=nperio, cd_type='T', psgn=psgn)
    ax, ix = find_axis (ttab_0, 'x')
    az, iz = find_axis (ttab_0, 'z')
    if ix :
        if action == 'ave'  :
            utab = 0.5 *      (ttab_0 + np.roll (ttab_0, axis=ix, shift=-1))
        if action == 'min'  :
            utab = np.minimum (ttab_0 , np.roll (ttab_0, axis=ix, shift=-1))
        if action == 'max'  :
            utab = np.maximum (ttab_0 , np.roll (ttab_0, axis=ix, shift=-1))
        if action == 'mult' :
            utab =             ttab_0 * np.roll (ttab_0, axis=ix, shift=-1)
        utab = lbc_del (utab  , nperio=nperio, cd_type='U', psgn=psgn)
    else :
        utab = lbc_del (ttab_0, nperio=nperio, cd_type='U', psgn=psgn)

    if mmath == xr :
        if ax :
            utab = ttab.assign_coords({ax:np.arange(utab.shape[ix])+1.})
        if zdim and az :
            if az != zdim :
                utab = utab.rename( {az:zdim})

    pop_stack ( 't2u' )
    return utab

def t2v (ttab, nperio=None, psgn=1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from T grid to V grid (j-mean)
    '''
    push_stack ( f't2v (ttab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 , nperio=nperio, cd_type='T', psgn=psgn)
    ay, jy = find_axis (ttab_0, 'y')
    az, jz = find_axis (ttab_0, 'z')
    if jy :
        if action == 'ave'  :
            vtab = 0.5 *      (ttab_0 + np.roll (ttab_0, axis=jy, shift=-1))
        if action == 'min'  :
            vtab = np.minimum (ttab_0 , np.roll (ttab_0, axis=jy, shift=-1))
        if action == 'max'  :
            vtab = np.maximum (ttab_0 , np.roll (ttab_0, axis=jy, shift=-1))
        if action == 'mult' :
            vtab =             ttab_0 * np.roll (ttab_0, axis=jy, shift=-1)
        vtab = lbc_del (vtab  , nperio=nperio, cd_type='V', psgn=psgn)
    else :
        vtab = lbc_del (ttab_0, nperio=nperio, cd_type='V', psgn=psgn)

    if mmath == xr :
        if ay :
            vtab = vtab.assign_coords({ay:np.arange(vtab.shape[jy])+1.})
        if zdim and az :
            if az != zdim :
                vtab = vtab.rename( {az:zdim})
 
    pop_stack ( 't2v' )
    return vtab

def v2f (vtab, nperio=None, psgn=-1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from V grid to F grid (i-mean)
    '''
    push_stack ( f'v2f (vtab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (vtab)
    vtab_0 = mmath.where ( np.isnan(vtab), 0., vtab)
    vtab_0 = lbc_add (vtab_0 , nperio=nperio, cd_type='V', psgn=psgn)
    ax, ix = find_axis (vtab_0, 'x')
    az, jz = find_axis (vtab_0, 'z')
    if ix :
        if action == 'ave'  :
            ftab = 0.5 *      (vtab_0 + np.roll (vtab_0, axis=ix, shift=-1))
        if action == 'min'  :
            ftab = np.minimum (vtab_0 , np.roll (vtab_0, axis=ix, shift=-1))
        if action == 'max'  :
            ftab = np.maximum (vtab_0 , np.roll (vtab_0, axis=ix, shift=-1))
        if action == 'mult' :
            ftab =             vtab_0 * np.roll (vtab_0, axis=ix, shift=-1)
        ftab = lbc_del (ftab  , nperio=nperio, cd_type='F', psgn=psgn)
    else :
        ftab = lbc_del (vtab_0, nperio=nperio, cd_type='F', psgn=psgn)

    if mmath == xr :
        if ax :
            ftab = ftab.assign_coords({ax:np.arange(ftab.shape[ix])+1.})
        if zdim and az :
            if az != zdim :
                ftab = ftab.rename( {az:zdim})

    ftab = lbc_del (ftab, nperio=nperio, cd_type='F', psgn=psgn)
    
    pop_stack ( 'v2f' )
    return ftab

def u2f (utab, nperio=None, psgn=-1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from U grid to F grid i-mean)
    '''
    push_stack ( f'u2f (utab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (utab)
    utab_0 = mmath.where ( np.isnan(utab), 0., utab)
    utab_0 = lbc_add (utab_0 , nperio=nperio, cd_type='U', psgn=psgn)
    ay, jy = find_axis (utab_0, 'y')
    az, kz = find_axis (utab_0, 'z')
    if jy :
        if action == 'ave'  :
            ftab = 0.5 *      (utab_0 + np.roll (utab_0, axis=jy, shift=-1))
        if action == 'min'  :
            ftab = np.minimum (utab_0 , np.roll (utab_0, axis=jy, shift=-1))
        if action == 'max'  :
            ftab = np.maximum (utab_0 , np.roll (utab_0, axis=jy, shift=-1))
        if action == 'mult' :
            ftab =             utab_0 * np.roll (utab_0, axis=jy, shift=-1)
        ftab = lbc_del (ftab, nperio=nperio, cd_type='F', psgn=psgn)
    else :
        ftab = lbc_del (utab_0, nperio=nperio, cd_type='F', psgn=psgn)

    if mmath == xr :
        if ay :
            ftab = ftab.assign_coords({'y':np.arange(ftab.shape[jy])+1.})
        if zdim and az :
            if az != zdim :
                ftab = ftab.rename( {az:zdim})
    
    pop_stack ( 'u2f' )
    return ftab

def t2f (ttab, nperio=None, psgn=1.0, zdim=None, action='mean') :
    '''
    Interpolates an array on T grid to F grid (i- and j- means)
    '''
    push_stack ( f't2f (utab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 , nperio=nperio, cd_type='T', psgn=psgn)
    ftab = t2u (u2f (ttab, nperio=nperio, psgn=psgn, zdim=zdim, action=action),
                     nperio=nperio, psgn=psgn, zdim=zdim, action=action)

    ftab = lbc_del (ftab, nperio=nperio, cd_type='F', psgn=psgn) 

    pop_stack ( 'v2f' )
    return ftab

def f2u (ftab, nperio=None, psgn=1.0, zdim=None, action='ave') :
    '''
    Interpolates an array on F grid to U grid (j-mean)
    '''
    push_stack ( f'f2u (utab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (ftab)
    ftab_0 = mmath.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , nperio=nperio, cd_type='F', psgn=psgn)
    ay, jy = find_axis (ftab_0, 'y')
    az, kz = find_axis (ftab_0, 'z')
    if jy :
        if action == 'ave'  :
            utab = 0.5 *      (ftab_0 + np.roll (ftab_0, axis=jy, shift=-1))
        if action == 'min'  :
            utab = np.minimum (ftab_0 , np.roll (ftab_0, axis=jy, shift=-1))
        if action == 'max'  :
            utab = np.maximum (ftab_0 , np.roll (ftab_0, axis=jy, shift=-1))
        if action == 'mult' :
            utab =             ftab_0 * np.roll (ftab_0, axis=jy, shift=-1)
        utab = lbc_del (utab  , nperio=nperio, cd_type='U', psgn=psgn)
    else :
        utab = lbc_del (ftab_0, nperio=nperio, cd_type='U', psgn=psgn)

    if mmath == xr :
        utab = utab.assign_coords({ay:np.arange(ftab.shape[jy])+1.})
        if zdim and az and az != zdim :
            utab = utab.rename( {az:zdim})

    pop_stack ( 'f2u' )
    return utab

def f2v (ftab, nperio=None, psgn=1.0, zdim=None, action='ave') :
    '''
    Interpolates an array from F grid to V grid (i-mean)
    '''
    push_stack ( f'f2v (ftab, {nperio=}, {psgn=}, {zdim=}, {action=} )' )
    mmath = __mmath__ (ftab)
    ftab_0 = mmath.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , nperio=nperio, cd_type='F', psgn=psgn)
    ax, ix = find_axis (ftab_0, 'x')
    az, kz = find_axis (ftab_0, 'z')
    if ix :
        if action == 'ave'  :
            vtab = 0.5 *      (ftab_0 + np.roll (ftab_0, axis=ix, shift=-1))
        if action == 'min'  :
            vtab = np.minimum (ftab_0 , np.roll (ftab_0, axis=ix, shift=-1))
        if action == 'max'  :
            vtab = np.maximum (ftab_0 , np.roll (ftab_0, axis=ix, shift=-1))
        if action == 'mult' :
            vtab =             ftab_0 * np.roll (ftab_0, axis=ix, shift=-1)
        vtab = lbc_del (vtab  , nperio=nperio, cd_type='V', psgn=psgn)
    else :
        vtab = lbc_del (ftab_0, nperio=nperio, cd_type='V', psgn=psgn)

    if mmath == xr :
        vtab = vtab.assign_coords({ax:np.arange(ftab.shape[ix])+1.})
        if zdim and az :
            if az != zdim :
                vtab = vtab.rename( {az:zdim})

    pop_stack ( 'f2v' )
    return vtab

def w2t (wtab, zcoord=None, zdim=None, sval=np.nan) :
    '''
    Interpolates an array on W grid to T grid (k-mean)
    sval is the bottom value
    '''
    push_stack ( f'w2t (wtab, {zcoord=}, {zdim=}, {sval=} )' )
    mmath = __mmath__ (wtab)
    wtab_0 = mmath.where ( np.isnan(wtab), 0., wtab)

    az, kz = find_axis (wtab_0, 'z')

    if kz :
        ttab = 0.5 * ( wtab_0 + np.roll (wtab_0, axis=kz, shift=-1) )
    else :
        ttab = wtab_0

    if mmath == xr :
        ttab[{az:kz}] = sval
        if zdim and az :
            if az != zdim :
                ttab = ttab.rename ( {az:zdim} )
        if zcoord is not None :
            ttab = ttab.assign_coords ( {zdim:zcoord} )
    else :
        ttab[..., -1, :, :] = sval

    pop_stack ( 'w2t' )
    return ttab

def t2w (ttab, zcoord=None, zdim=None, sval=np.nan, extrap_surf=False) :
    '''
    Interpolates an array from T grid to W grid (k-mean)

    sval is the surface value
    if extrap_surf==True, surface value is taken from 1st level value.
    '''
    push_stack ( f't2w (utab, {zcoord=}, {zdim=}, {sval=}, {extrap_surf=} )' )
    mmath = __mmath__ (ttab)
    ttab_0 = mmath.where ( np.isnan(ttab), 0., ttab)
    az, kz = find_axis (ttab_0, 'z')
    wtab = 0.5 * ( ttab_0 + np.roll (ttab_0, axis=kz, shift=1) )

    if mmath == xr :
        if extrap_surf :
            wtab[{az:0}] = ttab[{az:0}]
        else           :
            wtab[{az:0}] = sval
    else :
        if extrap_surf :
            wtab[..., 0, :, :] = ttab[..., 0, :, :]
        else           :
            wtab[..., 0, :, :] = sval

    if mmath == xr :
        if zdim and az and az != zdim :
            wtab = wtab.rename ( {az:zdim})
        if zcoord is not None :
            wtab = wtab.assign_coords ( {zdim:zcoord})
        else :
            wtab = wtab.assign_coords ( {zdim:np.arange(ttab.shape[kz])+1.} )

    pop_stack ( 't2w' )
    return wtab

def fill (ptab, nperio, cd_type='T', npass=1, sval=np.nan) :
    '''
    Fills np.nan values with mean of neighbours

    Inputs :
       ptab : input field to fill
       nperio, cd_type : periodicity characteristics
    '''
    push_stack ( f'fill (ptab, {perio=}, {cd_type=}, {npass=}, {sval=} ) ')
    mmath = __mmath__ (ptab)
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    
    do_perio  = False
    lperio    = nperio
    if nperio == 4.2 :
        do_perio, lperio = True, 4
    if nperio == 6.2 :
        do_perio, lperio = True, 6

    if do_perio :
        ztab = lbc_add (ptab, nperio=nperio)
    else :
        ztab = ptab

    if np.isnan (sval) :
        ztab   = mmath.where (np.isnan(ztab), np.nan, ztab)
    else :
        ztab   = mmath.where (ztab==sval    , np.nan, ztab)

    for _ in np.arange (npass) :
        zmask = mmath.where ( np.isnan(ztab), 0., 1.   )
        ztab0 = mmath.where ( np.isnan(ztab), 0., ztab )
        # Compte du nombre de voisins
        zcount = 1./6. * ( zmask \
          + np.roll(zmask, shift=1, axis=ix) + np.roll(zmask, shift=-1, axis=ix) \
          + np.roll(zmask, shift=1, axis=jy) + np.roll(zmask, shift=-1, axis=jy) \
          + 0.5 * ( \
                + np.roll(np.roll(zmask, shift= 1, axis=jy), shift= 1, axis=ix) \
                + np.roll(np.roll(zmask, shift=-1, axis=jy), shift= 1, axis=ix) \
                + np.roll(np.roll(zmask, shift= 1, axis=jy), shift=-1, axis=ix) \
                + np.roll(np.roll(zmask, shift=-1, axis=jy), shift=-1, axis=ix) ) )

        znew =1./6. * ( ztab0 \
           + np.roll(ztab0, shift=1, axis=ix) + np.roll(ztab0, shift=-1, axis=ix) \
           + np.roll(ztab0, shift=1, axis=jy) + np.roll(ztab0, shift=-1, axis=jy) \
           + 0.5 * ( \
                + np.roll(np.roll(ztab0 , shift= 1, axis=jy), shift= 1, axis=ix) \
                + np.roll(np.roll(ztab0 , shift=-1, axis=jy), shift= 1, axis=ix) \
                + np.roll(np.roll(ztab0 , shift= 1, axis=jy), shift=-1, axis=ix) \
                + np.roll(np.roll(ztab0 , shift=-1, axis=jy), shift=-1, axis=ix) ) )

        zcount = lbc (zcount, nperio=lperio, cd_type=cd_type)
        znew   = lbc (znew  , nperio=lperio, cd_type=cd_type)

        ztab = mmath.where (np.logical_and (zmask==0., zcount>0), znew/zcount, ztab)

    ztab = mmath.where (zcount==0, sval, ztab)
    if do_perio :
        ztab = lbc_del (ztab, nperio=lperio)

    pop_stack ( 'fill' )
    return ztab

def correct_uv (u, v, lat) :
    '''
    Corrects a Cartopy bug in orthographic projection

    See https://github.com/SciTools/cartopy/issues/1179

    The correction is needed with cartopy <= 0.20
    It seems that version 0.21 will correct the bug (https://github.com/SciTools/cartopy/pull/1926)
    Later note : the bug is still present in Cartopy 0.22

    Inputs :
       u, v : eastward/northward components
       lat  : latitude of the point (degrees north)

    Outputs :
       modified eastward/nothward components to have correct polar projections in cartopy
    '''
    push_stack (f' correct_uv (u, v, lat)')
    uv = np.sqrt (u*u + v*v)           # Original modulus
    zu = u
    zv = v * np.cos (np.deg2rad(lat))
    zz = np.sqrt ( zu*zu + zv*zv )     # Corrected modulus
    uc = zu*uv/zz
    vc = zv*uv/zz      # Final corrected values

    pop_stack ( 'correct_uv' )
    return uc, vc

def norm_uv (u, v) :
    '''Returns norm of a 2 components vector
    '''
    push_stack ( 'norm_uv (u, v)' )
    zz = np.sqrt (u*u + v*v)
    Poptack ( 'norm_uv' )
    return zz

def normalize_uv (u, v) :
    '''Normalizes 2 components vector
    '''
    push_stack ( 'normalize_uv (u, v)' )
    uv = norm_uv (u, v)
    uu = u/uv
    vv = v/uv
    pop_stack ( 'normalize_uv' )
    return uu, vv

def zonmean (var, bb, plat1d) :
    '''
    Computes the meridonal stream function

    var : var
    bb  : volume
    '''
    push_stack ( 'zonmean (vv, bb, plat1d)' )

    if OPTIONS.Debug :
        print ( f'{bb.dims = } {bb.shape=}' )
        print ( f'{var.dims = } {var.shape}' )

    ax, ix = find_axis (var, 'x')
    ay, jy = find_axis (var, 'y')
    az, kz = find_axis (var, 'z')

    ldims = UDIMS.copy()
    ldims.update ({'x':ax, 'y':ay, 'z':az})

    if OPTIONS.Debug : print ( f'zonmean : {ldims=}' )
    
    if OPTIONS.Debug : print ('zonmean : zonal mean of volume')
    zon_bb  = unify_dims (bb, **ldims).sum(dim=ldims['x'], min_count=1, keep_attrs=True)
    zon_bb  = zon_bb.where (zon_bb>0., np.nan)
    if OPTIONS.Debug : print ( f'zonmean : {zon_bb.dims = }' )
    if OPTIONS.Debug : print ('zonmean : zonal mean of variable')
    zon_var = (var * unify_dims (bb, **ldims)).sum(dim=ldims['x'], min_count=1, keep_attrs=True) / zon_bb
    zon_var = zon_var.where ( np.logical_not(np.isnan(zon_bb)), np.nan)
    if OPTIONS.Debug : print ( f'zonmean : {zon_var.dims = }' )
    
    if OPTIONS.Debug : print ( 'zonmean : Change coords')
    zon_var = zon_var.assign_coords ( {ldims['y']:(ldims['y'], plat1d.values)} )
    zon_var = zon_var.rename ( {ldims['y']:'lat'} )

    zon_var.attrs.update (var.attrs)
    if 'standard_name' in zon_var.attrs :
        zon_var.attrs ['long_name'] = zon_var.attrs ['standard_name'] + ' - zonal mean'
    zon_var.lat.attrs = plat1d.attrs

    pop_stack ( 'zon' )
    return zon_var

def msf (vv, e1v_e3v, plat1d, depthw, south=None) :
    '''
    Computes the meridonal stream function

    vv : meridional_velocity
    e1v_e3v : product of scale factors e1v*e3v
    '''
    push_stack ( 'msf (vv, e1v_e3v, plat1d, depthw)' )

    ax, ix = find_axis (vv, 'x')
    ay, jy = find_axis (vv, 'y')
    az, kz = find_axis (vv, 'z')

    ldims = UDIMS.copy()
    ldims.update ({'x':ax, 'y':ay, 'z':az})
    
    v_e1v_e3v = vv * unify_dims(e1v_e3v, **ldims)
    v_e1v_e3v.attrs = vv.attrs

    mm = e1v_e3v.sum (dim=ax, keep_attrs=True, min_count=1)
    
    zomsf = -v_e1v_e3v.cumsum (dim=az, keep_attrs=True).sum (dim=ax, min_count=1, keep_attrs=True)
    zomsf = zomsf - zomsf.isel ({az:-1})
    zomsf = zomsf.where (mm>0, np.nan)

    ay = find_axis (zomsf, 'y' )[0]
    #zomsf = zomsf.assign_coords ({az:depthw.values, ay:plat1d.values})
    zomsf = zomsf.assign_coords ({ay:plat1d.values})
    zomsf = zomsf.rename ({ay:'lat'})
    
    zomsf.attrs ['standard_name'] = 'stfmmcgo'
    zomsf.attrs ['long_name']     = 'ocean_meridional_overturning_streamfunction'
    zomsf.attrs ['units']         = 'm3s-1'
    zomsf.lat.attrs = plat1d.attrs

    if south == True : south = -30
    
    if south :
        if OPTIONS.Debug : print ( f'Masque south of {south}')
        zomsf = zomsf.where (zomsf.lat > south, np.nan)

    pop_stack ( 'msf' )
    return zomsf

def zmsf_index (zmsf, name="nadw", latname='nav_lat', lat=None) :
    '''
    Compute index of zonal meridional stream function
    
    Known case (name) : nadw, aabw, npdw, deacon
    '''
    push_stack ( f'zmsf_index (zmsf, {name=}, {latname=}, lat)' )

    if name == "nadw"   :
        zlim = slice( 500,4000) ; ylim = slice( 11, 55) ; long_name = 'North Atlantic Deep Water'
    if name == "aabw"   :
        zlim = slice(2000,6000) ; ylim = slice(-30, 60) ; long_name = 'Antarctic Bottom Water'
    if name == "npdw"   :
        zlim = slice( 500,6000) ; ylim = slice( 15, 60) ; long_name = 'North Pacific Bottom Water'
    if name == "deacon" :
        zlim = slice(2000,6000) ; ylim = slice(-80,-30) ; long_name = 'Deacon Cell'
    
    zlat1d = lat1d  (zmsf[latname])
    zmsf_lat = unify_dims (zmsf, **UDIMS)
    if lat :
        zmsf_lat = zmsf_lat.assign_coords ( {UDIMS['y']:lat} )
    else : 
        zmsf_lat = zmsf_lat.assign_coords ( {UDIMS['y']:zlat1d.values} )
    if OPTIONS.Debug :
        print ( f'{ylim=} - {zlim=}' )
        print ( f'{zlat1d=}' )
        print ( f'{zmsf_lat.y}' )
        print ( f'{zmsf_lat.olevel}' )

    za = zmsf_lat.sel ({UDIMS['z']:zlim})
    if OPTIONS.Debug :
        print ( f'{za.shape=}')
        print ( f'{za=}')
    index_ocean = zmsf_lat.sel ({UDIMS['z']:zlim}).max (dim=UDIMS['z']).sel ({UDIMS['y']:ylim}).max (dim=UDIMS['y'])
    index_ocean.name = f'{name}_ocean'
    index_ocean.attrs.update (zmsf.attrs)
    index_ocean.attrs.update ({'long_name':long_name})
    pop_stack ('zmsf_index')
    return index_ocean

def bsf (uu, e2u_e3u, mask, nperio=None, bsf0=None ) :
    '''
    Computes the barotropic stream function

    uu      : zonal_velocity
    e2u_e3u : product of scales factor e2u*e3u
    bsf0    : the point with bsf=0
    (ex: bsf0={'x':3, 'y':120} for orca2,
         bsf0={'x':5, 'y':300} for eORCA1
    '''
    push_stack ( f'bsf (uu, e2u_e3u, mask, {nperio=}, {bsf0=} )' )
    
    u_e2u_e3u       = uu * e2u_e3u
    u_e2u_e3u.attrs = uu.attrs
    if OPTIONS.Debug : print ( f'{u_e2u_e3u.dims=} {mask.dims=}' )


    ay, jy = find_axis (u_e2u_e3u, 'y')
    az, kz = find_axis (u_e2u_e3u, 'z')

    zbsf = -u_e2u_e3u.cumsum (dim=ay, keep_attrs=True )
    if OPTIONS.Debug : print ( f'1 - {zbsf.dims=}' )
    zbsf = zbsf.sum (dim=az, keep_attrs=True)
    if OPTIONS.Debug : print ( f'2 - {zbsf.dims=}' )
    if bsf0 : 
        zbsf = zbsf - zbsf.isel (bsf0)

    zbsf = zbsf.where (mask !=0, np.nan)
    if OPTIONS.Debug : print ( f'3 - {zbsf.dims=}' )
    zbsf.attrs.update (uu.attrs)
    zbsf.attrs['standard_name'] = 'stfbaro'
    zbsf.attrs['long_name']     = 'ocean_barotropic_stream_function'
    zbsf.attrs['units']         = 'm3s-1'
    zbsf = lbc (zbsf, nperio=nperio, cd_type='F')

    pop_stack ( 'bsf' )
    return zbsf

if f90nml :
    def namelist_read (ref=None, cfg=None, out='dict', flat=False) :
        '''
        Read NEMO namelist(s) and return either a dictionnary or an xarray dataset

        ref : file with reference namelist, or a f90nml.namelist.Namelist object
        cfg : file with config namelist, or a f90nml.namelist.Namelist object
        At least one namelist neaded

        out:
        'dict' to return a dictonnary
        'xr'   to return an xarray dataset
        flat : only for dict output. Output a flat dictionary with all values.

        '''
        push_stack ( f'namelist_read (ref, cfg, {out=}, {flat=})' )
        if ref :
            if isinstance (ref, str) :
                nml_ref = f90nml.read (ref)
            if isinstance (ref, f90nml.namelist.Namelist) :
                nml_ref = ref

        if cfg :
            if isinstance (cfg, str) :
                nml_cfg = f90nml.read (cfg)
            if isinstance (cfg, f90nml.namelist.Namelist) :
                nml_cfg = cfg

        if out == 'dict' :
            dict_namelist = Container ()
        if out == 'xr'   :
            xr_namelist = xr.Dataset ()

        list_nml     = []
        list_comment = []

        if ref :
            list_nml.append (nml_ref)
            list_comment.append ('ref')
        if cfg :
            list_nml.append (nml_cfg)
            list_comment.append ('cfg')

        for nml, comment in zip (list_nml, list_comment) :
            if OPTIONS.Debug : print (comment)
            if flat and out =='dict' :
                for nam in nml.keys () :
                    if OPTIONS.Debug : print (nam)
                    for value in nml[nam] :
                        if out == 'dict' :
                            dict_namelist[value] = nml[nam][value]
                        if OPTIONS.Debug :
                            print (nam, ':', value, ':', nml[nam][value])
            else :
                for nam in nml.keys () :
                    if OPTIONS.Debug : print (nam)
                    if out == 'dict' :
                        if nam not in dict_namelist.keys () :
                            dict_namelist[nam] = Container ()
                    for value in nml[nam] :
                        if out == 'dict' :
                            dict_namelist[nam][value] = nml[nam][value]
                        if out == 'xr'   :
                            xr_namelist[value] = nml[nam][value]
                        if OPTIONS.Debug : print (nam, ':', value, ':', nml[nam][value])

        pop_stack ( 'namelist_read' )
        if out == 'dict' :
            return dict_namelist
        if out == 'xr'   :
            return xr_namelist
else :
     def namelist_read (ref=None, cfg=None, out='dict', flat=False) :
        '''
        Shadow version of namelist read, when f90nm module was not found

        namelist_read : 
        Read NEMO namelist(s) and return either a dictionnary or an xarray dataset
        '''
        push_stack ( f'namelist_read [void version] (ref, cfg, {out=}, {flat=})' )

        print ( 'Error : module f90nml not found' )
        print ( 'Cannot call namelist_read' )
        print ( 'Call parameters where : ')
        print ( f'{err=} {ref=} {cfg=} {out=} {flat=}' )
        pop_stack ( 'namelist_read [void version]' )

def fill_closed_seas (imask, nperio=None,  cd_type='T') :
    '''Fill closed seas with image processing library

    imask : mask, 1 on ocean, 0 on land
    '''
    push_stack ( f'fill_closed_seas (imask, {nperio=}, {cd_type=} )' )
    from scipy import ndimage

    imask_filled = ndimage.binary_fill_holes ( lbc (imask, nperio=nperio, cd_type=cd_type))
    imask_filled = lbc ( imask_filled, nperio=nperio, cd_type=cd_type)

    pop_stack ( 'fill_closed_seas' )
    return imask_filled

# ======================================================
# Sea water state function parameters from NEMO code

RDELTAS = 32.0
R1_S0   = 0.875/35.16504
R1_T0   = 1.0/40.
R1_Z0   = 1.0e-4

EOS000 =  8.0189615746e+02
EOS100 =  8.6672408165e+02
EOS200 = -1.7864682637e+03
EOS300 =  2.0375295546e+03
EOS400 = -1.2849161071e+03
EOS500 =  4.3227585684e+02
EOS600 = -6.0579916612e+01
EOS010 =  2.6010145068e+01
EOS110 = -6.5281885265e+01
EOS210 =  8.1770425108e+01
EOS310 = -5.6888046321e+01
EOS410 =  1.7681814114e+01
EOS510 = -1.9193502195
EOS020 = -3.7074170417e+01
EOS120 =  6.1548258127e+01
EOS220 = -6.0362551501e+01
EOS320 =  2.9130021253e+01
EOS420 = -5.4723692739
EOS030 =  2.1661789529e+01
EOS130 = -3.3449108469e+01
EOS230 =  1.9717078466e+01
EOS330 = -3.1742946532
EOS040 = -8.3627885467
EOS140 =  1.1311538584e+01
EOS240 = -5.3563304045
EOS050 =  5.4048723791e-01
EOS150 =  4.8169980163e-01
EOS060 = -1.9083568888e-01
EOS001 =  1.9681925209e+01
EOS101 = -4.2549998214e+01
EOS201 =  5.0774768218e+01
EOS301 = -3.0938076334e+01
EOS401 =  6.6051753097
EOS011 = -1.3336301113e+01
EOS111 = -4.4870114575
EOS211 =  5.0042598061
EOS311 = -6.5399043664e-01
EOS021 =  6.7080479603
EOS121 =  3.5063081279
EOS221 = -1.8795372996
EOS031 = -2.4649669534
EOS131 = -5.5077101279e-01
EOS041 =  5.5927935970e-01
EOS002 =  2.0660924175
EOS102 = -4.9527603989
EOS202 =  2.5019633244
EOS012 =  2.0564311499
EOS112 = -2.1311365518e-01
EOS022 = -1.2419983026
EOS003 = -2.3342758797e-02
EOS103 = -1.8507636718e-02
EOS013 =  3.7969820455e-01

def rhop (ptemp, psal) :
    '''
    Returns potential density referenced to surface

    Computation from NEMO code
    '''
    push_stack ( 'rhop ( ptemp, psal )' )
    zt      = ptemp * R1_T0                                  # Temperature (°C)
    zs      = np.sqrt ( np.abs( psal + RDELTAS ) * R1_S0 )   # Square root of salinity (PSS)
    #
    prhop = (
      (((((EOS060*zt
         + EOS150*zs     + EOS050)*zt
         + (EOS240*zs    + EOS140)*zs + EOS040)*zt
         + ((EOS330*zs   + EOS230)*zs + EOS130)*zs + EOS030)*zt
         + (((EOS420*zs  + EOS320)*zs + EOS220)*zs + EOS120)*zs + EOS020)*zt
         + ((((EOS510*zs + EOS410)*zs + EOS310)*zs + EOS210)*zs + EOS110)*zs + EOS010)*zt
         + (((((EOS600*zs+ EOS500)*zs + EOS400)*zs + EOS300)*zs + EOS200)*zs + EOS100)*zs + EOS000 )
    #
    pop_stack ( 'rhop' )
    return prhop

def rho (pdep, ptemp, psal) :
    '''
    Returns in situ density

    Computation from NEMO code
    '''
    push_stack ( 'rho ( ptemp, psal) ' )
    zh      = pdep  * R1_Z0                                  # Depth (m)
    zt      = ptemp * R1_T0                                  # Temperature (°C)
    zs      = np.sqrt ( np.abs( psal + RDELTAS ) * R1_S0 )   # Square root salinity (PSS)
    #
    zn3 = EOS013*zt + EOS103*zs+EOS003
    #
    zn2 = (EOS022*zt + EOS112*zs+EOS012)*zt + (EOS202*zs+EOS102)*zs+EOS002
    #
    zn1 = (
      (((EOS041*zt
       + EOS131*zs   + EOS031)*zt
       + (EOS221*zs  + EOS121)*zs + EOS021)*zt
       + ((EOS311*zs  + EOS211)*zs + EOS111)*zs + EOS011)*zt
       + (((EOS401*zs + EOS301)*zs + EOS201)*zs + EOS101)*zs + EOS001 )
    #
    zn0 = (
      (((((EOS060*zt
         + EOS150*zs      + EOS050)*zt
         + (EOS240*zs     + EOS140)*zs + EOS040)*zt
         + ((EOS330*zs    + EOS230)*zs + EOS130)*zs + EOS030)*zt
         + (((EOS420*zs   + EOS320)*zs + EOS220)*zs + EOS120)*zs + EOS020)*zt
         + ((((EOS510*zs  + EOS410)*zs + EOS310)*zs + EOS210)*zs + EOS110)*zs + EOS010)*zt
         + (((((EOS600*zs + EOS500)*zs + EOS400)*zs + EOS300)*zs +
                                         EOS200)*zs + EOS100)*zs + EOS000 )
    #
    prho  = ( ( zn3 * zh + zn2 ) * zh + zn1 ) * zh + zn0
    #
    pop_stack ( 'rho' )
    return prho

## ===========================================================================
##                                                                            
##                               That's all folk's !!!                        
##                                                                            
## ===========================================================================

# def __is_orca_north_fold__ ( Xtest, cname_long='T' ) :
#     '''
#     Ported (pirated !!?) from Sosie

#     Tell if there is a 2/point band overlaping folding at the north pole typical of the ORCA grid

#     0 => not an orca grid (or unknown one)
#     4 => North fold T-point pivot (ex: ORCA2)
#     6 => North fold F-point pivot (ex: ORCA1)

#     We need all this 'cname_long' stuff because with our method, there is a
#     confusion between "Grid_U with T-fold" and "Grid_V with F-fold"
#     => so knowing the name of the longitude array (as in namelist, and hence as
#     in netcdf file) might help taking the righ decision !!! UGLY!!!
#     => not implemented yet
#     '''

#     ifld_nord =  0 ; cgrd_type = 'X'
#     ny, nx = Xtest.shape[-2:]

#     if ny > 3 : # (case if called with a 1D array, ignoring...)
#         if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-1:nx-nx//2+1:-1] ).sum() == 0. :
#           ifld_nord = 4 ; cgrd_type = 'T' # T-pivot, grid_T

#         if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-2:nx-nx//2  :-1] ).sum() == 0. :
#             if cnlon == 'U' : ifld_nord = 4 ;  cgrd_type = 'U' # T-pivot, grid_T
#                 ## LOLO: PROBLEM == 6, V !!!

#         if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-1:nx-nx//2+1:-1] ).sum() == 0. :
#             ifld_nord = 4 ; cgrd_type = 'V' # T-pivot, grid_V

#         if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-2, nx-1-1:nx-nx//2:-1] ).sum() == 0. :
#             ifld_nord = 6 ; cgrd_type = 'T'# F-pivot, grid_T

#         if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-1, nx-1:nx-nx//2-1:-1] ).sum() == 0. :
#             ifld_nord = 6 ;  cgrd_type = 'U' # F-pivot, grid_U

#         if ( Xtest [ny-1, 1:nx//2-1] - Xtest [ny-3, nx-2:nx-nx//2  :-1] ).sum() == 0. :
#             if cnlon == 'V' : ifld_nord = 6 ; cgrd_type = 'V' # F-pivot, grid_V
#                 ## LOLO: PROBLEM == 4, U !!!

#     return ifld_nord, cgrd_type
