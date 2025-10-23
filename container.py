# -*- coding: utf-8 -*-
'''
Utilitaires

author: olivier.marti@lsce.ipsl.fr

This software is governed by the CeCILL license under French law and
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
import copy
from typing import Self, Dict, Any, Optional
from collections.abc import ItemsView, KeysView, ValuesView, Iterable


## ============================================================================
def pretty (value, htchar:str='\t', lfchar:str='\n', indent:int=0) -> str:
    '''
    Pretty printing for almost anything hierachical

    key can be of any valid type. Indent and Newline character can be changed for everything we'd like.
    Dict, Container, List and Tuples are pretty printed.
    '''
    nlch = lfchar + htchar * (indent + 1)
    if isinstance (value, dict) :
        items = [ nlch + repr(key) + ': ' + pretty(value[key], htchar, lfchar, indent+1) for key in value.keys() ]
        return f"{','.join(items)}{lfchar}{htchar*indent}"
    elif '__dict__' in dir (value) :
        items = [ nlch + repr(key) + ': ' + pretty(value.__dict__[key], htchar, lfchar, indent+1) for key in value.__dict__.keys() ]
        return f"{','.join(items)}{lfchar}{htchar*indent}"
    elif isinstance (value, list) or isinstance (value, tuple) :
        items = [ nlch + pretty(item, htchar, lfchar, indent+1) for item in value ]
        return f"{','.join(items)}{lfchar}{htchar*indent}"
    else:
        return repr (value)
     
## ============================================================================
class Container :
    '''
    Void class to fill the gap between dictonnaries and spacenames
    Class members can be accessed either with dictionnary or namespace syntax
       i.e  <Container>['member'] or <Container>.member
    '''
    def update (self:Self, dico:Dict[str,Any]|Self|None=None, **kwargs:Any) -> None :
        '''Use a dictionnary or a Container to update values'''
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

    ## Public functions
    def keys(self: Self) -> KeysView[str]:
        return self.__dict__.keys()

    def values(self: Self) -> ValuesView[Any]:
        return self.__dict__.values()

    def items(self: Self) -> ItemsView[str, Any]:
        return self.__dict__.items()

    def dict(self: Self) -> Dict[str, Any]:
        return self.__dict__

    def pop(self: Self, attr: str) -> Any:
        value = self[attr]
        delattr(self, attr)
        return value
    
    def copy (self:Self) -> 'Container' :
        return Container (**self)
    
    ## Hidden functions
    def __copy__    (self:Self) -> 'Container' :
        return Container (**self)
    
    def __deepcopy__(self:Self, memo=None)-> 'Container' :
        return Container (copy.deepcopy(self.__dict__, memo=memo))
    
    def __replace__(
            self: Self,
            dico: Dict[str, Any]|Self|None = None,
            **kwargs: Any
    ) -> None:
        return self.update(dico=dico, **kwargs)

    def __update__(
            self: Self,
            dico: Dict[str, Any]|Self|None = None,
            **kwargs: Any
    ) -> None:
        return self.update(dico=dico, **kwargs)
    
    def __str__     (self:Self) :
        return str  (self.__dict__)
    def __repr__ (self:Self):
        return pretty (self)
    
    def __name__    (self:Self) :
        return self.__class__.__name__
    
    def __getitem__ (self:Self, attr) :
        return getattr (self, attr)
    
    def __setitem__ (self:Self, attr, value) -> None :
        if isinstance (value, dict) :
            setattr (self, attr, Container(value))
        else :
            setattr (self, attr, value)
            
    def __iter__    (self:Self) :
        return self.__dict__.__iter__()
    
    def __contains__ (self:Self, item) -> bool :
        if item in self.keys() :
            return True
        else :
            return False
        
    #def __next__  (self:Self) :
    #    return self.__dict__.__next__()
    
    def __len__     (self:Self) :
        return len (self.__dict__)

    ## Initialisation
    def __init__    (self:Self, dico:Dict|Self|None=None, Debug=False, level=0, **kwargs) -> None :
        if dico is not None :
            zargs = dico
        else :
            zargs = {}
        zargs.update (**kwargs)
        for attr, value in zargs.items () :
            if Debug :
                print ( f"{level=} - {attr=} - {type(value)=}" )
            if isinstance (value, dict) : 
                # Dictionnaries are handeld by recursivity
                super().__setattr__ (attr, Container (value, level=level+1))
            else :
                super().__setattr__ (attr, value)
    
