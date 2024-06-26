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
'''

## SVN information
__Author__   = "$Author:  $"
__Date__     = "$Date: $"
__Revision__ = "$Revision:  $"
__Id__       = "$Id: $"
__HeadURL    = "$HeadURL: $"

import numpy as np
try    : import xarray as xr
except ImportError : pass

rpi = np.pi ; rad = np.deg2rad (1.0) ; dar = np.rad2deg (1.0)

def zgr_z (config='orca2') :
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
    ----------------------------------------------------------------------
    '''

    #
    # Set variables from parameters
    # ------------------------------
    
    zkth   = ppkth   ; zacr  = ppacr
    zdzmin = ppdzmin ; zhmax = pphmax
    zkth2  = ppkth2  ; zacr2 = ppacr2   # optional (ldbletanh=T) double tanh parameters
    
    # If ppa1 and ppa0 and ppsur are et to pp_to_be_computed
    #  za0, za1, zsur are computed from ppdzmin , pphmax, ppkth, ppacr
    if ppa1  == pp_to_be_computed and ppa0  == pp_to_be_computed and ppsur == pp_to_be_computed:
        #
        if key_agrif :
            za1  = (  ppdzmin - pphmax / (jpkdta-1)  )  \
              / ( np.tanh((1-ppkth)/ppacr) - ppacr/(jpkdta-1) * (  np.log( np.cosh( (jpkdta - ppkth) / ppacr) ) \
                                                                 - np.log( np.cosh( (    1  - ppkth) / ppacr) )  )  )
        else : 
            za1  = (  ppdzmin - pphmax / (jpkm1)  )               \
              / ( np.tanh((1-ppkth)/ppacr) - ppacr/(jpk   -1) * (  np.log( np.cosh( (jpk - ppkth) / ppacr) )      \
                                                                 - np.log( np.cosh( ( 1  - ppkth) / ppacr) )  )  )
                
            za0  = ppdzmin - za1 *                np.tanh ( (1-ppkth) / ppacr )
            zsur =   - za0 - za1 * ppacr * np.log( np.cosh( (1-ppkth) / ppacr )  )
    else : 
        za1 = ppa1 ;       za0 = ppa0 ;          zsur = ppsur
        za2 = ppa2                            # optional (ldbletanh=T) double tanh parameter
        
        
    # Reference z-coordinate (depth - scale factor at T- and W-points)
    # ======================
    if ppkth == 0. :           #  uniform vertical grid
        if key_agrif : za1 = zhmax / (jpkdta-1)
        else         : za1 = zhmax / (jpk-1)
            
        zw       = np.arange (jpk) + 1.0
        zt       = zw + 0.5
        gdepw_1d = ( zw - 1 ) * za1
        gdept_1d = ( zt - 1 ) * za1
        e3w_1d   =  za1
        e3t_1d   =  za1
         
    else :                                # Madec & Imbard 1996 function
        if not ldbletanh :
            zw       = np.arange (jpk)+1.
            zt       = zw + 0.5
            gdepw_1d = ( zsur + za0 * zw + za1 * zacr * np.log ( np.cosh( (zw-zkth) / zacr ) )  )
            gdept_1d = ( zsur + za0 * zt + za1 * zacr * np.log ( np.cosh( (zt-zkth) / zacr ) )  )
            e3w_1d   =          za0      + za1        * np.tanh(       (zw-zkth) / zacr   )
            e3t_1d   =          za0      + za1        * np.tanh(       (zt-zkth) / zacr   )
            
        else :
            zw = np.arange (jpk) + 1.
            zt = zw + 0.5
            # Double tanh function
            gdepw_1d = ( zsur + za0 * zw + za1 * zacr * np.log ( np.cosh( (zw-zkth ) / zacr  ) )    \
                                                + za2 * zacr2* np.log ( np.cosh( (zw-zkth2) / zacr2 ) )  )
            gdept_1d = ( zsur + za0 * zt + za1 * zacr * np.log ( np.cosh( (zt-zkth ) / zacr  ) )    \
                                                + za2 * zacr2* np.log ( np.cosh( (zt-zkth2) / zacr2 ) )  )
            e3w_1d   =          za0      + za1        * np.tanh(       (zw-zkth ) / zacr  )      \
                                         + za2        * np.tanh(       (zw-zkth2) / zacr2 )
            e3t_1d   =          za0      + za1        * np.tanh(       (zt-zkth ) / zacr  )      \
                                         + za2        * np.tanh(       (zt-zkth2) / zacr2 )
                
          
        gdepw_1d [0] = 0.                    # force first w-level to be exactly at zero
       

     # if ln_isfcav :
     #    # need to be like this to compute the pressure gradient with ISF. If not, level beneath the ISF are not aligned (sum(e3t) /= depth)
     #    # define e3t_0 and e3w_0 as the differences between gdept and gdepw respectively


         
     #    DO jk = 1, jpkm1
     #        e3t_1d(jk) = gdepw_1d(jk+1)-gdepw_1d(jk)
        
     #     e3t_1d(jpk) = e3t_1d(jpk-1)   # we don't care because this level is masked in NEMO

     #     DO jk = 2, jpk
     #        e3w_1d(jk) = gdept_1d(jk) - gdept_1d(jk-1)
     #     END DO
     #     e3w_1d(1  ) = 2. * (gdept_1d(1) - gdepw_1d(1))
     #  END IF 

    ##gm BUG in s-coordinate this does not work#
      # deepest/shallowest W level Above/Below ~10m
      #zrefdep = 10. - 0.1 * MINVAL( e3w_1d )                   # ref. depth with tolerance (10% of minimum layer thickness)
      #nlb10 = MINLOC( gdepw_1d, mask = gdepw_1d > zrefdep, dim = 1 ) # shallowest W level Below ~10m
      #nla10 = nlb10 - 1                                              # deepest    W level Above ~10m
