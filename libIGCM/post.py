#!/usr/bin/env python3
'''
This library provides some utilities for post processing

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
personal.
'''

import os
from typing import Self, Dict
import json
import cftime
import numpy as np
import xarray as xr
import re

import libIGCM
from libIGCM.options import get_options
from libIGCM.options import push_stack
from libIGCM.options import pop_stack

class Config (libIGCM.sys.Config) :
    '''
    Defines the libIGCM directories and simulations characteristics

    Overload libIGCM.sys.Config to add knowldege about some simulations
    described in a catalog (at json format)
    '''
    def __init__ (self:Self,
                  JobName:str|None=None, TagName:str|None=None, SpaceName:str|None=None, ExperimentName:str|None=None,
                  LongName:str|None=None, ModelName:str|None=None, ShortName:str|None=None, LongtName:str|None=None, Comment:str|None=None,
                  Source:str|None=None, MASTER:str|None=None,
                  ConfigCard:str|None=None, RunCard:str|None=None,
                  User:str|None=None, Group:str|None=None, LocalGroup:str|None=None,
                  TGCC_User:str|None=None, TGCC_Group:str|None=None,
                  IDRIS_User:str|None=None, IDRIS_Group:str|None=None,
                  ARCHIVE:str|None=None, SCRATCHDIR:str|None=None,
                  STORAGE:str|None=None,
                  R_IN:str|None=None, R_OUT:str|None=None, R_FIG:str|None=None,
                  L_EXP:str|None=None,
                  R_SAVE:str|None=None, R_FIGR:str|None=None, R_BUF:str|None=None,
                  R_BUFR:str|None=None, R_BUF_KSH:str|None=None,
                  REBUILD_DIR:str|None=None, POST_DIR:str|None=None,
                  ThreddsPrefix:str|None=None, DapPrefix:str|None=None, SshPrefix:str|None=None,
                  R_GRAF:str|None=None,
                  DB:str|None=None,
                  IGCM_OUT:str|None=None, IGCM_OUT_name:str|None=None,
                  rebuild:str|None=None, TmpDir:str|None=None,
                  TGCC_ThreddsPrefix:str|None=None, TGCC_DapPrefix:str|None=None, TGCC_SshPrefix:str|None=None,
                  IDRIS_ThreddsPrefix:str|None=None, IDRIS_DapPrefix:str|None=None, IDRIS_SshPrefix:str|None=None,
                  DateBegin:str|None=None, DateEnd:str|None=None, YearBegin:str|None=None,
                  YearEnd:str|None=None, PeriodLength:str|None=None,
                  SeasonalFrequency:str|None=None, CalendarType:str|None=None,
                  DateBeginGregorian:str|None=None, DateEndGregorian:str|None=None,
                  FullPeriod:str|None=None, DatePattern:str|None=None,
                  Period:str|None=None, PeriodSE:str|None=None, CumulPeriod:str|None=None,
                  PeriodState:str|None=None,
                  PeriodDateBegin:str|None=None,
                  PeriodDateEnd:str|None=None,
                  Shading:str|np.ndarray|list|None=None,
                  Marker:str|Dict|None=None,
                  Line:str|Dict|None=None,
                  OCE:str|None=None, ATM:str|None=None,
                  CMIP6_BUF:str|None=None,
                  IGCM_Catalog:str|None=None, IGCM_Catalog_list:list|None=None,
                  config:libIGCM.sys.Config|None=None, Debug:bool=False,
                  **kwargs) -> None :


        def search_catalog (pCatalog:str, pJobName:str|None=None, pShortName:str|None=None, Debug:bool=False) -> dict :
            '''
            Search for JobName or ShortName in a catalog file
            Return the found experiment dictionnary
            '''
            push_stack ( f'search_catalog ( {pCatalog=} {pJobName=} {pShortName=} )' )
            ldebug = OPTIONS['Debug'] or Debug
            if ldebug :
                    print ( f'Catalog file : {pCatalog=} {pJobName=} {pShortName=}' )
            zExp_file    = open (pCatalog)
            zExperiments = json.load (zExp_file)
            exp_out=None
            if ldebug :
                    print ( f'zExperiments : {zExperiments.keys()=}' )
            if pJobName is None :
                if pShortName is not None :
                    if ldebug :
                            print ( f'searching {pShortName=} in Catalog {pCatalog}')
                    for exp in zExperiments.values() :
                        if ldebug :
                            print ( f'searching {exp=}')
                        if isinstance (exp, dict) :
                            if ldebug :
                                print ( f'searching dictionnary {exp=}')
                            if 'ShortName' in exp.keys() :
                                if exp['ShortName'] == pShortName :
                                    exp_out=exp
                                    pJobName = exp_out['JobName']
                                    if ldebug :
                                        print ( f'Found {pShortName=} in {pJobName=}')
                                    break
                    if not pJobName :
                        raise KeyError ( f'libIGCM.post.Config : ShortName={pShortName} not found in Catalog {pCatalog}' )
            else :
                if ldebug :
                    print ( f'searching {pJobName=} in Catalog {pCatalog}')
                if pJobName in zExperiments.keys () :
                    exp_out = zExperiments[pJobName]
                else :
                    raise KeyError ( f'libIGCM.post.Config : JobName={pJobName} not found in Catalog {pCatalog}' )

            pop_stack ( 'libIGCM.post.search_catalog' )
            return exp_out
        
        ### ===========================================================================================
        ## Read catalog of known simulations
        push_stack ( 'libIGCM.post.__init__')

        OPTIONS = get_options ()
        ldebug = OPTIONS['Debug'] or Debug

        if ldebug :
            print ( f'libIGCM.post.Config : {Source    =}' )
            print ( f'libIGCM.post.Config : {MASTER    =}' )
            print ( f'libIGCM.post.Config : {User      =}' )
            print ( f'libIGCM.post.Config : {TGCC_User =}' )
            print ( f'libIGCM.post.Config : {TGCC_Group=}' )
            print ( f'libIGCM.post.Config : {TGCC_SshPrefix=}' )

        self.ARCHIVE              = ARCHIVE
        self.ATM                  = ATM
        self.CMIP6_BUF            = CMIP6_BUF
        self.CalendarType         = CalendarType
        self.Comment              = Comment
        self.ConfigCard           = ConfigCard
        self.DB                   = DB
        self.DapPrefix            = DapPrefix
        self.DateBegin            = DateBegin
        self.DateBeginGregorian   = DateBeginGregorian
        self.DateEnd              = DateEnd
        self.DateEndGregorian     = DateEndGregorian
        self.DatePattern          = DatePattern
        self.PeriodDateBegin      = PeriodDateBegin
        self.PeriodDateEnd        = PeriodDateEnd
        self.Debug                = Debug
        self.ExperimentName       = ExperimentName
        self.FullPeriod           = FullPeriod
        self.Group                = Group
        self.IDRIS_DapPrefix      = IDRIS_DapPrefix
        self.IDRIS_Group          = IDRIS_Group
        self.IDRIS_ThreddsPrefix  = IDRIS_ThreddsPrefix
        self.IDRIS_SshPrefix      = IDRIS_SshPrefix
        self.IDRIS_User           = IDRIS_User
        self.IGCM_Catalog         = IGCM_Catalog
        self.IGCM_Catalog_list    = IGCM_Catalog_list
        self.IGCM_OUT             = IGCM_OUT
        self.IGCM_OUT_name        = IGCM_OUT_name
        self.JobName              = JobName
        self.L_EXP                = L_EXP
        self.Line                 = Line
        self.LongName             = LongName
        self.MASTER               = MASTER
        self.Marker               = Marker
        self.ModelName            = ModelName
        self.OCE                  = OCE
        self.POST_DIR             = POST_DIR
        self.Period               = Period
        self.PeriodLength         = PeriodLength
        self.PeriodSE             = PeriodSE
        self.REBUILD_DIR          = REBUILD_DIR
        self.R_BUF                = R_BUF
        self.R_BUFR               = R_BUFR
        self.R_BUF_KSH            = R_BUF_KSH
        self.R_FIG                = R_FIG
        self.R_FIGR               = R_FIGR
        self.R_GRAF               = R_GRAF
        self.R_IN                 = R_IN
        self.R_OUT                = R_OUT
        self.R_SAVE               = R_SAVE
        self.RunCard              = RunCard
        self.SCRATCHDIR           = SCRATCHDIR
        self.STORAGE              = STORAGE
        self.SeasonalFrequency    = SeasonalFrequency
        self.Shading              = Shading
        self.ShortName            = ShortName
        self.Source               = Source
        self.SpaceName            = SpaceName
        self.SshPrefix            = SshPrefix
        self.TGCC_DapPrefix       = TGCC_DapPrefix
        self.TGCC_Group           = TGCC_Group
        self.TGCC_ThreddsPrefix   = TGCC_ThreddsPrefix
        self.TGCC_SshPrefix       = TGCC_SshPrefix
        self.TGCC_User            = TGCC_User
        self.TagName              = TagName
        self.ThreddsPrefix        = ThreddsPrefix
        self.TmpDir               = TmpDir
        self.User                 = User
        self.YearBegin            = YearBegin
        self.YearEnd              = YearEnd
        self.rebuild              = rebuild

        # - Set the catalog and the catalog list
        if not self.IGCM_Catalog      :
            self.IGCM_Catalog      = OPTIONS['IGCM_Catalog']
        if not self.IGCM_Catalog_list :
            self.IGCM_Catalog_list = OPTIONS['IGCM_Catalog_list']

        if ldebug :
            print ( f'{self.IGCM_Catalog_list=}' )
            print ( f'{self.IGCM_Catalog=}' )

        exp = None

        if ldebug :
            print ( f'{IGCM_Catalog=}' )
        if self.IGCM_Catalog is not None :
            if ldebug :
                print ( f'Searching for catalog file : {self.IGCM_Catalog=}' )
            if os.path.isfile (self.IGCM_Catalog) :
                exp = search_catalog (pCatalog=self.IGCM_Catalog, pJobName=self.JobName, pShortName=self.ShortName, Debug=Debug)
            else :
                raise ValueError ( f'libIGCM.post.Config : Catalog file not found : {self.IGCM_Catalog}' )

        else :
            if self.IGCM_Catalog_list is not None :
                for cfile in self.IGCM_Catalog_list :
                    if ldebug :
                        print ( f'Searching for {cfile=}')
                    if os.path.isfile (cfile) :
                        if ldebug :
                            print ( f'Reads catalog file : {cfile=}' )
                        exp = search_catalog (pCatalog=self.IGCM_Catalog, pJobName=self.JobName, pShortName=self.ShortName, Debug=Debug)    

        ## End of catalog search

        if ldebug :
            print (f'exp    before analysing (1) : {exp=}')
            print (f'kwargs before analysing (1) : {kwargs=}')

        if len(kwargs)>0 :
            if exp is None :
                if ldebug :
                    print ( 'Updates exp with *kwargs')
                exp = dict (**kwargs)
            else :
                if ldebug :
                    print ( 'Creates exp from *kwargs')
                exp.update (**kwargs)

        if ldebug :
            print (f'exp before analysing (2) : {exp=}')
            #print (f'{len(exp)}')


        # A revoir : on prend les valeurs de self, puis de exp, puis celles de OPTIONS
        if exp is not None :
            if ldebug :
                print ( f'Read catalog file for {self.JobName=}' )
            exp = dict (**exp)
            if ldebug :
                print (f'exp at start of analysing : {exp=}')

            liste_pop = []
            for key, value in exp.items () :
                liste_pop.append (key)

                if key in self.keys() :
                    if ldebug :
                        print ( f'  {key=} found in self : {self[key]}')
                    if self[key] is not None :
                        if ldebug :
                            print ( f'  {key:18} found in self : {self[key]}')
                    else :
                        setattr (self, key, value)
                        if ldebug :
                            print ( f'  {key:18} set from exp (1) : {self[key]} {value}')
                else :
                    setattr (self, key, value)
                    if ldebug :
                        print ( f'{key:18} set from exp (2) : {self[key]}')

            for key in liste_pop :
                exp.pop (key)
            if ldebug :
                print ( f'exp after analysing : {exp=}' )

            for key, value in self.items () :
                if value is None :
                    if key in OPTIONS.keys () :
                        if OPTIONS[key] is not None :
                            setattr (self, key, OPTIONS[key])
                            if ldebug :
                                print (f'  {key:18} set from OPTIONS : {self[key]}')

        else :
            if IGCM_Catalog :
                raise RuntimeError ( f'{self.JobName} not found in {self.IGCM_Catalog=}' )
            elif IGCM_Catalog_list :
                raise RuntimeError ( f'{self.JobName} not found in {self.IGCM_Catalog_list=}' )
            else :
                raise RuntimeError ( f'{self.JobName} not found' )

        if self.YearBegin and self.YearEnd and not self.Period :
            self.Period = f'{self.YearBegin}0101_{self.YearEnd}1231'
            if YearBegin and self.YearEnd and not self.PeriodSE :
                self.PeriodSE = f'{self.YearBegin}_{self.YearEnd}'
            if Period and not (self.YearBegin or not self.YearEnd) :
                Y1, Y2 = self.Period.split ('_')
                if not self.YearBegin :
                    self.YearBegin = Y1[0:4]
                if not self.YearEnd   :
                    self.YearEnd   = Y2[0:4]
            if self.PeriodSE and not (self.YearBegin or not self.YearEnd) :
                Y1, Y2 = self.PeriodSE.split ('_')
                if not self.YearBegin :
                    self.YearBegin = Y1
                if not YearEnd   :
                    self.YearEnd   = Y2

        if len(exp)== 0 :
            add_values = dict ()
        else :
            if ldebug :
                print ( f'exp after analyzing : {exp=}' )
            add_values = exp

        libIGCM.sys.Config.__init__ (self, JobName=self.JobName, TagName=self.TagName, SpaceName=self.SpaceName,
                                     ExperimentName=self.ExperimentName, LongName=self.LongName,
                                     ModelName=self.ModelName, ShortName=self.ShortName, Comment=self.Comment,
                                     Source=self.Source, MASTER=self.MASTER, ConfigCard=self.ConfigCard,
                                     RunCard=self.RunCard, User=self.User, Group=self.Group,
                                     TGCC_User=self.TGCC_User, TGCC_Group=self.TGCC_Group,
                                     IDRIS_User=self.IDRIS_User, IDRIS_Group=self.IDRIS_Group,
                                     ARCHIVE=self.ARCHIVE, SCRATCHDIR=self.SCRATCHDIR,
                                     STORAGE=self.STORAGE, R_IN=self.R_IN, R_OUT=self.R_OUT, R_FIG=self.R_FIG,
                                     L_EXP=self.L_EXP, R_SAVE=self.R_SAVE, R_FIGR=self.R_FIGR, R_BUF=self.R_BUF,
                                     R_BUFR=self.R_BUFR, R_BUF_KSH=self.R_BUF_KSH,
                                     REBUILD_DIR=self.REBUILD_DIR, POST_DIR=self.POST_DIR,
                                     ThreddsPrefix=self.ThreddsPrefix, DapPrefix=self.DapPrefix, SshPrefix=self.SshPrefix,
                                     R_GRAF=self.R_GRAF, DB=self.DB,
                                     IGCM_OUT=self.IGCM_OUT, IGCM_OUT_name=self.IGCM_OUT_name, rebuild=self.rebuild,
                                     TmpDir=self.TmpDir,
                                     TGCC_ThreddsPrefix  = self.TGCC_ThreddsPrefix,
                                     TGCC_DapPrefix      = self.TGCC_DapPrefix,
                                     IDRIS_ThreddsPrefix = self.IDRIS_ThreddsPrefix,
                                     IDRIS_DapPrefix     = self.IDRIS_DapPrefix,
                                     IDRIS_SshPrefix     = self.IDRIS_SshPrefix,
                                     DateBegin=self.DateBegin, DateEnd=self.DateEnd,
                                     YearBegin=self.YearBegin, YearEnd=self.YearEnd, PeriodLength=self.PeriodLength,
                                     SeasonalFrequency=self.SeasonalFrequency, CalendarType=self.CalendarType,
                                     DateBeginGregorian=self.DateBeginGregorian, DateEndGregorian=self.DateEndGregorian,
                                     FullPeriod=self.FullPeriod, DatePattern=self.DatePattern,
                                     Period=self.Period, PeriodSE=self.PeriodSE, Shading=self.Shading,
                                     Marker=self.Marker, Line=self.Line, OCE=self.OCE, ATM=self.ATM,
                                     CMIP6_BUF=self.R_BUF,
                                     Debug=self.Debug, **add_values)

        pop_stack ('libIGCM.post.__init__')

def catalog (keep_all:bool=False, Debug:bool=False) -> Dict|None :
    '''
    Return a dictionnary from the catalog file
    By defaults, keeps only experiments entries
    '''
    OPTIONS = get_options ()
    ldebug= OPTIONS['Debug'] or Debug

    cata_list = OPTIONS['IGCM_Catalog_list']
    cata_log  = OPTIONS['IGCM_Catalog']

    lcatalog=None

    if cata_log is not None :
        if ldebug :
            print ( f'Searching for catalog file : {cata_log=}' )
        if os.path.isfile (cata_log) :
            if ldebug :
                print ( f'Catalog file : {cata_log=}' )
            exp_file = open (cata_log, mode='r')
            lcatalog = json.load (exp_file)
        else :
            raise FileNotFoundError ( f'libIGCM.post.catalog : Catalog file not found : {cata_log}' )

    else :
        if cata_list is not None :
            for cfile in cata_list :
                if ldebug :
                    print ( f'Searching for {cfile=}')
                if os.path.isfile (cfile) :
                    if ldebug :
                        print ( f'Reads catalog file : {cfile=}' )
                exp_file = open (cfile, mode='r')
                lcatalog = json.load (exp_file)

    if lcatalog is not None and not keep_all :
        ccz = lcatalog.copy ()
        for kk in lcatalog.keys() :
            if 'keys' not in dir(ccz[kk]) :
                ccz.pop(kk)
            else :
                if 'JobName' not in ccz[kk].keys() :
                    ccz.pop (kk)
        lcatalog = ccz

    return lcatalog

def VarOut2VarIn (VarOut:str, JobName:str) -> str :
    '''
    From a variable name, try to get a more standard name
    Useful because variable names may be different for different model version (mainly for NEMO)
    '''
    push_stack ( f'VarOut2VarIn ({VarOut=} {JobName=})' )

    VarIn = VarOut

    # match JobName :
    #     case 'TR5AS-Vlr01' :
    #         match VarOut :
    #             case 'siconc'   :
    #                 VarIn='ice_pres'
    #             #case 'ice_conc' :
    #             #    VarIn='ice_pres'
    #             case 'sistem'   :
    #                 VarIn='tsice'
    #             case 'sithic' | 'sivolu' :
    #                 VarIn='iicethic'
    #             case 'snthic' | 'snvolu' :
    #                 VarIn='isnowthi'

    #     case 'TR6AV-Sr02' :
    #         match VarOut :
    #             case 'siconc' :
    #                 VarIn='ice_pres'
    #             case 'sistem' :
    #                 VarIn='iicetemp'
    #             case 'sithic' | 'sivolu' :
    #                 VarIn='iicethic'
    #             case 'snthic' | 'snvolu' :
    #                 VarIn='isnowthi'

    # pop_stack ( f'VarOut2VarIn ({VarIn=})' )
    return VarIn
