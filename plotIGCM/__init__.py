# -*- coding: utf-8 -*-
'''
plotIGCM : a few utilities for post processing

Author : olivier.marti@lsce.ipsl.fr

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
personal. Be warned that the author himself may not respect the prerequisites.                                                                  
'''

from plotIGCM.options import OPTIONS       as OPTIONS
from plotIGCM.options import set_options   as set_options
from plotIGCM.options import get_options   as get_options
from plotIGCM.options import reset_options as reset_options
from plotIGCM.options import push_stack    as push_stack
from plotIGCM.options import pop_stack     as pop_stack
from plotIGCM.utils   import copy_attrs    as copy_attrs

from plotIGCM import sphere   as sphere
from plotIGCM import nemo     as nemo
from plotIGCM import lmdz     as lmdz
from plotIGCM import utils    as utils
from plotIGCM import oasis    as oasis
from plotIGCM import interp1d as interp1d