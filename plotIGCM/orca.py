import numpy as np
nam_config = {
    'orca2' : {
        'key_agrif'   : False, 
        #-----------------------------------------------------------------------
        # namcfg        #   parameters of the configuration
        # -----------------------------------------------------------------------
        'namcfg' : {
            'cp_cfg'      :  "orca", #  name of the configuration
            'jp_cfg'      :       2, #  resolution of the configuration
            'jpidta'      :     182, #  1st lateral dimension ( >: jpi )
            'jpjdta'      :     149, #  2nd    "         "    ( >= jpj )
            'jpkdta'      :      31, #  number of levels      ( >= jpk )
            'jpiglo'      :     182, #  1st dimension of global domain --> i =jpidta
            'jpjglo'      :     149, #  2nd    -                  -    --> j  =jpjdta
            'jpizoom'     :       1, #  left bottom (i,j) indices of the zoom
            'jpjzoom'     :       1, #  in data domain indices
            'jperio'      :       4, #  lateral cond. type (between 0 and 6)
            'nperio'      :       4,
            'jpk'         :      31,
            'jpj'         :     149,
            'jpi'         :     182,
            },
        #-----------------------------------------------------------------------
        # namdom        #   space and time domain (bathymetry, mesh, timestep)
        #-----------------------------------------------------------------------
        'namdom' : { 
            'rn_rdt'      :    5760., #  time step for the dynamics (and tracer if nn_acc=0)
            'nn_closea'   :        1, #  remove (=0) or keep (=1) closed seas and lakes (ORCA)
            'jphgr_msh'   :        0, #  type of horizontal mesh
            'ppglam0'     :   np.nan, #  longitude of first raw and column T-point (jphgr_msh = 1)
            'ppgphi0'     :   np.nan, # latitude  of first raw and column T-point (jphgr_msh = 1)
            'ppe1_deg'    :   np.nan, #  zonal      grid-spacing (degrees)
            'ppe2_deg'    :   np.nan, #  meridional grid-spacing (degrees)
            'ppe1_m'      :   np.nan, #  zonal      grid-spacing (degrees)
            'ppe2_m'      :   np.nan, #  meridional grid-spacing (degrees)
            'ppsur'       :   -4762.96143546300,   #  ORCA r4, r2 and r05 coefficients
            'ppa0'        :     255.58049070440,   # (default coefficients)
            'ppa1'        :     245.58132232490,   #
            'ppkth'       :      21.43336197938,   #
            'ppacr'       :       3.0,             #
            'ppdzmin'     :   np.nan, #  Minimum vertical spacing
            'pphmax'      :   np.nan, #  Maximum depth
            'ldbletanh'   :  False,   #  Use/do not use double tanf function for vertical coordinates
            'ppa2'        :   np.nan, #  Double tanh function parameters
            'ppkth2'      :   np.nan, #
            'ppacr2'      :   np.nan, #
            }
        }, 
        'eorca1' : {
            'key_agrif' : False,
            #-----------------------------------------------------------------------
            # namcfg        #   parameters of the configuration
            #-----------------------------------------------------------------------
            'namcfg' : {
                'cp_cfg'      :  "orca",  #  name of the configuration
                'jp_cfg'      :       1,  #  resolution of the configuration
                'jpidta'      :     362,  #  1st lateral dimension ( >= jpi )
                'jpjdta'      :     332,  #  2nd    "         "    ( >= jpj )
                'jpkdta'      :      75,  #  number of levels      ( >= jpk )
                'jpiglo'      :     362,  #  1st dimension of global domain --> i =jpidta
                'jpjglo'      :     332,  #  2nd    -                  -    --> j  =jpjdta
                'jperio'      :       6,  #  lateral cond. type (between 0 and 6)
                'nperio'      :       6,
                'jpk'         :      75,
                'jpj'         :     332,
                'jpi'          :    382,
                } ,
            #-----------------------------------------------------------------------
            # namdom        #   space and time domain (bathymetry, mesh, timestep)
            #-----------------------------------------------------------------------
            'namdom' : {
                'nn_closea'   :       1,                #  remove (=0) or keep (=1) closed seas and lakes (ORCA)
                'jphgr_msh'   :       0,                #  type of horizontal mesh
                'ppglam0'     :   np.nan,               #  longitude of first raw and column T-point (jphgr_msh = 1)
                'ppgphi0'     :   np.nan,               # latitude  of first raw and column T-point (jphgr_msh = 1)
                'ppe1_deg'    :   np.nan,               #  zonal      grid-spacing (degrees)
                'ppe2_deg'    :   np.nan,               #  meridional grid-spacing (degrees)
                'ppe1_m'      :   np.nan,               #  zonal      grid-spacing (degrees)
                'ppe2_m'      :   np.nan,               #  meridional grid-spacing (degrees)
                'ppsur'       :   -3958.951371276829,   #  ORCA r4, r2 and r05 coefficients
                'ppa0'        :     103.9530096000000,  # (default coefficients)
                'ppa1'        :       2.415951269000000,   #
                'ppkth'       :      15.35101370000000,    #
                'ppacr'       :       7.0,              #
                'ppdzmin'     :   np.nan,               #  Minimum vertical spacing
                'pphmax'      :   np.nan,               #  Maximum depth
                'ppa2'        :     100.7609285000000,  #  Double tanh function parameters
                'ldbletanh'   :  True,   #  Use/do not use double tanf function for vertical coordinates
                'ppkth2'      :      48.02989372000000, #
                'ppacr2'      :      13.00000000000,    #
                'rn_rdt'      :       2700.,            #  time step for the dynamics (and tracer if nn_acc=0)
                'rn_hmin'     :   20.,
                }
            }
    }
