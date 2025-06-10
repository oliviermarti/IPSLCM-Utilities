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

import copy
import time
import numpy as np
import xarray as xr
import pint

from libIGCM import utils
from libIGCM.utils import Container, OPTIONS, set_options, get_options, reset_options, push_stack, pop_stack
from plotIGCM.interp1d import interp1d
from plotIGCM.utils import pmath, xr_quantify, xr_dequantify, pint_unit, copy_attrs, distance, aire_triangle, aire_quadri

try :
    from pint_xarray import unit_registry as ureg
except ImportError :
    from pint import UnitRegistry
    ureg = UnitRegistry()
    pintx = False
else :
    pintx = True
##    
Q_ = ureg.Quantity

## Units not recognized by pint
try    : ureg.define ('degree_C      = degC')
except : pass
try    : ureg.define ('DU            = 10^-5 * m = du')
except : pass
try    : ureg.define ('ppb           = 10^-9 * kg/kg' )
except : pass
try    : ureg.define ('psu           = g/kg'   )
except : pass
try    : ureg.define ('degrees_east  = degree' )
except : pass
try    : ureg.define ('degrees_north = degree' )
except : pass

from plotIGCM import nemo
