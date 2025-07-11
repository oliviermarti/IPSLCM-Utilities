# -*- coding: utf-8 -*-
'''
libIGCM.sys

author: olivier.marti@lsce.ipsl.fr

GitHub : https://github.com/oliviermarti/IPSLCM-Utilities

This library if a layer under some usefull
environment variables and commands.
All those definitions depend on host particularities.

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

import os
import subprocess
import configparser
import time
import copy
from typing import Any, Self, Literal, Dict, Union, Hashable
import numpy as np
import libIGCM.date
from libIGCM.utils import OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack

# Where do we run ?
SysName, NodeName, Release, Version, Machine = os.uname ()

## ============================================================================
def Mach (long:bool=False) -> Union[str,None] :
    '''
    Find the computer we are on

    Returns a standardized name of the computer we run on

    On Irene, Mach returns Irene, Irene-Next, Rome or Rome-Prev if long==True
    '''

    zmach = None

    if SysName == 'Darwin' and 'sargas028' in NodeName :
        zmach = 'Spip'
    if 'obelix'    in NodeName :
        zmach = 'Obelix'
    if 'jupyter'   in NodeName and "/home/users/" in os.path.abspath ("")  :
        zmach = 'Obelix'
    if 'forge'     in NodeName :
        zmach = 'Forge'
    if 'ciclad'    in NodeName :
        zmach = 'Ciclad'
    if 'climserv'  in NodeName :
        zmach = 'SpiritX'
    if 'spirit'    in NodeName :
        zmach = 'SpiritJ'
    if 'spiritj'   in NodeName :
        zmach = 'SpiritJ'
    if 'spiritx'   in NodeName :
        zmach = 'SpiritX'
    if 'irene'     in NodeName :
        zmach = 'Irene'
    if 'jean-zay'  in NodeName :
        zmach = 'Jean-Zay'

    if long :
        zmachfull = zmach

        if zmach == 'Irene' :
            CPU    = subprocess.getoutput ('lscpu')

            if "Intel(R) Xeon(R) Platinum" in CPU :
                zmachfull = 'Irene'

            if "AMD" in CPU :
                zmachfull = 'Rome'

        zmach = zmachfull

    return zmach
# =======================================================================

MASTER    = Mach (long=False)
LocalUser = os.environ ['USER']

IGCM_Catalog      = get_options ()['IGCM_Catalog']
IGCM_Catalog_list = get_options ()['IGCM_Catalog_list']

if LocalUser in  ['marti', 'omamce', 'p25mart', 'p86mart', 'rces009' ] :
    IGCM_Catalog_list.append (os.path.join(os.environ['HOME'], 'Python', 'Library', 'IGCM_Catalog.json' ))
    IGCM_Catalog_list.append (os.path.join(os.environ['HOME'], 'Python', 'Library', 'TRHOL_Catalog.json'))
    
# =======================================================================

if 'IGCM_Catalog' in os.environ :
    IGCM_Catalog = os.environ['IGCM_Catalog']

if 'IGCM_Catalog_list' in os.environ :
    IGCM_Catalog_list = os.environ['IGCM_Catalog_list']

set_options (IGCM_Catalog=IGCM_Catalog, IGCM_Catalog_list=IGCM_Catalog_list)

## Where do we run ?
#SysName, NodeName, Release, Version, Machine = os.uname ()

class Config :
    '''
    ! Defines the libIGCM directories
        
    Source : for Spip
    Possibilities :
        Local         : local (~/Data/IGCMG/...)
        TGCC_sshfs    : TGCC disks mounted via sshfs
        TGCC_thredds  : thredds TGCC via IPSL
        IDRIS_thredds : thredds IDRIS via IPSL
    '''
    ## Public functions
    def update (self:Self, dico:Union[Dict,None]=None, **kwargs):
        '''Use a dictionnary to update values'''
        if dico is not None : 
            for attr in dico.keys () :
                super().__setattr__(attr, dico[attr])
        self.__dict__.update (kwargs)
    def keys    (self:Self) :
        return self.__dict__.keys()
    def values  (self:Self) :
        return self.__dict__.values()
    def items   (self:Self) :
        return self.__dict__.items()
    def dict    (self:Self) :
        return self.__dict__()
    def pop     (self:Self, attr) :
        zv = self[attr]
        delattr (self, attr)
        return zv
    ## Hidden functions
    def __str__     (self:Self) :
        return str  (self.__dict__)
    def __repr__    (self:Self) :
        return repr (self.__dict__)
    def __name__    (self:Self) :
        return self.__class__.__name__
    def __getitem__ (self:Self, attr) :
        return getattr (self, attr)
    def __setitem__ (self, attr, value) -> None :
        setattr (self, attr, value)
    def __iter__    (self:Self) :
        return self.__dict__.__iter__()
    def __next__    (self:Self) :
        return self.__dict__.__next__()
    def __len__     (self:Self) :
        return len(self.__dict__)
    def __copy__    (self:Self) :
        return copy.deepcopy (self)

    def __init__ (self:Self, 
                  JobName:Union[str,None]=None, TagName:Union[str,None]=None, SpaceName:Union[str,None]=None, ExperimentName:Union[str,None]=None,
                  LongName:Union[str,None]=None, ModelName:Union[str,None]=None, ShortName:Union[str,None]=None, Comment:Union[str,None]=None,
                  Source:Union[str,None]=None, MASTER:Union[str,None]=None, 
                  ConfigCard:Union[str,None]=None, RunCard:Union[str,None]=None,
                  User:Union[str,None]=None, Group:Union[str,None]=None, LocalGroup:Union[str,None]=None,
                  TGCC_User:Union[str,None]=None, TGCC_Group:Union[str,None]=None, 
                  IDRIS_User:Union[str,None]=None, IDRIS_Group:Union[str,None]=None,
                  ARCHIVE:Union[str,None]=None, SCRATCHDIR:Union[str,None]=None,
                  STORAGE:Union[str,None]=None, 
                  R_IN:Union[str,None]=None, R_OUT:Union[str,None]=None, R_FIG:Union[str,None]=None,
                  L_EXP:Union[str,None]=None,
                  R_SAVE:Union[str,None]=None, R_FIGR:Union[str,None]=None, R_BUF:Union[str,None]=None, 
                  R_BUFR:Union[str,None]=None, R_BUF_KSH:Union[str,None]=None,
                  REBUILD_DIR:Union[str,None]=None, POST_DIR:Union[str,None]=None,
                  ThreddsPrefix:Union[str,None]=None, DapPrefix:Union[str,None]=None, R_GRAF:Union[str,None]=None, 
                  DB:Union[str,None]=None,
                  IGCM_OUT:Union[str,None]=None, IGCM_OUT_name:Union[str,None]=None, 
                  rebuild:Union[str,None]=None, TmpDir:Union[str,None]=None,
                  TGCC_ThreddsPrefix:Union[str,None]=None, TGCC_DapPrefix:Union[str,None]=None,
                  IDRIS_ThreddsPrefix:Union[str,None]=None, IDRIS_DapPrefix:Union[str,None]=None,
                  DateBegin:Union[str,None]=None, DateEnd:Union[str,None]=None, YearBegin:Union[str,None]=None, YearEnd:Union[str,None]=None, PeriodLength:Union[str,None]=None,
                  SeasonalFrequency:Union[str,None]=None, CalendarType:Union[str,None]=None,
                  DateBeginGregorian:Union[str,None]=None, DateEndGregorian:Union[str,None]=None, 
                  FullPeriod:Union[str,None]=None, DatePattern:Union[str,None]=None,
                  Period:Union[str,None]=None, PeriodSE:Union[str,None]=None, CumulPeriod:Union[str,None]=None, PeriodState:Union[str,None]=None,
                  PeriodDateBegin:Union[str,None]=None, PeriodDateEnd:Union[str,None]=None,
                  Shading:Union[str,np.ndarray,list,None]=None, Marker:Union[str,Dict,None]=None, Line:Union[str,Dict,None]=None,
                  OCE:Union[str,None]=None, ATM:Union[str,None]=None,
                  CMIP6_BUF:Union[str,None]=None, Debug:bool=False, **kwargs) -> None :

        if OPTIONS['Debug'] or Debug : # type: ignore
            print ( f'libIGCM.sys.Config : {MASTER    =}' )
            print ( f'libIGCM.sys.Config : {User      =}' )
            print ( f'libIGCM.sys.Config : {LocalUser =}' )
            print ( f'libIGCM.sys.Config : {TGCC_User =}' )
            print ( f'libIGCM.sys.Config : {TGCC_Group=}' )
   
        if not Debug               :
            Debug               = OPTIONS['Debug'] # type: ignore
        if not User                :
            User                = OPTIONS['User'] # type: ignore
        if not Group               :
            Group               = OPTIONS['Group'] # type: ignore
        if not TGCC_User           :
            TGCC_User           = OPTIONS['TGCC_User'] # type: ignore
        if not TGCC_Group          :
            TGCC_Group          = OPTIONS['TGCC_Group'] # type: ignore
        if not IDRIS_User          :
            IDRIS_User          = OPTIONS['IDRIS_User'] # type: ignore
        if not IDRIS_Group         :
            IDRIS_Group         = OPTIONS['IDRIS_Group'] # type: ignore
        if not TGCC_ThreddsPrefix  :
            TGCC_ThreddsPrefix  = OPTIONS['TGCC_ThreddsPrefix'] # type: ignore
        if not TGCC_DapPrefix      :
            TGCC_DapPrefix      = OPTIONS['TGCC_DapPrefix'] # type: ignore
        if not IDRIS_ThreddsPrefix :
            IDRIS_ThreddsPrefix = OPTIONS['IDRIS_ThreddsPrefix'] # type: ignore
        if not IDRIS_DapPrefix     :
            IDRIS_DapPrefix     = OPTIONS['IDRIS_DapPrefix'] # type: ignore
        if not ThreddsPrefix       :
            ThreddsPrefix       = OPTIONS['ThreddsPrefix'] # type: ignore
        if not DapPrefix           :
            DapPrefix           = OPTIONS['DapPrefix'] # type: ignore

        if not MASTER :
            MASTER = Mach (long=False)
        if not MASTER :
            MASTER = 'Unknown'
            
        if OPTIONS['Debug'] or Debug : # type: ignore
            print ( f'libIGCM.sys.Config : {MASTER    =}' )
            print ( f'libIGCM.sys.Config : {User      =}' )
            print ( f'libIGCM.sys.Config : {LocalUser =}' )
            print ( f'libIGCM.sys.Config : {TGCC_User =}' )
            print ( f'libIGCM.sys.Config : {TGCC_Group=}' )
             
        # ===========================================================================================
        # Reads config.card if available
        if ConfigCard :
            # Text existence of ConfigCard
            if not os.path.exists (ConfigCard ) :
                raise FileExistsError ( f"libIGCM.sys.Config : File not found : {ConfigCard = }" )
                
            ## Creates parser for reading .ini input file
            MyReader = configparser.ConfigParser (interpolation=configparser.ExtendedInterpolation() )
            MyReader.optionxform = str # To keep capitals # type: ignore
            MyReader.read (ConfigCard)
            
            if not JobName        :
                JobName         = MyReader['UserChoices']['JobName']
            #----- Short Name of Experiment
            if not ExperimentName :
                ExperimentName  = MyReader['UserChoices']['ExperimentName']
            #----- DEVT TEST PROD
            if not SpaceName      :
                SpaceName       = MyReader['UserChoices']['SpaceName']
            if not LongName       :
                LongName        = MyReader['UserChoices']['LongName']
            if not ModelName      :
                ModelName       = MyReader['UserChoices']['ModelName']
            if not TagName        :
                TagName         = MyReader['UserChoices']['TagName']


        # Reads run.card if available
        if RunCard :
            # Text existence of RunCard
            if not os.path.exists (RunCard) :
                raise FileExistsError ( f"libIGCM.sys.Config : File not found : {RunCard = }" )
                
            ## Creates parser for reading .ini input file
            MyReader = configparser.ConfigParser (interpolation=configparser.ExtendedInterpolation() )
            MyReader.optionxform = str # type: ignore
            
            MyReader.read (RunCard)

            if not PeriodDateBegin :
                PeriodDateBegin = MyReader['Configuration']['PeriodDateBegin']
            if not PeriodDateEnd   :
                PeriodDateEnd   = MyReader['Configuration']['PeriodDateEnd']
            if not CumulPeriod     :
                CumulPeriod     = MyReader['Configuration']['CumulPeriod']
            if not PeriodState     :
                PeriodState     = MyReader['Configuration']['PeriodState']
                
        ## ===========================================================================================
        if YearBegin and not DateBegin          :
            DateBegin = f'{YearBegin}-01-01'
        if YearEnd   and not DateEnd            :
            DateEnd   = f'{YearEnd}-12-31'
        if DateBegin and not DateBeginGregorian :
            DateBeginGregorian = libIGCM.date.ConvertFormatToGregorian (DateBegin)
        if DateEnd   and not DateEndGregorian   :
            DateEndGregorian   = libIGCM.date.ConvertFormatToGregorian (DateEnd  )
        if not FullPeriod and DateBeginGregorian and DateEndGregorian :
            FullPeriod = f'{DateBeginGregorian}_{DateEndGregorian}'
            
        ### ===========================================================================================
        ## Part specific to access by OpenDAP/Thredds server
        
        # ===========================================================================================
        if Source == 'TGCC_thredds' :
            if not User  and TGCC_User  :
                User  = TGCC_User
            if not Group and TGCC_Group :
                Group = TGCC_Group
                
            if not ThreddsPrefix :
                ThreddsPrefix = OPTIONS['TGCC_ThreddsPrefix'] # type: ignore
            if not DapPrefix     :
                DapPrefix     = OPTIONS['TGCC_DapPrefix'] # type: ignore
               
            if not ARCHIVE :
                ARCHIVE = f'{DapPrefix}/store/{TGCC_User}'
            if not R_FIG   :
                R_FIG   = f'{DapPrefix}/work/{TGCC_User}'
            if not R_IN    :
                R_IN    = f'{DapPrefix}/work/igcmg/IGCM'
            if not R_GRAF  :
                R_GRAF  = f'{DapPrefix}/work/p86mart/GRAF/DATA'
                
        # ===========================================================================================
        if Source == 'IDRIS_thredds' :
            if not User  and IDRIS_User  :
                User  = IDRIS_User
            if not Group and IDRIS_Group :
                Group = IDRIS_Group
                
            if not ThreddsPrefix :
                ThreddsPrefix = OPTIONS['IDRIS_ThreddsPrefix'] # type: ignore
            if not DapPrefix     :
                DapPrefix     = OPTIONS['IDRIS_DapPrefix'] # type: ignore
                
            if not ARCHIVE :
                ARCHIVE = f'{DapPrefix}/store/{IDRIS_User}'
            if not R_FIG   :
                R_FIG   = f'{DapPrefix}/work/{IDRIS_User}'
            if not R_IN    :
                R_IN    = f'{DapPrefix}/work/igcmg/IGCM'
            if not R_GRAF  :
                R_GRAF  = 'https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds/work/p86mart/GRAF/DATA'
              
        ### ===========================================================================================
        ## Machine dependant part
        
        # ===========================================================================================
        if MASTER == 'Obelix' :
            if not User   :
                User = LocalUser
            if Source :
                IGCM_OUT_name = ''
            else      :
                IGCM_OUT_name = 'IGCM_OUT'
            if not ARCHIVE    :
                ARCHIVE     = os.path.join ( os.path.expanduser ('~{User}'), 'Data'    )
            if not SCRATCHDIR :
                SCRATCHDIR  = os.path.join ( os.path.expanduser ('~{User}'), 'Scratch' )
            if not R_BUF      :
                R_BUF       = os.path.join ( os.path.expanduser ('~{User}'), 'Scratch' )
            if not R_FIG      :
                R_FIG       = os.path.join ( os.path.expanduser ('~{User}'), 'Data'    )
                
            if not STORAGE    :
                STORAGE     = ARCHIVE
            if not R_IN       :
                R_IN        = os.path.join ( '/home', 'orchideeshare', 'igcmg', 'IGCM' )
            if not R_GRAF or 'http' in str(R_GRAF) :
                R_GRAF      = os.path.join ( os.path.expanduser ('~marti'), 'GRAF', 'DATA' )
            if not DB         :
                DB          = os.path.join ( '/home', 'biomac1', 'geocean', 'ocmip'   )
            if not TmpDir     :
                TmpDir      = os.path.join ( os.path.expanduser ('~'), 'Scratch' )
                
        # ===========================================================================================
        if MASTER == 'Spip' :
            if not User   :
                User = LocalUser
            if Source :
                IGCM_OUT_name = ''
            else      :
                IGCM_OUT_name = 'IGCM_OUT'
            if not ARCHIVE    :
                ARCHIVE     = os.path.join ( os.path.expanduser (f'~{User}'), 'Data' )
            if not SCRATCHDIR :
                SCRATCHDIR  = os.path.join ( os.path.expanduser (f'~{User}'), 'Data' )
            if not R_BUF      :
                R_BUF       = os.path.join ( os.path.expanduser (f'~{User}'), 'Data' )
            if not R_FIG      :
                R_FIG       = os.path.join ( os.path.expanduser (f'~{User}'), 'Data' )
                
            if not STORAGE    :
                STORAGE     = ARCHIVE
            if not R_IN       :
                R_IN        = os.path.join ( os.path.expanduser (f'~{User}'), 'Data', 'IGCM' )
            if not R_GRAF or 'http' in str(R_GRAF) :
                R_GRAF      = os.path.join ( os.path.expanduser (f'~{User}'), 'GRAF', 'DATA' )
            if not DB         :
                DB          = os.path.join ( os.path.expanduser (f'~{User}'), 'GRAF', 'DB' )
            if not TmpDir     :
                TmpDir      = os.path.join ( os.path.expanduser (f'~{User}'), 'Scratch' )

        # ===========================================================================================
        if ( 'Irene' in MASTER ) or ( 'Rome' in MASTER ) :
            ccc_home = os.path.isfile ( subprocess.getoutput ( 'which ccc_home'))

            if Debug :
                print ( f'{TGCC_User=} {TGCC_Group=}' )
                
            if not User or User == 'marti' :
                if not TGCC_User :
                    User = LocalUser
                else             :
                    User = TGCC_User
                    
            if not Group :
                if TGCC_Group :
                    Group = TGCC_Group
                else          :
                    Group = LocalGroup

            if Debug :
                print ( f'{User=} {Group=}' )
                    
            LocalHome  = subprocess.getoutput ( 'ccc_home --ccchome' )
            LocalGroup = os.path.basename ( os.path.dirname (LocalHome))

            if Debug :
                print ( f'{MASTER=} {LocalHome=} {LocalGroup=}' )

            if not Source :
                IGCM_OUT_name = 'IGCM_OUT'
            
            if not R_IN        :
                if ccc_home :
                    R_IN       = os.path.join ( subprocess.getoutput ('ccc_home --cccwork -d igcmg -u igcmg' ), 'IGCM')
                else        :
                    R_IN       = '/ccc/work/cont003/igcmg/igcmg/IGCM'
            if Debug :
                print ( f'{R_IN}' )
            if not ARCHIVE  :
                if ccc_home :
                    ARCHIVE    = subprocess.getoutput ( f'ccc_home --cccstore   -u {User} -d {Group}')
                else        :
                    ARCHIVE    = f'/ccc/store/cont003/{TGCC_Group}/{TGCC_User}'
            if Debug :
                print ( f'{ARCHIVE}' )
            if not STORAGE  :
                if ccc_home :
                    STORAGE    = subprocess.getoutput ( f'ccc_home --cccwork    -u {User} -d {Group}')
                else        :
                    STORAGE    = f'/ccc/store/cont003/{TGCC_Group}/{TGCC_User}'
            if Debug :
                print ( f'{STORAGE}' )
            if not SCRATCHDIR  :
                if ccc_home :
                    SCRATCHDIR = subprocess.getoutput ( f'ccc_home --cccscratch -u {User} -d {Group}')
                else        :
                    SCRATCHDIR = f'/ccc/scratch/cont003/{TGCC_Group}/{TGCC_User}'
            if Debug :
                print ( f'{SCRATCHDIR}' )
            if not R_BUF       :
                if ccc_home :
                    R_BUF      = subprocess.getoutput ( f'ccc_home --cccscratch -u {User} -d {Group}')
                else        :
                    R_BUF      = f'/ccc/scratch/cont003/{TGCC_Group}/{TGCC_User}'
            if Debug :
                print ( f'{R_BUF}' )
            if not R_FIG       :
                if ccc_home :
                    R_FIG      = subprocess.getoutput ( f'ccc_home --cccwork    -u {User} -d {Group}')
                else        :
                    R_FIG      = f'/ccc/store/cont003/{TGCC_Group}/{TGCC_User}'
            if Debug :
                print ( f'{R_FIG}' )
            if not R_GRAF or 'http' in str(R_GRAF) :
                if ccc_home :
                    R_GRAF     = os.path.join ( subprocess.getoutput ('ccc_home --cccwork -d drf -u p86mart'), 'GRAF', 'DATA')
                else        :
                    R_GRAF     = '/ccc/store/cont003/drf/p86mart'
            if Debug :
                print ( f'{R_GRAF}' )
            if not DB          :
                if ccc_home :
                    DB         = os.path.join ( subprocess.getoutput ('ccc_home --cccwork -d igcmg -u igcmg'), 'database')
                else        :
                    DB         = '/ccc/store/cont003/igcmg/igcmg/database'
            if Debug :
                print ( f'{DB}' )

                
                    
            if not rebuild :
                rebuild = os.path.join ( subprocess.getoutput ('ccc_home --ccchome -d igcmg -u igcmg' ),
                    'Tools', 'irene', 'rebuild_nemo', 'bin', 'rebuild_nemo' )
                
            if not TmpDir :
                if ccc_home :
                    TmpDir = subprocess.getoutput ('ccc_home --cccscratch')
                else        :
                    TmpDir = f'/ccc/scratch/cont003/{TGCC_Group}/{TGCC_User}'
                
        # ===========================================================================================
        if MASTER in ['SpiritJ', 'SpiritX', 'Spirit'] :
            if not IGCM_OUT_name :
                IGCM_OUT_name = ''
                    
            if not User  :
                if TGCC_User  :
                    User = TGCC_User
                else          :
                    User = LocalUser
            if not ARCHIVE    :
                ARCHIVE    = os.path.join ( '/', 'thredds', 'tgcc', 'store', User )
            if not  STORAGE   :
                STORAGE    = os.path.join ( '/', 'thredds', 'tgcc', 'work' , User )
            if not R_IN       :
                R_IN       = os.path.join ( '/', 'projsu', 'igcmg', 'IGCM' )
            #if not R_GRAF     : R_GRAF     = os.path.join ('/', 'data', 'omamce', 'GRAF', 'DATA' )
            if not R_GRAF or 'http' in str(R_GRAF) :
                R_GRAF     = os.path.join  ( '/', 'thredds', 'tgcc', 'work', 'p86mart', 'GRAF', 'DATA' )
            if not DB         :
                DB         = os.path.join  ( '/', 'data', 'igcmg', 'database' )
            if not TmpDir     :
                if MASTER in ['SpiritJ',] :
                    TmpDir = os.path.join ( '/', 'scratchu', LocalUser )
                if MASTER in ['SpiritX',] :
                    TmpDir = os.path.join ( '/', 'scratchx', LocalUser )
   
        # ===========================================================================================
        if MASTER == 'Jean-Zay' :
            if not User  :
                User  = os.environ ['USER']
            LocalGroup = os.path.basename ( os.path.dirname ( os.path.expanduser ('~') ))
            if not Group :
                Group = LocalGroup

            if not Source :
                IGCM_OUT_name = 'IGCM_OUT'

            if not ARCHIVE    :
                ARCHIVE    = os.path.join ( '/', 'gpfsstore'  , 'rech', Group, User )
            if not STORAGE    :
                STORAGE    = os.path.join ( '/', 'gpfswork'   , 'rech', Group, User )
            if not SCRATCHDIR :
                SCRATCHDIR = os.path.join ( '/', 'gpfsscratch', 'rech', Group, User )
            if not R_FIG      :
                R_FIG      = os.path.join ( '/', 'cccwork'    , 'rech', Group, User )
            if not R_BUF      :
                R_BUF      = os.path.join ( '/', 'gpfsscratch', 'rech', Group, User )
            if not R_IN       :
                R_IN       = os.path.join ( '/', 'gpfswork'   , 'rech', 'psl', 'commun', 'IGCM' )
            if not R_GRAF     :
                R_GRAF     = os.path.join ( '/', 'gpfswork'   , 'rech', Group, User, 'GRAF', 'DATA' )
            if not DB         :
                DB         = os.path.join ( '/', 'gpfswork'   , 'rech', 'psl', 'commun', 'database' )
            if not rebuild :
                rebuild = os.path.join ( '/', 'gpfswork', 'rech', 'psl', 'commun', 'Tools',
                                            'rebuild', 'modipsl_IOIPSL_PLUS_v2_2_4', 'bin', 'rebuild' )
            if not TmpDir :
                TmpDir = os.path.join ( '/', 'gpfsscratch', 'rech',
                                os.path.basename ( os.path.dirname ( os.path.expanduser ('~') )), LocalUser )
                
        ### ===========================================================================================
        ### The construction of the following variables is not machine dependant
        ### ===========================================================================================
        if SpaceName == 'TEST' :
            if SCRATCHDIR and not R_OUT :
                R_OUT = SCRATCHDIR
            if SCRATCHDIR and not R_FIG :
                R_FIG = SCRATCHDIR
        else  :
            if ARCHIVE    and not R_OUT :
                R_OUT = ARCHIVE
            if STORAGE    and not R_FIG :
                R_FIG = STORAGE
        if R_OUT and IGCM_OUT_name :
            R_OUT = os.path.join ( R_OUT, IGCM_OUT_name )
        if R_FIG and IGCM_OUT_name :
            R_FIG = os.path.join ( R_FIG, IGCM_OUT_name )
            
        if SCRATCHDIR and not R_BUF and IGCM_OUT_name :
            R_BUF  = os.path.join ( SCRATCHDIR, IGCM_OUT_name )
        if not IGCM_OUT :
            IGCM_OUT = R_OUT
            
        if TagName and SpaceName and ExperimentName and JobName :
            if not L_EXP :
                L_EXP = os.path.join (TagName, SpaceName, ExperimentName, JobName)

            if Debug :
                print ( f'libIGCM.sys.Config : libIGCM.sys : {R_BUF=}' )
                print ( f'libIGCM.sys.Config : libIGCM.sys : {IGCM_OUT_name=}' )
                print ( f'libIGCM.sys.Config : libIGCM.sys : {L_EXP=}' )
                
            if R_OUT and not R_SAVE :
                R_SAVE      = os.path.join ( R_OUT  , L_EXP )
            if IGCM_OUT_name :
                if STORAGE and not R_FIGR :
                    R_FIGR      = os.path.join (STORAGE, IGCM_OUT_name, L_EXP)
            else :
                if STORAGE and not R_FIGR  :
                    R_FIGR      = os.path.join ( STORAGE, L_EXP )
            if R_BUF   and not R_BUFR and IGCM_OUT_name and L_EXP :
                R_BUFR      = os.path.join ( R_BUF  , IGCM_OUT_name, L_EXP )
            if R_BUFR  and not R_BUF_KSH   :
                R_BUF_KSH   = os.path.join ( R_BUFR , 'Out' )
            if R_BUF   and not REBUILD_DIR :
                REBUILD_DIR = os.path.join ( R_BUF  , L_EXP, 'REBUILD' )
            if R_BUF   and not POST_DIR    :
                POST_DIR    = os.path.join ( R_BUF  , L_EXP, 'Out' )
            if STORAGE and not CMIP6_BUF and IGCM_OUT_name  :
                CMIP6_BUF   = os.path.join ( STORAGE, IGCM_OUT_name )

        ### =========
        if isinstance (Line, dict) :
            if OPTIONS['Debug'] or Debug : # type: ignore
                print ( f'{type(Line) = } - {Line =}' )
            if "color" in Line.keys () : 
                if isinstance (Line["color"], list) :
                    Line["color"] = np.array (Line["color"])
                    if isinstance (Line["color"], np.ndarray) :
                        if np.max (Line["color"]) > 1.0 :
                            Line["color"] = Line["color"] / 255.
            else :
                Line['color'] = 'black'
            if 'style' not in Line.keys() :
                Line['style']='solid'
        else :
            Line = dict (color='black', style='solid')
                                                 
        if Marker is None :
            Marker = dict (marker='D', fillstyle='full' )
        else : 
            if isinstance (Marker, dict) :
                if "marker" not in Marker.keys () :
                    Marker['marker']='D'
                if "fillstyle" not in Marker.keys() :
                    Marker['fillstyle']='full'

        if Shading is not None :
            if isinstance (Shading, list) :
                Shading = np.array (Shading)
            if isinstance (Shading, np.ndarray) :
                if np.max (Shading) > 1.0 :
                    Shading = Shading / 255.
                
        ### ===========================================================================================
        ## Builds the class attributes
        
        self.TagName             = TagName
        self.SpaceName           = SpaceName
        self.ExperimentName      = ExperimentName
        self.JobName             = JobName
        self.LongName            = LongName
        self.ModelName           = ModelName
        self.ShortName           = ShortName
        self.Comment             = Comment
        self.ConfigCard          = ConfigCard
        self.DateBegin           = DateBegin
        self.DateEnd             = DateEnd
        self.YearBegin           = YearBegin
        self.YearEnd             = YearEnd
        self.PeriodLength        = PeriodLength
        self.SeasonalFrequency   = SeasonalFrequency
        self.CalendarType        = CalendarType
        self.DateBeginGregorian  = DateBeginGregorian
        self.DateEndGregorian    = DateEndGregorian
        self.FullPeriod          = FullPeriod
        self.RunCard             = RunCard
        self.ARCHIVE             = ARCHIVE
        self.STORAGE             = STORAGE
        self.SCRATCHDIR          = SCRATCHDIR
        self.R_OUT               = R_OUT
        self.R_BUF               = R_BUF
        self.R_GRAF              = R_GRAF
        self.DB                  = DB
        self.IGCM_OUT            = IGCM_OUT
        self.R_SAVE              = R_SAVE
        self.R_FIGR              = R_FIGR
        self.R_BUFR              = R_BUFR
        self.REBUILD_DIR         = REBUILD_DIR
        self.POST_DIR            = POST_DIR
        self.R_IN                = R_IN
        self.MASTER              = MASTER
        self.Source              = Source
        self.User                = User
        self.Group               = Group
        self.IGCM_OUT_name       = IGCM_OUT_name
        self.rebuild             = rebuild
        self.TmpDir              = TmpDir
        self.TGCC_User           = TGCC_User
        self.TGCC_Group          = TGCC_Group
        self.IDRIS_User          = IDRIS_User
        self.IDRIS_Group         = IDRIS_Group
        self.TGCC_DapPrefix      = TGCC_DapPrefix
        self.IDRIS_DapPrefix     = IDRIS_DapPrefix
        self.TGCC_ThreddsPrefix  = TGCC_ThreddsPrefix
        self.IDRIS_ThreddsPrefix = IDRIS_ThreddsPrefix
        self.DapPrefix           = DapPrefix
        self.ThreddsPrefix       = ThreddsPrefix
        self.CMIP6_BUF           = CMIP6_BUF
        self.Debug               = Debug
        self.DatePattern         = DatePattern
        self.Period              = Period
        self.PeriodSE            = PeriodSE
        self.Shading             = Shading
        self.Line                = Line
        self.Marker              = Marker
        self.OCE                 = OCE
        self.ATM                 = ATM

        ### ===========================================================================================
        ## Add user defined attributes
        if kwargs :
            for attr, value in kwargs.items() :
                super().__setattr__(attr, value)

        ### ===========================================================================================
        ## Add custom attributes
        return None
        
### ===========================================================================
def Dap2Thredds (file:str, mm:Union[Config,None]=None) :
    '''
    ! Convert a Dap URL to http URL
    '''
    push_stack ( f'Dap2Thredds ({file=}, {mm=})'  )
    replaced = False
    zfile    = file
    
    if mm : 
        if not replaced and mm.DapPrefix       and mm.ThreddsPrefix       :
                zfile = zfile.replace (mm.DapPrefix       , mm.ThreddsPrefix      )
                replaced = True
        if not replaced and mm.TGCC_DapPrefix  and mm.TGCC_ThreddsPrefix  :
                zfile = zfile.replace (str(mm.TGCC_DapPrefix), str(mm.TGCC_ThreddsPrefix) )
                replaced = True
        if not replaced and mm.IDRIS_DapPrefix and mm.IDRIS_ThreddsPrefix :
            zfile = zfile.replace (str(mm.IDRIS_DapPrefix) , str(mm.IDRIS_ThreddsPrefix))
            replaced = True
            
    if not replaced : 
        zfile = zfile.replace ('dodsC', 'fileServer')


    pop_stack ( f'Dap2Thredds -> {zfile=}' )
    return zfile
