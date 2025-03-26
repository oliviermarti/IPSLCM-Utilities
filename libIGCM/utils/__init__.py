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
import copy
import time

## ============================================================================
class Container :
    '''
    Void class to fill the gap between dictonnaries and spacenames
    Class members can be accessed either with dictionnary or namespace syntax
       i.e  <Container>['member'] or <Container>.member
    '''
    def update (self, dico=None, **kwargs):
        '''Use a dictionnary to update values'''
        if dico :
            for attr in dico.keys () :
                value = dico[attr]
                if isinstance (value, dict) :
                    super().__setattr__ (attr, Container (value))
                else :
                    super().__setattr__ (attr, value)
        for key, value in kwargs.items():
            if isinstance (value, dict) :
                setattr (self, key, Container(value))
            else :
                setattr (self, key, value)
        #self.__dict__.update (kwargs)
            
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
    def copy (self) :
        return Container (self)
    #def __deepcopy__(self, memo):
    #    return Container(copy.deepcopy(self.name, memo))
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
        if isinstance (value, dict) :
            setattr (self, attr, Container(value))
        else : 
            setattr (self, attr, value)
    def __iter__    (self) :
        return self.__dict__.__iter__()
    def __next__    (self) :
        return self.__dict__.__next__()
    def __len__     (self) :
        return len (self.__dict__)
    def __copy__    (self) :
        return Container (self)
    
    def __init__ (self, dico=None, **kwargs) :
        if dico :
            zargs = dico
        else :
            zargs = {}
        zargs.update (**kwargs)
        for attr, value in zargs.items () :
             if isinstance (value, dict) :
                 # Dictionnaries are handeld by recursivity
                 super().__setattr__ (attr, Container (value))
             else :
                 super().__setattr__ (attr, value)
        return None
    
DEFAULT_OPTIONS = Container (Debug  = False,
                             Trace  = False,
                             Timing = None,
                             t0     = None,
                             Depth  = None,
                             Stack  = None,
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
                             Pint                 = False)

OPTIONS = copy.deepcopy (DEFAULT_OPTIONS)

class set_options :
    '''
    Set options for libIGCM
    
    See Also :
    ----------
    reset_options, get_options
    
    '''
    def __init__ (self, **kwargs) :
        self.old = Container ()
        for k, v in kwargs.items() :
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update (kwargs)

    def _apply_update (self, options_dict) :
        OPTIONS.update (options_dict)
    def __enter__ (self) :
        return
    def __exit__ (self, type, value, traceback) :
        self._apply_update (self.old)

def get_options () -> dict :
    '''
    Get options for libIGCM

    See Also :
    ----------
    set_options, reset_options

    '''
    return OPTIONS

def reset_options():
    '''
    Reset options to default_options for libIGCM

    See Also :
    ----------
    set_options, get_options

    '''
    return set_options (**DEFAULT_OPTIONS)

def return_stack () :
    return OPTIONS.Stack

def push_stack (string:str) :
    if OPTIONS.Depth :
        OPTIONS.Depth += 1
    else             :
        OPTIONS.Depth = 1
    if OPTIONS.Trace :
        print ( '  '*(OPTIONS.Depth-1), f'-->{__name__}.{string}' )
    #
    if OPTIONS.Stack :
        OPTIONS.Stack.append (string)
    else             :
        OPTIONS.Stack = [string,]
    #
    if OPTIONS.Timing :
        if OPTIONS.t0 :
            OPTIONS.t0.append (time.time())
        else :
            OPTIONS.t0 = [time.time(),]

def pop_stack (string:str) :
    if OPTIONS.Timing :
        dt = time.time() - OPTIONS.t0[-1]
        OPTIONS.t0.pop()
    else :
        dt = None
    if OPTIONS.Trace or dt :
        if dt :
            if dt < 1e-3 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1e6:5.1f} micro s')
            if dt >= 1e-3 and dt < 1 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1e3:5.1f} milli s')
            if dt >= 1 : 
                print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string} : time: {dt*1:5.1f} second')
        else : 
            print ( '  '*(OPTIONS.Depth-1), f'<--{__name__}.{string}')
    #
    OPTIONS.Depth -= 1
    if OPTIONS.Depth == 0 :
        OPTIONS.Depth = None
    OPTIONS.Stack.pop ()
    if OPTIONS.Stack == list () :
        OPTIONS.Stack = None
    #
    
   
