#!/usr/bin/env python3
'''
This library provide some utilities for post processing
'''

# libIGCM_post internal options
import warnings
from typing import TYPE_CHECKING, Literal, TypedDict
import re
import numpy as np

import libIGCM_sys


Stack = list()

if TYPE_CHECKING :
    Options = Literal [ "DefaultCalendar", "Debug", "Trace", "Depth", "Stack" ]

    class T_Options (TypedDict) :
        DefaultCalendar = 'Gregorian'
        Debug = bool
        Trace = bool
        Depth = -1
        Stack = list()
        #DefaultCalendarType = ['Gregorian', 'GREGORIAN', 'leap', 'LEAP', 'Leap', 'gregorian',
        #                             '360d', '360_day', '360d', '360_days', '360D', '360_DAY', '360D', '360_DAYS', 
        #                             'noleap', '365_day', '365_days', 'NOLEAP', '365_DAY', '365_DAYS',
        #                             'all_leap', '366_day', 'allleap', '366_days', '336d', 'ALL_LEAP', '366_DAY', 'ALLLEAP', '366_DAYS', '336D',]

OPTIONS = { 'DefaultCalendar':'Gregorian', 'Debug':False, 'Trace':False, 'Depth':None, 'Stack':None, }

class set_options :
    """
    set options for libIGCM_post
    """
    def __init__ (self, **kwargs):
        self.old = {}
        for k, v in kwargs.items():
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update (self, options_dict) : OPTIONS.update (options_dict)
    def __enter__ (self) : return
    def __exit__ (self, type, value, traceback) : self._apply_update (self.old)

def get_options () -> dict :
    """
    Get options for libIGCM_post

    See Also
    ----------
    set_options
    """
    return OPTIONS

def return_stack () :
    return OPTIONS['Stack']

def PushStack (string:str) :
    if OPTIONS['Depth'] : OPTIONS['Depth'] += 1
    else                : OPTIONS['Depth'] = 1
    if OPTIONS['Trace'] : print ( '  '*OPTIONS['Depth'], f'-->{__name__}.{string}' )
    #
    if OPTIONS['Stack'] : OPTIONS['Stack'].append (string)
    else                : OPTIONS['Stack'] = [string,]

def PopStack (string:str) :
    if OPTIONS['Trace'] : print ( '  '*OPTIONS['Depth'], f'<--{__name__}.{string}')
    OPTIONS['Depth'] -= 1
    if OPTIONS['Depth'] == 0 : OPTIONS['Depth'] = None
    OPTIONS['Stack'].pop ()
    if OPTIONS['Stack'] == list () : OPTIONS['Stack'] = None

class config (libIGCM_sys.config) :
    '''
    Defines the libIGCM directories and simulations characteristics
      

    Overload libIGCM_sys.config to add knowldege about some simulations
    '''

    def __init__ (self, JobName=None, TagName=None, SpaceName=None, ExperimentName=None,
                  LongName=None, ModelName=None, ShortName=None,
                  Source=None, MASTER=None, ConfigCard=None, RunCard=None, User=None, Group=None,
                  TGCC_User=None, TGCC_Group=None, IDRIS_User=None, IDRIS_Group=None,
                  ARCHIVE=None, SCRATCHDIR=None, STORAGE=None, R_IN=None, R_OUT=None,
                  R_FIG=None, L_EXP=None,
                  R_SAVE=None, R_FIGR=None, R_BUF=None, R_BUFR=None, R_BUF_KSH=None,
                  REBUILD_DIR=None, POST_DIR=None,
                  ThreddsPrefix=None, DapPrefix=None, R_GRAF=None, DB=None,
                  IGCM_OUT=None, IGCM_OUT_name=None, rebuild=None, TmpDir=None,
                  Debug=None, TGCC_ThreddsPrefix=None, TGCC_DapPrefix=None, IDRIS_ThreddsPrefix=None, IDRIS_DapPrefix=None,
                  DateBegin=None, DateEnd=None, YearBegin=None, YearEnd=None, PeriodLength=None, SeasonalFrequency=None, CalendarType=None,
                  DateBeginGregorian=None, DateEndGregorian=None, FullPeriod=None, DatePattern=None,
                  ColorLine=None, ColorShading=None, Marker=None,
                  CMIP6_BUF=None ) :
        
        ### ===========================================================================================
        ## Known simulations

        if JobName == 'TR5AS-Vlr01' :
            if not SpaceName      : SpaceName      = 'PROD'
            if not TagName        : TagName        = 'IPSLCM5A2'
            if not ShortName      : ShortName      = 'Vlr01 CM5A2'
            if not ExperimentName : ExperimentName = 'Holocene'
            if not ModelName      : ModelName      = 'IPSL CM5 VLR'
            if not TGCC_User      : TGCC_User      = 'p86mart'
            if not TGCC_Group     : TGCC_Group     = 'gen2212'
            if not YearBegin      : YearBegin      = 2000
            if not YearEnd        : YearEnd        = 7999
            if not CalendarType   : CalendarType   = 'leap'
            if not DatePattern    : DatePattern    = '[2-7]??00101_[2-7]??91231'
            if not ColorShading   : ColorShading   =  np.array ([128, 128, 128])/255
            if not ColorLine      : ColorLine      =  np.array ([  0,   0,   0])/255
            if not Marker         : Marker         = 'o'

        if JobName == 'TR6AV-Sr02' :
            if not SpaceName      : SpaceName      = 'PROD'
            if not TagName        : TagName        = 'IPSLCM6'
            if not ShortName      : ShortName      = 'Sr02 CM6.0 Veg'
            if not ExperimentName : ExperimentName = 'Holocene'
            if not ModelName      : ModelName      = 'IPSL CM6 Veg'
            if not TGCC_User      : TGCC_User      = 'p86mart'
            if not TGCC_Group     : TGCC_Group     = 'gen2212'
            if not YearBegin      : YearBegin      = 2000
            if not YearEnd        : YearEnd        = 7999
            if not CalendarType   : CalendarType   = 'leap'
            if not DatePattern    : DatePattern    = '[2-7]??00101_[2-7]??91231'
            if not ColorShading   : ColorShading   = np.array ([ 91, 174, 178])/255
            if not ColorLine      : ColorLine      = np.array ([112, 160, 205])/255 
            if not Marker         : Marker         = 's'

        if JobName == 'TR6kCM6AS-Sr01' :
            if not SpaceName      : SpaceName      = 'PROD'
            if not TagName        : TagName        = 'IPSLCM6'
            if not ShortName      : ShortName      = 'Sr01 CM6.2'
            if not ExperimentName : ExperimentName = 'Holocene'
            if not ModelName      : ModelName      = 'IPSL CM6.2 LR'
            if not TGCC_User      : TGCC_User      = 'p86mart'
            if not TGCC_Group     : TGCC_Group     = 'gen12006'
            if not YearBegin      : YearBegin      = 2000
            if not YearEnd        : YearEnd        = 7999
            if not CalendarType   : CalendarType   = 'leap'
            if not DatePattern    : DatePattern    = '[2-7]??00101_[2-7]??91231'
            if not ColorShading   : ColorShading   = np.array ([204, 174, 113])/255
            if not ColorLine      : ColorLine      = np.array ([196, 121,   0])/255
            if not Marker         : Marker         = '^'

        if JobName == 'TR6kCM6AS-Sr02' :
            if not SpaceName      : SpaceName      = 'PROD'
            if not TagName        : TagName        = 'IPSLCM6'
            if not ShortName      : ShortName      = 'Sr02 CM6.2'
            if not ExperimentName : ExperimentName = 'Holocene'
            if not ModelName      : ModelName      = 'IPSL CM6.2 LR'
            if not TGCC_User      : TGCC_User      = 'p86mart'
            if not TGCC_Group     : TGCC_Group     = 'gen12006'
            if not YearBegin      : YearBegin      = 4000
            if not YearEnd        : YearEnd        = 7999
            if not CalendarType   : CalendarType   = 'leap'
            if not DatePattern    : DatePattern    = '[4-7]??00101_[2-7]??91231'
            if not ColorShading   : ColorShading   = np.array ([191, 191, 191])/255
            if not ColorLine      : ColorLine      = np.array ([178, 178, 178])/255
            if not Marker         : Marker         = 'v'

        if JobName == 'TR6kCM6AS-Sr04' :
            if not SpaceName      : SpaceName      = 'PROD'
            if not TagName        : TagName        = 'IPSLCM6'
            if not ShortName      : ShortName      = 'Sr04 CM6.2'
            if not ExperimentName : ExperimentName = 'Holocene'
            if not ModelName      : ModelName      = 'IPSL CM6.2 LR'
            if not TGCC_User      : TGCC_User      = 'p86mart'
            if not TGCC_Group     : TGCC_Group     = 'gen12006'
            if not YearBegin      : YearBegin      = 5000
            if not YearEnd        : YearEnd        = 7999
            if not CalendarType   : CalendarType   = 'leap'
            if not DatePattern    : DatePattern    = '[5-7]??00101_[2-7]??91231'
            if not ColorShading   : ColorShading   = np.array ([ 67, 147, 195])/255
            if not ColorLine      : ColorLine      = np.array ([  0,  52, 102])/255
            if not Marker         : Marker         = '<'

        if JobName == 'TR6kCM6AV-Sr28' :
            if not SpaceName      : SpaceName      = 'PROD'
            if not TagName        : TagName        = 'IPSLCM6'
            if not ShortName      : ShortName      = 'Sr28 CM6.2 Veg'
            if not ExperimentName : ExperimentName = 'Holocene'
            if not ModelName      : ModelName      = 'IPSL CM6 Veg'
            if not TGCC_User      : TGCC_User      = 'p86mart'
            if not TGCC_Group     : TGCC_Group     = 'gen2212'
            if not YearBegin      : YearBegin      = 2000
            if not YearEnd        : YearEnd        = 7999
            if not CalendarType   : CalendarType   = 'leap'
            if not DatePattern    : DatePattern    = '[2-7]??00101_[2-7]??91231'
            if not ColorShading   : ColorShading   = np.array ([223, 237, 195])/255
            if not ColorLine      : ColorLine      = np.array ([  0,  79,   0])/255
            if not Marker         : Marker         = 'D'
            
                
        libIGCM_sys.config.__init__ (self, JobName=JobName, TagName=TagName, SpaceName=SpaceName, ExperimentName=ExperimentName,
                  LongName=LongName, ModelName=ModelName, ShortName=ShortName,
                  Source=Source, MASTER=MASTER, ConfigCard=ConfigCard, RunCard=RunCard, User=User, Group=Group,
                  TGCC_User=TGCC_User, TGCC_Group=TGCC_Group, IDRIS_User=IDRIS_User, IDRIS_Group=IDRIS_Group,
                  ARCHIVE=ARCHIVE, SCRATCHDIR=SCRATCHDIR, STORAGE=STORAGE, R_IN=R_IN, R_OUT=R_OUT,
                  R_FIG=R_FIG, L_EXP=L_EXP,
                  R_SAVE=R_SAVE, R_FIGR=R_FIGR, R_BUF=R_BUF, R_BUFR=R_BUFR, R_BUF_KSH=R_BUF_KSH,
                  REBUILD_DIR=REBUILD_DIR, POST_DIR=POST_DIR,
                  ThreddsPrefix=ThreddsPrefix, DapPrefix=DapPrefix, R_GRAF=R_GRAF, DB=DB,
                  IGCM_OUT=IGCM_OUT, IGCM_OUT_name=IGCM_OUT_name, rebuild=rebuild, TmpDir=TmpDir,
                  Debug=Debug, TGCC_ThreddsPrefix=TGCC_ThreddsPrefix, TGCC_DapPrefix=TGCC_DapPrefix,
                  IDRIS_ThreddsPrefix=IDRIS_ThreddsPrefix, IDRIS_DapPrefix=IDRIS_DapPrefix,
                  DateBegin=DateBegin, DateEnd=DateEnd, YearBegin=YearBegin, YearEnd=YearEnd, PeriodLength=PeriodLength,
                  SeasonalFrequency=SeasonalFrequency, CalendarType=CalendarType,
                  DateBeginGregorian=DateBeginGregorian, DateEndGregorian=DateEndGregorian, DatePattern=DatePattern,
                  ColorShading=ColorShading, ColorLine=ColorLine, Marker=Marker,
                  CMIP6_BUF=CMIP6_BUF )

def Var2COMP ( varName ) :
    '''
    Find the component from the variable name
    '''
    PushStack ( f'Var2COMP ({varName=})' )
    Comp = None
    if varName in ['Ahyb', 'Ahyb_bounds', 'Ahyb_mid', 'Ahyb_mid_bounds', 'Bhyb', 'Bhyb_bounds', 'Bhyb_mid', 'Bhyb_mid_bounds', 'CFC11_ppt', 'CFC12_ppt',
                       'CH4_ppb', 'LWdnSFC', 'LWdnSFCclr', 'LWupSFC', 'LWupSFCclr', 'N2O_ppb', 'R_ecc', 'R_incl', 'R_peri', 'SWdnSFC', 'SWdnSFCclr',
                       'SWdnTOA', 'SWdnTOAclr', 'SWupSFC', 'SWupSFCclr', 'SWupTOAclr', 'abs550aer', 'ages_lic', 'ages_sic', 'aire', 'alb1', 'alb1',
                       'alb2', 'alb2', 'albe_lic', 'albe_oce', 'albe_sic', 'albe_ter', 'ale', 'ale_bl', 'ale_bl_stat', 'ale_bl_trig', 'ale_wk',
                       'alp', 'alp_bl', 'alp_bl_conv', 'alp_bl_det', 'alp_bl_fluct_m', 'alp_bl_stat', 'alp_wk', 'ave_t2m_daily_max', 'ave_t2m_daily_min',
                       'bils', 'bils_diss', 'bils_ec', 'bils_enthalp', 'bils_kinetic', 'bils_latent', 'bils_tke', 'bnds', 'cape', 'cdrh', 'cdrm', 'cin',
                       'cldh', 'cldicemxrat', 'cldl', 'cldm', 'cldq', 'cldt', 'cldwatmxrat', 'co2_ppm', 'colO3_strat', 'colO3_trop', 'concbc', 'concbc',
                       'concdust', 'concno3', 'concoa', 'concoa', 'concso4', 'concso4', 'concss', 'cool_volc', 'dqajs2d', 'dqajs2d', 'dqcon2d',
                       'dqcon2d', 'dqdyn2d', 'dqdyn2d', 'dqeva2d', 'dqeva2d', 'dqldyn2d', 'dqldyn2d', 'dqlphy2d', 'dqlphy2d', 'dqlsc2d', 'dqlsc2d',
                       'dqphy2d', 'dqphy2d', 'dqsdyn2d', 'dqsdyn2d', 'dqsphy2d', 'dqsphy2d', 'dqthe2d', 'dqthe2d', 'dqvdf2d', 'dqvdf2d', 'dqwak2d',
                       'dqwak2d', 'dryod550aer', 'ec550aer', 'epmax', 'epmax', 'evap', 'evap_lic', 'evap_oce', 'evap_sic', 'evap_ter', 'evappot_lic',
                       'evappot_oce', 'evappot_sic', 'evappot_ter', 'f0_th', 'f0_th', 'fbase', 'fder', 'ffonte', 'fl', 'flat', 'flw_lic', 'flw_oce',
                       'flw_sic', 'flw_ter', 'fqcalving', 'fqfonte', 'fract_lic', 'fract_oce', 'fract_sic', 'fract_ter', 'fsnow', 'fsw_lic', 'fsw_oce',
                       'fsw_sic', 'fsw_ter', 'ftime_con', 'ftime_con', 'ftime_deepcv', 'ftime_deepcv', 'ftime_th', 'ftime_th', 'geop', 'geoph', 'gusts',
                       'heat_volc', 'io_lat', 'io_lon', 'iwp', 'lat', 'lat_lic', 'lat_oce', 'lat_sic', 'lat_ter', 'lon', 'lwp', 'mass', 'mrroli',
                       'msnow', 'n2', 'ndayrain', 'nettop', 'ocond', 'od550_STRAT', 'od550aer', 'od550lt1aer', 'od865aer', 'oliq', 'ovap', 'ozone',
                       'ozone_daylight', 'paprs', 'pbase', 'phis', 'plfc', 'pluc', 'plul', 'plun', 'pourc_lic', 'pourc_oce', 'pourc_sic', 'pourc_ter',
                       'pr_con_i', 'pr_con_l', 'pr_lsc_i', 'pr_lsc_l', 'precip', 'pres', 'presnivs', 'prlw', 'proba_notrig', 'prsw', 'prw', 'psol',
                       'pt0', 'ptop', 'ptstar', 'q2m', 'qsol', 'qsurf', 'radsol', 'rain_con', 'rain_fall', 'random_notrig', 're', 'ref_liq', 'rh2m',
                       'rhum', 'rneb', 'rsu', 'rsun1', 'rsun2', 'rsun3', 'rsun4', 'rsun5', 'rsun6', 'rugs_lic', 'rugs_oce', 'rugs_sic', 'rugs_ter',
                       'runofflic', 's2', 's_lcl', 's_pblh', 's_pblt', 's_therm', 'sconcbc', 'sconcoa', 'sconcso4', 'sens', 'sens_lic', 'sens_oce',
                       'sens_sic', 'sens_ter', 'sicf', 'slab_bils_oce', 'slp', 'snow', 'snow_lic', 'snow_sic', 'solaire', 'soll', 'soll0', 'sols',
                       'sols0', 'stratomask', 'sza', 't2m', 't_oce_sic', 'taux', 'taux_lic', 'taux_oce', 'taux_sic', 'taux_ter', 'tauy', 'tauy_lic',
                       'tauy_oce', 'tauy_sic', 'tauy_ter', 'temp', 'theta', 'tke_max', 'tke_max', 'topl', 'topl0', 'toplwad', 'toplwad0', 'tops',
                       'tops0', 'topswad', 'topswad0', 'tsol', 'tsol_lic', 'tsol_oce', 'tsol_sic', 'tsol_ter', 'u10m', 'ue', 'uq', 'ustar', 'uwat',
                       'v10m', 've', 'vitu', 'vitv', 'vitw', 'vq', 'vwat', 'wake_dens', 'wake_dens', 'wake_h', 'wake_h', 'wake_s', 'wake_s', 'wape',
                       'wbeff', 'wbilo_lic', 'wbilo_oce', 'wbilo_sic', 'wbilo_ter', 'wbils_lic', 'wbils_oce', 'wbils_sic', 'wbils_ter', 'wevap_lic',
                       'wevap_oce', 'wevap_sic', 'wevap_ter', 'wind10m', 'wrain_lic', 'wrain_oce', 'wrain_sic', 'wrain_ter', 'wsnow_lic',
                       'wsnow_oce', 'wsnow_sic', 'wsnow_ter', 'wstar', 'wvapp', 'z0h_lic', 'z0h_lic', 'z0h_oce', 'z0h_oce', 'z0h_sic', 'z0h_sic',
                       'z0h_ter', 'z0h_ter', 'z0m_lic', 'z0m_lic', 'z0m_oce', 'z0m_oce', 'z0m_sic', 'z0m_sic', 'z0m_ter', 'z0m_ter', 'zfull',
                       'zmax_th', 'zmax_th', ] :
        Comp = 'ATM'

    if varName in [ 'BLT', 'area', 'calving', 'depti', 'emp', 'emp_ice', 'emp_oce', 'evap_ao_cea', 'friver', 'hc300', 'heatc', 'hfcorr', 
                    'hflx_cal_cea', 'hflx_evap_cea', 'hflx_rain_cea', 'hflx_snow_cea', 'iceberg', 'iceshelf', 'mldr10_1', 
                    'nshfls', 'olevel', 'olevel_bounds', 'qemp_ice', 'qemp_oce', 'qt_ice', 'qt_oce', 'rain', 'rsntds', 'runoffs', 
                    'snow_ai_cea', 'snow_ao_cea', 'so', 'sos', 'sosflxdo', 'subl_ai_cea', 'thetao', 'tinv', 'tos', 'vfxice', 'vfxsnw', 
                    'vfxspr', 'vfxsub', 'wfcorr', 'wfo', 'zos', 'e3u', 'ahu_bbl', 'e3v', 'ahv_bbl', 'sosstsst', 'sosaline',
                    'NEMO_difvho', 'NEMO_difvho_noevd', 'NEMO_difvso', 'NEMO_difvso_noevd', 'tauuo',  'tauvo',  'nshfls',  'rsntds',
                    'rsds',  'qt_*',  'emp_oce',  'nsh*',  'thedepth',  'mldr10_1',  'friver', 'wfo' ] :
        Comp = 'OCE'

    if varName in [ 'ice_pres',  'siconc',  'ithic',  'sivolu',  'snconc',  'snvolu' ] :
        Comp = 'ICE'

    if varName in ['Alkalini',  '*CHL',  'DIC',  'Fer',  'NO*',  'O2',  'PO4',  'Si',  'TPP',  'Cflx',  'Dpco2',  'EPC100',  'INTPP'] :
        Comp = 'MBG'

    if varName in [ 'lai',  '*vegetfrac', '*Frac', 'alb_nir', 'alb_vis', 'bqsb', 'gqsb', 'nee', 'temp_sol', 'nbp',
                    'AGE',  'CFLUX*',  'CO2*',  'CONTFRAC',  'CONVFLUX',  'GPP',  'GROWTH*', 'HEIGHT', 'HARVEST*', 'LAI*',
                    'lai*',  'NPP*',  'gpp',  'npp',  'TOTAL*',  'VEGET*', 'HET_RESP' ] :
        Comp = 'SBG'
            
    PopStack ( f'{Comp=}' )
    return Comp


