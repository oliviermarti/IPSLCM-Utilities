# -*- coding: utf-8 -*-
'''
Defines libIGCM directories, depending of the computer

olivier.marti@lsce.ipsl.fr

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
  personal.

SVN information
 $Author:  $
 $Date:  $
 $Revision:  $
 $Id:  $
 $HeadURL:  $
'''

import os, subprocess, configparser, types, sys

import warnings
from typing import TYPE_CHECKING, Literal, TypedDict

Stack = list()
# Where do we run ?
SysName, NodeName, Release, Version, Machine = os.uname ()

def Mach (long:bool=False) -> str :
    '''
    Find the computer we are on
    On Irene, Mach returns Irene, Irene-Next, Rome or Rome-Prev if long==True
    '''

    zmach = None

    if SysName == 'Darwin' and ( 'lsce5138' in NodeName or 'sargas028' in NodeName ) : zmach = 'Spip'
    if 'obelix'    in NodeName : zmach = 'Obelix'
    if 'jupyter'   in NodeName and "/home/users/" in os.path.abspath ("")  : zmach = 'Obelix'
    if 'forge'     in NodeName : zmach = 'Forge'
    if 'ciclad'    in NodeName : zmach = 'Ciclad'
    if 'climserv'  in NodeName : zmach = 'SpiritX'
    if 'spirit'    in NodeName : zmach = 'SpiritJ'
    if 'spiritj'   in NodeName : zmach = 'SpiritJ'
    if 'spiritx'   in NodeName : zmach = 'SpiritX'
    if 'irene'     in NodeName : zmach = 'Irene'
    if 'jean-zay'  in NodeName : zmach = 'Jean-Zay'

    if long :
        zmachfull = zmach

        if zmach == 'Irene' :
            CPU    = subprocess.getoutput ('lscpu')
            ccc_os = subprocess.getoutput ('ccc_os')

            if "Intel(R) Xeon(R) Platinum" in CPU :
                zmachfull = 'Irene'

            if "AMD" in CPU : zmachfull = 'Rome'

        zmach = zmachfull

    return zmach


MASTER = Mach (long=False)

# libIGCM_sys internal options
if TYPE_CHECKING :
    Options = Literal ["Debug", 'TGCC_User', 'TGCC_Group', 'IDRIS_User', 'IDRIS_Group', 'TGCC_ThreddsPrefix', 'IDRIS_ThreddsPrefix', 'Trace', 'Stack']

    class T_Options (TypedDict) :
        TGCC_User           = 'p86mart'
        TGCC_Group          = 'gen12006'
        IDRIS_User          = 'rces009'
        IDRIS_Group         = 'ces'
        TGCC_ThreddsPrefix  = 'https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds'
        IDRIS_ThreddsPrefix = 'https://thredds-su.ipsl.fr/thredds/dodsC/idris_thredds'
        Stack               = list()
        
OPTIONS = { 'Debug'              : False,
            'Trace'              : False,
            'TGCC_User'          : 'p86mart',
            'TGCC_Group'         : 'gen12006',
            'IDRIS_User'         : 'rces009',
            'IDRIS_Group'        : 'ces',
            'TGCC_ThreddsPrefix' : 'https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds',
            'IDRIS_ThreddsPrefix': 'https://thredds-su.ipsl.fr/thredds/dodsC/idris_thredds',
            'Stack'              : list(),
            }

class set_options :
    """
    Set options for libIGCM_sys
    """
    def __init__ (self, **kwargs) :
        self.old = {}
        for k, v in kwargs.items () :
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update (kwargs)

    def _apply_update (self, options_dict) : OPTIONS.update (options_dict)
    def __enter__ (self) : return
    def __exit__ (self, type, value, traceback) : self._apply_update (self.old)

def get_options () :
    """
    Get options for libIGCM_sys

    See Also
    ----------
    set_options

    """
    return OPTIONS

def return_stack () :
    return Stack

def PushStack (string:str) :
    OPTIONS['Depth'] += 1
    if OPTIONS['Trace'] : print ( '  '*OPTIONS['Depth'], '-->libIGCM_date: ', string)
    Stack.append (string)
    return

def PopStack (string:str) :
    if OPTIONS['Trace'] : print ( '  '*OPTIONS['Depth'], '<--libIGCM_date: ', string)
    OPTIONS['Depth'] -= 1
    Stack.pop ()
    return

# Where do we run ?
SysName, NodeName, Release, Version, Machine = os.uname ()

# def unDefined (char: str) -> bool :
#     '''Returns True if a variable is not defined, ot if it's set to None'''
#     if char in globals () :
#         if globals ()[char] == None or  globals ()[char] == 'None': unDefined = True
#         else                                                      : unDefined = False
#     else : unDefined = True
#     return unDefined


#@classmethod
#def from_dict (cls, data_dict) :
#    return cls ( **data_dict )

class config :
    '''
    Defines the libIGCM directories
        
    Source : for Spip
    Possibilities :
        Local        : local (~/Data/IGCMG/...)
        TGCC_sshfs   : TGCC disks mounted via sshfs
        TGCC_thredds : thredds TGCC via IPSL
              ('https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds/store/...)       
    '''
    ## Public functions
    def update (self, dico):
        '''Use a dictionnary to update values'''
        for attr in dico.keys () :
            super().__setattr__(attr, dico[attr])

    def setattr (self, attr, value) : super().__setattr__(attr, value)

    ## Hidden functions
    def __str__     (self) : return str (self.__dict__)
    def __repr__    (self) : return str (self.__dict__)
    def __name__    (self) : return self.__class__.__name__
    def __getitem__ (self, attr) : return getattr (self, attr)
    def __setitem__ (self, attr, value) : setattr (self, attr, value)
    def __iter__    (self) : return self
    def __next__    (self) :
        if self.index == 0 : raise StopIteration
        self.index = self.index - 1
        return self.data[self.index]

    def __init__ (self, JobName=None, TagName=None, SpaceName=None, ExperimentName=None,
                  LongName=None, ModelName=None, ShortName=None,
                  Source=None, MASTER=None, ConfigCard=None, RunCard=None, User=None, Group=None,
                  TGCC_User=None, TGCC_Group=None, IDRIS_User=None, IDRIS_Group=None,
                  ARCHIVE=None, SCRATCHDIR=None, STORAGE=None, R_IN=None, R_OUT=None,
                  R_FIG=None, L_EXP=None,
                  R_SAVE=None, R_FIGR=None, R_BUF=None, R_BUFR=None, R_BUF_KSH=None,
                  REBUILD_DIR=None, POST_DIR=None,
                  ThreddsPrefix=None, R_GRAF=None, DB=None,
                  IGCM_OUT=None, IGCM_OUT_name=None, rebuild=None, TmpDir=None,
                  Debug=None, TGCC_ThreddsPrefix=None, IDRIS_ThreddsPrefix=None, CMIP6_BUF=None ) :
   

        if not Debug               : Debug               = OPTIONS['Debug']
        if not TGCC_User           : TGCC_User           = OPTIONS['TGCC_User']
        if not TGCC_Group          : TGCC_Group          = OPTIONS['TGCC_Group']
        if not IDRIS_User          : IDRIS_User          = OPTIONS['IDRIS_User']
        if not IDRIS_Group         : IDRIS_Group         = OPTIONS['IDRIS_Group']
        if not TGCC_ThreddsPrefix  : TGCC_ThreddsPrefix  = OPTIONS['TGCC_ThreddsPrefix']
        if not IDRIS_ThreddsPrefix : IDRIS_ThreddsPrefix = OPTIONS['IDRIS_ThreddsPrefix']

        if not MASTER : MASTER = Mach (long=False)
        if not MASTER : MASTER = 'Unknown'
            
        LocalUser = os.environ ['USER']

        if Debug :
            print ( f'libIGCM_sys : {MASTER=}' )
            print ( f'libIGCM_sys : {LocalUser=}' )
            
        # ===========================================================================================
        # Reads config.card if available
        if ConfigCard :
            # Text existence of ConfigCard
            if not os.path.exists (ConfigCard ) :
                raise FileExistsError ( f"File not found : {ConfigCard = }" )
                
            ## Creates parser for reading .ini input file
            MyReader = configparser.ConfigParser (interpolation=configparser.ExtendedInterpolation() )
            MyReader.optionxform = str # To keep capitals
            
            MyReader.read (ConfigCard)
            
            JobName        = MyReader['UserChoices']['JobName']
            #----- Short Name of Experiment
            ExperimentName = MyReader['UserChoices']['ExperimentName']
            #----- DEVT TEST PROD
            SpaceName      = MyReader['UserChoices']['SpaceName']
            LongName       = MyReader['UserChoices']['LongName']
            ModelName      = MyReader['UserChoices']['ModelName']
            TagName        = MyReader['UserChoices']['TagName']


        # Reads run.card if available
        if RunCard :
            # Text existence of RunCard
            if not os.path.exists (RunCard ) :
                raise FileExistsError ( f"File not found : {RunCard = }" )
                
            ## Creates parser for reading .ini input file
            MyReader = configparser.ConfigParser (interpolation=configparser.ExtendedInterpolation() )
            MyReader.optionxform = str # To keep capitals
            
            MyReader.read (ConfigCard)

            PeriodDateBegin= MyReader['Configuration']['PeriodDateBegin']
            PeriodDateEnd  = MyReader['Configuration']['PeriodDateEnd']
            CumulPeriod    = MyReader['Configuration']['CumulPeriod']
            PeriodState    = MyReader['Configuration']['PeriodState']

        ### ===========================================================================================
        ## Part specific to access by OpenDAP/Thredds server
        
        # ===========================================================================================
        if Source == 'TGCC_thredds' :
            if not User  and TGCC_User  : User  = TGCC_User
            if not Group and TGCC_Group : Group = TGCC_Group
                
            if not ThreddsPrefix : ThreddsPrefix = OPTIONS['TGCC_ThreddsPrefix']
               
            if not ARCHIVE : ARCHIVE = f'{ThreddsPrefix}/store/{TGCC_User}'
            if not R_FIG   : R_FIG   = f'{ThreddsPrefix}/work/{TGCC_User}'
            if not R_IN    : R_IN    = f'{ThreddsPrefix}/work/igcmg/IGCM'
            if not R_GRAF  : R_GRAF  = f'{ThreddsPrefix}/work/p86mart/GRAF/DATA'
                
        # ===========================================================================================
        if Source == 'IDRIS_thredds' :
            if not User  and IDRIS_User  : User  = IDRIS_User
            if not Group and IDRIS_Group : Group = IDRIS_Group
                
            if not ThreddsPrefix : ThreddsPrefix = OPTIONS['IDRIS_ThreddsPrefix']
                
            if not ARCHIVE : ARCHIVE = f'{ThreddsPrefix}/store/{IDRIS_User}'
            if not R_FIG   : R_FIG   = f'{ThreddsPrefix}/work/{IDRIS_User}'
            if not R_IN    : R_IN    = f'{ThreddsPrefix}/work/igcmg/IGCM'
            if not R_GRAF  : R_GRAF  = 'https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds/work/p86mart/GRAF/DATA'
              
        ### ===========================================================================================
        ## Machine dependant part
        
        # ===========================================================================================
        if MASTER == 'Obelix' :
            if not User   : User = LocalUser
            if Source : IGCM_OUT_name = ''
            else      : IGCM_OUT_name = 'IGCM_OUT'
            if not ARCHIVE    : ARCHIVE     = os.path.join ( os.path.expanduser ('~'), 'Data' )
            if not SCRATCHDIR : SCRATCHDIR  = os.path.join ( os.path.expanduser ('~'), 'Scratch' )
            if not R_BUF      : R_BUF       = os.path.join ( os.path.expanduser ('~'), 'Scratch' )
            if not R_FIG      : R_FIG       = os.path.join ( os.path.expanduser ('~'), 'Data'    )
                
            if not STORAGE    : STORAGE     = ARCHIVE
            if not R_IN       : R_IN        = os.path.join ( '/home', 'orchideeshare', 'igcmg', 'IGCM' )
            if not R_GRAF     : R_GRAF      = os.path.join ( os.path.expanduser ('~marti'), 'GRAF', 'DATA' )
            if not DB         : DB          = os.path.join ( '/home', 'biomac1', 'geocean', 'ocmip'   )
            if not TmpDir     : TmpDir      = os.path.join ( os.path.expanduser ('~'), 'Scratch' )
                
        # ===========================================================================================
        if MASTER == 'Spip' :
            if not User   : User = LocalUser
            if Source : IGCM_OUT_name = ''
            else      : IGCM_OUT_name = 'IGCM_OUT'
            if not ARCHIVE    : ARCHIVE     = os.path.join ( os.path.expanduser ('~'), 'Data'    )
            if not SCRATCHDIR : SCRATCHDIR  = os.path.join ( os.path.expanduser ('~'), 'Data' )
            if not R_BUF      : R_BUF       = os.path.join ( os.path.expanduser ('~'), 'Data'    )
            if not R_FIG      : R_FIG       = os.path.join ( os.path.expanduser ('~'), 'Data'    )
                
            if not STORAGE    : STORAGE     = ARCHIVE
            if not R_IN       : R_IN        = os.path.join ( os.path.expanduser ('~'), 'Data', 'IGCM' )
            if not R_GRAF     : R_GRAF      = os.path.join ( os.path.expanduser ('~'), 'GRAF', 'DATA' )
            if not DB         : DB          = os.path.join ( os.path.expanduser ('~'), 'marti', 'GRAF', 'DB' )
            if not TmpDir     : TmpDir      = os.path.join ( os.path.expanduser ('~'), 'Scratch' )
                
        # ===========================================================================================
        if ( 'Irene' in MASTER ) or ( 'Rome' in MASTER ) :
        
            LocalHome  = subprocess.getoutput ( 'ccc_home --ccchome' )
            LocalGroup = os.path.basename ( os.path.dirname (LocalHome))
            if not User or User == 'marti' :
                if not TGCC_User : User = LocalUser
                else             : User = TGCC_User
                    
            if not Group :
                if TGCC_Group : Group = TGCC_Group
                else          : Group = LocalGroup
                    
            if not Source : IGCM_OUT_name = 'IGCM_OUT'
            
            if not R_IN        :
                R_IN       = os.path.join ( subprocess.getoutput (
                    'ccc_home --cccwork -d igcmg -u igcmg' ), 'IGCM')
            if not ARCHIVE     :
                ARCHIVE    = subprocess.getoutput (
                    f'ccc_home --cccstore   -u {User} -d {Group}' )
            if not STORAGE     :
                STORAGE    = subprocess.getoutput (
                    f'ccc_home --cccwork    -u {User} -d {Group}' )
            if not SCRATCHDIR  :
                SCRATCHDIR = subprocess.getoutput (
                    f'ccc_home --cccscratch -u {User} -d {Group}' )
            if not R_BUF       :
                R_BUF      = subprocess.getoutput (
                    f'ccc_home --cccscratch -u {User} -d {Group}' )
            if not R_FIG       :
                R_FIG      = subprocess.getoutput (
                    f'ccc_home --cccwork    -u {User} -d {Group}' )
            if not R_GRAF      :
                R_GRAF     = os.path.join ( subprocess.getoutput (
                    'ccc_home --cccwork -d drf -u p86mart'), 'GRAF', 'DATA' )
            if not DB          :
                DB         = os.path.join ( subprocess.getoutput (
                    'ccc_home --cccwork -d igcmg -u igcmg'), 'database' )
            if not rebuild :
                rebuild = os.path.join (
                    subprocess.getoutput ( 'ccc_home --ccchome -d igcmg -u igcmg' ),
                    'Tools', 'irene', 'rebuild_nemo', 'bin', 'rebuild_nemo' )
                
            if not TmpDir : TmpDir = subprocess.getoutput ( f'ccc_home --cccscratch' )
                
        # ===========================================================================================
        if MASTER == ['SpiritJ', 'SpiritX', 'Spirit'] :
            if not User  :
                if TGCC_User  : User = TGCC_User
                else          : User = LocalUser
            if not ARCHIVE    :
                ARCHIVE    = os.path.join ( '/', 'thredds', 'tgcc', 'store', User )
            if not  STORAGE   :
                STORAGE    = os.path.join ( '/', 'thredds', 'tgcc', 'work' , User )
            if not R_IN       :
                R_IN       = os.path.join ( '/', 'projsu', 'igcmg', 'IGCM' )
            #if not R_GRAF     : R_GRAF     = os.path.join ('/', 'data', 'omamce', 'GRAF', 'DATA' )
            if not R_GRAF     :
                R_GRAF     = os.path.join  ( '/', 'thredds', 'tgcc', 'work', 'p86mart', 'GRAF', 'DATA' )
            if not DB         :
                DB         = os.path.join  ( '/', 'data', 'igcmg', 'database' )
            if not TmpDir     :
                if MASTER == ['SpiritJ'] : TmpDir = os.path.join ( '/', 'data'    , LocalUser )
                if MASTER == ['SpiritX'] : TmpDir = os.path.join ( '/', 'scratchx', LocalUser )
   
        # ===========================================================================================
        if MASTER == 'Jean-Zay' :
            if not User  : User  = os.environ ['USER']
            LocalGroup = os.path.basename ( os.path.dirname ( os.path.expanduser ('~') ))
            if not Group : Group = LocalGroup

            if not Source : IGCM_OUT_name = 'IGCM_OUT'

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
            if not TmpDir : TmpDir = os.path.join ( '/', 'gpfsscratch', 'rech',
                                os.path.basename ( os.path.dirname ( os.path.expanduser ('~') )), LocalUser )
                
        ### ===========================================================================================
        ### The construction of the following variables is not machine dependant
        ### ===========================================================================================
        if SpaceName == 'TEST' :
            if SCRATCHDIR and not R_OUT : R_OUT = SCRATCHDIR
            if SCRATCHDIR and not R_FIG : R_FIG = SCRATCHDIR
        else  :
            if ARCHIVE    and not R_OUT : R_OUT = ARCHIVE
            if STORAGE    and not R_FIG : R_FIG = STORAGE
        if IGCM_OUT_name :
            R_OUT = os.path.join ( R_OUT, IGCM_OUT_name )
            R_FIG = os.path.join ( R_FIG, IGCM_OUT_name )
            
        if SCRATCHDIR and not R_BUF : R_BUF  = os.path.join ( SCRATCHDIR, IGCM_OUT_name )
        if not IGCM_OUT : IGCM_OUT = R_OUT
            
        if TagName and SpaceName and ExperimentName and JobName :
            if not L_EXP : L_EXP = os.path.join ( TagName, SpaceName, ExperimentName, JobName )

            if Debug :
                print ( f'libIGCM_sys : {R_BUF=}' )
                print ( f'libIGCM_sys : {IGCM_OUT_name=}' )
                print ( f'libIGCM_sys : {L_EXP=}' )
                
            if R_OUT and not R_SAVE : R_SAVE      = os.path.join ( R_OUT  , L_EXP )
            if IGCM_OUT_name :
                if STORAGE and not R_FIGR : R_FIGR      = os.path.join ( STORAGE, IGCM_OUT_name, L_EXP )
            else :
                if STORAGE and not R_FIGR  : R_FIGR      = os.path.join ( STORAGE, L_EXP )
            if R_BUF   and not R_BUFR      : R_BUFR      = os.path.join ( R_BUF  , IGCM_OUT_name, L_EXP )
            if R_BUFR  and not R_BUF_KSH   : R_BUF_KSH   = os.path.join ( R_BUFR , 'Out' )
            if R_BUF   and not REBUILD_DIR : REBUILD_DIR = os.path.join ( R_BUF  , L_EXP, 'REBUILD' )
            if R_BUF   and not POST_DIR    : POST_DIR    = os.path.join ( R_BUF  , L_EXP, 'Out' )
            if STORAGE and not CMIP6_BUF   : CMIP6_BUF   = os.path.join ( STORAGE, IGCM_OUT_name )
                
        ### ===========================================================================================
        ## Builds the class attributes
        
        self.TagName             = TagName
        self.SpaceName           = SpaceName
        self.ExperimentName      = ExperimentName
        self.JobName             = JobName
        self.LongName            = LongName
        self.ModelName           = ModelName
        self.ShortName           = ShortName
        self.ConfigCard          = ConfigCard
        self.RunCard             = RunCard
        self.ARCHIVE             = ARCHIVE
        self.STORAGE             = STORAGE
        self.SCRATCHDIR          = SCRATCHDIR
        self.R_OUT               = R_OUT
        self.R_BUF               = R_BUFR
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
        self.ThreddsPrefix       = ThreddsPrefix
        self.IDRIS_User          = IDRIS_User
        self.IDRIS_Group         = IDRIS_Group
        self.TGCC_ThreddsPrefix  = TGCC_ThreddsPrefix
        self.IDRIS_ThreddsPrefix = IDRIS_ThreddsPrefix
        self.CMIP6_BUF           = CMIP6_BUF
        self.Debug               = Debug
        

 
