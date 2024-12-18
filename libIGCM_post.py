#!/usr/bin/env python3
'''
This library provide some utilities for post processing
'''

import os, sys, re
import json

from Utils import Container
import libIGCM_sys
from libIGCM_sys import OPTIONS, push_stack, pop_stack, set_options, get_options
    
class Config (libIGCM_sys.Config) :
    '''
    Defines the libIGCM directories and simulations characteristics

    Overload libIGCM_sys.config to add knowldege about some simulations
    '''
    def __init__ (self, JobName=None, SpaceName=None, TagName=None, ShortName=None, ExperimentName=None, ModelName=None, Comment=None,
                        TGCC_User=None, TGCC_Group=None,
                        YearBegin=None, YearEnd=None, CalendarType=None, DatePattern=None,
                        ColorShading=None, ColorLine=None, Line=None, Marker=None,
                        OCE=None, ATM=None,
                        IGCM_Catalog=None, **kwargs) :

        ### ===========================================================================================
        ## Read catalog of known simulations
        push_stack ( '__init__')

        if not IGCM_Catalog : IGCM_Catalog = OPTIONS.IGCM_Catalog
        
        if OPTIONS.Debug : print ( f'{IGCM_Catalog=}' )

        if IGCM_Catalog : 
            if os.path.isfile (IGCM_Catalog) :
                if OPTIONS.Debug : print ( f'Catalog file : {IGCM_Catalog=}' )
                exp_file = open (IGCM_Catalog)
                Experiments = json.load (exp_file)
            else : 
                raise Exception ( f'Catalog file not found : {IGCM_Catalog}' )

            if JobName in Experiments.keys () :
                exp = Experiments[JobName]
                if OPTIONS.Debug : print ( f'Read catalog file for {JobName=}' )

                if not SpaceName       :
                    if 'SpaceName'     in exp.keys() : SpaceName      = exp['SpaceName']
                if not TagName         : 
                   if 'SpaceName'      in exp.keys() : TagName        = exp['TagName']
                if not ShortName       :
                   if 'ShortName'      in exp.keys() : ShortName      = exp['ShortName']
                if not ExperimentName  :
                   if 'ExperimentName' in exp.keys() : ExperimentName = exp['ExperimentName']
                if not ModelName       :
                   if 'ModelName'      in exp.keys() : ModelName      = exp['ModelName']
                if not Comment         :
                   if 'Comment'        in exp.keys() : Comment        = exp['Comment']
                if not YearBegin       :
                    if 'YearBegin'     in exp.keys() : YearBegin      = exp['YearBegin']
                if not YearBegin       :
                    if 'YearBegin'     in exp.keys() : YearBegin      = exp['YearBegin']
                if not YearEnd         :
                    if 'YearEnd'       in exp.keys() : YearEnd        = exp['YearEnd']
                if not CalendarType    :
                    if 'CalendarType'  in exp.keys() : CalendarType   = exp['CalendarType']
                if not DatePattern     :
                    if 'DatePattern'   in exp.keys() : DatePattern    = exp['DatePattern']
                if not TGCC_User       :
                    if 'TGCC_User'     in exp.keys() : TGCC_User      = exp['TGCC_User']
                if not TGCC_Group      :
                    if 'TGCC_Group'    in exp.keys() : TGCC_Group     = exp['TGCC_Group']
                if not CalendarType    :
                    if 'CalendarType'  in exp.keys() : CalendarType   = exp['CalendarType']
                if not DatePattern     :
                    if 'DatePattern'   in exp.keys() : DatePattern    = exp['DatePattern']
                if not ColorLine       :
                    if 'ColorLine'     in exp.keys() : ColorLine      = exp['ColorLine']
                if not ColorShading    :
                    if 'ColorShading'  in exp.keys() : ColorShading   = exp['ColorShading']
                if not Marker          :
                    if 'Marker'        in exp.keys() : Marker         = Container (**exp['Marker'])
                if not Line            :
                    if 'Line'          in exp.keys() : Line           = exp['Line']
                if not OCE             :
                    if 'OCE'           in exp.keys() : OCE            = exp['OCE']
                if not ATM             :
                    if 'ATM'           in exp.keys() : ATM            = exp['ATM'] 

        libIGCM_sys.Config.__init__ (self, JobName=JobName, SpaceName=SpaceName, TagName=TagName, ShortName=ShortName, Comment=Comment,
                                           ExperimentName=ExperimentName, ModelName=ModelName,
                                           TGCC_User=ModelName, TGCC_Group=TGCC_Group,
                                           YearBegin=YearBegin, YearEnd= YearEnd, CalendarType=CalendarType, DatePattern=DatePattern,
                                           ColorShading=ColorShading, ColorLine=ColorLine, Line=Line, Marker=Marker,
                                           OCE=OCE, ATM=ATM, **kwargs)
        pop_stack ( '__init__' )

        
def comp ( varName ) :
    class RegexEqual (str):
        def __eq__(self, pattern):
            return bool(re.search(pattern, self))
    '''
    Find the component from the variable name
    '''
    push_stack ( f'comp ({varName=})' )
    Comp = None

    match RegexEqual(varName) :
        case "Ahyb.*.*" | "Bhyb.*" | ".*_ppm" | ".*_ppb|R_.*" : Comp = 'ATM'
        case "SW.*" | "LW.*" | "[flw|fsw|sens]_[oce|lic|sic|ter]*" |  "[pourc|fract]_[oce|lic|sic|ter]" : Comp = 'ATM'
        case "w.*_[oce|sic|lic|ter]" : Comp = 'ATM'
        case "dq.*" : Comp = 'ATM'
        case "tau[xy]_[oce|ter|lic|sic]" : Comp = 'ATM'
        case ".*10m" | ".*2m" : Comp = 'ATM'
        case "rsun.*" : Comp = 'ATM'
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

        case "si.*|sn.*|ice.*|it.*" : Comp = 'ICE'
        
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
    push_stack ( f'VarOut2VarIn ({VarOut=} {JobName=})' )
    
    VarIn = VarOut

    match JobName :
        case 'TR5AS-Vlr01' :	
            match VarOut :
                case 'siconc'   : VarIn='ice_pres'
                case 'ice_conc' : VarIn='ice_pres'
                case 'sistem'   : VarIn='tsice'    
                case 'sithic' | 'sivolu' : varIn='iicethic' 
                case 'snthic' | 'snvolu' : VarIn='isnowthi' 
    
        case 'TR6AV-Sr02' :
            match VarOut :
                case 'siconc' : VarIn='ice_pres'
                case 'sistem' : VarIn='iicetemp'
                case 'sithic' | 'sivolu' : VarIn='iicethic'
                case 'snthic' | 'snvolu' : VarIn='isnowthi'
                 
    pop_stack ( f'VarOut2VarIn ({VarIn=})' )
    return VarIn
