# -*- coding: utf-8 -*-
## ===========================================================================
##                                                                            
##  This software is governed by the CeCILL  license under French law and     
##  abiding by the rules of distribution of free software.  You can  use,     
##  modify and/ or redistribute the software under the terms of the CeCILL    
##  license as circulated by CEA, CNRS and INRIA at the following URL         
##  "http://www.cecill.info".                                                 
##                                                                            
##  Warning, to install, configure, run, use any of Olivier Marti's           
##  software or to read the associated documentation you'll need at least     
##  one (1) brain in a reasonably working order. Lack of this implement       
##  will void any warranties (either express or implied).                     
##  O. Marti assumes no responsability for errors, omissions,                 
##  data loss, or any other consequences caused directly or indirectly by     
##  the usage of his software by incorrectly or partially configured          
##  personal.                                                                 
##                                                                            
## ===========================================================================
'''
olivier.marti@lsce.ipsl.fr

GitHub : https://github.com/oliviermarti/IPSLCM-Utilities

'''
import numpy as np
import xarray as xr

from libIGCM.options import push_stack as push_stack
from libIGCM.options import pop_stack  as pop_stack
import orca


def zgr_z (config:str='orca2') -> tuple[xr.DataArray,xr.DataArray,xr.DataArray,xr.DataArray]:
    '''
    ** Purpose :   set the depth of model levels and the resulting
    vertical scale factors.
    
    ** Method  :   z-coordinate system (use in all type of coordinate)
        The depth of model levels is defined from an analytical
        function the derivative of which gives the scale factors.
        both depth and scale factors only depend on k (1d arrays).
        w-level: gdepw_1d  = gdep(k)
        e3w_1d(k) = dk(gdep)(k)     = e3(k)
        t-level: gdept_1d  = gdep(k+0.5)
        e3t_1d(k) = dk(gdep)(k+0.5) = e3(k+0.5)
        
    ** Action  : - gdept_1d, gdepw_1d : depth of T- and W-point (m)
    - e3t_1d  , e3w_1d   : scale factors at T- and W-levels (m)
    
    Reference : Marti, Madec & Delecluse, 1992, JGR, 97, No8, 12,763-12,766.
    ------------------------------------------------------------------------
    '''

    namcfg = orca.nam_config[config]['namcfg']
    namdom = orca.nam_config[config]['namdom']

    pp_to_be_computed = 0
    #
    # Set variables from parameters
    # ------------------------------

    jpk       = namcfg['jpk']
    
    ppkth     = namdom['ppkth']
    ppacr     = namdom['ppacr']
    ppdzmin   = namdom['ppdzmin']
    pphmax    = namdom['pphmax']
    ppkth2    = namdom['ppkth2']
    ppacr2    = namdom['ppacr2'] 
    ppa0      = namdom['ppa0']
    ppsur     = namdom['ppsur']
    ppa1      = namdom['ppa1']
    ppa2      = namdom['ppa2']
    ldbletanh = namdom['ldbletanh'] 
    
    # If ppa1 and ppa0 and ppsur are et to pp_to_be_computed
    #  za0, za1, zsur are computed from ppdzmin , pphmax, ppkth, ppacr
    if ppa1  == pp_to_be_computed and ppa0  == pp_to_be_computed and ppsur == pp_to_be_computed:
        #
        
        za1  = (  ppdzmin - pphmax / (jpk-1)  )               \
            / ( np.tanh((1-ppkth)/ppacr) - ppacr/(jpk   -1) * (  np.log( np.cosh( (jpk - ppkth) / ppacr) )    \
                                                               - np.log( np.cosh( ( 1  - ppkth) / ppacr) ) ) )
        
        za0  = ppdzmin - za1 *                 np.tanh ( (1-ppkth) / ppacr )
        zsur =   - za0 - za1 * ppacr * np.log( np.cosh ( (1-ppkth) / ppacr ))
    else : 
        za1  = ppa1
        za0  = ppa0
        zsur = ppsur
        za2  = ppa2                            # optional (ldbletanh=T) double tanh parameter
             
    # Reference z-coordinate (depth - scale factor at T- and W-points)
    # ======================
    if ppkth == 0. :           #  uniform vertical grid
        za1      = pphmax / (jpk-1)
        def gdep (zz) :
            return (zz-1) * za1
        def e3 (zz) :
            return za1
        
    else :                                # Madec & Imbard 1996 function
        if not ldbletanh :
            def gdep (zz) :
                return zsur + za0*zz + za1 * ppacr * np.log ( np.cosh ( (zz-ppkth)/ ppacr ) )
            def e3 (zz) :
                return za0 + za1 * np.tanh ((zz-ppkth) / ppacr)
        else :
            def gdep (zz) :
                return zsur + za0*zz + za1 * ppacr * np.log ( np.cosh( (zz-ppkth ) / ppacr ) ) \
                                     + za2 * ppacr2* np.log ( np.cosh( (zz-ppkth2) / ppacr2) )
            def e3 (zz) :
                return za0  + za1*np.tanh ( (zz-ppkth ) / ppacr  ) \
                            + za2*np.tanh ( (zz-ppkth2) / ppacr2 )
            
    zw = np.arange (jpk) + 1.0
    zt = zw + 0.5
    
    gdepw = gdep (zw) 
    gdept = gdep (zt)
    e3w   = e3   (zw)
    e3t   = e3   (zt)

    #dp = 0.00001
    #e3w   = (gdep(zw+dp) - gdep(zw-dp))/(2.0*dp)
    #e3t   = (gdep(zt+dp) - gdep(zt-dp))/(2.0*dp)
           
          
    gdepw [0] = 0.                    # force first w-level to be exactly at zero
       
    gdept = xr.DataArray (gdept, dims=('gdept',), coords=(gdept,))
    e3t   = xr.DataArray (e3t  , dims=('gdept',), coords=(gdept,))
    gdepw = xr.DataArray (gdepw, dims=('gdepw',), coords=(gdepw,))
    e3w   = xr.DataArray (e3w  , dims=('gdepw',), coords=(gdepw,))

    return gdept, gdepw, e3t, e3w
  
