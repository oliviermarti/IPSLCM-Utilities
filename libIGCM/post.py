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

import libIGCM
from libIGCM.utils import Container, OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack

class Config (libIGCM.sys.Config) :
    '''
    Defines the libIGCM directories and simulations characteristics

    Overload libIGCM.sys.Config to add knowldege about some simulations
    '''
    def __init__ (self, JobName=None, SpaceName=None, TagName=None, ShortName=None, ExperimentName=None, ModelName=None, Comment=None,
                        TGCC_User=None, TGCC_Group=None,
                        YearBegin=None, YearEnd=None, CalendarType=None, DatePattern=None, Period=None, PeriodSE=None,
                        Shading=None, Line=None, Marker=None,
                        OCE=None, ATM=None, Perio=None,
                        IGCM_Catalog=None, IGCM_Catalog_list=None, **kwargs) :

        OPTIONS=get_options ()

        ### ===========================================================================================
        ## Read catalog of known simulations
        push_stack ( 'libIGCM.post.__init__')

        if OPTIONS.Debug :
            print ( f'{OPTIONS = }' )

        if not IGCM_Catalog      :
            IGCM_Catalog      = OPTIONS.IGCM_Catalog
        if not IGCM_Catalog_list :
            IGCM_Catalog_list = OPTIONS.IGCM_Catalog_list
        
        if OPTIONS.Debug :
            print ( f'{IGCM_Catalog_list=}' )
            print ( f'{IGCM_Catalog=}' )

        exp = None

        if IGCM_Catalog :
            if os.path.isfile (IGCM_Catalog) :
                if OPTIONS.Debug :
                    print ( f'Catalog file : {IGCM_Catalog=}' )
                exp_file = open (IGCM_Catalog)
                Experiments = json.load (exp_file)
                if JobName in Experiments.keys () :
                    exp = Experiments[JobName]
            else :
                raise Exception ( f'libIGCM.post.Config : Catalog file not found : {IGCM_Catalog}' )

        else :
            for cfile in OPTIONS.IGCM_Catalog_list :
                if os.path.isfile (cfile) :
                    if OPTIONS.Debug :
                        print ( f'Catalog file : {cfile=}' )
                    exp_file = open (cfile)
                    Experiments = json.load (exp_file)
                    if JobName in Experiments.keys () :
                        exp = Experiments[JobName]
                        break

            if exp :
                if OPTIONS.Debug :
                    print ( f'Read catalog file for {JobName=}' )
                exp = Container (**exp)
                    
                exp.pop ('JobName')    
                if not SpaceName      and 'SpaceName'      in exp.keys() :
                    SpaceName      = exp['SpaceName']
                    exp.pop ('SpaceName')
                if not TagName        and 'TagName'        in exp.keys() :
                    TagName        = exp['TagName']
                    exp.pop ('TagName')
                if not ShortName      and 'ShortName'      in exp.keys() :
                    ShortName      = exp['ShortName']
                    exp.pop ('ShortName')
                if not ExperimentName and 'ExperimentName' in exp.keys() :
                    ExperimentName = exp['ExperimentName']
                    exp.pop ('ExperimentName')
                if not ModelName      and 'ModelName'      in exp.keys() :
                    ModelName      = exp['ModelName']
                    exp.pop ('ModelName')
                if not Comment        and 'Comment'        in exp.keys() :
                    Comment        = exp['Comment']
                    exp.pop ('Comment')
                if not YearBegin      and 'YearBegin'      in exp.keys() :
                    YearBegin      = exp['YearBegin']
                    exp.pop ('YearBegin')
                if not YearEnd        and 'YearEnd'        in exp.keys() :
                    YearEnd        = exp['YearEnd']
                    exp.pop ('YearEnd')
                if not CalendarType   and 'CalendarType'   in exp.keys() :
                    CalendarType   = exp['CalendarType']
                    exp.pop ('CalendarType')
                if not DatePattern    and 'DatePattern'    in exp.keys() :
                    DatePattern    = exp['DatePattern']
                    exp.pop ('DatePattern')
                if not Period         and 'Period'         in exp.keys() :
                    Period         = exp['Period']
                    exp.pop ('Period')
                if not PeriodSE       and 'PeriodSE'       in exp.keys() :
                    PeriodSE       = exp['PeriodSE']
                    exp.pop ('PeriodSE')
                if not TGCC_User      and 'TGCC_User'      in exp.keys() :
                    TGCC_User      = exp['TGCC_User']
                    exp.pop ('TGCC_User')
                if not TGCC_Group     and 'TGCC_Group'     in exp.keys() :
                    TGCC_Group     = exp['TGCC_Group']
                    exp.pop ('TGCC_Group')
                if not CalendarType   and 'CalendarType'   in exp.keys() :
                    CalendarType   = exp['CalendarType']
                    exp.pop ('CalendarType')
                if not Shading        and 'Shading'        in exp.keys() :
                    Shading        = exp['Shading']
                    exp.pop ('Shading')
                if not Marker         and 'Marker'         in exp.keys() :
                    #Marker         = Container (**exp['Marker'])
                    Marker         = exp['Marker']
                    exp.pop ('Marker')
                if not Line           and 'Line'           in exp.keys() :
                    #Line           = Container (**exp['Line'])
                    Line           = exp['Line']
                    exp.pop ('Line')
                if not OCE            and 'OCE'            in exp.keys() :
                    OCE            = exp['OCE']
                    exp.pop ('OCE')
                if not ATM            and 'ATM'            in exp.keys() :
                    ATM            = exp['ATM']
                    exp.pop ('ATM')

                #if OCE :
                #    OCE_DOM = nemo.domain (cfg_name=OCE)
                    
                #if not OCE_DOM :
                #    if 'OCE_DOM' in exp.keys() :
                #        OCE_DOM = Container (**exp['OCE_DOM'])
                #        if OCE :
                #            OCE_DOM['cfg_name']=OCE
                #        OCE_DOM = nemo.domain (**OCE_DOM)
                #if not ATM_DOM :
                #    if 'ATM_DOM' in exp.keys() :
                #        ATM_DOM = Container (**exp['ATM_DOM'])

                if YearBegin and YearEnd and not Period :
                    Period   = f'{YearBegin}0101_{YearEnd}1231'
                if YearBegin and YearEnd and not PeriodSE :
                    PeriodSE = f'{YearBegin}_{YearEnd}'
                if Period and not (YearBegin or not YearEnd) :
                    Y1, Y2 = Period.split('_')
                    if not YearBegin :
                        YearBegin = Y1[0:4]
                    if not YearEnd   :
                        YearEnd   = Y2[0:4]
                if PeriodSE and not (YearBegin or not YearEnd) :
                    Y1, Y2 = PeriodSE.split('_')
                    if not YearBegin :
                        YearBegin = Y1
                    if not YearEnd   :
                        YearEnd   = Y2

                if len(exp)== 0 :
                    add_values = Container ()
                else :
                    add_values = exp
                    
                if kwargs :
                    add_values.update (kwargs)
                    
            else :
                if IGCM_Catalog : 
                    raise Exception ( f'{JobName} not found in {IGCM_Catalog=}' )
                elif IGCM_Catalog_list :
                    raise Exception ( f'{JobName} not found in {IGCM_Catalog_list=}' )
                else :
                    raise Exception ( f'{JobName} not found' )
                                          
                
        libIGCM.sys.Config.__init__ (self, JobName=JobName, SpaceName=SpaceName, TagName=TagName, ShortName=ShortName, Comment=Comment,
                                           ExperimentName=ExperimentName, ModelName=ModelName,
                                           TGCC_User=ModelName, TGCC_Group=TGCC_Group,
                                           YearBegin=YearBegin, YearEnd= YearEnd, CalendarType=CalendarType, DatePattern=DatePattern,
                                           Period=Period, PeriodSE=PeriodSE,
                                           Shading=Shading, Line=Line, Marker=Marker,
                                           OCE=OCE, ATM=ATM, **add_values)
        
        pop_stack ( 'libIGCM.post.__init__' )

        
def comp ( varName ) :
    #OPTIONS=get_options ()
    class RegexEqual (str):
        def __eq__(self, pattern):
            return bool(re.search(pattern, self))
    '''
    Find the component from the variable name
    '''
    push_stack ( f'comp ({varName=})' )
    Comp = None

    match RegexEqual(varName) :
        case "Ahyb.*.*" | "Bhyb.*" | ".*_ppm" | ".*_ppb|R_.*" :
            Comp = 'ATM'
        case "SW.*" | "LW.*" | "[flw|fsw|sens]_[oce|lic|sic|ter]*" |  "[pourc|fract]_[oce|lic|sic|ter]" :
            Comp = 'ATM'
        case "w.*_[oce|sic|lic|ter]" :
            Comp = 'ATM'
        case "dq.*" :
            Comp = 'ATM'
        case "tau[xy]_[oce|ter|lic|sic]" :
            Comp = 'ATM'
        case ".*10m" | ".*2m" :
            Comp = 'ATM'
        case "rsun.*" :
            Comp = 'ATM'
        case 'abs550aer'| 'ages_lic'| 'ages_sic'| 'aire'| 'alb1'| 'alb1'| \
             'alb2'| 'alb2'| 'albe_lic'| 'albe_[oce|sic|lic|ter]' | 'ale'| 'ale_.*' 'ale_wk' :
             Comp = 'ATM'
        case 'alp' | 'alp_bl.*' | 'bils.*' | 'bnds' | 'cape' | 'cdrh' | 'cdrm' | 'cin' | \
             'cldh' | 'cldicemxrat' | 'cldl' | 'cldm' | 'cldq' | 'cldt' | 'cldwatmxrat' | 'co2_ppm' | 'colO3.*' | 'concbc' | \
             'concdust' | 'concno3' | 'concoa' | 'concso4' | 'concso4' | 'concss' | 'cool_volc' :
             Comp = 'ATM' 
        case  '.*aer'| 'epmax' | 'evap' | 'evap_[oce|lic|ter|oce]' \
             'evappot_[oce|lic|sic|ter]' | 'f0_th'| 'f0_th'| 'fbase'| 'fder'| 'ffonte'| 'fl'| 'flat' :
            Comp = 'ATM' 
        case 'fqcalving' | 'fqfonte'| 'fsnow' | \
             'ftime_con' | 'ftime_con' | 'ftime_deepcv' | 'ftime_deepcv' | 'ftime_th' | 'ftime_th'| 'geop' | 'geoph' | 'gusts'| \
             'heat_volc' | 'io_lat' | 'io_lon' | 'iwp' | 'lat'| 'lat_[sic|lic|oce|ter]' | 'lon' | 'lwp'| 'mass' | 'mrroli'| \
             'msnow'| 'n2'| 'ndayrain'| 'nettop'| 'ocond'| 'od550.*_STRAT' | 'od865aer'| 'oliq'| 'ovap'| 'ozone' :
            Comp = 'ATM'
        case  'ozone_daylight' | 'paprs' | 'pbase' | 'phis' | 'plfc'| 'plu.*' | \
              'pr_con_i'| 'pr_con_l' | 'pr_lsc_i' | 'pr_lsc_l' | 'precip'| 'pres'| 'presnivs'| 'prlw'| 'proba_notrig'| 'prsw'| 'prw'| 'psol'| \
              'pt0' | 'ptop' | 'ptstar' | 'qsol'| 'qsurf'| 'radsol'| 'rain_con'| 'rain_fall'| 'random_notrig'| 're'| 'ref_liq'| \
              'rhum' | 'rneb'| 'rsu'| 'rugs_lic'| 'rugs_oce'| 'rugs_sic'| 'rugs_ter' :
            Comp = 'ATM'
        case 'runofflic' | 's2' | 's_lcl' | 's_pblh' | 's_pblt' | 's_therm' | 'scon.*cbc' | 'sens'| \
             'sicf'| 'slab_bils_oce'| 'slp'| 'snow_[oce|sic|ter|lic]'| 'solaire'| 'soll'| 'soll0'| 'sols'| \
             'sols0'| 'stratomask'| 'sza'| 't_oce_sic'| 'taux' | 'tauy' | 'tau[xy]_[oce|sic|ter|lic]'| \
             'temp'| 'theta'| 'tke_.*'| 'topl'| 'topl.*' | 'tops' :
            Comp = 'ATM'
        case 'tops.*' | 'tsol'| 'tsol_[lic|sic|ter|oce]' | '[uv]e' | '[uv]q' | 'ustar' | '[uv]wat' | \
              've'| 'vit[uvw]' | 'wake_.*' | 'wape'| \
              'wbeff' :
            Comp = 'ATM'
        case 'wstar' | 'wvapp' | 'z0h_[ter|lic|sic|oce]' | 'zm0_[ter|lic|sic|oce]' | 'zfull' | 'zmax_th' :
            Comp = 'ATM'

        case 'snow' :
            Comp = 'ATM|SRF'

        case  "so.*" | "vo.*" | "zo.*" | "NEMO*" | "e[123].*" | "tau[uv]o" | "qt_.*" :
            Comp = 'OCE'
        
        case  'BLT' | 'area' | 'calving' | 'depti' | 'emp' | 'emp_[oce|ice]' | 'friver' | 'hc300' | 'heatc' | 'hfcorr'|  \
              'iceberg' | 'iceshelf' | 'mldr10_1'|  \
              'nshfls' | 'olevel' | 'olevel_bounds' | 'qemp_[oce|ice]' | 'qt_[oce|ice]' | 'rain' | 'rsntds'| 'runoffs'|  \
              '.*_cea' | 'thetao' | 'tinv'| 'tos' | \
              'vfx.*' | 'wfcorr' | 'wfo' | 'ah[uv]_bbl' | 'nshfls' |  'rsntds'| \
              'rsds' | 'emp_oce' | 'nsh*' | 'thedepth' | 'mldr10_1' | 'friver' | 'wfo'  :
            Comp = 'OCE'

        case 'icevol*' | 'sosaline*' :
            Comp = 'OCE'

        case "si.*|sn.*|ice.*|it.*" :
            Comp = 'ICE'
        
        case 'Alkalini' | '*CHL' | 'DIC' | 'Fer' | 'NO*' | 'O2' | 'PO4' | 'Si' | 'TPP' | 'Cflx' | 'Dpco2' | 'EPC100' | 'INTPP' :
            Comp = 'MBG'

        case "CFLUX.*" | "CO2.*" | ".*Frac" | "HARVEST.*" | "LAI.*" | "lai.*" | "NPP.*" | "VEGET.*" | ".*vegetfrac" | "TOTAL.*" | "GROWTH.*" :
            Comp = 'SBG'
        case 'lai' | 'alb_nir'| 'alb_vis'| 'bqsb'| 'gqsb' | 'nee' | 'temp_sol' | 'nbp'| \
             'AGE'|  'CONTFRAC'|  'CONVFLUX'|  'GPP'| 'gpp'|  'npp'| 'HET_RESP' :
            Comp = 'SBG'
            
    pop_stack ( f"{comp=}" )
    return Comp

def VarOut2VarIn (VarOut, JobName) :
    '''
    From a variable name, try to get a more standard name
    Useful because variable names may be different for different model version (mainly for NEMO)
    '''
    push_stack ( f'VarOut2VarIn ({VarOut=} {JobName=})' )
    
    VarIn = VarOut

    match JobName :
        case 'TR5AS-Vlr01' :	
            match VarOut :
                case 'siconc'   :
                    VarIn='ice_pres'
                #case 'ice_conc' :
                #    VarIn='ice_pres'
                case 'sistem'   :
                    VarIn='tsice'    
                case 'sithic' | 'sivolu' :
                    VarIn='iicethic' 
                case 'snthic' | 'snvolu' :
                    VarIn='isnowthi' 
    
        case 'TR6AV-Sr02' :
            match VarOut :
                case 'siconc' :
                    VarIn='ice_pres'
                case 'sistem' :
                    VarIn='iicetemp'
                case 'sithic' | 'sivolu' :
                    VarIn='iicethic'
                case 'snthic' | 'snvolu' :
                    VarIn='isnowthi'

    pop_stack ( f'VarOut2VarIn ({VarIn=})' )
    return VarIn
