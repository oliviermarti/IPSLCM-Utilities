# -*- coding: utf-8 -*-
'''
libIGCM_utils : a few utilities

Author : olivier.marti@lsce.ipsl.fr

Github : https://github.com/oliviermarti/IPSLCM-Utilities

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
personal. Be warned that the author himself may not respect the prerequisites.                                                               
'''
import time
import copy
from typing import Self, Any, Optional, Type, cast

## ============================================================================
DEFAULT_OPTIONS = dict ( Debug                = False, 
                         Trace                = False,
                         Timing               = None,
                         t0                   = None,
                         Depth                = 0,
                         Stack                = [],
                         DefaultCalendar      = 'Gregorian',
                         User                 = None,
                         Group                = None,
                         TGCC_User            = 'p86mart',
                         TGCC_Group           = 'gen12006',
                         IDRIS_User           = 'rces009',
                         IDRIS_Group          = 'ces',
                         TGCC_DapPrefix       = 'https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds',
                         TGCC_ThreddsPrefix   = 'https://thredds-su.ipsl.fr/thredds/fileServer/tgcc_thredds',
                         IDRIS_DapPrefix      = 'https://thredds-su.ipsl.fr/thredds/dodsC/idris_thredds',
                         IDRIS_ThreddsPrefix  = 'https://thredds-su.ipsl.fr/thredds/fileServer/idris_thredds',
                         DapPrefix            = None,
                         ThreddsPrefix        = None,
                         IGCM_Catalog         = None,
                         IGCM_Catalog_list    = [ 'IGCM_catalog.json', ],
                         )

OPTIONS: dict[str, Any] = copy.deepcopy(DEFAULT_OPTIONS)

class set_options :
    '''
    Set OPTIONS for libIGCM
    
    See Also :
    ----------
    reset_options, get_options
    
    '''
    def __init__ (self:Self, **kwargs) -> None :
        self.old = dict ()
        for k, v in kwargs.items() :
            if k not in OPTIONS :
                raise ValueError ( f"argument name {k!r} is not in the set of valid OPTIONS {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update (kwargs)

    def _apply_update (self:Self, options_dict:dict) -> None :
        OPTIONS.update (options_dict)
        
    def __enter__(self: Self) -> None:
        return None

    def __exit__(self: Self, type: Optional[Type[BaseException]], value: Optional[BaseException], traceback: Optional[Any]) -> None:
        self._apply_update(self.old)

def get_options() -> dict[str, Any]:
    '''
    Get OPTIONS for libIGCM

    See Also :
    ----------
    set_options, reset_options
    '''
    return OPTIONS

def reset_options () :
    '''
    Reset OPTIONS to DEFAULT_OPTIONS for libIGCM

    See Also :
    ----------
    set_options, get_options

    '''
    return set_options (**DEFAULT_OPTIONS) 

def return_stack() -> list[str]|str|int|bool|None:
    return OPTIONS['Stack']

def push_stack (string:str) -> None :
    OPTIONS['Depth'] += 1
    if OPTIONS['Trace'] :
        print ( '  '*(OPTIONS['Depth']-1), f'-->{__name__}.{string}' )
    #
    OPTIONS['Stack'].append (string)
    #
    if OPTIONS['Timing'] :
        if OPTIONS['t0'] :
            OPTIONS['t0'].append (time.time())
        else :
            OPTIONS['t0'] = [time.time(),]

def pop_stack (string:str) -> None :
    if OPTIONS['Timing'] :
        dt = time.time() - OPTIONS['t0'][-1]
        OPTIONS['t0'].pop()
    else :
        dt = None
    if OPTIONS['Trace'] or dt :
        if dt :
            if dt < 1e-3 : 
                print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string} : time: {dt*1e6:5.1f} micro s')
            if dt >= 1e-3 and dt < 1 : 
                print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string} : time: {dt*1e3:5.1f} milli s')
            if dt >= 1 : 
                print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string} : time: {dt*1:5.1f} second')
        else : 
            print ( '  '*(OPTIONS['Depth']-1), f'<--{__name__}.{string}')
    #
    OPTIONS['Depth'] -= 1
    OPTIONS['Stack'].pop ()
    #
    
   
