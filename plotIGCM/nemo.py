# -*- coding: utf-8 -*-
'''
Utilities to plot NEMO ORCA fields,

Handles periodicity and other stuff related to the crooked orca grids

- Lots of tests for xarray object
- Support of numpy objects slowly vanishing

Author: olivier.marti@lsce.ipsl.fr

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
prerequisites. Please be aware that the author himself may not
respects the above prerequisite.

'''

## Modules                                                                     
import time
import copy
from typing import Any, Self, Literal, Dict, Union, Hashable
import numpy as np
import xarray as xr
from shapely.geometry import box, Polygon
    
try :
    import xcdat as xc
except ImportError as err :
    print (f'===> Warning : Module nemo : Import error of xcdat : {err}')
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

from plotIGCM import copy_attrs
from plotIGCM.utils import OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack

## Useful constants and parameters                                             
    
REPSI = np.finfo (1.0).eps

RAAMO  = xr.DataArray (12       , name='RAAMO' , attrs={'units':"month"  , 'long_name':"Number of months in one year" })
RJJHH  = xr.DataArray (24       , name='RJJHH' , attrs={'units':"hour"   , 'long_name':"Number of hours in one day"} )
RHHMM  = xr.DataArray (60       , name='RHHMM' , attrs={'units':"min"    , 'long_name':"Number of minutes in one hour"} )
RMMSS  = xr.DataArray (60       , name='RMMSS' , attrs={'units':"second" , 'long_name':"Number of seconds in one minute"} )
RA     = xr.DataArray (6371229.0, name='RA'    , attrs={'units':"meter"  , 'long_name':"Earth radius"} )
GRAV   = xr.DataArray (9.80665  , name='GRAV'  , attrs={'units':"m/s2"   , 'long_name':"Gravity"} )
RT0    = xr.DataArray (273.15   , name='RT0'   , attrs={'units':"K"      , 'long_name':"Freezing point of fresh water"} )
RAU0   = xr.DataArray (1026.0   , name='RAU0'  , attrs={'units':"kg/m3"  , 'long_name':"Volumic mass of sea water"} )
RAUREF = xr.DataArray (1006.0   , name='RAUREF', attrs={'units':"kg/m3"  , 'long_name':"Reference to convert rho<-->sigma"} )
SICE   = xr.DataArray (6.0      , name='SICE'  , attrs={'units':"psu"    , 'long_name':"Salinity of ice (for pisces)"} )
SOCE   = xr.DataArray (34.7     , name='SOCE'  , attrs={'units':"psu"    , 'long_name':"Salinity of sea (for pisces and isf)"} )
RLEVAP = xr.DataArray (2.5e+6   , name='RLEVAP', attrs={'units':"J/K"    , 'long_name':"Latent heat of evaporation (water)"} )
VKARMN = xr.DataArray (0.4      , name='VKARMN', attrs={                   'long_name':"Von Karman constant"} )
STEFAN = xr.DataArray (5.67e-8  , name='STEFAN', attrs={'units':"W/m2/K4", 'long_name':"Stefan-Boltzmann constant"} )
RHOS   = xr.DataArray (330.     , name='RHOS'  , attrs={'units':"kg/m3"  , 'long_name':"Volumic mass of snow"} )
RHOI   = xr.DataArray (917.     , name='RHOI'  , attrs={'units':"kg/m3"  , 'long_name':"Volumic mass of sea ice"} )
RHOW   = xr.DataArray (1000.    , name='RHOW'  , attrs={'units':"kg/m3"  , 'long_name':"Volumic mass of freshwater in melt ponds"} )
RCND_I = xr.DataArray (2.034396 , name='RCND_I', attrs={'units':"W/m/J"  , 'long_name':"Thermal conductivity of fresh ice"} )
CP     = xr.DataArray (4000.0   , name='CP'    , attrs={'units':"J/kg/K" , 'long_name':"Specific heat of sea water"} )
RCP    = xr.DataArray (3991.8679, name='RCP'   , attrs={'units':"J/K"    , 'long_name':"Specific heat of sea water"} )
RCPI   = xr.DataArray (2067.0   , name='RCPI'  , attrs={'units':"J/kg/K" , 'long_name':"Specific heat of fresh ice"} )
RLSUB  = xr.DataArray (2.834e+6 , name='RLSUB' , attrs={'units':"J/kg"   , 'long_name':"Pure ice latent heat of sublimation"} )
RLFUS  = xr.DataArray (0.334e+6 , name='RLFUS' , attrs={'units':"J/kg"   , 'long_name':"Latent heat of fusion of fresh ice"} )
RTMLT  = xr.DataArray (0.054    , name='RTMLT' , attrs={'units':"C/PSU"  , 'long_name':"Decrease of seawater meltpoint with salinity"} )

RDAY   = xr.DataArray (RJJHH*RHHMM*RMMSS           , name='RDAY'  , attrs={'units':"s"  , 'long_name':"Day length"} )
RSIYEA = xr.DataArray (365.25*RDAY*2*np.pi/6.283076, name='RSIYEA', attrs={'units':"s"  , 'long_name':"Sideral year length"} )
RSIDAY = xr.DataArray (RDAY/(1+RDAY/RSIYEA)        , name='RSIDAY', attrs={'units':"s"  , 'long_name':"Sideral day length"} )
ROMEGA = xr.DataArray (2*np.pi/RSIDAY              , name='ROMEGA', attrs={'units':"s-1", 'long_name':"Earth rotation parameter"} )

APERIO_VALID_RANGE = [0, 1, 4, 4.2, 5, 6, 6.2]

## Default names of dimensions                                                 
UDIMS=dict({'x':'x', 'y':'y', 'z':'olevel', 't':'time_counter'})

## All possible names of lon/lat variables in Nemo files                       
LONNAME=['nav_lon', 'nav_lon_T', 'nav_lon_U', 'nav_lon_V', 'nav_lon_F', 'nav_lon_W',
             'nav_lon_grid_T', 'nav_lon_grid_U', 'nav_lon_grid_V', 'nav_lon_grid_F', 'nav_lon_grid_W']
LATNAME=['nav_lat', 'nav_lat_T', 'nav_lat_U', 'nav_lat_V', 'nav_lat_F', 'nav_lat_W',
             'nav_lat_grid_T', 'nav_lat_grid_U', 'nav_lat_grid_V', 'nav_lat_grid_F', 'nav_lat_grid_W']

## All possible names of dimensions in Nemo files                             
XNAME = [ 'x_grid_W', 'x_grid_T', 'x_grid_U', 'x_grid_V', 'x_grid_F',
          'lon', 'nav_lon', 'longitude', 'X1', 'x_c', 'x_f', 'x', 'X', 'X1', 'xx', 'XX',]
YNAME = [ 'y_grid_W', 'y_grid_T', 'y_grid_U', 'y_grid_V', 'y_grid_F',
          'lat', 'nav_lat', 'latitude' , 'Y1', 'y_c', 'y_f', 'y', 'Y', 'Y1', 'yy', 'YY',]
ZNAME = [ 'z', 'Z', 'Z1', 'zz', 'ZZ', 'depth', 'tdepth', 'udepth',
          'vdepth', 'wdepth', 'fdepth', 'deptht', 'depthu',
          'depthv', 'depthw', 'depthf', 'olevel', 'z_c', 'z_f',
          'rho', 'rhop', 'Rho', 'Rhop', 'RHO', 'RHOP', 'sigma', 'Sigma', 'SIGMA']
TNAME = [ 't', 'T', 'tt', 'TT', 'time', 'time_counter', 'time_centered', 'time', 'TIME', 'TIME_COUNTER', 'TIME_CENTERED', ]
BNAME = [ 'bnd', 'bnds', 'bound', 'bounds', 'vertex', 'nvertex', 'two', 'two1', 'two2', 'four', 'axis_nbounds' ]

## All possible units of dimensions in NEMO files                     
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
Ttab = np.linspace (-2, 40, 100)
Stab = np.linspace ( 0, 40, 100)

Ttab = xr.DataArray (Ttab, dims=('Temperature',), coords=(Ttab,), attrs={'unit':'degrees_celcius', 'long_name':'Temperature'})
Stab = xr.DataArray (Stab, dims=('Salinity'   ,), coords=(Stab,), attrs={'unit':'PSU'            , 'long_name':'Salinity'   })

##                                                                             
Regions = dict (
    { 'region' : {
        'NorthAtlantic'    : {'Basin': 'North Atlantic'         , 'ColorLine':np.array ([  0, 255,   0])/255, 'Marker':'1'},
        'SubpolarNorthAtl' : {'Basin': "Subpolar North Atlantic", 'ColorLine':np.array ([  0,   0,   0])/255, 'Marker':'p'},
        'Labrador'         : {'Basin': "Labrador Sea"           , 'ColorLine':np.array ([112, 160, 205])/255, 'Marker':'s'},
        'Barents'          : {'Basin': "Barents Sea"            , 'ColorLine':np.array ([196, 121,   0])/255, 'Marker':'^'},
        'Irminger'         : {'Basin': "Irminger Sea"           , 'ColorLine':np.array ([178, 178, 178])/255, 'Marker':'v'},
        'NordicSeas'       : {'Basin': "Nordic Seas"            , 'ColorLine':np.array ([  0,  52, 102])/255, 'Marker':'<'},     
        'Rockal'           : {'Basin': "Rockal"                 , 'ColorLine':np.array ([  0,  79,   0])/255, 'Marker':'>'},
        'MedWest'          : {'Basin': "Mediterranean (west)"   , 'ColorLine':np.array ([255,   0,   0])/255, 'Marker':'P'},        
        'MedEast'          : {'Basin': "Mediterranean (east)"   , 'ColorLine':np.array ([0  ,   0, 255])/255, 'Marker':'x'},     
        'Wedell'           : {'Basin': "Wedell Sea"             , 'ColorLine':np.array ([0  ,   0, 255])/255, 'Marker':'x'},     
        'Davis'            : {'Basin': "Davis Sector"           , 'ColorLine':np.array ([255,   0,   0])/255, 'Marker':'p'},
        'CircumPolar'      : {'Basin': "Circum Polar"           , 'ColorLine':np.array ([0  , 255,   0])/255, 'Marker':'p'},  
      },
      'eORCA1': {
        'NorthAtlantic'    : {'idyx': {'x':slice(226,299), 'y':slice(259,313)}},
        'SubpolarNorthAtl' : {'idyx': {'x':slice(226,299), 'y':slice(259,281)}},
        'Labrador'         : {'idyx': {'x':slice(226,249), 'y':slice(260,288)}},
        'Barents'          : {'idyx': {'x':slice(270,304), 'y':slice(312,330)}},
        'Irminger'         : {'idyx': {'x':slice(246,267), 'y':slice(260,285)}},
        'NordicSeas'       : {'idyx': {'x':slice(260,299), 'y':slice(283,313)}},
        'Rockal'           : {'idyx': {'x':slice(265,290), 'y':slice(263,283)}},
        'MedWest'          : {'idyx': {'x':slice(285,303), 'y':slice(235,253)}},
        'MedEast'          : {'idyx': {'x':slice(302,325), 'y':slice(233,253)}},
        'Wedell'           : {'idyx': {'x':slice(228,300), 'y':slice( 10, 93)}},
        'Davis'            : {'idyx': {'x':slice(  1, 20), 'y':slice( 60, 93)}},
        'CircumPolar'      : {'idyx': {'x':slice(  2,360), 'y':slice( 50, 93)}},
      },
      'ORCA2': {
        'NorthAtlantic'    : {'idyx': {'x':slice(111,146), 'y':slice(109,135)}},
        'SubpolarNorthAtl' : {'idyx': {'x':slice(111,146), 'y':slice(109,123)}},
        'Labrador'         : {'idyx': {'x':slice(111,122), 'y':slice(112,127)}},
        'Barents'          : {'idyx': {'x':slice(136,149), 'y':slice(134,146)}},
        'Irminger'         : {'idyx': {'x':slice(121,131), 'y':slice(112,122)}},
        'NordicSeas'       : {'idyx': {'x':slice(130,150), 'y':slice(119,135)}},
        'Rockal'           : {'idyx': {'x':slice(130,143), 'y':slice(111,121)}},
        'MedWest'          : {'idyx': {'x':slice(141,153), 'y':slice(100,108)}},
        'MedEast'          : {'idyx': {'x':slice(153,179), 'y':slice( 95,105)}},
        'Wedell'           : {'idyx': {'x':slice(112,149), 'y':slice(  2, 25)}},
        'Davis'            : {'idyx': {'x':slice(  1, 10), 'y':slice( 10, 25)}},
        'CircumPolar'      : {'idyx': {'x':slice(  2,180), 'y':slice( 10, 25)}},
      }
   }
)

Regions['eORCA1.2']   = Regions['eORCA1']
Regions['eORCA1.4']   = Regions['eORCA1']
Regions['eORCA1.4.2'] = Regions['eORCA1']

Regions['ORCA2.3']    = Regions['ORCA2']
Regions['ORCA2.4']    = Regions['ORCA2']

for name, bas in Regions['ORCA2.4'].items() :
    #print (bas)
    Regions['ORCA2.4'][name]['idyx']['y'] = slice(bas['idyx']['y'].start-1, bas['idyx']['y'].stop-1)
    Regions['ORCA2.4'][name]['idyx']['x'] = slice(bas['idyx']['x'].start-1, bas['idyx']['x'].stop-1)
for name, bas in Regions['eORCA1.4.2'].items() :
    #print (bas)
    Regions['eORCA1.4.2'][name]['idyx']['y'] = slice(bas['idyx']['y'].start-1, bas['idyx']['y'].stop-1)
    Regions['eORCA1.4.2'][name]['idyx']['x'] = slice(bas['idyx']['x'].start-1, bas['idyx']['x'].stop-1)
    
known_domains = dict ( 
    { 'orca2'      : {'cfg_name':'orca2'      , 'CFG_name':'ORCA2'     , 'cd_cfg':'orca', 'kk_cfg': 2, 'jpk':31, 'jpj': 149, 'jpi': 182, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'T', 'nperio':4, 'aperio':4  , 'Halo':True },
      'orca2.3'    : {'cfg_name':'orca2.3'    , 'CFG_name':'ORCA2.3'   , 'cd_cfg':'orca', 'kk_cfg': 2, 'jpk':31, 'jpj': 149, 'jpi': 182, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'T', 'nperio':4, 'aperio':4  , 'Halo':True },
      'orca2.4'    : {'cfg_name':'orca2.4  '  , 'CFG_name':'ORCA2.4'   , 'cd_cfg':'orca', 'kk_cfg': 2, 'jpk':31, 'jpj': 148, 'jpi': 180, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'T', 'nperio':4, 'aperio':4  , 'Halo':True },
      'orca2.4.2'  : {'cfg_name':'orca2.4.2'  , 'CFG_name':'ORCA2.4.2' , 'cd_cfg':'orca', 'kk_cfg': 2, 'jpk':31, 'jpj': 148, 'jpi': 180, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'T', 'nperio':4, 'aperio':4.2, 'Halo':False},
      'eorca1.2'   : {'cfg_name':'eorca1.2'   , 'CFG_name':'eORCA1.2'  , 'cd_cfg':'orca', 'kk_cfg': 1, 'jpk':75, 'jpj': 332, 'jpi': 362, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'F', 'nperio':6, 'aperio':6  , 'Halo':True },
      'eorca1.4 '  : {'cfg_name':'eorca1.4'   , 'CFG_name':'eORCA1.4'  , 'cd_cfg':'orca', 'kk_cfg': 1, 'jpk':75, 'jpj': 332, 'jpi': 362, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'F', 'nperio':6, 'aperio':6  , 'Halo':True },
      'eorca1.4.0' : {'cfg_name':'eorca1.4.0' , 'CFG_name':'eORCA1.4.0', 'cd_cfg':'orca', 'kk_cfg': 1, 'jpk':75, 'jpj': 332, 'jpi': 362, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'F', 'nperio':6, 'aperio':6  , 'Halo':True },
      'eorca1.4.2' : {'cfg_name':'eorca1.4.2' , 'CFG_name':'eORCA1.4.2', 'cd_cfg':'orca', 'kk_cfg': 1, 'jpk':75, 'jpj': 331, 'jpi': 360, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'F', 'nperio':6, 'aperio':6.2, 'Halo':False},
      'eorca025'   : {'cfg_name':'eorca025'   , 'CFG_name':'eORCA025'  , 'cd_cfg':'orca', 'kk_cfg':25, 'jpk':75, 'jpj':1207, 'jpi':1442, 'Iperio':True, 'Jperio':False, 'NFold':True, 'NFtype':'F', 'nperio':6, 'aperio':6  , 'Halo':True },
    } )

class Domain :
    '''
    Defines all values defining a NEMO domain
    Tries to infers all values from partial information
    '''
    def update (self, dico=None, **kwargs) :
        '''Use a dictionnary to update values'''
        if dico :
            for attr in dico.keys () :
                super().__setattr__ (attr, dico[attr])
        self.__dict__.update (kwargs)
    def keys    (self) :
        return self.__dict__.keys()
    def values  (self) :
        return self.__dict__.values()
    def items   (self) :
        return self.__dict__.items()
    def dict    (self) :
        return self.__dict__
    def pop     (self, attr) :
        zv = self[attr]
        delattr (self, attr)
        return zv
    ## Hidden functions
    def __str__     (self) :
        return str  (self.__dict__)
    def __repr__    (self) :
        return repr (self.__dict__)
    def __name__    (self) :
        return self.__class__.__name__
    def __getitem__ (self, attr) :
        return getattr (self, attr)
    def __setitem__ (self, attr, value) :
        setattr (self, attr, value)
    def __iter__    (self) :
        return self.__dict__.__iter__()
    def __next__    (self) :
        return self['__dict__'].__next__()
    def __len__     (self) :
        return len (self.__dict__)
    def __copy__    (self) :
        return dict (self)
    
    def __init__ (self:Self, ptab:Union[xr.DataArray,None]=None, cfg_name:Union[str,None]=None, CFG_name:Union[str,None]=None, 
                  cd_cfg:Union[str,None]=None, kk_cfg:Union[int,None]=None, jpi:Union[int,None]=None, jpj:Union[int,None]=None, jpk:Union[int,None]=None,
                  Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None,
                  nperio:Union[int,None]=None, aperio:Union[int,float,None]=None,
                  Halo:Union[bool,None]=None, ForceDefaults:Union[bool,None]=False, Debug:Union[bool,None]=False,
                  domain=None) -> None :

        if OPTIONS['Debug'] or Debug :# type: ignore
            print ( f'{ptab=}' )
            print ( f'{ptab is None = }, {ptab is not None = }, {(not (ptab is None))=}')
            
        if domain is not None :
            if domain.cfg_name and cfg_name is not None : cfg_name = domain.cfg_name
            if domain.CFG_name and not CFG_name : CFG_name = domain.CFG_name
            if domain.cd_cfg   and not cd_cfg   : cd_cfg   = domain.cd_cfg
            if domain.kk_cfg   and not kk_cfg   : kk_cfg   = domain.kk_cfg
            if domain.jpi      and not jpi      : jpi      = domain.jpi
            if domain.jpj      and not jpj      : jpj      = domain.jpj
            if domain.jpk      and not jpk      : jpk      = domain.jpk
            if domain.Iperio   and not Iperio   : Iperio   = domain.Iperio
            if domain.Jperio   and not Jperio   : Jperio   = domain.Jperio
            if domain.NFold    and not NFold    : NFold    = domain.NFold
            if domain.NFtype   and not NFtype   : NFtype   = domain.NFtype
            if domain.nperio   and not nperio   : nperio   = domain.nperio
            if domain.aperio   and not aperio   : aperio   = domain.aperio
            if domain.Halo     and not Halo     : Halo     = domain.Halo
            if domain.ForceDefaults and not ForceDefaults : ForceDefaults=domain.ForceDefaults

        if cfg_name :
            cfg_name = cfg_name.lower ()
            CFG_name = cfg_name.upper ()
            if 'EORCA' in CFG_name :
                CFG_name = CFG_name.replace ( "EORCA", "eORCA" )

        if CFG_name and not cfg_name :
            cfg_name = CFG_name.lower ()
            CFG_name = CFG_name.upper ()
            if 'EORCA' in CFG_name :
                CFG_name = CFG_name.replace ( "EORCA", "eORCA" )        
                 
        if not (ptab is None) :
            if OPTIONS['Debug'] or Debug :
                print ( f'{ptab.shape=}' )
            ax, ix = find_axis (ptab, 'x')
            ay, jy = find_axis (ptab, 'y')
            az, kz = find_axis (ptab, 'z')

            if OPTIONS['Debug'] or Debug : 
                print (f'{ax=}, {ix=}, {ay=}, {jy=}, {az=}, {kz=}')

            if ix is not None :  zjpi = ptab.shape[ix]
            else :               zjpi = None
            if jy is not None :  zjpj = ptab.shape[jy]
            else :               zjpj = None
            if kz is not None :  zjpk = ptab.shape[kz]
            else :               zjpk = None

            if OPTIONS['Debug'] or Debug : 
                print (f'{jpk=} {jpj=} {jpi=} {zjpk=} {zjpj=} {zjpi=}')

            zerr = 0
            if jpi :
                if zjpi  is not None :
                    if jpi != zjpi : zerr += 1
            else :
                if zjpi : jpi = zjpi
                
            if jpj :
                if zjpj  is not None :
                    if jpj != zjpj : zerr += 1
            else :
                if zjpj : jpj = zjpj
                    
            if jpk :
                if zjpk is not None :
                    if jpk != zjpk : zerr += 1
            else :
                if zjpk : jpk = zjpk

            if zerr > 0 :
                raise Exception (f'Error : shape of ptab ={ptab.shape} does not match {jpk=}, {jpj=}, {jpi=}')

        if OPTIONS['Debug'] or Debug : 
            print (f'{jpk=} {jpj=} {jpi=}')

        if OPTIONS['Debug'] or Debug : 
            print ('Find by dimensions')
        if jpj == 149 and jpi == 182 :
            domain = Domain (cfg_name='orca2.3')
        if jpj == 148 and jpi == 180 :
            domain = Domain (cfg_name='orca2.3')
        if jpj == 332 and jpi == 362 :
            domain = Domain (cfg_name='eorca1.4.0')
        if jpj == 331 and jpi == 360 :
            domain = Domain (cfg_name='eorca1.4.2')
        if OPTIONS['Debug'] or Debug : 
            print (domain)

        if domain is not None :
            if domain.cfg_name and not cfg_name : cfg_name = domain.cfg_name
            if domain.CFG_name and not CFG_name : CFG_name = domain.CFG_name
            if domain.cd_cfg   and not cd_cfg   : cd_cfg   = domain.cd_cfg
            if domain.kk_cfg   and not kk_cfg   : kk_cfg   = domain.kk_cfg
            if domain.jpi      and not jpi      : jpi      = domain.jpi
            if domain.jpj      and not jpj      : jpj      = domain.jpj
            if domain.jpk      and not jpk      : jpk      = domain.jpk
            if domain.Iperio   and not Iperio   : Iperio   = domain.Iperio
            if domain.Jperio   and not Jperio   : Jperio   = domain.Jperio
            if domain.NFold    and not NFold    : NFold    = domain.NFold
            if domain.NFtype   and not NFtype   : NFtype   = domain.NFtype
            if domain.nperio   and not nperio   : nperio   = domain.nperio
            if domain.aperio   and not aperio   : aperio   = domain.aperio
            if domain.Halo     and not Halo     : Halo     = domain.Halo
            if domain.ForceDefaults and not ForceDefaults : ForceDefaults=domain.ForceDefaults

        if OPTIONS['Debug'] or Debug : 
            print ( f'{cfg_name=} {cd_cfg=} {kk_cfg=} {Halo=} {NFtype=} {jpj=} {jpi=} {nperio=} {aperio=}' )

        if OPTIONS['Debug'] or Debug : 
            print ('Find by configuration names')
        zf = None
        
        for zd in known_domains.values() :
            if OPTIONS['Debug'] or Debug : 
                print  ( f'handling {zd=}')
            if cfg_name and zd['cfg_name'] :
                if cfg_name.lower() == zd['cfg_name'].lower () :
                    zf = zd
            if CFG_name and zd['CFG_name'] :
                if CFG_name.upper() == zd['CFG_name'].upper () :
                    zf = zd
            if not zf :
                if cd_cfg and kk_cfg and zd['cd_cfg'] and zd['kk_cfg'] :
                    if cd_cfg == zd['cd_cfg'] and kk_cfg == zd['kk_cfg'] :
                        if OPTIONS['Debug'] or Debug : 
                            print  ( f"handling {zd['cd_cfg']=} {zd['kk_cfg']=} {cd_cfg=} {kk_cfg=}")
                        zf = zd
            if zf : break

        if zf :
            if OPTIONS['Debug'] or Debug : 
                print  ( f'handling {cfg_name=}')
            if ForceDefaults or cd_cfg is None :
                cd_cfg = 'orca'
                if ForceDefaults or kk_cfg is None : kk_cfg = zd['kk_cfg']
                if ForceDefaults or nperio is None : nperio = zd['nperio']
                if ForceDefaults or aperio is None : aperio = zd['aperio']
                if ForceDefaults or Iperio is None : Iperio = zd['Iperio']
                if ForceDefaults or Jperio is None : Jperio = zd['Jperio']
                if ForceDefaults or NFold  is None : NFold  = zd['NFold']
                if ForceDefaults or NFtype is None : NFtype = zd['NFtype']
                if ForceDefaults or Halo   is None : Halo   = zd['Halo']
                if ForceDefaults or jpk    is None : jpk    = zd['jpk']
                if ForceDefaults or jpj    is None : jpj    = zd['jpj']
                if ForceDefaults or jpi    is None : jpi    = zd['jpi']

        if OPTIONS['Debug'] or Debug : 
            print ( 'Fill missing values' )
        if aperio == 4 :
            if ForceDefaults or nperio is None : nperio = 4
            if ForceDefaults or Iperio is None : Iperio = True
            if ForceDefaults or Jperio is None : Jperio = False
            if ForceDefaults or NFold  is None : NFold  = True
            if ForceDefaults or NFtype is None : NFtype = 'T'
            if ForceDefaults or Halo   is None : Halo   = True
    
        if aperio == 4.2 :
            if ForceDefaults or nperio is None : nperio = 4
            if ForceDefaults or Iperio is None : Iperio = True
            if ForceDefaults or Jperio is None : Jperio = False
            if ForceDefaults or NFold  is None : NFold  = True
            if ForceDefaults or NFtype is None : NFtype = 'T'
            if ForceDefaults or Halo   is None : Halo   = False

        if aperio == 6 :
            if ForceDefaults or nperio is None : nperio = 6
            if ForceDefaults or Iperio is None : Iperio = True
            if ForceDefaults or Jperio is None : Jperio = False
            if ForceDefaults or NFold  is None : NFold  = True
            if ForceDefaults or NFtype is None : NFtype = 'F'
            if ForceDefaults or Halo   is None : Halo   = True

        if aperio == 6.2 :
            if ForceDefaults or nperio is None : nperio = 6
            if ForceDefaults or Iperio is None : Iperio = True
            if ForceDefaults or Jperio is None : Jperio = False
            if ForceDefaults or NFold  is None : NFold  = True
            if ForceDefaults or NFtype is None : NFtype = 'F'
            if ForceDefaults or Halo   is None : Halo   = False

        if nperio == 4 :
            if ForceDefaults or aperio is None : aperio = 4 if Halo else 4.2

        if nperio == 6 :
            if ForceDefaults or aperio is None : aperio = 6 if Halo else 6.2

        if Iperio and NFold and NFtype=='T' and Halo     : nperio, aperio = 4, 4
        if Iperio and NFold and NFtype=='F' and Halo     : nperio, aperio = 6, 6
        if Iperio and NFold and NFtype=='T' and not Halo : nperio, aperio = 4, 4.2
        if Iperio and NFold and NFtype=='F' and not Halo : nperio, aperio = 6, 6.2

        if CFG_name :
            if 'EORCA' in CFG_name :
                CFG_name = CFG_name.replace ( "EORCA", "eORCA" )

        self.cfg_name = cfg_name
        self.CFG_name = CFG_name
        self.cd_cfg   = cd_cfg
        self.kk_cfg   = kk_cfg
        self.jpk      = jpk  
        self.jpj      = jpj
        self.jpi      = jpi
        self.Iperio   = Iperio
        self.Jperio   = Jperio
        self.NFold    = NFold
        self.NFtype   = NFtype
        self.nperio   = nperio
        self.aperio   = aperio
        self.Halo     = Halo
        self.ForceDefaults=ForceDefaults
                     
def get_shape (ptab:xr.DataArray) -> str :
    '''Get shape of ptab return a string with axes names

    shape may contain X, Y, Z or T
    Y is missing for a latitudinal slice
    X is missing for on longitudinal slice
    etc ...
    '''
    push_stack ( 'get_shape ( ptab )' )
    g_shape = ''
    if find_axis (ptab, 'x')[0] :
        g_shape = 'X' + g_shape
    if find_axis (ptab, 'y')[0] :
        g_shape = 'Y' + g_shape
    if find_axis (ptab, 'z')[0] :
        g_shape = 'Z' + g_shape
    if find_axis (ptab, 't')[0] :
        g_shape = 'T' + g_shape
        
    pop_stack ( f'get_shape : {g_shape}' )
    return g_shape

def find_axis (ptab:Union[xr.DataArray,xr.Dataset], axis:str='z', back:bool=True, Debug:bool=False) -> tuple[Union[str,None], Union[int,None]] :
    '''Returns name and name of the requested axis'''
    push_stack ( f'find_axis ( ptab, {axis=}, {back=}' )
    
    ax, ix = None, None

    ax_found, ax_name, unit_list, length = None, None, None, None
    
    if axis in XNAME :
        ax_found, ax_name, unit_list, length   = 'x', XNAME, XUNIT, XLENGTH
    if axis in YNAME :
        ax_found, ax_name, unit_list, length   = 'y', YNAME, YUNIT, YLENGTH
    if axis in ZNAME :
        ax_found, ax_name, unit_list, length   = 'z', ZNAME, ZUNIT, ZLENGTH
    if axis in TNAME :
        ax_found, ax_name, unit_list, length   = 't', TNAME, TUNIT, None
    if axis in BNAME :
        ax_found, ax_name, unit_list, length   = 'b', BNAME, None , None
    if OPTIONS['Debug'] or Debug :
        if ax_name is not None :
            print ( f'Working on axis found by name : {axis=} : {ax_name=} {unit_list=} {length=}' )

    # Try by 'axis' attribute
    if ix is None :
        if OPTIONS['Debug'] or Debug :
            print ( 'ix not found - 1' )
        for ii, dim in enumerate (ptab.dims) :
            if OPTIONS['Debug'] or Debug :
                print ( f'{ii=} {dim=}' )
            if 'axis' in ptab.coords[dim].attrs.keys() :
                l_axis = ptab.coords[dim].attrs['axis']
                if OPTIONS['Debug'] or Debug :
                    print ( f'Rule 1 : Trying {ii=} {dim=} {l_axis=}' )
                if l_axis in ax_name and l_axis == str('X') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 1 : xaxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix, ax = (ii, dim)
                if l_axis in ax_name and l_axis == str('Y') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 1 : yaxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix, ax = (ii, dim)
                if l_axis in ax_name and l_axis == str('Z') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 1 : zaxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix, ax = (ii, dim)
                if l_axis in ax_name and l_axis == str('T') :
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 1 : taxis found by attribute : {ax=} {l_axis=} {axis=} : {ax_name=} {l_axis=} {ii=} {dim=}' )
                    ix, ax = (ii, dim)

    # Try by name
    if OPTIONS['Debug'] or Debug :
        print ( 'Try by name')
    if ix is None :
        for ii, dim in enumerate (ptab.dims) :
            if OPTIONS['Debug'] or Debug :
                print ( f'{ii=} {dim=}' )
            if dim in ax_name :
                if OPTIONS['Debug'] or Debug :
                    print ( f'Rule 2 : {dim=} axis found by name in : {ax_name=}' )
                ix, ax = ii, dim


    # If not found, try by units
    if ix is None  :
        for ii, dim in enumerate (ptab.dims) :
            if 'units' in ptab.coords[dim].attrs.keys() :
                zunit =  str(ptab.coords[dim].attrs['units'])
                if unit_list :
                    for name in unit_list :
                        if name in zunit :
                            if OPTIONS['Debug'] or Debug :
                                print ( f'Rule 3 : {name=} found by unit : {axis=} : {unit_list=} {ii=} {dim=}' )
                            ix, ax = ii, dim

    # If dimension not found, try by length
    if not ix :
        if not length is None :
            l_shape = list(ptab.sizes)
            for nn in np.arange ( len(l_shape) ) :
                if l_shape[nn] in length :
                    ix = nn
                    ax = None
                    if OPTIONS['Debug'] or Debug :
                        print ( f'Rule 4 : {ax_name=} axis found by length : {axis=} : {XNAME=} {ix=} {ax=}' )

    if ix and back :
        ix -= len (ptab.dims)

    pop_stack ( f'find_axis : {ax}, {ix}' )
    return ax, ix

def find_axis_bounds (ds:Union[xr.DataArray,xr.Dataset], axis:str='z', Debug:bool=False) -> tuple :
    '''
    Find axis and associated bounds
    '''
    push_stack ( f'find_axis_bounds ( ds, {axis=}' )

    ax, ix = find_axis (ds, axis)
    if OPTIONS['Debug'] or Debug :
        print ( f'{ax=} {ix=}' )

    ab   = None
    bdim = None
    for bname in BNAME :
        zname = f'{ax}_{bname}'
        if OPTIONS['Debug'] or Debug :
            print ( f'{zname=}' )
        for var in ds.variables :
            if zname == var :
                ab = zname

    for bname in ['axis_nbounds'] :
        if OPTIONS['Debug'] or Debug :
            print ( f'{bname=}' )
        for var in ds.variables :
            if bname == var :
                ab = bname

    if ab :
        for dim in ds[ab].dims :
            if dim != ax :               
                bdim = dim
                
    pop_stack ( f'find_axis_bounds : {ax=}, {ab=} {bdim=}' )

    return ax, ab, bdim

def build_bounds2d (glont:Union[xr.DataArray,None]=None, glatt:Union[xr.DataArray,None]=None, 
                    glonu:Union[xr.DataArray,None]=None, glatu:Union[xr.DataArray,None]=None, 
                    glonv:Union[xr.DataArray,None]=None, glatv:Union[xr.DataArray,None]=None,
                    glonf:Union[xr.DataArray,None]=None, glatf:Union[xr.DataArray,None]=None,
                    rpoint:Union[str,None]=None, 
                    Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None,
                    NFtype:Union[str,None]=None, Halo:Union[bool,None]=None,
                    aperio:Union[int,float,None]=None, domain:Union[Domain,None]=None,
                    close:bool=False, first:bool=True, positive:bool=True, vertex2d:bool=False, Debug:bool=False) -> tuple[xr.DataArray|None, xr.DataArray|None]|None :
    '''
    Builds arrays of corners for each point (T, U, V or F)

    T corners are build is glonf, glatt are given
    U corners are build is glonv, glatv are given
    V corners are build is glonu, glatu are given
    F corners are build is glont, glatf are given

    Corners that can not be computed are set to None

    If close is True, return 5 corners to close each polygon (useful if you use shapely).

    If vertex2d, builds bounds with shape (nlat, nlon, 2, 2)
    
    Corners dimension 'bounds' is the last dimension
    if first is True, it is the first dimension
   
    If rpoint is set to any in ['T', 'U', 'V', 'F'], returns bounds_lon{rpoint}, bounds_lat{rpoint}
    Else, returns bounds_lont, bounds_latt, bounds_lonu, bounds_latu, bounds_lonv, bounds_latv, bounds_lonf, bounds_latf
    (some arrays set to None when the computation is not possible)
    '''
    zdom= Domain (Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                  aperio=aperio, domain=domain)

    if not glont is None :
        zdom  = Domain (glont, domain=zdom)
    else : 
        if not glonu is None :
            zdom  = Domain (glonu, domain=zdom)
        else : 
            if not glonv is None :
                zdom  = Domain (glonv, domain=zdom)
            else : 
                if not glonf is None :
                    zdom  = Domain (glonf, domain=zdom)

    if glont is not None :
        axt, ixt = find_axis (glont, 'x')
        ayt, iyt = find_axis (glont, 'y')
        glont = lbc (glont, domain=zdom, cd_type='T')
    if glont is not None :
        glatt = lbc (glatt, domain=zdom, cd_type='T')
    if glonu is not None :
        axu, ixu = find_axis (glonu, 'x')
        ayu, iyu = find_axis (glonu, 'y')
        glonu = lbc (glonu, domain=zdom, cd_type='U')
    if glatu is not None :
        glatu = lbc (glatu, domain=zdom, cd_type='U')
    if glonv is not None :
        axv, ixv = find_axis (glonv, 'x')
        ayv, iyv = find_axis (glonv, 'y')
        glonv = lbc (glonv, domain=zdom, cd_type='V')
    if glatv is not None :
        glatv = lbc (glatv, domain=zdom, cd_type='V')
    if glonf is not None :
        axf, ixf = find_axis (glonf, 'x')
        ayf, iyf = find_axis (glonf, 'y')
        glonf = lbc (glonf, domain=zdom, cd_type='F')
    if glatf is not None :
        glatf = lbc (glatf, domain=zdom, cd_type='F')
        
    jpj, jpi = zdom.jpj, zdom.jpi
    if vertex2d :
        bounds=2
        nver_coord = np.arange (bounds)
        nver_coord = xr.DataArray ( [nver_coord, nver_coord], dims=('nver1', 'nver2'), coords=(nver_coord,nver_coord))
        nver_list = [ {'two1':0, 'two2':0},  {'two1':1, 'two2':1},  {'two1':1, 'two2':0},  {'two1':0, 'two2':1}, ]

        if close :
            raise ValueError ( 'close polygon is not available with vertex2d=True')
        
    else :
        bounds = 5 if close else 4
        nver_coord = np.arange (bounds)
        nver_coord = xr.DataArray (nver_coord, dims=('bounds',), coords=(nver_coord,))
        
        if positive : 
            nver_list = [ {'bounds':0}, {'bounds':3}, {'bounds':2}, {'bounds':1}]
        else :
            nver_list = [ {'bounds':0}, {'bounds':1}, {'bounds':2}, {'bounds':3}]
            
        if close :
            nver_list.append ({'bounds':-1})

    if not (glonf is None and glatf is None) :
        if glont is not None :
            if first : 
                bounds_lont = nver_coord * glont * np.nan
            else :
                bounds_lont = glont * nver_coord * np.nan
        else :
            if first : 
                bounds_lont = nver_coord * glonf * np.nan
            else : 
                bounds_lont = glonf * nver_coord * np.nan
        if glatt is not None :
            if first : 
                bounds_latt = nver_coord * glatt * np.nan
            else : 
                bounds_latt = glatt * nver_coord * np.nan
        else :
            if first : 
                bounds_latt = nver_coord * glatf * np.nan
            else :
                bounds_latt = glatf * nver_coord * np.nan
                
        bounds_lont [nver_list[0]] = glonf.roll ({ayf: 1,axf: 1})
        bounds_latt [nver_list[0]] = glatf.roll ({ayf: 1,axf: 1})
        bounds_lont [nver_list[1]] = glonf.roll ({ayf: 0,axf: 1})
        bounds_latt [nver_list[1]] = glatf.roll ({ayf: 0,axf: 1})
        bounds_lont [nver_list[2]] = glonf.roll ({ayf: 0,axf: 0})
        bounds_latt [nver_list[2]] = glatf.roll ({ayf: 0,axf: 0})
        bounds_lont [nver_list[3]] = glonf.roll ({ayf: 1,axf: 0})
        bounds_latt [nver_list[3]] = glatf.roll ({ayf: 1,axf: 0})
        
        if close :
            bounds_lont [nver_list[-1]] = bounds_lont [nver_list[0]]
            bounds_latt [nver_list[-1]] = bounds_latt [nver_list[0]]

        bounds_lont = lbc (bounds_lont, domain=zdom)
        bounds_latt = lbc (bounds_latt, domain=zdom)
        if not glont is None :
            bounds_lont = clo_lon (bounds_lont, glont)
            bounds_lont.attrs.update (glont.attrs)
        else :            
            bounds_lont = clo_lon (bounds_lont, glonf)
            bounds_lont.attrs.update (glonf.attrs)
        if not glatt is None :
            bounds_latt.attrs.update (glatt.attrs)
        else : 
            bounds_latt.attrs.update (glatf.attrs)
        
    else :
        bounds_lont = None
        bounds_latt = None

    if not (glonv is None and glatv is None) : 
        if glonu is not None :
            if first : 
                bounds_lonu = nver_coord * glonu * np.nan
            else :
                bounds_lonu = glonu * nver_coord * np.nan
        else :
            if first : 
                bounds_lonu = nver_coord * glonv * np.nan
            else : 
                bounds_lonu = glonv * nver_coord * np.nan
        if glatu is not None :
            if first : 
                bounds_latu = nver_coord * glatu * np.nan
            else : 
                bounds_latu = glatu * nver_coord * np.nan
        else :
            if first : 
                bounds_latu = nver_coord * glatv * np.nan
            else :
                bounds_latu = glatv * nver_coord * np.nan
        
        bounds_lonu [nver_list[0]] = glonv.roll ({ayv: 1,axv: 0})
        bounds_latu [nver_list[0]] = glatv.roll ({ayv: 1,axv: 0})
        bounds_lonu [nver_list[1]] = glonv.roll ({ayv: 0,axv: 0})
        bounds_latu [nver_list[1]] = glatv.roll ({ayv: 0,axv: 0})
        bounds_lonu [nver_list[2]] = glonv.roll ({ayv: 0,axv:-1})
        bounds_latu [nver_list[2]] = glatv.roll ({ayv: 0,axv:-1})
        bounds_lonu [nver_list[3]] = glonv.roll ({ayv: 1,axv:-1})
        bounds_latu [nver_list[3]] = glatv.roll ({ayv: 1,axv:-1})
        if close :
            bounds_lonu [nver_list[-1]] = bounds_lonu [nver_list[0]]
            bounds_latu [nver_list[-1]] = bounds_latu [nver_list[0]]
        
        bounds_lonu = lbc (bounds_lonu, domain=zdom)
        bounds_latu = lbc (bounds_latu, domain=zdom)
        if glonu is not None :
            bounds_lonu = clo_lon (bounds_lonu, glonu)
            bounds_lonu.attrs.update (glonu.attrs)
        else :            
            bounds_lonu = clo_lon (bounds_lonu, glonv)
            bounds_lonu.attrs.update (glonv.attrs)
        if glatu is not None :
            bounds_latu.attrs.update (glatu.attrs)
        else : 
            bounds_latu.attrs.update (glatv.attrs)
    else :
        bounds_lonu = None
        bounds_latu = None

    if not (glonu is None and glatu is None) :        
        if glonv is not None :
            if first : 
                bounds_lonv = nver_coord * glonv * np.nan
            else :
                bounds_lonv = glonv * nver_coord * np.nan
        else :
            if first : 
                bounds_lonv = nver_coord * glonu * np.nan
            else : 
                bounds_lonv = glonu * nver_coord * np.nan
        if glatv is not None :
            if first : 
                bounds_latv = nver_coord * glatv * np.nan
            else : 
                bounds_latv = glatv * nver_coord * np.nan
        else :
            if first : 
                bounds_latv = nver_coord * glatu * np.nan
            else :
                bounds_latv = glatu * nver_coord * np.nan

        bounds_lonv [nver_list[0]] = glonu.roll ({ayu: 0,axu: 1})
        bounds_latv [nver_list[0]] = glatu.roll ({ayu: 0,axu: 1})
        bounds_lonv [nver_list[1]] = glonu.roll ({ayu:-1,axu: 1})
        bounds_latv [nver_list[1]] = glatu.roll ({ayu:-1,axu: 1})
        bounds_lonv [nver_list[2]] = glonu.roll ({ayu:-1,axu: 0})
        bounds_latv [nver_list[2]] = glatu.roll ({ayu:-1,axu: 0})
        bounds_lonv [nver_list[3]] = glonu.roll ({ayu: 0,axu: 0})
        bounds_latv [nver_list[3]] = glatu.roll ({ayu: 0,axu: 0})
        if close :
            bounds_lonv [nver_list[-1]] = bounds_lonv [nver_list[0]]
            bounds_latv [nver_list[-1]] = bounds_latv [nver_list[0]]
      
        bounds_lonv = lbc (bounds_lonv, domain=zdom)
        bounds_latv = lbc (bounds_latv, domain=zdom)
        if not glonv is None :
            bounds_lonv = clo_lon (bounds_lonv, glonv)
            bounds_lonv.attrs.update (glonv.attrs)
        else :            
            bounds_lonv = clo_lon (bounds_lonv, glonu)
            bounds_lonv.attrs.update (glonu.attrs)
        if not glatv is None :
            bounds_latv.attrs.update (glatv.attrs)
        else : 
            bounds_latv.attrs.update (glatu.attrs)
    else :
        bounds_lonv = None
        bounds_latv = None

    if not (glont is None and glatt is None ): 
        if glonf is not None :
            if first : 
                bounds_lonf = nver_coord * glonf * np.nan
            else :
                bounds_lonf = glonf * nver_coord * np.nan
        else :
            if first : 
                bounds_lonf = nver_coord * glont * np.nan
            else : 
                bounds_lonf = glont * nver_coord * np.nan
        if glatf is not None :
            if first : 
                bounds_latf = nver_coord * glatf * np.nan
            else : 
                bounds_latf = glatf * nver_coord * np.nan
        else :
            if first : 
                bounds_latf = nver_coord * glatt * np.nan
            else :
                bounds_latf = glatt * nver_coord * np.nan

        bounds_lonf [nver_list[0]] = glont.roll ({ayt: 0,axt: 0})
        bounds_latf [nver_list[0]] = glatt.roll ({ayt: 0,axt: 0})
        bounds_lonf [nver_list[1]] = glont.roll ({ayt:-1,axt: 0})
        bounds_latf [nver_list[1]] = glatt.roll ({ayt:-1,axt: 0})
        bounds_lonf [nver_list[2]] = glont.roll ({ayt:-1,axt:-1})
        bounds_latf [nver_list[2]] = glatt.roll ({ayt:-1,axt:-1})
        bounds_lonf [nver_list[3]] = glont.roll ({ayt: 0,axt:-1})
        bounds_latf [nver_list[3]] = glatt.roll ({ayt: 0,axt:-1})
        if close :
            bounds_lonf [nver_list[-1]] = bounds_lonf [nver_list[0]]
            bounds_latf [nver_list[-1]] = bounds_latf [nver_list[0]]

        bounds_lonf = lbc (bounds_lonf, domain=zdom)
        bounds_latf = lbc (bounds_latf, domain=zdom)
        if not glonf is None :
            bounds_lonf = clo_lon (bounds_lonf, glonf)
            bounds_lonf.attrs.update (glonf.attrs)
        else :            
            bounds_lonf = clo_lon (bounds_lonf, glont)
            bounds_lonf.attrs.update (glont.attrs)
        if not glatf is None :
            bounds_latf.attrs.update (glatf.attrs)
        else : 
            bounds_latf.attrs.update (glatt.attrs)
    else :
        bounds_lonf = None
        bounds_latf = None

    if rpoint is None :
        return bounds_lont, bounds_latt, bounds_lonu, bounds_latu, bounds_lonv, bounds_latv, bounds_lonf, bounds_latf
    else : 
        if rpoint in ['t', 'T'] :
            return bounds_lont, bounds_latt
        if rpoint in ['u', 'U'] :
            return bounds_lonu, bounds_latu
        if rpoint in ['v', 'V'] :
            return bounds_lonv, bounds_latv
        if rpoint in ['f', 'F'] :
            return bounds_lonf, bounds_latf

def close_bounds (blon:xr.DataArray, blat:Union[xr.DataArray,None]=None) -> xr.DataArray :
    '''
    Close each polygon by adding the first point at the end of the polygon
    '''
    ab, ib = find_axis ( blon, 'bnds')
    blon = xr.concat ( [blon, blon[{ab:-1}]], dim=ab )
    if not blat is None :
        ab, ib = find_axis ( blon, 'bnds')
        blat = xr.concat ( [blat, blat[{ab:-1}]], dim=ab )
        return blon, blat
    else :
        return blon

def build_bounds1d (b2d:xr.DataArray, Debug:bool=False) -> xr.DataArray :
       
    az, ik = find_axis (b2d, 'z')
    ab, lk = find_axis (b2d, 'axis_nbounds')

    if OPTIONS['Debug'] or Debug :
        print (f'{az=} {ik=} {ab=} {lk=}')
    lshape = list(b2d.shape)
    lshape [ik] = lshape[ik]+1
    ldims = list(b2d.dims)
    ndim  = ldims[ik] + '_bnds1d'
    ldims [ik] = ldims[ik] + '_bnds1d'
    lshape.pop (lk)
    ldims.pop (lk)

    bnds1d = xr.DataArray (np.empty (lshape), dims=ldims)
    bnds1d [{ndim:slice(0,-1)}] = b2d.isel({ab:0}).values
    bnds1d [{ndim:-1}]           = b2d.isel({az:-1, ab:1}).values

    bnds1d = bnds1d.assign_coords ( {ndim:bnds1d.values})

    return bnds1d
    
#def build_bounds1d (ds, axis='z', Debug:bool=False) :
    # '''
    # Build cbounds variable at the XGCM format
    # '''
    # push_stack ( f'build_bounds ( ds, {axis=}' )

    # depth_bnds1d = None
    
    # var, var_bnds1d, bdim = find_axis_bounds (ds, axis)

    # if OPTIONS['Debug'] or Debug :
    #     print ( f'{bdim=}')
    # if bdim : 
    #     az, kz = find_axis ( ds[var], axis)
    #     ab, kb = find_axis ( ds[var_bnds1d], bdim)
        
    #     if OPTIONS['Debug'] or Debug :
    #         print (var, var_bnds1d, bdim, az, kz, ab, kb )
        
    #     lshape = list(ds[var].shape)
    #     lshape[kz] = lshape[kz]+1
    #     ldims=list(ds[var].dims)
    #     ldims[kz] = ldims[kz] + '_bnds1d'
        
    #     depth_bnds1d = xr.DataArray (np.empty (lshape), dims=ldims)
    #     depth_bnds1d[{ldims[kz]:slice(0,-1)}] = ds[var_bnds1d].isel({bdim:0}).values
    #     depth_bnds1d[{ldims[kz]:-1}]          = ds[var_bnds1d].isel({az:-1, bdim:1}).values

    # pop_stack ( 'build_bounds1d' )

    # return depth_bnds1d

def add_bounds1d (ds:xr.Dataset, Debug:bool=True) -> xr.Dataset : 
    '''
    Add bounds variable for T and Z axis, at the XGCM format
    '''
    push_stack ( 'add_bounds1d (ds)' )

    az, ik = find_axis (ds, 'z')
    at, il = find_axis (ds, 't')
    z_bnds = build_bounds1d (ds, 'z')
    t_bnds = build_bounds1d (ds, 't')

    if OPTIONS['Debug'] or Debug :
        print ( f'{az=} {ik=} {at=} {il=} {z_bnds=} {t_bnds=}' )
    
    if z_bnds is not None :
        ds = ds.merge ({f'{az}_bnds1d':z_bnds})
    if t_bnds is not None :
        ds = ds.merge ({f'{at}_bnds1d':t_bnds})

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

def fixed_lon (plon:xr.DataArray, center_lon:float=0.0, Debug:bool=False) -> xr.DataArray :
    '''
    Returns corrected longitudes for nicer plots

    lon        : longitudes of the grid. At least 2D.
    center_lon : center longitude. Default=0.

    Designed by Phil Pelson.
    See https://gist.github.com/pelson/79cf31ef324774c97ae7
    '''
    push_stack ( f'fixed_lon ( plon, {center_lon=}' )

    ax, ix = find_axis (plon, axis='x', back=True)
    ay, iy = find_axis (plon, axis='x', back=True)

    f_lon = plon.values.copy ()

    f_lon = xr.where (f_lon > center_lon+180., f_lon-360., f_lon)
    f_lon = xr.where (f_lon < center_lon-180., f_lon+360., f_lon)

    if OPTIONS['Debug'] or Debug :
        print ( f'fixed_lon : {type(f_lon)=}' )
    
    for i, start in enumerate (np.argmax (np.abs (np.diff (f_lon, axis=ix)) > 180., axis=ix)) :
        f_lon [..., i, start+1:] += 360

    if OPTIONS['Debug'] or Debug :
        print ( f'fixed_lon : {type(f_lon)=}' )

    # Special case for eORCA025
    if f_lon.shape [ix] == 1442 :
        f_lon [..., -2, :] = f_lon [..., -3, :]
    if f_lon.shape [ix] == 1440 :
        f_lon [..., -1, :] = f_lon [..., -2, :]

    if OPTIONS['Debug'] or Debug :
        print ( f'fixed_lon : {type(f_lon)=}' )

    if f_lon.min () > center_lon       : f_lon += -360.
    if f_lon.max () < center_lon       : f_lon +=  360.

    if OPTIONS['Debug'] or Debug :
        print ( f'fixed_lon : {type(f_lon)=}' )

    if f_lon.min () < center_lon-360. : f_lon +=  360.
    if f_lon.max () > center_lon+360. : f_lon += -360.

    f_lon = copy_attrs (f_lon, plon)

    pop_stack ( 'fixed_lon : f_lon' )
    return f_lon

# def bounds_clolon (pbounds_lon, plon, rad:bool=False, deg:bool=True) :
#     '''
#     Choose closest to lon0 longitude, adding/substacting 360° if needed
#     '''
#     push_stack ( f'bounds_clolon (pbounds_lon, plon, {rad=}, {deg=})' )
#     #if rad and deg :
        
#     if rad :
#         lon_range = 2.0*np.pi
#     if deg :
#         lon_range = 360.
#     b_clolon = pbounds_lon.copy ()

#     b_clolon = xr.where ( b_clolon < plon-lon_range/2., b_clolon+lon_range, b_clolon )
#     b_clolon = xr.where ( b_clolon > plon+lon_range/2., b_clolon-lon_range, b_clolon )

#     pop_stack ( 'bounds_clolon : b_clolon' )
#     return b_clolon

def unify_dims (dd:Union[xr.DataArray,xr.Dataset], x:Union[str,None]=None, y:Union[str,None]=None, z:Union[str,None]=None, t:Union[str,None]=None, 
                xgrid:Union[str,None]=None, use_xgcm:bool=False, Debug:bool=False) -> Union[xr.DataArray,xr.Dataset] :
    '''
    Rename dimensions to unify them between NEMO versions
    If xgrid is set, force to xgcm standard
    '''
    push_stack ( f'unify_dims (dd, {x=}, {y=}, {z=}, {t=})' )

    if dd is not None :
        if xgrid :
            if xgrid.upper () ==  'T' :
                x, y, z = 'x_c', 'y_c', 'z_c'
            if xgrid.upper () ==  'U' :
                x, y, z = 'x_f', 'y_c', 'z_c'
            if xgrid.upper () ==  'V' :
                x, y, z = 'x_c', 'y_f', 'z_c'
            if xgrid.upper () ==  'F' :
                x, y, z = 'x_f', 'y_f', 'z_c'
            if xgrid.upper () ==  'W' :
                x, y, z = 'x_c', 'y_c', 'z_f'

        if use_xgcm :
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
            if OPTIONS['Debug'] or Debug :
                print ( f"unify_dims : working on {x=}" )

            xx, ii = find_axis (dd, 'x')
            if xx and xx != x :
                if OPTIONS['Debug'] or Debug :
                    print ( f"unify_dims : {xx} renamed to {x}" )
                dd = dd.rename ({xx:x})
                dd[x].attrs.update ({'axis':'X', 'name':x})
                if x == 'x_f' :
                    dd.x_f.attrs.update({'c_grid_axis_shift':0.5})
            if xgrid :
                if x == 'x_c' and 'x_c' in dd.dims  :
                    dd['x_c'] = np.arange (len(dd[x])) + 1
                if x == 'x_f' and 'x_f' in dd.dims  :
                    dd['x_f'] = np.arange (len(dd[x])) + 0.5

        if y :
            if OPTIONS['Debug'] or Debug :
                print ( f"unify_dims : working on {y=}" )
            yy, jj = find_axis (dd, 'y')
            if yy and yy != y  :
                if OPTIONS['Debug'] or Debug :
                    print ( f"unify_dims : {yy} renamed to {y}" )
                dd = dd.rename ( {yy:y} )
                dd[y].attrs.update ({'axis':'Y', 'name':y})
                if y == 'y_f' :
                    dd.y_f.attrs.update ({'c_grid_axis_shift':0.5})
            if xgrid :
                if y == 'y_c' and 'y_c' in dd.dims  :
                    dd['y_c'] = np.arange (len(dd[y])) + 1
                if y == 'y_f' and 'y_f' in dd.dims  :
                    dd['y_f'] = np.arange (len(dd[y])) + 0.5

        if z :
            if OPTIONS['Debug'] or Debug :
                print ( f"unify_dims : working on {z=}" )
            zz, kk = find_axis (dd, 'z')
            if zz and zz != z :
                if OPTIONS['Debug'] or Debug :
                    print ( f"unify_dims : {zz} renamed to {z}" )
                dd = dd.rename ({zz:z})
                dd[z].attrs.update ({'axis':'Z', 'name':z})
                if z == 'z_f' :
                    dd.z_f.attrs.update ({'c_grid_axis_shift':0.5})
            if isinstance (dd, xr.core.dataset.Dataset) and z in dd.variables and 'bounds' in dd[z].attrs :
                bound_var =  dd[z].attrs['bounds']
                if bound_var in dd.variables :
                    new_bv = bound_var.replace (zz, z)
                    if new_bv != bound_var : 
                        dd = dd.rename ({bound_var:new_bv})
                        dd[z].attrs['bounds'] = new_bv

        if t :
            if OPTIONS['Debug'] or Debug :
                print ( f"unify_dims : working on {t=}" )
            tt, ll = find_axis (dd, 't')
            if tt and tt != t :
                if OPTIONS['Debug'] or Debug :
                    print ( f"unify_dims : {tt} renamed to {t}" )
                dd = dd.rename ({tt:t})
                dd[t].attrs.update ({'axis':'T', 'name':t})
            if isinstance (dd, xr.core.dataset.Dataset) and t in dd.variables and 'bounds' in dd[t].attrs :
                bound_var =  dd[t].attrs['bounds']
                if bound_var in dd.variables :
                    new_bv = bound_var.replace (tt, t)
                    if new_bv != bound_var : 
                        dd = dd.rename ({bound_var:new_bv})
                        dd[t].attrs['bounds'] = new_bv

        if use_xgcm :
            fg = None
            if OPTIONS['Debug'] or Debug :
                print ( f'{dd.dims=} {("x_c" in list(dd.dims))=} {"y_c" in dd.dims=}')
                print ( f'{dd.coords=}')
            if 'x_c' in dd.dims and 'y_c' in dd.dims :
                fg = 'T'
            if 'x_f' in dd.dims and 'y_c' in dd.dims :
                fg = 'U'
            if 'x_c' in dd.dims and 'y_f' in dd.dims :
                fg = 'V'
            if 'x_f' in dd.dims and 'y_f' in dd.dims :
                fg = 'F'
            if OPTIONS['Debug'] or Debug : 
                print ( f'{fg=}')
            if fg : 
                for xg in '', '_T', '_U', '_V', '_F' :
                    if OPTIONS['Debug'] or Debug : 
                        print ( f'1 {fg=} {xg=}')
                    for cc in ['lat', 'nav_lat', 'lon', 'nav_lon' ] :
                        if OPTIONS['Debug'] or Debug : 
                            print ( f'2 {fg=} {cc=}', f'{cc}{xg}', f'{cc}_{fg}' )
                        if f'{cc}{xg}' in dd.coords and f'{cc}{xg}' != f'{cc}_{fg}' :
                            if OPTIONS['Debug'] or Debug :
                                print ( f'{cc}{xg}', '->', f'{cc}_{fg}' )
                            dd = dd.rename ( {f'{cc}{xg}':f'{cc}_{fg}'})

                            
            # if 'x_f' in dd.dims and 'y_t' in dd.dims :
            #     for xg in '', '_T', '_U', '_V' :
            #         for cc in ['lat', 'nav_lat', 'lon', 'nav_lon' ] :
            #             if f'{cc}{xg}' in dd.coords :
            #                 dd = dd.rename ( {f'{cc}{xg}':f'{cc}_U'})
            # if 'x_t'in dd.dims and 'y_f' in dd.dims :
            #     for xg in '', '_T', '_U', '_V' :
            #         for cc in ['lat', 'nav_lat', 'lon', 'nav_lon' ] :
            #             if f'{cc}{xg}' in dd.coords :
            #                 dd = dd.rename ( {f'{cc}{xg}':f'{cc}_V'})
            # if 'x_f' in dd.dims and 'y_f' in dd.dims :
            #     for xg in '', '_T', '_U', '_V' :
            #         for cc in ['lat', 'nav_lat', 'lon', 'nav_lon' ] :
            #             if f'{cc}{xg}' in dd.coords :
            #                 dd = dd.rename ( {f'{cc}{xg}':f'{cc}_F'})
            
                    
    pop_stack ( 'unify_dims : dd' )
    return dd


def lbcu (ptab:xr.DataArray, x:Union[str,None]=None, y:Union[str,None]=None, z:Union[str,None]=None, t:Union[str,None]=None, use_xgcm:Union[bool,None]=None, cd_type:str='T', psgn:int=1, nemo_4U_bug:bool=False,
          Iperio:Union[bool,None]=None, Jperio:Union[bool,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
          aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False, btype:str='lbc') -> xr.DataArray :
    '''
    Performs both lbc and unify_dims operations
    See theses functions for details
    '''
    push_stack ( f'lbcu (ptab, {type=})' )

    if x or y or z or t or use_xgcm :
        ptab = unify_dims (ptab, x=x, y=y, z=z, t=t, xgrid=cd_type, use_xgcm=use_xgcm, Debug=Debug)
    if btype in [ 'lbc', 'full'] :
        ptab = lbc      (ptab, cd_type=cd_type, psgn=psgn, nemo_4U_bug=nemo_4U_bug, Iperio=Iperio, Jperio=Jperio,
                             NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, nperio=nperio, domain=domain, Debug=Debug)
    if btype == 'plot' :
        ptab = lbc_plot (ptab, cd_type=cd_type, psgn=psgn, nemo_4U_bug=nemo_4U_bug, Iperio=Iperio, Jperio=Jperio,
                         NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, nperio=nperio, domain=domain, Debug=Debug)
    if btype in ['mask', 'msk' ] :
        ptab = lbc_mask (ptab, cd_type=cd_type, psgn=psgn, nemo_4U_bug=nemo_4U_bug, Iperio=Iperio, Jperio=Jperio,
                         NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, nperio=nperio, domain=domain, Debug=Debug)
    if btype == 'add' : 
        ptab = lbc_add  (ptab, cd_type=cd_type, psgn=psgn, nemo_4U_bug=nemo_4U_bug, Iperio=Iperio, Jperio=Jperio,
                         NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, nperio=nperio, domain=domain, Debug=Debug)
    pop_stack ('lbcu : ptab')
    return ptab
    

if SimpleImputer : 
    def fill_empty (ptab, sval:float=np.nan, transpose:bool=False) :
        '''
        Fill empty values

        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, have no
        values
        '''
        push_stack ( f'fill_empty ( ptab, {sval=} {transpose=}' )

        imp = SimpleImputer (missing_values=sval, strategy='mean')
        if transpose :
            imp.fit (ptab.T)
            ztab = imp.transform (ptab.T).T
        else :
            imp.fit (ptab)
            ztab = imp.transform (ptab)

        ztab = xr.DataArray (ztab, dims=ztab.dims, coords=ztab.coords)
        ztab.attrs.update (ptab.attrs)

        pop_stack ( 'fill_empty : ztab' )
        return ztab

    def fill_latlon (plat, plon, sval=0., Debug:bool=False) :
        '''
        Fill longitude/latitude values
        
        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, have no
        lon/lat values
        '''
        push_stack ( f'fill_latlon (plat, plon, {sval=}' )
        from sklearn.impute import SimpleImputer
        zval = -9999.

        zlat = plat.where (plat != sval, zval)
        zlon = plat.where (plon != sval, zval)
        
        je = jeq (plat)
        if OPTIONS['Debug'] or Debug : 
            print ( f'{je=}')

        imp = SimpleImputer (missing_values=zval, strategy='mean')
        if OPTIONS['Debug'] or Debug : 
            print ( 'imp.fit on longitude')
        imp.fit (plon)
        if OPTIONS['Debug'] or Debug : 
            print ( 'imp.transform on longitude')
        zlon = imp.transform (plon)
        if OPTIONS['Debug'] or Debug : 
            print (f'{type(zlon)=} {zlon.shape=} {plon.shape}')
            print ( 'imp.fit on latitude')
        imp.fit (plat.T)
        if OPTIONS['Debug'] or Debug : 
            print ( 'imp.transform on latitude')
        zlat = imp.transform (zlat.T).T
        if OPTIONS['Debug'] or Debug : 
            print (f'{type(zlat)=} {zlat.shape} {plat.shape}')
        
        if OPTIONS['Debug'] or Debug : 
            print ( 'copy attrs on longitude')
        zlon = copy_attrs (zlon, plon)

        if OPTIONS['Debug'] or Debug : 
            print ( 'copy attrs on latitude')
        if je >= 0 :
            zlat[...,je,:] = 0.0
        zlat = copy_attrs (zlat, plat)

        pop_stack ('fill_latlon')
        return zlat, zlon

    def fill_bounds_lonlat (pbounds_lon, pbounds_lat, sval:int=-1) :
        '''
        Fill longitude/latitude bounds values
        
        Useful when NEMO has run with no wet points options :
        some parts of the domain, with no ocean points, as no
        lon/lat values
        '''
        push_stack ( f'fill_bounds_lonlat (pbounds_lon, pbounds_lat, {sval=}' )
        
        z_bounds_lon = np.empty_like (pbounds_lon)
        z_bounds_lat = np.empty_like (pbounds_lat)

        imp = SimpleImputer (missing_values=sval, strategy='mean')
        
        for n in np.arange (4) :
            imp.fit (pbounds_lon[...,n])
            z_bounds_lon[:,:,n] = imp.transform (pbounds_lon[:,:,n])
            imp.fit (pbounds_lat[:,:,n].T)
            z_bounds_lat[:,:,n] = imp.transform (pbounds_lat[:,:,n].T).T
            
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
        pop_stack ( 'fill_empty [void version]' )
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

        pop_stack ( 'fill_latlon [void version]')
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

        pop_stack ( 'fill_lonlat [void version]' )
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

def jeq (plat:xr.DataArray, Debug=False) -> int:
    '''
    Returns j index of equator in the grid

    lat : latitudes of the grid. At least 2D.
    '''
    push_stack ( 'jeq (plat) ' )
    ay, jy = find_axis (plat, 'y')
    if OPTIONS['Debug'] or Debug :
        print ( f'{ay=}, {jy=}, {plat.shape=}' )

    aa = np.argmin (np.abs (plat.values), axis=jy)
    jj = int (np.nanmean (np.where (aa!=0, aa, np.nan)))

    pop_stack ( f'jeq : {jj}' )
    return jj

def lon1d (plon:xr.DataArray, plat:Union[xr.DataArray,None]=None) :
    '''
    Returns 1D longitude for simple plots.

    plon : longitudes of the grid
    plat (optionnal) : latitudes of the grid
    '''
    push_stack ( 'lon1d (plon, plat) ' ) 
   
    jpj, jpi  = plon.shape [-2:]
    if np.max (plat) :
        je     = jeq (plat)
        lon0   = plon [..., je, 0].copy().values.item()
        dlon   = (plon [..., je, 1].copy() - plon [..., je, 0].copy()).values.item()
        lon_1d = np.linspace (start=lon0, stop=lon0+360.+2*dlon, num=jpi)
    else :
        lon0   = plon [..., jpj//3, 0].copy().item()
        dlon   = (plon [..., jpj//3, 1].copy() - plon [..., jpj//3, 0].copy()).values.item()
        lon_1d = np.linspace ( start=lon0, stop=lon0+360.+2*dlon, num=jpi )

    lon_1d = xr.DataArray (lon_1d, dims=('lon',), coords=(lon_1d,))
    lon_1d.attrs.update (plon.attrs)
    lon_1d.attrs.update ({'units': 'degrees_east', 'standard_name':'longitude', 'long_name':'Longitude'})

    pop_stack ( 'lon_1d' )
    return lon_1d

def latreg (plat:xr.DataArray, diff:float=0.1, Debug:bool=False) :
    '''
    Returns maximum j index where gridlines are along latitudes
    in the northern hemisphere

    lat : latitudes of the grid (2D)
    diff [optional] : tolerance
    '''
    push_stack ( f'latreg ( plat, {diff=}' )

    ax, ix = find_axis (plat, 'x')
    ay, iy = find_axis (plat, 'y')
    if OPTIONS['Debug'] or Debug :
        print ( f'Found axis : {ax=} {ix=} {ay=} {iy=}' )

    if diff is None :
        dy = np.mean (np.abs (plat - np.roll (plat,shift=1,axis=iy, roll_coords=False)))
        if OPTIONS['Debug'] or Debug :
            print ( f'latreg : {dy=}' )
        diff = dy/100.

    je = jeq (plat)
    if OPTIONS['Debug'] or Debug :
        print ( f'{je=}')
    if ix and plat.shape[ix] > 1 : 
        #jreg   = np.where (plat[...,je:,:].max(axis=ix) -
        #                   plat[...,je:,:].min(axis=ix)  < diff)[-1][-1] + je
        #lareg  = float (plat[...,jreg,:].mean(axis=ix))
        jreg   = np.count_nonzero  (plat.isel({ay:slice(je,None)}).max(dim=ax) -
                           plat.isel({ay:slice(je,None)}).min(dim=ax)  < diff) + je
        lareg  = plat.isel({ay:jreg}).mean(dim=ax)
    else : 
        jreg  = len (plat)-2
        lareg = np.max (plat)
        
    pop_stack ( f'latreg : {jreg=}, {lareg=}' )
    return jreg, lareg

def lat1d (plat:xr.DataArray, Debug:bool=False) :
    '''
    Returns 1D latitudes for zonal means and simple plots.

    plat : latitudes of the grid (2D)
    '''
    push_stack ( 'lat1d ( plat )' )

    ax, ix = find_axis (plat, 'x')
    ay, iy = find_axis (plat, 'y')
    jpj = plat.shape[iy]

    dy = (plat.max() - plat.min())/plat.shape[iy]
    #if OPTIONS['Debug'] or Debug :
    #    print (f'{dy = }' )
    je     = jeq (plat)

    lat_N = np.minimum (90.0, plat.max()+dy)
    #if OPTIONS['Debug'] or Debug :
    #    print (f'{lat_N=}') 
    
    if ix :
        lat_eq = plat[...,je,:].mean(axis=ix)
    else  :
        lat_eq = plat[...,je]
                                  
    jreg, lat_reg = latreg (plat)
    if ix :
        lat_ave = np.mean (plat, axis=ix)
    else  :
        lat_ave = plat
    
    if np.abs (lat_eq) < dy/100. : # T, U or W grid
        if jpj-1 > jreg :
            dys = (lat_N-lat_reg) / (jpj-jreg-1)*0.5
        else            :
            dys = (lat_N-lat_reg) / 2.0
        yrange = (lat_N-dys-lat_reg).values.item()
    else :
        yrange = (lat_N-lat_reg).values.item() # V or F grid

    #if OPTIONS['Debug'] or Debug :
    #    print (f'{lat_N} {jreg=} {lat_reg=} {dy=} {dys=} {yrange=}')
    newlat = lat_reg + yrange * xr.DataArray ((np.arange(jpj)-jreg)/(jpj-jreg-1), dims=(ay,))
    #if OPTIONS['Debug'] or Debug :
    #    print (f'{newlat=}')
    
    if jpj-1 > jreg :
        lat_1d = xr.where (lat_ave<lat_reg, lat_ave, newlat)
    else :
        lat_1d = lat_ave

    lat_1d[-1] = lat_N

    # Et le sud ?
    # Cherche la décroissance
    js = np.diff(lat_1d).argmin()
    ys = np.maximum (-89, lat_1d[js+1].values.item()-5.)
    if OPTIONS['Debug'] or Debug :
        print (f'{js=} {lat_1d[js]=} {lat_1d[js+1]=} {ys=}')
        print (f'{lat_1d[0:js+3]=}')
    lat_1d [0:js+1] = np.linspace(-89.0, ys, js+1)

    lat_1d = xr.DataArray (lat_1d.values, dims=('lat',), coords=(lat_1d,))
    lat_1d.attrs.update (plat.attrs)
    lat_1d.attrs.update ( {'units':'degrees_north', 'standard_name':'latitude', 'long_name':'Latitude'})

    pop_stack ( 'lat1d' )
    return lat_1d

def latlon1d (plat:xr.DataArray, plon:xr.DataArray) -> xr.DataArray :
    '''
    Returns simple latitude and longitude (1D) for simple plots.

    plat, plon : latitudes and longitudes of the grid (2D)
    '''
    push_stack ( 'latlon1d ( plat, plon) ' )
    zla = lat1d (plat)
    zlo = lon1d (plon, plat)

    pop_stack ( 'latlon1d' )
    return zla, zlo

def ff (plat:xr.DataArray) -> xr.DataArray :
    '''
    Returns Coriolis factor
    '''
    push_stack ( 'ff ( plat )' )
    zff   = np.sin (np.deg2rad(plat)) * ROMEGA
    pop_stack ( 'ff' )
    return zff

def beta (plat:xr.DataArray) -> xr.DataArray :
    '''
    Return Beta factor (derivative of Coriolis factor)
    '''
    push_stack ( 'beta ( plat )' )
    zbeta = np.cos (np.deg2rad(plat)) * ROMEGA / RA
    pop_stack ( 'beta' )
    return zbeta

def mask_lonlat (ptab:xr.DataArray, x0:xr.DataArray, x1:xr.DataArray, y0:xr.DataArray, y1:xr.DataArray,
                 lon:xr.DataArray, lat:xr.DataArray, sval:float=np.nan) -> xr.DataArray :
    '''
    Returns masked values outside a lat/lon box
    '''
    push_stack ( f'mask_lonlat  (ptab, {x0=}, {x1=}, {y0=}, {y1=}, lon, lat, {sval=}' )
   
    zlon = lon.copy().to_masked_array()
    zlat = lat.copy().to_masked_array()

    mask = np.logical_and (np.logical_and(zlat>y0, zlat<y1),
                np.logical_or (np.logical_or (
                np.logical_and (zlon>x0, zlon<x1),
                np.logical_and (zlon+360.>x0, zlon+360.<x1)),
                np.logical_and (zlon-360.>x0, zlon-360.<x1)))
    tab = xr.where (mask, ptab, sval)

    pop_stack ( 'mask_lonlat' )
    return tab

def extend (ptab:xr.DataArray, blon:bool=False, jplus:int=25, jpi:Union[int,None]=None, 
            Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None,
            aperio:Union[int,float,None]=None, domain:Union[Domain,None]=None) -> xr.DataArray :
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
    push_stack ( f'extend ( ptab, {blon=}, {jplus=}, {jpi=}, {aperio=}' )
    zdom   = Domain (ptab=ptab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, domain=domain)
    ix, ax = find_axis (ptab, 'x')
    
    if ptab.shape[-1] == 1 :
        tabex = ptab

    else :
        if not jpi :
            jpi = ptab.shape[-1]

        xplus = -360. if blon else 0.
            
        if ptab.shape[-1] > jpi :
            tabex = ptab
        else :
            if (zdom.Iperio and not zdom.Jperio and not NFold ) or (zdom.Iperio and not zdom.Jperio and NFold and NFtype=='T' and not Halo) :
            #aperio in [ 0, 4.2 ] :
                istart, le, la = 0, jpi+1, 0
            if zdom.Iperio and not zdom.Jperio and not NFold and Halo : # iperio==1
                istart, le, la = 0, jpi+1, 0
            if zdom.Iperio and zdom.NFold : # aperio in [4, 6] : # OPA case with two halo points for periodicity
                # Perfect, except at the pole that should be masked by lbc_plot
                istart, le, la = 1, jpi-2, 1

            tabex = np.concatenate (
                (ptab.values[..., istart   :istart+le+1    ] + xplus,
                 ptab.values[..., istart+la:istart+la+jplus]         ),
                axis=ix)
            lon    = ptab.dims[-1]
            new_coords = []
            for coord in ptab.dims :
                if coord == lon :
                    new_coords.append (np.arange( tabex.shape[-1]))
                else            :
                    new_coords.append ( ptab.coords[coord].values)
                tabex = xr.DataArray ( tabex, dims=ptab.dims,
                                           coords=new_coords )

    pop_stack ( 'extend' )
    return tabex

def orca2reg (dd:xr.DataArray, lat_name:Union[str,None]=None, lon_name:Union[str,None]=None, y_name:Union[str,None]=None, x_name:Union[str,None]=None, Debug:bool=True) -> xr.DataArray :
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
    if not x_name :
        x_name, ix = find_axis (dd, axis='x')
    if not y_name :
        y_name, jy = find_axis (dd, axis='y')

    if not lon_name :
        for xn in LONNAME :
            if xn in dd.variables :
                lon_name = xn
    if not lat_name :
        for yn in LATNAME :
            if yn in dd.variables :
                lat_name = yn

    if OPTIONS['Debug'] or Debug :
        print ( 'orga2reg : ' )
        print ( f'{dd.dims=}'   )
        print ( f'{x_name=} {y_name=}' )
    
    # Compute 1D longitude and latitude
    ylat, xlon   = fill_latlon (dd[lat_name], dd[lon_name], sval=-1)
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
    for dim in ZNAME : 
        if dim in zdd.dims :
            coord_order.insert (0, dim)
    for dim in TNAME : 
        if dim in zdd.dims :
            coord_order.insert (0, dim)
    for dim in BNAME : 
        if dim in zdd.dims :
            coord_order.insert (0, dim)

    zdd = zdd.transpose (*coord_order)

    pop_stack ( 'orca2reg' )
    return zdd

def lbc (ptab:xr.DataArray, cd_type:Union[str,None]=None, psgn=1, nemo_4U_bug:bool=False, 
         Iperio:Union[bool,None]=None, Jperio:Union[bool,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None,
         Halo:Union[bool,None]=None, aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Set periodicity on input field

    ptab      : Input array (works for rank 2 at least : ptab[...., lat, lon])
    aperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F
    psgn      : For change of sign for vector components (1 for scalars, -1 for vector components)

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc ( ptab, {aperio=}, {cd_type=}, {psgn=}, {nemo_4U_bug=}' )
    zdom   = Domain (ptab=ptab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, nperio=nperio, domain=domain)
    jpi    = zdom.jpi
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    psgn   = ptab.dtype.type (psgn)

    if not cd_type  :
        if 'x_c' in ptab.dims and 'y_c' in ptab.dims : cd_type = 'T'
        if 'x_f' in ptab.dims and 'y_c' in ptab.dims : cd_type = 'U'
        if 'x_c' in ptab.dims and 'y_f' in ptab.dims : cd_type = 'V'
        if 'x_f' in ptab.dims and 'y_f' in ptab.dims : cd_type = 'T'

    if OPTIONS['Debug'] or Debug :
        print (f'{jpi=} {zdom.Iperio=} {zdom.Jperio=} {zdom.NFold=} {zdom.NFtype=} {zdom.Halo=} {ax=} {ay=} {ix=} {jy=}')

    ztab  = ptab.copy ()
   
    if ax :
        #
        #> East-West boundary conditions
        # ------------------------------
        if zdom.Iperio and zdom.Halo :
        # ... cyclic
            ztab[{ax: 0}] = ztab[{ax:-2}]
            ztab[{ax:-1}] = ztab[{ax:1}]
        
        if ay :
            #
            #> North-South boundary conditions
            # --------------------------------
            if zdom.NFold and zdom.NFtype == 'T' and zdom.Halo : # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [{ay:-1, ax:slice(1,None)}     ] = psgn * ztab [{ay:-3, ax:slice(-1,0,-1)}    ].data
                    ztab [{ay:-1, ax:0}                 ] = psgn * ztab [{ay:-3, ax:2}        ]
                    ztab [{ay:-2, ax:slice(jpi//2,None)}] = psgn * ztab [{ay:-2, ax:slice(jpi//2,0,-1)}].data
                if cd_type == 'U' :
                    ztab [{ay:-1, ax:slice( 0,-1)}] = psgn * ztab [{ay:-3, ax:slice(-1,0,-1)}].data
                    ztab [{ay:-1, ax:0}           ] = psgn * ztab [{ay:-3, ax:1}   ].data
                    ztab [{ay:-1, ax:-1}          ] = psgn * ztab [{ay:-3, ax:-2}  ].data

                    if nemo_4U_bug :
                        ztab [{ay:-2, ax:slice(jpi//2+1,-1)}] = psgn * ztab [{ay:-2, ax:slice(jpi//2-2,0,-1)}].data
                        ztab [{ay:-2, ax:jpi//2-1}          ] = psgn * ztab [{ay:-2, ax:jpi//2}              ].data
                    else :
                        ztab [{ay:-2, ax:slice(jpi//2-1,-1)}] = psgn * ztab [{ay:-2, ax:slice(jpi//2,0,-1)}].data
                            
                if cd_type == 'V' :
                    ztab [{ay:-2, ax:slice(1,None)}] = psgn * ztab [{ay:-3, ax:slice(jpi-1,0,-1)}].data
                    ztab [{ay:-1, ax:slice(1,None)}] = psgn * ztab [{ay:-4, ax:slice(-1,0,-1)}   ].data
                    ztab [{ay:-1, ax:0}            ] = psgn * ztab [{ay:-4, ax:2}               ]

                if cd_type == 'F' :
                    ztab [{ay:-2, ax:slice(0,-1)}] = psgn * ztab [{ay:-3, ax:slice(-1,0,-1)}].data
                    ztab [{ay:-1, ax:slice(0,-1)}] = psgn * ztab [{ay:-4, ax:slice(-1,0,-1)}].data
                    ztab [{ay:-1, ax: 0}         ] = psgn * ztab [{ay:-4, ax: 1}            ]
                    ztab [{ay:-1, ax:-1}         ] = psgn * ztab [{ay:-4, ax:-2}            ]

            if zdom.NFold and zdom.NFtype == 'T' and not zdom.Halo :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [{ay:-1, ax:slice(jpi//2,None)} ] = psgn * ztab [{ay:-1, ax:slice(jpi//2,0,-1)}].data
                if cd_type == 'U' :
                    ztab [{ay:-1, ax:slice(jpi//2-1,-1)}] = psgn * ztab [{ay:-1, ax:slice(jpi//2,0,-1)}].data
                if cd_type == 'V' :
                    ztab [{ay:-1, ax:slice(1,None)}] = psgn * ztab [{ay:-2, ax:slice(jpi-1,0,-1)} ].data

                if cd_type == 'F' :
                    ztab [{ay:-1, ay:slice(0,-1)}     ] = psgn * ztab [{ay:-2, ax:slice(-1,0,-1)} ]

            if zdom.NFold and zdom.NFtype == 'F' and zdom.Halo  : #  North fold F-point pivot
                if cd_type in ['T', 'W']  :
                    ztab [{ay:-1, ax:slice(0,None)}] = psgn * ztab [{ay:-2, ax:slice(-1,None,-1)}].data

                if cd_type == 'U' :
                    ztab [{ay:-1, ax:slice(0,-1)}] = psgn * ztab [{ay:-2, ax:slice(-2,None,-1)}].data
                    ztab [{ay:-1, ax:-1}         ] = psgn * ztab [{ay:-2, ax:0}                ]

                if cd_type == 'V' :
                    ztab [{ay:-1, ax:slice(0,None)}     ] = psgn * ztab [{ay:-3, ax:slice(-1,None,-1)}       ].data
                    ztab [{ay:-2, ax:slice(jpi//2,None)}] = psgn * ztab [{ay:-2, ax:slice(jpi//2-1,None,-1)} ].data

                if cd_type == 'F' :
                    ztab [{ay:-1, ax:slice(0,-1)}     ] = psgn * ztab [{ay:-3, ax:slice(-2,None,-1)}].data
                    ztab [{ay:-1, ax:-1}              ] = psgn * ztab [{ay:-3, ax:0}                ]
                    ztab [{ay:-2, ax:slice(jpi//2,-1)}] = psgn * ztab [{ay:-2, ax:slice(jpi//2-2,None,-1)} ].data

            if zdom.NFold and zdom.NFtype == 'F' and not zdom.Halo  : #  North fold F-point pivot
                if cd_type == 'V' :
                    ztab [{ay:-1, ax:slice(jpi//2,None)}] = psgn * ztab [{ay:-1, ax:slice(jpi//2-1,None,-1)} ].data

                if cd_type == 'F' :
                    ztab [{ay:-1, ax:slice(jpi//2,-1)}] = psgn * ztab [{ay:-1, ax:slice(jpi//2-2,None,-1)} ].data

            #
            #> East-West boundary conditions
            # ------------------------------
            if zdom.Iperio and zdom.Halo :
                # ... cyclic
                ztab[{ax: 0}] = ztab[{ax:-2}]
                ztab[{ax:-1}] = ztab[{ax: 1}]
       
    pop_stack ( 'lbc' )
    return ztab

def lbc_mask (ptab:xr.DataArray, cd_type:str='T', sval:float=np.nan,
              Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:str=None,
              Halo:bool=False, aperio:Union[int,float,None]=None, nperio:int=None, domain:Domain=None, Debug:bool=False) :
    '''
    Mask fields on duplicated points

    ptab      : Input array. Rank 2 at least : ptab [...., lat, lon]
    aperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_mask (ptab, {cd_type=}, {sval=}' )
    zdom   = Domain (ptab=ptab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype,
                     Halo=Halo, aperio=aperio, nperio=nperio, domain=domain)
    jpi    = zdom.jpi
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    ztab   = ptab.copy ()

    if not cd_type :
        if 'x_c' in ptab.dims and 'y_c' in ptab.dims : cd_type = 'T'
        if 'x_f' in ptab.dims and 'y_c' in ptab.dims : cd_type = 'U'
        if 'x_c' in ptab.dims and 'y_f' in ptab.dims : cd_type = 'V'
        if 'x_f' in ptab.dims and 'y_f' in ptab.dims : cd_type = 'T'
    
    if ax :
        #
        #> East-West boundary conditions
        # ------------------------------
        if zdom.Iperio and zdom.Halo :
            # ... cyclic
            ztab[{ax: 0}] = sval
            ztab[{ax:-1}] = sval

        if ay :
            #
            #> South (in which aperio cases ?)
            # --------------------------------
            if zdom.Halo and not zdom.Jperio :
                ztab [{ay:0}]    = sval
            #
            #> North-South boundary conditions
            # --------------------------------
            if zdom.NFold and zdom.NFtype=='T' and zdom.Halo :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [{ay:-1}                       ] = sval
                    ztab [{ay:-2, ax:slice(jpi//2,None)}] = sval

                if cd_type == 'U' :
                    ztab [{ay:-1}                         ] = sval
                    ztab [{ay:-2, ax:slice(jpi//2+1,None)}] = sval

                if cd_type == 'V' :
                    ztab [{ay:-2}       ] = sval
                    ztab [{ay:-1}       ] = sval

                if cd_type == 'F' :
                    ztab [{ay:-2}       ] = sval
                    ztab [{ay:-1}       ] = sval

            if zdom.NFold and zdom.NFtype=='T' and not zdom.Halo :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [{ay:-1, ax:slice(jpi//2,None)} ] = sval
                if cd_type == 'U' :
                    ztab [{ax:-1, ax:slice(jpi//2-1,-1)}] = sval
                if cd_type == 'V' :
                    ztab [{ay:-1, ax:slice(1,None)} ] = sval
                if cd_type == 'F' :
                    ztab [{ay:-1, ax:slice(0,-1)}] = sval

            if zdom.NFold and zdom.NFtype=='F' and zdom.Halo  :            #  North fold F-point pivot
                if cd_type in ['T', 'W']  :
                    ztab [{ay:-1}       ] = sval

                if cd_type == 'U' :
                    ztab [{ay:-1, ax:slice(0,-1)}] = sval
                    ztab [{ay:-1, ay:-1}         ] = sval

                if cd_type == 'V' :
                    ztab [{ay:-1}                        ] = sval
                    ztab [{ay:-2, ax:slice(jpi//2,None)} ] = sval

                if cd_type == 'F' :
                    ztab [{ay:-1, ax:slice(0,None)}     ] = sval
                    ztab [{ay:-2, ax:slice(jpi//2+1,-1)}] = sval

            if zdom.NFold and zdom.NFtype=='F' and not zdom.Halo  :            #  North fold F-point pivot
                if cd_type == 'V' :
                    ztab [{ay:-1, ax:slice(jpi//2,None)} ] = sval

                if cd_type == 'F' :
                    ztab [{ay:-1, ax:slice(jpi//2+1,-1)}] = sval

    pop_stack ( 'lbc_mask' )
    return ztab

def lbc_plot (ptab:xr.DataArray, cd_type:str='T', psgn:float=1.0, sval:float=np.nan,
              Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:str=None, aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, 
              Halo:bool=None, domain:Union[Domain,None]=None, Debug:bool=False) :
    '''
    Set periodicity on input field, for plotting for any cartopy projection

      Points at the north fold are masked
      Points for zonal periodicity are kept
    ptab      : Input array. Rank 2 at least : ptab[...., lat, lon]
    aperio    : Type of periodicity
    cd_type   : Grid specification : T, U, V or F
    psgn      : For change of sign for vector components
           (1 for scalars, -1 for vector components)

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_plot (ptab, {aperio=}, {cd_type=}, {psgn=}, {sval=}' )
    zdom   = Domain (ptab=ptab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, nperio=nperio, domain=domain)
    jpi    = zdom.jpi
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    psgn   = ptab.dtype.type (psgn)
    ztab   = ptab.copy ()

    if ax :
        #
        #> East-West boundary conditions
        # ------------------------------
        if zdom.Iperio and zdom.Halo :
            # ... cyclic
            ztab [{ax: 0}] = ztab [{ax:-2}]
            ztab [{ax:-1}] = ztab [{ax: 1}]

        if ay :
            #> Masks south
            # ------------
            if not zdom.Jperio :
                ztab [{ay:0}] = sval

            #
            #> North-South boundary conditions
            # --------------------------------
            if zdom.NFold and zdom.NFtype=='T' and zdom.Halo :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [{ay:-1}                     ] = sval
                    ztab [{ay:-2, ax:slice(0,jpi//2)} ] = sval
                if cd_type == 'U' :
                    ztab [{ay:-1}] = sval

                if cd_type == 'V' :
                    ztab [{ay:-2}] = sval
                    ztab [{ay:-1}] = sval

                if cd_type == 'F' :
                    ztab [{ay:-2} ] = sval
                    ztab [{ay:-1} ] = sval

            if zdom.NFold and zdom.NFtype=='T' and not zdom.Halo :  # North fold T-point pivot
                if cd_type in [ 'T', 'W' ] : # T-, W-point
                    ztab [{ay:-1, ax:slice(jpi//2,None)}  ] = sval
                if cd_type == 'U' :
                    ztab [{ay:-1, ax:slice(jpi//2-1,-1)}] = sval
                if cd_type == 'V' :
                    ztab [{ay:-1, ax:slice(1,None)} ] = sval
                if cd_type == 'F' :
                    ztab [{ay:-1, ax:slice(0,-1)} ] = sval

            if zdom.NFold and zdom.NFtype=='F' and zdom.Halo :            #  North fold F-point pivot
                if cd_type in ['T', 'W']  :
                    ztab [{ay:-1}] = sval

                if cd_type == 'U' :
                    ztab [{ay:-1}] = sval

                if cd_type == 'V' :
                    ztab [{ay:-1}                        ] = sval
                    ztab [{ay:-2, ax:slice(jpi//2,None)} ] = sval

                if cd_type == 'F' :
                    ztab [{ay:-1}                       ] = sval
                    ztab [{ay:-2, ax:slice(jpi//2+1,-1)}] = sval

            if zdom.NFold and zdom.NFtype=='F' and not zdom.Halo :            #  North fold F-point pivot
                if cd_type == 'V' :
                    ztab [{ay:-1, ax:slice(jpi//2,None)} ] = sval

                if cd_type == 'F' :
                    ztab [{ay:-1, ax:slice(jpi//2+1,-1)}] = sval      

    pop_stack ( 'lbc_plot' )
    return ztab

def lbc_add (ptab:xr.DataArray, cd_type:str=None, psgn=1, Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:str=None, 
             Halo:Union[bool,None]=None, aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) :
    '''
    Handles NEMO domain changes between NEMO 4.0 to NEMO 4.2

    Periodicity and north fold halos has been removed in NEMO 4.2
    This routine adds the halos if needed

    ptab      : Input array (works
      rank 2 at least : ptab[...., lat, lon]
    aperio    : Type of periodicity

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_add ( ptab, {aperio=}, {cd_type=}, {psgn=} )' )
    zdom   = Domain (ptab=ptab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo,
                     aperio=aperio, nperio=nperio, domain=domain)
    jpi    = zdom.jpi
    jpj    = zdom.jpj
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    psgn   = ptab.dtype.type (psgn)
    ptab_ext = ptab

    t_shape = np.array (ptab.shape)
    tjpi = jpi ; tjpj=jpj

    if zdom.Iperio and zdom.NFold and not zdom.Halo :
        ext_shape = t_shape.copy()
        if ax :
            tjpi = tjpi+2
            ext_shape[ix] = ext_shape[ix] + 2
        if ay :
            tjpj = tjpj+1
            ext_shape[jy] = ext_shape[jy] + 1
        if OPTIONS['Debug'] or Debug :
            print ( f'lbc_add: ext_shape = {ext_shape}' )

        ptab_ext = xr.DataArray (np.zeros (ext_shape), dims=ptab.dims)
        if ax and ay :
            ptab_ext.values[..., :-1, 1:-1] = ptab.values.copy ()
        else :
            if ax :
                ptab_ext.values[...,      1:-1] = ptab.values.copy ()
            if ay :
                ptab_ext.values[..., :-1      ] = ptab.values.copy ()

        tdom = Domain (jpi=tjpi, jpj=tjpj, domain=domain, Halo=True)

        ptab_ext = lbc (ptab_ext, cd_type=cd_type, psgn=psgn, domain=tdom)
        
        ptab_ext.attrs = ptab.attrs
        az = find_axis (ptab, 'z')[0]
        at = find_axis (ptab, 't')[0]
        if az :
            ptab_ext = ptab_ext.assign_coords ( {az:ptab.coords[az]} )
        if at :
            ptab_ext = ptab_ext.assign_coords ( {at:ptab.coords[at]} )

    ptab_ext = copy_attrs (ptab_ext, ptab)
    
    pop_stack ( 'lbc_add' )
    return ptab_ext

def lbc_del (ptab:xr.DataArray, cd_type:str='T', psgn:Union[int,float]=1, Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, 
             NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, 
             Halo:Union[bool,None]=None, aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None) :
    '''
    Handles NEMO domain changes between NEMO 4.0 to NEMO 4.2

    Periodicity and north fold halos has been removed in NEMO 4.2
    This routine removes the halos if needed

    ptab      : Input array (works
      rank 2 at least : ptab[...., lat, lon]
    aperio    : Type of periodicity

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_del (ptab, {aperio=}, {cd_type=}, {psgn=}' )
    zdom   = Domain (ptab=ptab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    jpi    = zdom.jpi
    jpj    = zdom.jpj
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    psgn   = ptab.dtype.type (psgn)
    ztab   = ptab

    if zdom.NFold and zdom.NFtype=='T' and not zdom.Halo :
        if ax :
            tjpi = tjpi-2
        if ay :
            tjpj = tjpj-1

        tdom = Domain (jpi=tjpi, jpj=tjpj, domain=domain, Halo=False)
        
        if ax and ay :
            ztab = lbc (ptab.isel ({ax:slice(1,-1), ay:slice(None,-1)}), cd_type=cd_type, psgn=psgn, domain=tdom)
        else :
            if ax    :
                ztab = lbc (ptab.isel ({ax:slice(1,-1)}   ), cd_type=cd_type, psgn=psgn, domain=tdom)
            if ay    :
                ztab = lbc (ptab.isel ({ay:slice(None,-1)}), cd_type=cd_type, psgn=psgn, domain=tdom)

    pop_stack ( 'lbc_del' )
    return ztab

def lbc_index (jj:int, ii:int, jpj:int, jpi:int, cd_type:str='T', Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:str=None, Halo:bool=None,
                aperio:int=None, nperio:int=None, domain:Domain=None) :
    '''
    For indexes of a NEMO point, give the corresponding point
        inside the domain (i.e. not in the halo)

    jj, ii    : indexes
    jpi, jpi  : size of domain
    aperio    : type of periodicity
    cd_type   : grid specification : T, U, V or F

    See NEMO documentation for further details
    '''
    push_stack ( f'lbc_index ( {jj=}, {ii=}, {jpj=}, {jpi=}, {aperio=}, {cd_type=} )' )
    zdom   = Domain (jpi=jpi, jpj=jpj, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    jpj, jpi = zdom.jpj, zdom.jpi

    ## For the sake of simplicity, switch to the convention of original
    ## lbc Fortran routine from NEMO : starts indexes at 1
    jy, ix = jj+1, ii+1


    #
    #> East-West boundary conditions
    # ------------------------------
    if zdom.Iperio and zdom.Halo : 
        #... cyclic
        ix = xr.where (ix==jpi, 2   , ix)
        ix = xr.where (ix== 1 ,jpi-1, ix)

    #
    def mod_ij (cond, jy_new, ix_new) :
        push_stack ( 'mod_ij (cond, jy_new, ix_new)' )
        jy_r = xr.where (cond, jy_new, jy)
        ix_r = xr.where (cond, ix_new, ix)
        pop_stack ( 'mod_ij' )
        return jy_r, ix_r
    #
    #> North-South boundary conditions
    # --------------------------------
    if zdom.NFold and zdom.NFtype=='T' and zdom.Halo :
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

    if zdom.NFold and zdom.NFtype=='F' and zdom.Halo : #f aperio in [ 5 , 6 ] :
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
    jy += -1
    ix += -1

    ## For simple case, return the value rather than a list with one element
    if isinstance (jj, int) :
        jy = jy.item ()
    if isinstance (ii, int) :
        ix = ix.item ()

    pop_stack ( f'lbc_index = {jy}, {ix}' )
    return jy, ix

def find_ji (lat_data:xr.DataArray, lon_data:xr.DataArray, lat_grid:xr.DataArray, lon_grid:xr.DataArray, mask:Union[xr.DataArray,float]=1.0,
             drop_duplicates:bool=False, out:Union[str,None]=None, ay:Union[str,None]=None, ax:Union[str,None]=None, Debug:bool=True) :
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
    if len (lon_grid.shape) == 2 :
        jpi = lon_grid.shape[-1]
    else                         :
        jpi = len(lon_grid)

    if not ay :
        ay, iy = find_axis (lon_grid, 'y')
    if not ax :
        ax, ix = find_axis (lon_grid, 'x')
    
    if OPTIONS['Debug'] or Debug :
        print ( 'find_ji' )
        print ( f'{lat_data=}' )
        print ( f'{lon_data=}' )
        print ( f'{ay=} {iy=}' )
        print ( f'{ax=} {ix=}' )

    # Compute distance from the point to all grid points (in RADian)
    arg      = ( np.sin (np.deg2rad(lat_data)) * np.sin (np.deg2rad(lat_grid))
               + np.cos (np.deg2rad(lat_data)) * np.cos (np.deg2rad(lat_grid)) *
                 np.cos (np.deg2rad((lon_data-lon_grid))) )

    if OPTIONS['Debug'] or Debug :
        print ( f'{type(arg)=} {arg.shape=}' )
    
    # Send masked points to 'infinite'
    distance = np.arccos (arg) + 4.0*np.pi*(1.0-mask)

    if OPTIONS['Debug'] or Debug :
        print ( f'{type(distance)=} {distance.shape=}' )

    # Truncates to alleviate precision problem encountered with some grids
    prec = int (1E7)
    distance = (distance*prec).astype(int) / prec
    if OPTIONS['Debug'] or Debug:
        print ( f'{type(distance)=} {distance.shape=}' )
        
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
        if OPTIONS['Debug'] or Debug :
            print ( f'{type(jimin)=} {jimin.shape}' )
            print ( f'{jimin=}' )

    # Compute 2D indices (Python/C flavor : starting at 0)
    jmin = jimin // jpi
    imin = jimin - jmin*jpi

    if OPTIONS['Debug'] or Debug :
        print ( f'{jmin=}' )
        print ( f'{imin=}' )
        
    if drop_duplicates :
        zz   = np.vstack ( (np.array (jmin), np.array (imin)) )
        zz   = np.swapaxes (zz , 0, 1)
        zz   = np.unique ( zz, axis=0)
        jmin = zz[:,-2]
        imin = zz[:,-1]

    pop_stack ( 'find_ji' )
    if   out == 'dict'                   :
        zdict = {ay:jmin, ax:imin}
        return zdict
    elif out in ['array', 'numpy', 'np'] :
        return np.array (jmin), np.array (imin)
    elif out in ['xarray', 'xr']         :
        jmin = xr.DataArray (jmin, dims=('Num',), name='j_index', attrs={'long_name':'j-index'})
        imin = xr.DataArray (imin, dims=('Num',), name='i_index', attrs={'long_name':'i-index'})
        return jmin, imin
    elif out=='list'                     :
        return [jmin, imin]
    elif out=='tuple'                    :
        return jmin, imin
    else                                 :
        return jmin, imin

def curl (tx:xr.DataArray, ty:xr.DataArray, e1u:xr.DataArray, e2v:xr.DataArray, e1f:xr.DataArray, e2f:xr.DataArray,
          Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
          aperio:Union[int,float]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Returns curl of a horizontal vector field defined on the C-grid
    '''
    push_stack ( f'curl ( tx, ty, e1u, e2v, e1f, e2f, {aperio=} )' )
    zdom   = Domain (ptab=tx, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    ax = find_axis (tx, 'x')[0]
    ay = find_axis (ty, 'y')[0]

    tx_0    = lbc_add (tx*e1u , cd_type='U', psgn=-1, domain=zdom)
    ty_0    = lbc_add (ty*e2v , cd_type='V', psgn=-1, domain=zdom)
    e1e2f_0 = lbc_add (e1f*e2f, cd_type='F', psgn= 1, domain=zdom)

    tx_1  = tx_0.roll ({ay:-1})
    ty_1  = ty_0.roll ({ax:-1})
    tx_1  = lbc (tx_1, domain=zdom, cd_type='U', psgn=-1)
    ty_1  = lbc (ty_1, domain=zdom, cd_type='V', psgn=-1)

    zcurl = ((ty_1 - ty_0) - (tx_1 - tx_0))/e1e2f_0

    mask = np.logical_or (
             np.logical_or (np.isnan(tx_0), np.isnan(tx_1)),
             np.logical_or (np.isnan(ty_0), np.isnan(ty_1)) )

    zcurl = zcurl.where (np.logical_not (mask), np.nan)

    zcurl = lbc_del (zcurl, domain=zdom, cd_type='F', psgn=1)
    zcurl = lbc     (zcurl, domain=zdom, cd_type='F', psgn=1)

    pop_stack ( 'curl' )
    return zcurl

def div (ux, uy, e1t, e2t, e1v, e2u, Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:str=None, Halo:bool=None, 
         aperio:int=None, nperio:int=None, domain:Domain=None, Debug:bool=False) :
    '''
    Returns divergence of a horizontal vector field defined on the C-grid
    '''
    push_stack ( f'div  (ux, uy, e1t, e2t, e1v, e2u, {aperio=}' )
    zdom   = Domain (ptab=ux, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    axt, ixt = find_axis (e1t, 'x')
    ayt, jyt = find_axis (e1t, 'y')
    axu, ixu = find_axis (ux , 'x')
    ayu, jyu = find_axis (ux , 'y')
    axv, ixv = find_axis (uy , 'x')
    ayv, jyv = find_axis (uy , 'y')

    if OPTIONS['Debug'] or Debug :
        print ( f'{axt=} {ayt} {axu=} {ayu=} {axv=} {ayv=}')

    ux_0    = lbc_add (ux*e2u , domain=zdom, cd_type='U', psgn=-1)
    uy_0    = lbc_add (uy*e1v , domain=zdom, cd_type='V', psgn=-1)
    e1e2t_0 = lbc_add (e1t*e2t, domain=zdom, cd_type='T', psgn= 1)

    if OPTIONS['Debug'] or Debug :
        print (f'{ux_0.dims=} {uy_0.dims=} {e1e2t_0.dims=}')

    ux_1 = ux_0.roll ({ayu:1})
    uy_1 = uy_0.roll ({axv:1})
    ux_1 = lbc (ux_1, domain=zdom, cd_type='U', psgn=-1)
    uy_1 = lbc (uy_1, domain=zdom, cd_type='V', psgn=-1)

    if OPTIONS['Debug'] or Debug :
        print (f'{ux_1.dims=} {uy_1.dims=} {e1e2t_0.dims=}')
    
    zdivu = ux_0 - ux_1
    zdivv = uy_0 - uy_1
    if OPTIONS['Debug'] or Debug :
        print (f'{zdivu.dims=} {zdivv.dims=}')
    zdivu = zdivu.assign_coords ( {axu:axt} )
    zdivv = zdivv.assign_coords ( {ayv:ayt} )

    if OPTIONS['Debug'] or Debug :
        print (f'{zdivu.dims=} {zdivv.dims=}')
    
    zdiv = (zdivu + zdivv)/e1e2t_0
    
    if OPTIONS['Debug'] or Debug :
        print (f'{zdiv.dims=}')

    mask = np.logical_or (
             np.logical_or ( np.isnan(ux_0), np.isnan(ux_1)),
             np.logical_or ( np.isnan(uy_0), np.isnan(uy_1)) )

    zdiv = zdiv.where (np.logical_not (mask), np.nan)

    zdiv = lbc_del (zdiv, aperio=aperio, domain=domain, cd_type='T', psgn=1)
    zdiv = lbc     (zdiv, aperio=aperio, domain=domain, cd_type='T', psgn=1)

    pop_stack ( 'zdiv' )
    return zdiv

def geo2en (pxx:xr.DataArray, pyy:xr.DataArray, pzz:xr.DataArray, glam:xr.DataArray, gphi:xr.DataArray) -> xr.DataArray :
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

def en2geo (pte:xr.DataArray, ptn:xr.DataArray, glam:xr.DataArray, gphi:xr.DataArray) -> xr.DataArray :
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

def clo_lon (lon:xr.DataArray, lon0:Union[float,xr.DataArray]=0., rad:bool=False, deg:bool=True) -> xr.DataArray :
    '''
    Choose closest to lon0 longitude, adding/substacting 360.
    if needed
    '''
    push_stack ( f'clo_lon (lon, {lon0=}, {rad=}, {deg=} )' )
    if rad and deg :
        raise 
    if rad :
        lon_range = 2.*np.pi
    if deg :
        lon_range = 360.
    c_lon = lon
    c_lon = xr.where (c_lon > lon0 + lon_range*0.5, c_lon-lon_range, c_lon)
    c_lon = xr.where (c_lon < lon0 - lon_range*0.5, c_lon+lon_range, c_lon)
    c_lon = xr.where (c_lon > lon0 + lon_range*0.5, c_lon-lon_range, c_lon)
    c_lon = xr.where (c_lon < lon0 - lon_range*0.5, c_lon+lon_range, c_lon)
    if c_lon.shape == () :
        c_lon = c_lon.item ()
    if lon.attrs :
        c_lon.attrs.update (lon.attrs)

    pop_stack ( 'clo_lon' )
    return c_lon

def index2depth (pk:xr.DataArray, gdept_0:float) -> np.ndarray :
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

def depth2index (pz:xr.DataArray, gdept_0:float) -> np.ndarray :
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

def index2depth_panels (pk:xr.DataArray, gdept_0:float, depth0:float, fact:float) -> np.ndarray :
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

def depth2index_panels (pz:xr.DataArray, gdept_0:float, depth0:float, fact:float) -> np.ndarray :
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

def depth2comp (pz:xr.DataArray, depth0:float, fact:float, Debug=False) -> np.ndarray :
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
    if OPTIONS['Debug'] or Debug :
        print ( f'depth2comp : {gz=}' )
    if type (pz) in [int, float] :
        return gz.item()
    else                         :
        return gz

def comp2depth (pz:xr.DataArray, depth0:float, fact:float ) -> np.ndarray :
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

def index2lon (pi:xr.DataArray, plon_1d:xr.DataArray) -> np.ndarray :
    '''
    From index (real, continuous), get longitude

    Needed to use transforms in Matplotlib
    '''
    # No stack here, to avoid problem in Matplotlib
    
    jpi = plon_1d.shape[0]
    ii  = xr.DataArray (pi)
    i   = np.maximum (0, np.minimum (jpi-1, ii    ))
    i0  = np.floor (i).astype (int)
    i1  = np.maximum (0, np.minimum (jpi-1,  i0+1))
    xx  = i - i0
    gx  = (1.0-xx)*plon_1d[i0]+ xx*plon_1d[i1]
    return gx.values

def lon2index (px:xr.DataArray, plon_1d:xr.DataArray) -> np.ndarray :
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
    xx   = xr.where ( xx>plon_1d.max(), xx-360., xx)
    xx   = xr.where ( xx<plon_1d.min(), xx+360., xx)
    xx   = np.minimum (plon_1d.max(), np.maximum(xx, plon_1d.min() ))
    idi1 = np.minimum ( (plon_1d-xx), 0.).argmax (axis=0).astype(int)
    idi1 = np.maximum (0, np.minimum (jpi-1,  idi1  ))
    idi2 = np.maximum (0, np.minimum (jpi-1,  idi1-1))

    zff = (xx - plon_1d[idi2])/(plon_1d[idi1]-plon_1d[idi2])
    idi = zff*idi1 + (1.0-zff)*idi2
    idi = xr.where ( np.isnan(idi), idi1, idi)
    return idi.values

def index2lat (pj:xr.DataArray, plat_1d:xr.DataArray) -> np.ndarray :
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

def lat2index (py:xr.DataArray, plat_1d:xr.DataArray) -> np.ndarray[int] :
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

def angle_full (glamt:xr.DataArray, gphit:xr.DataArray, glamu:xr.DataArray, gphiu:xr.DataArray,
                glamv:xr.DataArray, gphiv:xr.DataArray, glamf:xr.DataArray, gphif:xr.DataArray,
                Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None,
                aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False
) -> tuple [xr.DataArray, xr.DataArray, xr.DataArray, xr.DataArray, xr.DataArray, xr.DataArray, xr.DataArray, xr.DataArray] :
    '''
    Computes sinus and cosinus of model line direction with
    respect to east
    '''
    push_stack ( f'angle_full ( glamt, gphit, glamu, gphiu, glamv, gphiv, glamf, gphif, {aperio=} )')
    zdom   = Domain (ptab=glamt, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    ax, ix = find_axis (glamt, 'x')
    ay, iy = find_axis (glamt, 'y')

    zlamt = lbc_add (glamt, domain=zdom, cd_type='T', psgn=1.)
    zphit = lbc_add (gphit, domain=zdom, cd_type='T', psgn=1.)
    zlamu = lbc_add (glamu, domain=zdom, cd_type='U', psgn=1.)
    zphiu = lbc_add (gphiu, domain=zdom, cd_type='U', psgn=1.)
    zlamv = lbc_add (glamv, domain=zdom, cd_type='V', psgn=1.)
    zphiv = lbc_add (gphiv, domain=zdom, cd_type='V', psgn=1.)
    zlamf = lbc_add (glamf, domain=zdom, cd_type='F', psgn=1.)
    zphif = lbc_add (gphif, domain=zdom, cd_type='F', psgn=1.)

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
    zlan = np.roll (zlamv, axis=iy, shift=1)  # glamv (ji,jj-1)
    zphh = np.roll (zphiv, axis=iy, shift=1)  # gphiv (ji,jj-1)
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

    gsint = lbc_del (gsint, cd_type='T', psgn=-1., domain=zdom)
    gcost = lbc_del (gcost, cd_type='T', psgn=-1., domain=zdom)
    gsinu = lbc_del (gsinu, cd_type='U', psgn=-1., domain=zdom)
    gcosu = lbc_del (gcosu, cd_type='U', psgn=-1., domain=zdom)
    gsinv = lbc_del (gsinv, cd_type='V', psgn=-1., domain=zdom)
    gcosv = lbc_del (gcosv, cd_type='V', psgn=-1., domain=zdom)
    gsinf = lbc_del (gsinf, cd_type='F', psgn=-1., domain=zdom)
    gcosf = lbc_del (gcosf, cd_type='F', psgn=-1., domain=zdom)

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

def angle (glam:xr.DataArray, gphi:xr.DataArray, cd_type:str='T',
           Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:str=None, Halo:bool=None, 
           aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:Union[bool,None]=False) -> tuple[xr.DataArray, xr.DataArray] :
    '''
    Computes sinus and cosinus of model line direction with
    respect to east
    '''
    push_stack ( f'angle (glam, gphi, {aperio=}, {cd_type=} ) ')
    zdom   = Domain (ptab=glam, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    ax, ix = find_axis (glam, 'x')
    ay, iy = find_axis (glam, 'y')
    
    zlam = lbc_add (glam, domain=zdom, cd_type=cd_type, psgn=1.)
    zphi = lbc_add (gphi, domain=zdom, cd_type=cd_type, psgn=1.)

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

    gsin = lbc_del (gsin, cd_type=cd_type, domain=zdom, psgn=-1.)
    gcos = lbc_del (gcos, cd_type=cd_type, domain=zdom, psgn=-1.)

    gsin = gsin.assign_coords ( glam.coords )
    gcos = gcos.assign_coords ( glam.coords )

    pop_stack ( 'angle' )
    return gsin, gcos

def rot_en2ij ( u_e:xr.DataArray, v_n:xr.DataArray, gsin:xr.DataArray, gcos:xr.DataArray,
                cd_type:str='T', Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
                aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False)  -> (xr.DataArray, xr.DataArray) :
    '''
    Rotates the Repere: Change vector componantes between
    geographic grid --> stretched coordinates grid.

    All components are on the same grid (T, U, V or F)
    '''
    push_stack ( f'rot_en2ij ( u_e, v_n, gsin, gcos, aperio, {cd_type=} )' )
    zdom   = Domain (ptab=u_e, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    u_i = + u_e * gcos + v_n * gsin
    v_j = - u_e * gsin + v_n * gcos

    u_i = lbc (u_i, domain=zdom, cd_type=cd_type, psgn=-1.0)
    v_j = lbc (v_j, domain=zdom, cd_type=cd_type, psgn=-1.0)

    pop_stack ( 'rot_en2ij' )
    return u_i, v_j

def rot_ij2en ( u_i:xr.DataArray, v_j:xr.DataArray, gsin:xr.DataArray, gcos:xr.DataArray, 
               cd_type:str='T', Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:bool=None, NFtype:str=None, Halo:bool=None,
               aperio:int=None,  domain:Domain=None, Debug:bool=False) -> (xr.DataArray, xr.DataArray) :
    '''
    Rotates the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid

    All components are on the same grid (T, U, V or F)
    '''
    push_stack ( f'rot_ij2en ( u_i, v_j, gsin, gcos, {aperio=}, {cd_type=} )' )
    zdom   = Domain (ptab=u_i, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, aperio=aperio, domain=domain)
    
    u_e = + u_i * gcos - v_j * gsin
    v_n = + u_i * gsin + v_j * gcos

    u_e = lbc (u_e, domain=zdom, cd_type=cd_type, psgn=1.0)
    v_n = lbc (v_n, domain=zdom, cd_type=cd_type, psgn=1.0)

    pop_stack ( 'rot_ij2en' )
    return u_e, v_n

def rot_uv2en (uo:xr.DataArray, vo:xr.DataArray, gsint:xr.DataArray, gcost:xr.DataArray,
                Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None,
                aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> tuple[xr.DataArray, xr.DataArray] :
    '''
    Rotate the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid

    uo : velocity along i at the U grid point
    vo : valocity along j at the V grid point
    
    Returns east-north components on the T grid point
    '''
    push_stack ( f'rot_uv2en ( uo, vo, gsint, gcost, {aperio=})' )
    zdom   = Domain (ptab=uo, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    ut = u2t (uo, domain=zdom, psgn=-1.0)
    vt = v2t (vo, domain=zdom, psgn=-1.0)

    u_e = + ut * gcost - vt * gsint
    v_n = + ut * gsint + vt * gcost

    u_e = lbc (u_e, domain=zdom, cd_type='T', psgn=1.0)
    v_n = lbc (v_n, domain=zdom, cd_type='T', psgn=1.0)

    pop_stack ( 'rot_uv2en' )
    return u_e, v_n

def rot_uv2enf (uo:xr.DataArray, vo:xr.DataArray, gsinf:xr.DataArray, gcosf:xr.DataArray,
                zdim:Union[str,None]=None, Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
                aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> tuple[xr.DataArray, xr.DataArray] :
    '''
    Rotates the Repere: Change vector componantes from
    stretched coordinates grid --> geographic grid

    uo : velocity along i at the U grid point
    vo : valocity along j at the V grid point
    
    Returns east-north components on the F grid point
    '''
    push_stack ( f'rot_uv2enf ( uo, vo, gsint, gcost, {aperio=}, {zdim=} )' )
    zdom   = Domain (ptab=uo, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    uf = u2f (uo, domain=zdom, psgn=-1.0, zdim=zdim)
    vf = v2f (vo, domain=zdom, psgn=-1.0, zdim=zdim)

    u_e = + uf * gcosf - vf * gsinf
    v_n = + uf * gsinf + vf * gcosf

    u_e = lbc (u_e, domain=zdom, cd_type='F', psgn= 1.0)
    v_n = lbc (v_n, domain=zdom, cd_type='F', psgn= 1.0)

    pop_stack ( 'rot_uv2enf' )
    return u_e, v_n

def u2t (utab:xr.DataArray, psgn:float=-1.0, zdim:Union[str,None]=None, action:str='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:Union[bool,None]=False ) -> xr.DataArray :
    '''
    Interpolates an array from U grid to T grid (i-mean)
    '''
    push_stack ( f'u2t (utab, {psgn=}, {action=} )' )
    zdom   = Domain (ptab=utab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    utab_0 = xr.where ( np.isnan(utab), 0., utab)
    utab_0 = lbc_add (utab_0, domain=zdom, cd_type='U', psgn=psgn)
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
        ttab = lbc_del (ttab  , domain=zdom, cd_type='T', psgn=psgn)
    else :
        ttab = lbc_del (utab_0, domain=zdom, cd_type='T', psgn=psgn)

    if ax :
        ttab = ttab.assign_coords({ax:np.arange (ttab.shape[ix])+1.})
    if zdim and az :
        if az != zdim :
            ttab = ttab.rename( {az:zdim})
                
    pop_stack ( 'u2t' )
    return ttab

def v2t (vtab:xr.DataArray, psgn:float=-1.0, zdim:Union[str,None]=None, action:str='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None,
          aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array from V grid to T grid (j-mean)
    '''
    push_stack ( f'v2t (vtab, {aperio=}, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=vtab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo,
                      aperio=aperio, nperio=nperio, domain=domain)
    vtab_0 = xr.where ( np.isnan(vtab), 0., vtab)
    vtab_0 = lbc_add (vtab_0, domain=zdom, cd_type='V', psgn=psgn)
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
        ttab = lbc_del (ttab  , domain=zdom, cd_type='T', psgn=psgn)
    else :
        ttab = lbc_del (vtab_0, domain=zdom, cd_type='T', psgn=psgn)

    if ay :
        ttab = ttab.assign_coords({ay:np.arange(ttab.shape[jy])+1.})
    if zdim and az :
        if az != zdim :
            ttab = ttab.rename( {az:zdim})
                
    pop_stack ( 'v2t' )
    return ttab

def f2t (ftab:xr.DataArray, psgn:float=1.0, zdim:Union[str,None]=None, action='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain|None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array from F grid to T grid (i- and j- means)
    '''
    push_stack ( f'f2t (ftab, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=ftab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    ftab_0 = xr.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0, domain=zdom, cd_type='F', psgn=psgn)
    ttab = v2t (f2v (ftab_0, domain=zdom, psgn=psgn, zdim=zdim, action=action),
                             domain=zdom, psgn=psgn, zdim=zdim, action=action)

    ttab = lbc_del (ttab, domain=zdom, cd_type='T', psgn=psgn)
    
    pop_stack ( 'f2t' )
    return ttab

def t2u (ttab:xr.DataArray, psgn:float=1.0, zdim:Union[str,None]=None, action:Union[str,None]='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:Union[bool,None]=False) -> xr.DataArray :
    '''
    Interpolates an array from T grid to U grid (i-mean)
    '''
    push_stack ( f't2u (ttab, {psgn=}, {zdim=}, {action=} )' )

    zdom   = Domain (ptab=ttab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    ttab_0 = xr.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0, domain=zdom, cd_type='T', psgn=psgn)
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
        utab = lbc_del (utab  , domain=zdom, cd_type='U', psgn=psgn)
    else :
        utab = lbc_del (ttab_0, domain=zdom, cd_type='U', psgn=psgn)

    if ax :
        utab = utab.assign_coords({ax:np.arange(utab.shape[ix])+1.})
        if 'x_c' in utab.dims :
            utab = utab.rename ({'x_c':'x_f'})
    if zdim and az :
        if az != zdim :
            utab = utab.rename( {az:zdim})

    pop_stack ( 't2u' )
    return utab

def t2v (ttab:xr.DataArray, psgn:float=1.0, zdim=None, action='ave',
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array from T grid to V grid (j-mean)
    '''
    push_stack ( f't2v (ttab, {aperio=}, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=ttab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    ttab_0 = xr.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 ,domain=zdom, cd_type='T', psgn=psgn)
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
        vtab = lbc_del (vtab  , domain=zdom, cd_type='V', psgn=psgn)
    else :
        vtab = lbc_del (ttab_0, domain=zdom, cd_type='V', psgn=psgn)

    if ay :
        vtab = vtab.assign_coords({ay:np.arange(vtab.shape[jy])+1.})
        if 'y_c' in vtab.dims :
            vtab = vtab.rename ({'y_c':'y_f'})
    if zdim and az :
        if az != zdim :
            vtab = vtab.rename( {az:zdim})
 
    pop_stack ( 't2v' )
    return vtab

def v2f (vtab:xr.DataArray, psgn:float=-1.0, zdim:Union[str,None]=None, action:str='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array from V grid to F grid (i-mean)
    '''
    push_stack ( f'v2f (vtab, {aperio=}, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=vtab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    vtab_0 = xr.where ( np.isnan(vtab), 0., vtab)
    vtab_0 = lbc_add (vtab_0 , domain=zdom, cd_type='V', psgn=psgn)
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
        ftab = lbc_del (ftab  , domain=zdom, cd_type='F', psgn=psgn)
    else :
        ftab = lbc_del (vtab_0, domain=zdom, cd_type='F', psgn=psgn)

    if ax :
        ftab = ftab.assign_coords({ax:np.arange(ftab.shape[ix])+1.})
        if 'y_c' in ftab.dims :
            ftab = ftab.rename ({'x_c':'x_f'})
    if zdim and az :
        if az != zdim :
            ftab = ftab.rename( {az:zdim})

    ftab = lbc_del (ftab, domain=zdom, cd_type='F', psgn=psgn)
    
    pop_stack ( 'v2f' )
    return ftab

def u2f (utab:xr.DataArray, psgn:float=-1.0, zdim:Union[xr.DataArray,None]=None, action:str='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array from U grid to F grid i-mean)
    '''
    push_stack ( f'u2f (utab, {aperio=}, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=utab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo,
                      aperio=aperio, nperio=nperio, domain=domain)
    utab_0 = xr.where ( np.isnan(utab), 0., utab)
    utab_0 = lbc_add (utab_0 , domain=zdom, cd_type='U', psgn=psgn)
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
        ftab = lbc_del (ftab, aperio=aperio, domain=zdom, cd_type='F', psgn=psgn)
    else :
        ftab = lbc_del (utab_0, domain=zdom, cd_type='F', psgn=psgn)

    if ay :
        ftab = ftab.assign_coords({ay:np.arange(ftab.shape[jy])+1.})
        if 'y_c' in ftab.dims :
            utab = utab.rename ({'y_c':'y_f'})
    if zdim and az :
        if az != zdim :
            ftab = ftab.rename( {az:zdim})
    
    pop_stack ( 'u2f' )
    return ftab

def t2f (ttab:xr.DataArray, psgn:float=1.0, zdim:Union[xr.DataArray,None]=None, action:str='mean', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array on T grid to F grid (i- and j- means)
    '''
    push_stack ( f't2f (utab, {aperio=}, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=ttab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    ttab_0 = xr.where ( np.isnan(ttab), 0., ttab)
    ttab_0 = lbc_add (ttab_0 , zdom=zdom, cd_type='T', psgn=psgn)
    ftab = t2u (u2f (ttab, domain=zdom, psgn=psgn, zdim=zdim, action=action),
                           domain=zdom, psgn=psgn, zdim=zdim, action=action)

    ftab = lbc_del (ftab, domain=zdom, cd_type='F', psgn=psgn) 

    pop_stack ( 'v2f' )
    return ftab

def f2u (ftab:xr.DataArray, psgn:float=1.0, zdim:Union[str,None]=None, action:str='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array on F grid to U grid (j-mean)
    '''
    push_stack ( f'f2u (utab, {aperio=}, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=ftab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    ftab_0 = xr.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , domain=zdom, cd_type='F', psgn=psgn)
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
        utab = lbc_del (utab  , domain=zdom, cd_type='U', psgn=psgn)
    else :
        utab = lbc_del (ftab_0, domain=zdom, cd_type='U', psgn=psgn)

    utab = utab.assign_coords({ay:np.arange(ftab.shape[jy])+1.})
    if 'y_f' in utab.dims :
        utab = utab.rename ({'y_f':'y_c'})
    if zdim and az and az != zdim :
        utab = utab.rename( {az:zdim})

    pop_stack ( 'f2u' )
    return utab

def f2v (ftab:xr.DataArray, psgn:float=1.0, zdim:Union[xr.DataArray,None]=None, action:str='ave', 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Interpolates an array from F grid to V grid (i-mean)
    '''
    push_stack ( f'f2v (ftab, {aperio=}, {psgn=}, {zdim=}, {action=} )' )
    zdom   = Domain (ptab=ftab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)
    ftab_0 = xr.where ( np.isnan(ftab), 0., ftab)
    ftab_0 = lbc_add (ftab_0 , domain=zdom, cd_type='F', psgn=psgn)
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
        vtab = lbc_del (vtab  , domain=zdom, cd_type='V', psgn=psgn)
    else :
        vtab = lbc_del (ftab_0, domain=zdom, cd_type='V', psgn=psgn)

    vtab = vtab.assign_coords({ax:np.arange(ftab.shape[ix])+1.})
    if 'x_f' in ftab.dims :
        vtab = vtab.rename ({'x_f':'x_c'})
    if zdim and az :
        if az != zdim :
            vtab = vtab.rename( {az:zdim})

    pop_stack ( 'f2v' )
    return vtab

def w2t (wtab:xr.DataArray, zcoord:Union[xr.DataArray,None]=None, zdim:Union[xr.DataArray,None]=None, 
         sval:float=np.nan) -> xr.DataArray :
    '''
    Interpolates an array on W grid to T grid (k-mean)
    sval is the bottom value
    '''
    push_stack ( f'w2t (wtab, {zcoord=}, {zdim=}, {sval=} )' )
    wtab_0 = xr.where ( np.isnan(wtab), 0., wtab)

    az, kz = find_axis (wtab_0, 'z')

    if kz :
        ttab = 0.5 * (wtab_0 + np.roll (wtab_0, axis=kz, shift=-1))
    else :
        ttab = wtab_0

    ttab[{az:kz}] = sval
    if zdim and az :
        if az != zdim :
            ttab = ttab.rename ( {az:zdim} )
    if zcoord is not None :
        ttab = ttab.assign_coords ( {zdim:zcoord} )
    if 'z_f' in utab.dims :
        utab = utab.rename ({'z_f':'z_c'})

    pop_stack ( 'w2t' )
    return ttab

def t2w (ttab:xr.DataArray, zcoord:Union[xr.DataArray,None]=None, zdim:Union[str,None]=None, 
         sval:float=np.nan, extrap_surf:bool=False) -> xr.DataArray :
    '''
    Interpolates an array from T grid to W grid (k-mean)

    sval is the surface value
    if extrap_surf==True, surface value is taken from 1st level value.
    '''
    push_stack ( f't2w (utab, {zcoord=}, {zdim=}, {sval=}, {extrap_surf=} )' )
    ttab_0 = xr.where ( np.isnan(ttab), 0., ttab)
    az, kz = find_axis (ttab_0, 'z')
    wtab = 0.5 * ( ttab_0 + np.roll (ttab_0, axis=kz, shift=1) )

    if extrap_surf :
        wtab[{az:0}] = ttab[{az:0}]

    if zdim and az and az != zdim :
        wtab = wtab.rename ( {az:zdim})
    if zcoord is not None :
        wtab = wtab.assign_coords ( {zdim:zcoord})
    else :
        wtab = wtab.assign_coords ( {zdim:np.arange(ttab.shape[kz])+1.} )
    if 'z_c' in utab.dims :
        utab = utab.rename ({'z_c':'z_f'})

    pop_stack ( 't2w' )
    return wtab

def fill (ptab:xr.DataArray, cd_type:str='T', npass:int=1, sval=np.nan, 
          Iperio:Union[bool,None]=None, Jperio:Union[bool,None]=None, NFold:bool=None, NFtype:str=None, Halo:bool=None, 
          aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Fills np.nan values with mean of neighbours

    Inputs :
       ptab : input field to fill
       aperio, cd_type : periodicity characteristics
    '''
    push_stack ( f'fill (ptab, {aperio=}, {cd_type=}, {npass=}, {sval=} ) ')
    zdom   = Domain (ptab=ptab, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)    
    ax, ix = find_axis (ptab, 'x')
    ay, jy = find_axis (ptab, 'y')
    
    do_perio  = False
    ldomain   = zdom
    if zdom.Iperio and not zdom.Jperio and zdom.NFold and zdom.NFtype=='T' and not zdom.Halo : #aperio == 4.2 :
        do_perio = True
        ldom = Domain (Halo=True, domain=zdom)
    if Iperio and not Jperio and NFold and NFtype=='T' and not Halo : #aperio == 6.2 :
        do_perio = True
        ldom = Domain (Halo=True, domain=zdom)

    if do_perio :
        ztab = lbc_add (ptab, domain=zdom, cd_type=cd_type)
    else :
        ztab = ptab

    if np.isnan (sval) :
        ztab   = xr.where (np.isnan(ztab), np.nan, ztab)
    else :
        ztab   = xr.where (ztab==sval    , np.nan, ztab)

    for _ in np.arange (npass) :
        zmask = xr.where ( np.isnan(ztab), 0., 1.   )
        ztab0 = xr.where ( np.isnan(ztab), 0., ztab )
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

        zcount = lbc (zcount, domain=ldom, cd_type=cd_type)
        znew   = lbc (znew  , domain=ldom, cd_type=cd_type)

        ztab = xr.where (np.logical_and (zmask==0., zcount>0), znew/zcount, ztab)

    ztab = xr.where (zcount==0, sval, ztab)
    if do_perio :
        ztab = lbc_del (ztab, domain=ldom)

    pop_stack ( 'fill' )
    return ztab

def correct_uv (u:xr.DataArray, v:xr.DataArray, lat:xr.DataArray) -> tuple[xr.DataArray, xr.DataArray] :
    '''
    Corrects a Cartopy bug in orthographic projection

    See https://github.com/SciTools/cartopy/issues/1179

    The correction is needed with cartopy <= 0.20
    It seems that version 0.21 will correct the bug (https://github.com/SciTools/cartopy/pull/1926)
    Later note : the bug is still present in Cartopy 0.24

    Inputs :
       u, v : eastward/northward components
       lat  : latitude of the point (degrees north)

    Outputs :
       modified eastward/nothward components to have correct polar projections in cartopy
    '''
    push_stack (' correct_uv (u, v, lat)')
    uv = np.sqrt (u*u + v*v)           # Original modulus
    zu = u
    zv = v * np.cos (np.deg2rad(lat))
    zz = np.sqrt ( zu*zu + zv*zv )     # Corrected modulus
    uc = zu*uv/zz
    vc = zv*uv/zz      # Final corrected values

    pop_stack ( 'correct_uv' )
    return uc, vc

def norm_uv (u:xr.DataArray, v:xr.DataArray) -> xr.DataArray :
    '''Returns norm of a 2 components vector
    '''
    push_stack ( 'norm_uv (u, v)' )
    zz = np.sqrt (u*u + v*v)
    pop_stack ( 'norm_uv' )
    return zz

def normalize_uv (u:xr.DataArray, v:xr.DataArray) -> (xr.DataArray, xr.DataArray) :
    '''Normalizes 2 components vector
    '''
    push_stack ( 'normalize_uv (u, v)' )
    uv = norm_uv (u, v)
    uu = u/uv
    vv = v/uv
    pop_stack ( 'normalize_uv' )
    return uu, vv

def zonmean (var:xr.DataArray, bb:xr.DataArray, plat1d:xr.DataArray, Debug:bool=False) -> xr.DataArray :
    '''
    Computes the meridonal stream function

    var : var
    bb  : volume
    '''
    push_stack ( 'zonmean (vv, bb, plat1d)' )

    if OPTIONS['Debug'] or Debug :
        print ( f'{bb.dims = } {bb.shape=}' )
        print ( f'{var.dims = } {var.shape}' )

    ax, ix = find_axis (var, 'x')
    ay, jy = find_axis (var, 'y')
    az, kz = find_axis (var, 'z')

    ldims = UDIMS.copy()
    ldims.update ({'x':ax, 'y':ay, 'z':az})

    if OPTIONS['Debug'] or Debug :
        print ( f'zonmean : {ldims=}' )
    
    if OPTIONS['Debug'] or Debug :
        print ('zonmean : zonal mean of volume')
    zon_bb  = unify_dims (bb, **ldims).sum(dim=ldims['x'], min_count=1, keep_attrs=True)
    zon_bb  = zon_bb.where (zon_bb>0., np.nan)
    if OPTIONS['Debug'] or Debug :
        print ( f'zonmean : {zon_bb.dims = }' )
    if OPTIONS['Debug'] or Debug :
        print ('zonmean : zonal mean of variable')
    zon_var = (var * unify_dims (bb, **ldims)).sum(dim=ldims['x'], min_count=1, keep_attrs=True) / zon_bb
    zon_var = zon_var.where ( np.logical_not(np.isnan(zon_bb)), np.nan)
    if OPTIONS['Debug'] or Debug :
        print ( f'zonmean : {zon_var.dims = }' )
    
    if OPTIONS['Debug'] or Debug :
        print ( 'zonmean : Change coords')
    zon_var = zon_var.assign_coords ( {ldims['y']:(ldims['y'], plat1d.values)} )
    zon_var = zon_var.rename ( {ldims['y']:'lat'} )

    zon_var.attrs.update (var.attrs)
    if 'standard_name' in zon_var.attrs :
        zon_var.attrs ['long_name'] = zon_var.attrs ['standard_name'] + ' - zonal mean'
    zon_var.lat.attrs = plat1d.attrs

    pop_stack ( 'zon' )
    return zon_var

def msf (vv:xr.DataArray, e1v_e3v:xr.DataArray, plat1d:xr.DataArray, depthw:xr.DataArray, 
         south:Union[bool,None]=None, Debug:Union[bool,None]=True) -> xr.DataArray :
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
    
    zomsf = -v_e1v_e3v.cumsum(dim=az, keep_attrs=True).sum(dim=ax, min_count=1, keep_attrs=True)
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

    if south :
        south = -30
    
    if south :
        if OPTIONS['Debug'] or Debug :
            print ( f'Masque south of {south}')
        zomsf = zomsf.where (zomsf.lat > south, np.nan)

    pop_stack ( 'msf' )
    return zomsf

def zmsf_index (zmsf:Union[xr.DataArray,None], name:str="nadw", latname:str='nav_lat', lat:Union[xr.DataArray,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Compute index of zonal meridional stream function
    
    Known case (name) : nadw, aabw, npdw, deacon
    '''
    push_stack ( f'zmsf_index (zmsf, {name=}, {latname=}, lat)' )

    if name == "nadw"   :
        zlim = slice (500, 4000)
        ylim = slice (11, 55)
        long_name = 'North Atlantic Deep Water'
    if name == "aabw"   :
        zlim = slice (2000,6000)
        ylim = slice (-30, 60)
        long_name = 'Antarctic Bottom Water'
    if name == "npdw"   :
        zlim = slice( 500,6000)
        ylim = slice( 15, 60)
        long_name = 'North Pacific Bottom Water'
    if name == "deacon" :
        zlim = slice(2000,6000)
        ylim = slice(-80,-30)
        long_name = 'Deacon Cell'
    
    zlat1d   = lat1d  (zmsf[latname])
    zmsf_lat = unify_dims (zmsf, **UDIMS)
    if OPTIONS['Debug'] or Debug :
        print (f'{zmsf_lat.dims=} , {UDIMS=}')
    if not lat is None :
        zmsf_lat = zmsf_lat.assign_coords ( {'y':lat.values} )
    else : 
        zmsf_lat = zmsf_lat.assign_coords ( {UDIMS['y']:zlat1d.values} )
    if OPTIONS['Debug'] or Debug :
        print ( f'{ylim=} - {zlim=}' )
        print ( f'{zlat1d=}' )
        print ( f'{zmsf_lat.y}' )
        print ( f'{zmsf_lat.olevel}' )

    za = zmsf_lat.sel ({UDIMS['z']:zlim})
    if OPTIONS['Debug'] or Debug :
        print ( f'{za.shape=}')
        print ( f'{za=}')
        
    index_ocean = zmsf_lat.sel ({UDIMS['z']:zlim}).max (dim=UDIMS['z']).sel ({UDIMS['y']:ylim}).max (dim=UDIMS['y'])
    index_ocean.name = f'{name}_ocean'
    index_ocean.attrs.update (zmsf.attrs)
    index_ocean.attrs.update ({'long_name':long_name})
    pop_stack ('zmsf_index')
    return index_ocean

def bsf (uu:xr.DataArray, e2u_e3u:xr.DataArray, mask:xr.DataArray, bsf0:Union[list,Dict,None]=None, 
         Iperio:Union[int,None]=None, Jperio:Union[int,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
         aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Computes the barotropic stream function

    uu      : zonal velocity
    e2u_e3u : product of scales factor e2u*e3u
    bsf0    : the point with bsf=0
    (ex: bsf0={'x':3, 'y':120} for orca2,
         bsf0={'x':5, 'y':300} for eORCA1
    '''
    push_stack ( f'bsf (uu, e2u_e3u, mask, {aperio=}, {bsf0=} )' )
    zdom = Domain (ptab=uu, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                   aperio=aperio, nperio=nperio, domain=domain)    

    u_e2u_e3u       = uu * e2u_e3u
    u_e2u_e3u.attrs = uu.attrs
    if OPTIONS['Debug'] or Debug :
        print ( f'{u_e2u_e3u.dims=} {mask.dims=}' )

    ax, ix = find_axis (u_e2u_e3u, 'y')
    ay, jy = find_axis (u_e2u_e3u, 'y')
    az, kz = find_axis (u_e2u_e3u, 'z')

    zbsf = -u_e2u_e3u.cumsum (dim=ay, keep_attrs=True )
    if OPTIONS['Debug'] or Debug :
        print ( f'1 - {zbsf.dims=}' )
    zbsf = zbsf.sum (dim=az, keep_attrs=True)
    if OPTIONS['Debug'] or Debug :
        print ( f'2 - {zbsf.dims=}' )
    if bsf0 is not None : 
        zbsf = zbsf - zbsf.isel (bsf0)

    zbsf = zbsf.where (mask !=0, np.nan)
    if OPTIONS['Debug'] or Debug : #type: ignore
        print ( f'3 - {zbsf.dims=}' )
    zbsf.attrs.update (uu.attrs)
    zbsf.attrs['standard_name'] = 'stfbaro'
    zbsf.attrs['long_name']     = 'ocean_barotropic_stream_function'
    zbsf.attrs['units']         = 'm3s-1'
    zbsf = lbc (zbsf, domain=zdom, cd_type='F')

    pop_stack ( 'bsf' )
    return zbsf
    
if f90nml :
    def namelist_read (ref:Union[str,None]=None, cfg:Union[str,None]=None, out:str='dict', flat:bool=False, Debug:bool=False) :
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
            dict_namelist = dict()
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
            if OPTIONS['Debug'] or Debug :
                print (comment)
            if flat and out =='dict' :
                for nam in nml.keys () :
                    if OPTIONS['Debug'] or Debug :
                        print (nam)
                    for value in nml[nam] :
                        if out == 'dict' :
                            dict_namelist[value] = nml[nam][value]
                        if OPTIONS['Debug'] or Debug :
                            print (nam, ':', value, ':', nml[nam][value])
            else :
                for nam in nml.keys () :
                    if OPTIONS['Debug'] or Debug :
                        print (nam)
                    if out == 'dict' :
                        if nam not in dict_namelist.keys () :
                            dict_namelist[nam] = dict ()
                    for value in nml[nam] :
                        if out == 'dict' :
                            dict_namelist[nam][value] = nml[nam][value]
                        if out == 'xr'   :
                            xr_namelist[value] = nml[nam][value]
                        if OPTIONS['Debug'] or Debug : 
                            print (nam, ':', value, ':', nml[nam][value])

        pop_stack ( 'namelist_read' )
        if out == 'dict' :
            return dict_namelist
        if out == 'xr'   :
            return xr_namelist
else :
     def namelist_read (ref:Union[str,None]=None, cfg:Union[str,None]=None, out:str='dict', flat:bool=False) :
        '''
        Shadow version of namelist read, when f90nm module was not found

        namelist_read : 
        Read NEMO namelist(s) and return either a dictionnary or an xarray dataset
        '''
        push_stack ( f'namelist_read [void version] (ref, cfg, {out=}, {flat=})' )

        print ( 'Error : module f90nml not found' )
        print ( 'Cannot call namelist_read' )
        print ( 'Call parameters where : ')
        print ( f'{ref=} {cfg=} {out=} {flat=}' )
        pop_stack ( 'namelist_read [void version]' )

def fill_closed_seas (imask:xr.DataArray, cd_type:str='T', 
                      Iperio:Union[bool,None]=None, Jperio:Union[bool,None]=None, NFold:Union[bool,None]=None, NFtype:Union[str,None]=None, Halo:Union[bool,None]=None, 
                      aperio:Union[int,float,None]=None, nperio:Union[int,None]=None, domain:Union[Domain,None]=None, Debug:bool=False) -> xr.DataArray :
    '''
    Fill closed seas with image processing library

    imask : mask, 1 on ocean, 0 on land
    '''
    push_stack ( f'fill_closed_seas (imask, {aperio=}, {cd_type=} )' )
    zdom   = Domain (ptab=imask, Iperio=Iperio, Jperio=Jperio, NFold=NFold, NFtype=NFtype, Halo=Halo, 
                     aperio=aperio, nperio=nperio, domain=domain)

    from scipy import ndimage

    imask_filled = ndimage.binary_fill_holes ( lbc (imask, domain=zdom, cd_type=cd_type))
    imask_filled = xr.DataArray (imask_filled, coords=imask.coords, dims=imask.dims)
    imask_filled = lbc (imask_filled, domain=zdom, cd_type=cd_type)

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

def rhop (ptemp:xr.DataArray, psal:xr.DataArray) -> xr.DataArray :
    '''
    Returns potential density referenced to surface

    Computation from NEMO code
    '''
    push_stack ( 'rhop (ptemp, psal)' )
    zt      = ptemp * R1_T0                               # Temperature (°C)
    zs      = np.sqrt (np.abs (psal + RDELTAS) * R1_S0)   # Square root of salinity (PSS)
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

def rho (pdep:xr.DataArray, ptemp:xr.DataArray, psal:xr.DataArray) -> xr.DataArray :
    ''' 
    Returns in situ density

    Computation from NEMO code
    '''
    push_stack ( 'rho (pdep, ptemp, psal)' )
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
