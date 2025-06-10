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
import re
import json
import cftime
import xarray as xr

import libIGCM
from libIGCM.utils import Container, OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack

class Config (libIGCM.sys.Config) :
    '''
    Defines the libIGCM directories and simulations characteristics

    Overload libIGCM.sys.Config to add knowldege about some simulations
    described in a catalog (at json format)
    '''
    
    def __init__ (self, JobName=None, TagName=None, SpaceName=None, ExperimentName=None,
                  LongName=None, ModelName=None, ShortName=None, Comment=None,
                  Source=None, MASTER=None, ConfigCard=None, RunCard=None, User=None, Group=None,
                  TGCC_User=None, TGCC_Group=None, IDRIS_User=None, IDRIS_Group=None,
                  ARCHIVE=None, SCRATCHDIR=None, STORAGE=None, R_IN=None, R_OUT=None,
                  R_FIG=None, L_EXP=None, R_SAVE=None, R_FIGR=None, R_BUF=None, R_BUFR=None, R_BUF_KSH=None,
                  REBUILD_DIR=None, POST_DIR=None, ThreddsPrefix=None, DapPrefix=None,
                  R_GRAF=None, DB=None, IGCM_OUT=None, IGCM_OUT_name=None, rebuild=None, TmpDir=None,
                  TGCC_ThreddsPrefix=None, TGCC_DapPrefix=None, IDRIS_ThreddsPrefix=None, IDRIS_DapPrefix=None,
                  DateBegin=None, DateEnd=None, YearBegin=None, YearEnd=None, PeriodLength=None,
                  SeasonalFrequency=None, CalendarType=None,
                  DateBeginGregorian=None, DateEndGregorian=None, FullPeriod=None, DatePattern=None,
                  Period=None, PeriodSE=None, Shading=None, Marker=None, Line=None,
                  OCE=None, ATM=None, CMIP6_BUF=None,
                  IGCM_Catalog=None, IGCM_Catalog_list=None, config=None, Debug=False, **kwargs) :
        
        ### ===========================================================================================
        ## Read catalog of known simulations
        push_stack ( 'libIGCM.post.__init__')

        OPTIONS = get_options ()
        
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
        self.Debug                = Debug
        self.ExperimentName       = ExperimentName
        self.FullPeriod           = FullPeriod
        self.Group                = Group
        self.IDRIS_DapPrefix      = IDRIS_DapPrefix
        self.IDRIS_Group          = IDRIS_Group 
        self.IDRIS_ThreddsPrefix  = IDRIS_ThreddsPrefix
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
        self.TGCC_DapPrefix       = TGCC_DapPrefix
        self.TGCC_Group           = TGCC_Group
        self.TGCC_ThreddsPrefix   = TGCC_ThreddsPrefix
        self.TGCC_User            = TGCC_User
        self.TagName              = TagName
        self.ThreddsPrefix        = ThreddsPrefix
        self.TmpDir               = TmpDir
        self.User                 = User
        self.YearBegin            = YearBegin
        self.YearEnd              = YearEnd
        self.rebuild              = rebuild

        for key, value in OPTIONS.items () :
            if key in self.keys () :
                if self[key] is None and value is not None :
                    if OPTIONS.Debug or Debug :
                        print ( f'from OPTIONS, setting {key=} {value=}')
                    setattr (self, key, value)  
            
        if config is not None :
            for key, value in config.items () :
                if self[key] is None and value is not None :
                    if OPTIONS.Debug or Debug :
                        print ( f'from config, setting {key=} {value=}')
                    setattr (self, key, value)       
                    
        if not self.IGCM_Catalog      :
            self.IGCM_Catalog      = OPTIONS.IGCM_Catalog
        if not IGCM_Catalog_list :
            self.IGCM_Catalog_list = OPTIONS.IGCM_Catalog_list
        
        if OPTIONS.Debug or Debug :
            print ( f'{self.IGCM_Catalog_list=}' )
            print ( f'{self.IGCM_Catalog=}' )

        exp = None

        if OPTIONS.Debug or Debug :
            print ( f'{IGCM_Catalog=}' )
        if self.IGCM_Catalog is not None :
            if OPTIONS.Debug or Debug :
                print ( f'Searching for catalog file : {self.IGCM_Catalog=}' )
            if os.path.isfile (self.IGCM_Catalog) :
                if OPTIONS.Debug or Debug :
                    print ( f'Catalog file : {self.IGCM_Catalog=}' )
                exp_file = open (self.IGCM_Catalog)
                Experiments = json.load (exp_file)
                if self.JobName in Experiments.keys () :
                    exp = Experiments[JobName]
            else :
                raise Exception ( f'libIGCM.post.Config : Catalog file not found : {self.IGCM_Catalog}' )

        else :
            for cfile in self.IGCM_Catalog_list :
                if OPTIONS.Debug or Debug :
                    print ( f'Searching for {cfile=}')
                if os.path.isfile (cfile) :
                    if OPTIONS.Debug or Debug :
                        print ( f'Reads catalog file : {cfile=}' )
                    exp_file = open (cfile)
                    Experiments = json.load (exp_file)
                    if OPTIONS.Debug or Debug :
                        print ( f'{Experiments.keys()=}' )
                    if self.JobName in Experiments.keys () :
                        if OPTIONS.Debug or Debug :
                            print (f'{self.JobName=} found')
                        exp = Experiments[self.JobName]
                        break

        if OPTIONS.Debug or Debug :
            print (f'exp    before analysing (1) : {exp=}')
            print (f'kwargs before analysing (1) : {kwargs=}')
               
        if len(kwargs)>0 :
            if exp is None :
                if OPTIONS.Debug or Debug :
                    print ( 'Updates exp with *kwargs')
                exp = Container (**kwargs)
            else :
                if OPTIONS.Debug or Debug :
                    print ( 'Creates exp from *kwargs')
                exp.update (**kwargs)

        if OPTIONS.Debug or Debug :
            print (f'exp before analysing (2) : {exp=}')
            #print (f'{len(exp)}')
                    
        if exp is not None :
            if OPTIONS.Debug or Debug :
                print ( f'Read catalog file for {self.JobName=}' )
            exp = Container (**exp)
            if OPTIONS.Debug or Debug :
                print (f'exp at start of analysing : {exp=}')
                    
            liste_pop = []
            for key, value in exp.items () :
                liste_pop.append (key)
                if OPTIONS.Debug or Debug :
                    print ( f'Analyzing {key=} {value=}')
                if key in self.keys() :
                    if OPTIONS.Debug or Debug :
                        print ( f'  {key=} found in self : {self[key]}')
                    if self[key] is not None :
                        if OPTIONS.Debug or Debug :
                            print ( f'  {key:18} found in self : {self[key]}')
                    else :
                        setattr (self, key, value)
                        if OPTIONS.Debug or Debug :
                            print ( f'  {key:18} set from exp (1) : {self[key]} {value}')
                else :
                    setattr (self, key, value)
                    if OPTIONS.Debug or Debug :
                        print ( f'{key:18} set from exp (2) : {self[key]}')
                        
            for key in liste_pop :
                exp.pop (key)
            if OPTIONS.Debug or Debug :
                print ( f'exp after analysing : {exp=}' )

        else :
            if IGCM_Catalog : 
                raise Exception ( f'{self.JobName} not found in {self.IGCM_Catalog=}' )
            elif IGCM_Catalog_list :
                raise Exception ( f'{self.JobName} not found in {self.IGCM_Catalog_list=}' )
            else :
                raise Exception ( f'{self.JobName} not found' )
            
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
            add_values = Container ()
        else :
            if OPTIONS.Debug or Debug :
                print ( f'exp after analyzing : {exp=}' )
            add_values = exp

        libIGCM.sys.Config.__init__ (self, JobName=self.JobName, TagName=self.TagName, SpaceName=self.SpaceName,
                                     ExperimentName=self.ExperimentName, LongName=self.LongName, ModelName=self.ModelName,
                                     ShortName=self.ShortName, Comment=self.Comment, Source=self.Source,
                                     MASTER=self.MASTER, ConfigCard=self.ConfigCard, RunCard=self.RunCard,
                                     User=self.User, Group=self.Group, TGCC_User=self.TGCC_User, TGCC_Group=self.TGCC_Group,
                                     IDRIS_User=self.IDRIS_User, IDRIS_Group=self.IDRIS_Group,
                                     ARCHIVE=self.ARCHIVE, SCRATCHDIR=self.SCRATCHDIR, STORAGE=self.STORAGE,
                                     R_IN=self.R_IN, R_OUT=self.R_OUT, R_FIG=self.R_FIG, L_EXP=self.L_EXP,
                                     R_SAVE=self.R_SAVE, R_FIGR=self.R_FIGR, R_BUF=self.R_BUF, R_BUFR=self.R_BUFR,
                                     R_BUF_KSH=self.R_BUF_KSH,
                                     REBUILD_DIR=self.REBUILD_DIR, POST_DIR=self.POST_DIR,
                                     ThreddsPrefix=self.ThreddsPrefix, DapPrefix=self.DapPrefix,
                                     R_GRAF=self.R_GRAF, DB=self.DB,
                                     IGCM_OUT=self.IGCM_OUT, IGCM_OUT_name=self.IGCM_OUT_name, rebuild=self.rebuild,
                                     TmpDir=self.TmpDir, TGCC_ThreddsPrefix=self.TGCC_ThreddsPrefix, TGCC_DapPrefix=self.TGCC_DapPrefix,
                                     IDRIS_ThreddsPrefix=self.IDRIS_ThreddsPrefix, IDRIS_DapPrefix=self.IDRIS_DapPrefix,
                                     DateBegin=self.DateBegin, DateEnd=self.DateEnd,
                                     YearBegin=self.YearBegin, YearEnd=self.YearEnd, PeriodLength=self.PeriodLength,
                                     SeasonalFrequency=self.SeasonalFrequency, CalendarType=self.CalendarType,
                                     DateBeginGregorian=self.DateBeginGregorian, DateEndGregorian=self.DateEndGregorian,
                                     FullPeriod=self.FullPeriod, DatePattern=self.DatePattern,
                                     Period=self.Period, PeriodSE=self.PeriodSE, Shading=self.Shading,
                                     Marker=self.Marker, Line=self.Line, OCE=self.OCE, ATM=self.ATM, CMIP6_BUF=self.R_BUF,
                                     Debug=self.Debug, **add_values)
        
        pop_stack ('libIGCM.post.__init__')


def add_year (ptime_counter, year_shift=0) :
    '''
    Add years to a time variable
    Time variable is an xarray of cftime values
    '''
    dates_elements   = [ (date.year+year_shift, date.month, date.day, date.hour, date.minute, date.second, date.microsecond) for date in ptime_counter.values]
    time_counter_new = [ cftime.datetime (*date_el, calendar='standard', has_year_zero=False) for date_el in dates_elements]
    time_counter = xr.DataArray (time_counter_new, dims=('time_counter',), coords=(time_counter_new,))
    time_counter.attrs.update (ptime_counter.attrs)
    return time_counter

        
# def comp ( varName ) :
#     #OPTIONS=get_options ()
#     class RegexEqual (str):
#         def __eq__(self, pattern):
#             return bool(re.search(pattern, self))
#     '''
#     Find the component from the variable name
#     '''
#     push_stack ( f'comp ({varName=})' )
#     Comp = None

#     match RegexEqual(varName) :
#         case "Ahyb.*.*" | "Bhyb.*" | ".*_ppm" | ".*_ppb|R_.*" :
#             Comp = 'ATM'
#         case "SW.*" | "LW.*" | "[flw|fsw|sens]_[oce|lic|sic|ter]*" |  "[pourc|fract]_[oce|lic|sic|ter]" :
#             Comp = 'ATM'
#         case "w.*_[oce|sic|lic|ter]" :
#             Comp = 'ATM'
#         case "dq.*" :
#             Comp = 'ATM'
#         case "tau[xy]_[oce|ter|lic|sic]" :
#             Comp = 'ATM'
#         case ".*10m" | ".*2m" :
#             Comp = 'ATM'
#         case "rsun.*" :
#             Comp = 'ATM'
#         case 'abs550aer'| 'ages_lic'| 'ages_sic'| 'aire'| 'alb1'| 'alb1'| \
#              'alb2'| 'alb2'| 'albe_lic'| 'albe_[oce|sic|lic|ter]' | 'ale'| 'ale_.*' 'ale_wk' :
#              Comp = 'ATM'
#         case 'alp' | 'alp_bl.*' | 'bils.*' | 'bnds' | 'cape' | 'cdrh' | 'cdrm' | 'cin' | \
#              'cldh' | 'cldicemxrat' | 'cldl' | 'cldm' | 'cldq' | 'cldt' | 'cldwatmxrat' | 'co2_ppm' | 'colO3.*' | 'concbc' | \
#              'concdust' | 'concno3' | 'concoa' | 'concso4' | 'concso4' | 'concss' | 'cool_volc' :
#              Comp = 'ATM' 
#         case  '.*aer'| 'epmax' | 'evap' | 'evap_[oce|lic|ter|oce]' \
#              'evappot_[oce|lic|sic|ter]' | 'f0_th'| 'f0_th'| 'fbase'| 'fder'| 'ffonte'| 'fl'| 'flat' :
        #     Comp = 'ATM' 
        # case 'fqcalving' | 'fqfonte'| 'fsnow' | \
        #      'ftime_con' | 'ftime_con' | 'ftime_deepcv' | 'ftime_deepcv' | 'ftime_th' | 'ftime_th'| 'geop' | 'geoph' | 'gusts'| \
        #      'heat_volc' | 'io_lat' | 'io_lon' | 'iwp' | 'lat'| 'lat_[sic|lic|oce|ter]' | 'lon' | 'lwp'| 'mass' | 'mrroli'| \
        #      'msnow'| 'n2'| 'ndayrain'| 'nettop'| 'ocond'| 'od550.*_STRAT' | 'od865aer'| 'oliq'| 'ovap'| 'ozone' :
        #     Comp = 'ATM'
        # case  'ozone_daylight' | 'paprs' | 'pbase' | 'phis' | 'plfc'| 'plu.*' | \
        #       'pr_con_i'| 'pr_con_l' | 'pr_lsc_i' | 'pr_lsc_l' | 'precip'| 'pres'| 'presnivs'| 'prlw'| 'proba_notrig'| 'prsw'| 'prw'| 'psol'| \
        #       'pt0' | 'ptop' | 'ptstar' | 'qsol'| 'qsurf'| 'radsol'| 'rain_con'| 'rain_fall'| 'random_notrig'| 're'| 'ref_liq'| \
        #       'rhum' | 'rneb'| 'rsu'| 'rugs_lic'| 'rugs_oce'| 'rugs_sic'| 'rugs_ter' :
        #     Comp = 'ATM'
        # case 'runofflic' | 's2' | 's_lcl' | 's_pblh' | 's_pblt' | 's_therm' | 'scon.*cbc' | 'sens'| \
        #      'sicf'| 'slab_bils_oce'| 'slp'| 'snow_[oce|sic|ter|lic]'| 'solaire'| 'soll'| 'soll0'| 'sols'| \
        #      'sols0'| 'stratomask'| 'sza'| 't_oce_sic'| 'taux' | 'tauy' | 'tau[xy]_[oce|sic|ter|lic]'| \
        #      'temp'| 'theta'| 'tke_.*'| 'topl'| 'topl.*' | 'tops' :
        #     Comp = 'ATM'
        # case 'tops.*' | 'tsol'| 'tsol_[lic|sic|ter|oce]' | '[uv]e' | '[uv]q' | 'ustar' | '[uv]wat' | \
        #       've'| 'vit[uvw]' | 'wake_.*' | 'wape'| \
        #       'wbeff' :
        #     Comp = 'ATM'
        # case 'wstar' | 'wvapp' | 'z0h_[ter|lic|sic|oce]' | 'zm0_[ter|lic|sic|oce]' | 'zfull' | 'zmax_th' :
        #     Comp = 'ATM'

        # case 'snow' :
        #     Comp = 'ATM|SRF'

        # case  "so.*" | "vo.*" | "zo.*" | "NEMO*" | "e[123].*" | "tau[uv]o" | "qt_.*" :
        #     Comp = 'OCE'
        
        # case  'BLT' | 'area' | 'calving' | 'depti' | 'emp' | 'emp_[oce|ice]' | 'friver' | 'hc300' | 'heatc' | 'hfcorr'|  \
        #       'iceberg' | 'iceshelf' | 'mldr10_1'|  \
    #           'nshfls' | 'olevel' | 'olevel_bounds' | 'qemp_[oce|ice]' | 'qt_[oce|ice]' | 'rain' | 'rsntds'| 'runoffs'|  \
    #           '.*_cea' | 'thetao' | 'tinv'| 'tos' | \
    #           'vfx.*' | 'wfcorr' | 'wfo' | 'ah[uv]_bbl' | 'nshfls' |  'rsntds'| \
    #           'rsds' | 'emp_oce' | 'nsh*' | 'thedepth' | 'mldr10_1' | 'friver' | 'wfo'  :
    #         Comp = 'OCE'

    #     case 'icevol*' | 'sosaline*' :
    #         Comp = 'OCE'

    #     case "si.*|sn.*|ice.*|it.*" :
    #         Comp = 'ICE'
        
    #     case 'Alkalini' | '*CHL' | 'DIC' | 'Fer' | 'NO*' | 'O2' | 'PO4' | 'Si' | 'TPP' | 'Cflx' | 'Dpco2' | 'EPC100' | 'INTPP' :
    #         Comp = 'MBG'

    #     case "CFLUX.*" | "CO2.*" | ".*Frac" | "HARVEST.*" | "LAI.*" | "lai.*" | "NPP.*" | "VEGET.*" | ".*vegetfrac" | "TOTAL.*" | "GROWTH.*" :
    #         Comp = 'SBG'
    #     case 'lai' | 'alb_nir'| 'alb_vis'| 'bqsb'| 'gqsb' | 'nee' | 'temp_sol' | 'nbp'| \
    #          'AGE'|  'CONTFRAC'|  'CONVFLUX'|  'GPP'| 'gpp'|  'npp'| 'HET_RESP' :
    #         Comp = 'SBG'
            
    # pop_stack ( f"{comp=}" )
    # return Comp

def VarOut2VarIn (VarOut:str, JobName:str) :
    '''
    From a variable name, try to get a more standard name
    Useful because variable names may be different for different model version (mainly for NEMO)
    '''
    push_stack ( f'VarOut2VarIn ({VarOut=} {JobName=})' )
    
    # VarIn = VarOut

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
    # return VarIn
