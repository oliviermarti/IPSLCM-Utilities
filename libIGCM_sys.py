# -*- coding: utf-8 -*-
## ===========================================================================
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
## ===========================================================================
'''
Defines libIGCM directories, depending of the computer

olivier.marti@lsce.ipsl.fr
'''

import os
import subprocess
import configparser
import types
from pathlib import Path

# Where do we run ?
SysName, NodeName, Release, Version, Machine = os.uname ()

def unDefined (char) :
    '''Returns True if a variable is not defined, ot if it's set to None'''
    if char in globals () :
        if globals ()[char] is None or globals ()[char] == 'None':
            zunDefined = True
        else :
            zunDefined = False
    else :
        zunDefined = True

    return zunDefined

def Mach ( Long=False) :
    '''
    Find the computer we are on

    On Irene, Mach returns Irene, Irene-Next, Rome or Rome-Prev if Long==True
    '''

    zMach = 'unknown'

    if SysName == 'Darwin' and 'lsce5138' in NodeName : zMach = 'Spip'
    if 'obelix'    in NodeName : zMach = 'Obelix'
    if 'forge'     in NodeName : zMach = 'Forge'
    if 'ciclad'    in NodeName : zMach = 'Ciclad'
    if 'climserv'  in NodeName : zMach = 'SpiritX'
    if 'spirit'    in NodeName : zMach = 'SpiritJ'
    if 'spiritj'   in NodeName : zMach = 'SpiritJ'
    if 'spiritx'   in NodeName : zMach = 'SpiritX'
    if 'irene'     in NodeName : zMach = 'Irene'
    if 'jean-zay'  in NodeName : zMach = 'Jean-Zay'

    if Long :
        zMachFull = zMach

        if zMach == 'Irene' :
            CPU    = subprocess.getoutput ('lscpu')
            ccc_os = subprocess.getoutput ('ccc_os')

            if "Intel(R) Xeon(R) Platinum" in CPU :
                if "Atos_7__x86_64" in ccc_os : zMachFull = 'Irene-Prev'
                if "Rhel_8__x86_64" in ccc_os : zMachFull = 'Irene'

            if "AMD" in CPU :
                if "Atos_7__x86_64" in ccc_os : zMachFull = 'Rome-Prev'
                if "Rhel_8__x86_64" in ccc_os : zMachFull = 'Rome'

        zMach = zMachFull

    return zMach

def config ( JobName=None , TagName=None  , SpaceName=None, ExperimentName=None,
             LongName=None, ModelName=None, ShortName=None,
             Source=None  , Host=None     , ConfigCard=None, User=None, Group=None,
             TGCC_User='p86mart', TGCC_Group='gen12006', IDRIS_User='rces009', IDRIS_Group='ces',
             ARCHIVE=None, SCRATCHDIR=None, STORAGE=None, R_IN=None, R_OUT=None,
             R_FIG=None, L_EXP=None,
             R_SAVE=None , R_FIGR=None, R_BUF=None , R_BUFR=None, R_BUF_KSH=None,
             REBUILD_DIR=None, POST_DIR=None,
             ThreddsPrefix=None, R_GRAF=None, DB=None,
             IGCM_OUT=None, IGCM_OUT_name=None, rebuild=None, TmpDir=None,
             Out='dict') :
    '''
    Defines the libIGCM directories - Returns a dictionnary or a namespace

    Source : for Spip
          Possibilities :
          Local        : local (~/Data/IGCMG/...)
          TGCC_sshfs   : TGCC disks mounted via sshfs
          TGCC_thredds : thredds TGCC via IPSL
                ('https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds/store/...)

    Exemple of use :
    libIGCM = libIGCM_sys.config ( .... )
    globals().update ( libIGCM )

    '''

    if not Host : Host = Mach (Long=False)
    LocalUser = os.environ ['USER']

    # ===================================================================
    # Reads config.card if available
    if ConfigCard :
        # Text existence of ConfigCard
        if not os.path.exists (ConfigCard ) :
            raise FileExistsError ( f"File not found : {ConfigCard = }" )

        ## Creates parser for reading .ini input file
        MyReader = configparser.ConfigParser (
                interpolation=configparser.ExtendedInterpolation() )
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

    ### =================================================================
    ## Part specific to access by OpenDAP/Thredds servers

    # ===================================================================
    if Source == 'TGCC_thredds' :
        if not User  and TGCC_User  : User  = TGCC_User
        if not Group and TGCC_Group : Group = TGCC_Group
        if not IGCM_OUT_name : IGCM_OUT_name = '.'

        if not ThreddsPrefix :
            ThreddsPrefix = 'https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds'

        if not ARCHIVE :
            ARCHIVE = f'{ThreddsPrefix}/store/{TGCC_User}'
        if not R_FIG   :
            R_FIG   = f'{ThreddsPrefix}/work/{TGCC_User}'
        if not R_IN    :
            R_IN    = f'{ThreddsPrefix}/work/igcmg/IGCM'
        if not R_GRAF  :
            R_GRAF  = f'{ThreddsPrefix}/work/p86mart/GRAF/DATA'

    # ===================================================================
    if Source == 'IDRIS_thredds' :
        if not User  and IDRIS_User  :
            User  = IDRIS_User
        if not Group and IDRIS_Group :
            Group = IDRIS_Group
        if not IGCM_OUT_name : IGCM_OUT_name = '.'

        if not ThreddsPrefix :
            ThreddsPrefix = 'https://thredds-su.ipsl.fr/thredds/catalog/idris_thredds'

        if not ARCHIVE :
            ARCHIVE = f'{ThreddsPrefix}/store/{IDRIS_User}'
        if not R_FIG   :
            R_FIG   = f'{ThreddsPrefix}/work/{IDRIS_User}'
        if not R_IN    :
            R_IN    = f'{ThreddsPrefix}/work/igcmg/IGCM'
        if not R_GRAF  :
            R_GRAF  =  'https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds/work/p86mart/GRAF/DATA'

    ### =================================================================
    ## Machine dependant part

    # ===================================================================
    if Host == 'Spip' :
        if not User :
            User = LocalUser
        if not IGCM_OUT_name :
            IGCM_OUT_name = 'IGCM_OUT'
        if not ARCHIVE    :
            ARCHIVE    = os.path.join ( Path.home (), 'Data' )
        if not SCRATCHDIR :
            SCRATCHDIR = os.path.join ( Path.home (), 'Scratch' )
        if not R_BUF      :
            R_BUF      = os.path.join ( Path.home (), 'Scratch' )
        if not R_FIG      :
            R_FIG      = os.path.join ( Path.home (), 'Data'    )

        if not STORAGE :
            STORAGE    = ARCHIVE
        if not R_IN    :
            R_IN       = os.path.join ( '/', 'Users', 'marti', 'Data', 'IGCM' )
        if not R_GRAF  :
            R_GRAF     = os.path.join ( '/', 'Users', 'marti', 'GRAF', 'DATA' )
        if not DB      :
            DB         = os.path.join ( '/', 'Users', 'marti', 'GRAF', 'DB'   )
        if not TmpDir  :
            TmpDir     = os.path.join ( '/', 'Users', LocalUser, 'Scratch' )

    # ===================================================================
    if ( 'Irene' in Host ) or ( 'Rome' in Host ) :
        LocalHome  = subprocess.getoutput ( 'ccc_home --ccchome' )
        LocalGroup = os.path.basename ( os.path.dirname (LocalHome))
        if not User or User == 'marti' :
            if not TGCC_User : User = LocalUser
            else             : User = TGCC_User

        if not Group :
            if TGCC_Group : Group = TGCC_Group
            else          : Group = LocalGroup

        if not IGCM_OUT_name : IGCM_OUT_name = 'IGCM_OUT'

        if not R_IN        :
            R_IN       = os.path.join ( subprocess.getoutput (
                'ccc_home --cccwork -d igcmg -u igcmg' ), 'IGCM')
        if not ARCHIVE     :
            ARCHIVE    = subprocess.getoutput ( f'ccc_home --cccstore   -u {User} -d {Group}' )
        if not STORAGE     :
            STORAGE    = subprocess.getoutput ( f'ccc_home --cccwork    -u {User} -d {Group}' )
        if not SCRATCHDIR  :
            SCRATCHDIR = subprocess.getoutput ( f'ccc_home --cccscratch -u {User} -d {Group}' )
        if not R_BUF       :
            R_BUF      = subprocess.getoutput ( f'ccc_home --cccscratch -u {User} -d {Group}' )
        if not R_FIG       :
            R_FIG      = subprocess.getoutput ( f'ccc_home --cccwork    -u {User} -d {Group}' )
        if not R_GRAF      :
            R_GRAF     = os.path.join ( subprocess.getoutput (
                'ccc_home --cccwork -d drf -u p86mart'), 'GRAF', 'DATA' )
        if not DB          :
            DB         = os.path.join ( subprocess.getoutput (
                'ccc_home --cccwork -d igcmg -u igcmg'), 'database' )
        if not rebuild :
            rebuild = os.path.join ( subprocess.getoutput ('ccc_home --ccchome -d igcmg -u igcmg' ),
                                         'Tools', Machine, 'rebuild_nemo', 'bin', 'rebuild_nemo' )
        if not TmpDir      : TmpDir = subprocess.getoutput ( 'ccc_home --cccscratch' )

    # ===================================================================
    if Host == 'SpiritJ' :
        if not User  :
            if TGCC_User  : User = TGCC_User
            else          : User = LocalUser
        IGCM_OUT_name = '.'

        if not ARCHIVE    :
            ARCHIVE  = os.path.join ( '/', 'thredds'  , 'tgcc', 'store', User )
        if not  STORAGE   :
            STORAGE  = os.path.join ( '/', 'thredds'  , 'tgcc', 'work' , User )
        #if not SCRATCHDIR : SCRATCHDIR = os.path.join ( '/', 'thredds'  , 'tgcc', 'store', User )
        if not R_IN    :
            R_IN       = os.path.join ( '/', 'projsu', 'igcmg', 'IGCM' )
        #if not R_GRAF     : R_GRAF     = os.path.join ('/', 'data', 'omamce', 'GRAF', 'DATA' )
        if not R_GRAF   :
            R_GRAF     = os.path.join ( '/', 'thredds' , 'tgcc', 'work' , 'p86mart', 'GRAF', 'DATA' )
        if not DB         :
            DB         = os.path.join ( '/', 'data', 'igcmg', 'database' )
        if not TmpDir     :
            TmpDir = os.path.join ( '/', 'data', LocalUser )

    # ===================================================================
    if Host == 'SpiritX' :
        IGCM_OUT_name = '.'
        if not User  :
            if TGCC_User  : User  = TGCC_User
            else          : User = os.environ ['USER']
        if not ARCHIVE    :
            ARCHIVE    = os.path.join ( '/', 'thredds'  , 'tgcc', 'store', User )
        if not  STORAGE   :
            STORAGE    = os.path.join ( '/', 'thredds'  , 'tgcc', 'work' , User )
        #if not SCRATCHDIR : SCRATCHDIR = os.path.join ( '/', 'thredds'  , 'tgcc', 'store', User )
        if not R_IN       :
            R_IN       = os.path.join ( '/', 'projsu', 'igcmg', 'IGCM' )
        #if not R_GRAF     : R_GRAF     = os.path.join ('/', 'data', 'omamce', 'GRAF', 'DATA' )
        if not R_GRAF     :
            R_GRAF     = os.path.join  ( '/', 'thredds', 'tgcc', 'work' ,
                                             'p86mart', 'GRAF', 'DATA' )
        if not DB         :
            DB         = os.path.join  ( '/', 'data', 'igcmg', 'database' )

    # ===================================================================
    if Host == 'Jean-Zay' :
        if not User  : User  = os.environ ['USER']
        LocalGroup = os.path.basename ( os.path.dirname ( Path.home () ))
        if not Group : Group = LocalGroup

        if not ARCHIVE    :
            ARCHIVE    = os.path.join ( '/', 'gpfsstore'  , 'rech', Group, User )
        if not STORAGE    :
            STORAGE    = os.path.join ( '/', 'gpfswork'   , 'rech', Group, User )
        if not SCRATCHDIR : SCRATCHDIR = os.path.join ( '/', 'gpfsscratch', 'rech', Group, User )
        if not R_FIG      :
            R_FIG      = os.path.join ( '/', 'cccwork'    , 'rech', Group, User )
        if not R_BUF      :
            R_BUF      = os.path.join ( '/', 'gpfsscratch', 'rech', Group, User )
        if not R_IN       :
            R_IN       = os.path.join ( '/', 'gpfswork', 'rech', 'psl', 'commun', 'IGCM' )
        if not R_GRAF     :
            R_GRAF     = os.path.join ( '/', 'gpfswork', 'rech', Group, User, 'GRAF', 'DATA' )
        if not DB         :
            DB         = os.path.join ( '/', 'gpfswork', 'rech', 'psl', 'commun', 'database' )
        if not rebuild :
            rebuild = os.path.join ( '/', 'gpfswork', 'rech', 'psl', 'commun', 'Tools', 'rebuild',
                                         'modipsl_IOIPSL_PLUS_v2_2_4', 'bin', 'rebuild' )
        if not TmpDir : TmpDir = os.path.join ( '/', 'gpfsscratch', 'rech',
                               os.path.basename ( os.path.dirname ( Path.home () )), LocalUser )

    ### =================================================================
    ### The construction of the following variables is not machine dependant
    ### =================================================================
    if SpaceName == 'TEST' :
        if SCRATCHDIR and not R_OUT :
            R_OUT = SCRATCHDIR
        if SCRATCHDIR and not R_FIG :
            R_FIG = SCRATCHDIR
    else  :
        if ARCHIVE    and not R_OUT : R_OUT = ARCHIVE
        if STORAGE    and not R_FIG : R_FIG = STORAGE

    if IGCM_OUT_name :
        if IGCM_OUT_name != '.' :
            R_OUT = os.path.join ( R_OUT, IGCM_OUT_name )
            R_FIG = os.path.join ( R_FIG, IGCM_OUT_name )

    if SCRATCHDIR and not R_BUF : R_BUF  = os.path.join ( SCRATCHDIR, IGCM_OUT_name )
    if not IGCM_OUT : IGCM_OUT = R_OUT

    if TagName and SpaceName and ExperimentName and JobName :
        L_EXP = os.path.join ( TagName, SpaceName, ExperimentName, JobName )

        if R_OUT and not R_SAVE :
            R_SAVE      = os.path.join ( R_OUT  , L_EXP )
        if IGCM_OUT_name :
            if STORAGE and not R_FIGR :
                R_FIGR      = os.path.join ( STORAGE, IGCM_OUT_name, L_EXP )
        else :
            if STORAGE and not R_FIGR :
                R_FIGR      = os.path.join ( STORAGE, L_EXP )
        if R_BUF   and not R_BUFR      :
            R_BUFR      = os.path.join ( R_BUF  , L_EXP )
        if R_BUFR  and not R_BUF_KSH   : R_BUF_KSH   = os.path.join ( R_BUFR , 'Out' )
        if R_BUF   and not REBUILD_DIR :
            REBUILD_DIR = os.path.join ( R_BUF  , L_EXP, 'REBUILD' )
        if R_BUF   and not POST_DIR    :
            POST_DIR    = os.path.join ( R_BUF  , L_EXP, 'Out' )

    ### =================================================================
    ## Builds the final dictionnary

    libIGCM = {
        'TagName' : TagName , 'SpaceName' : SpaceName, 'ExperimentName': ExperimentName,
        'JobName':JobName, 'LongName': LongName, 'ModelName' : ModelName, 'ShortName' : ShortName ,
        'ConfigCard'    : ConfigCard,
        'ARCHIVE' : ARCHIVE , 'STORAGE'   : STORAGE  , 'SCRATCHDIR'    : SCRATCHDIR    ,
        'R_OUT'   : R_OUT   , 'R_BUF'     : R_BUFR   , 'R_GRAF'        : R_GRAF        ,
        'DB' : DB, 'IGCM_OUT': IGCM_OUT, 'R_SAVE'    : R_SAVE   , 'R_FIGR'        : R_FIGR ,
        'R_BUFR': R_BUFR, 'REBUILD_DIR': REBUILD_DIR,
        'POST_DIR': POST_DIR, 'R_IN'      : R_IN     , 'Mach'          : Host      ,
        'Source': Source,
        'User'    : User    , 'Group'     : Group    , 'IGCM_OUT_name' : IGCM_OUT_name,
        'rebuild':rebuild, 'TmpDir':TmpDir,
        'TGCC_User':TGCC_User, 'TGCC_Group':TGCC_Group, 'Thredds'      : ThreddsPrefix,
        'IDRIS_User':IDRIS_User, 'IDRIS_Group':IDRIS_Group,
        }

    if Out in ['namespace', 'space', 'name', 'Space', 'Name', 'Names', 'NameSpace'] :
        libIGCM = types.SimpleNamespace (**libIGCM)

    return libIGCM
