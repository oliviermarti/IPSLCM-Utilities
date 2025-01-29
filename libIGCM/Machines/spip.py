if not User   :
    User = LocalUser
if Source :
    IGCM_OUT_name = ''
else      :
    IGCM_OUT_name = 'IGCM_OUT'
if not ARCHIVE    :
    ARCHIVE     = os.path.join ( os.path.expanduser ('~'), 'Data'    )
if not SCRATCHDIR :
    SCRATCHDIR  = os.path.join ( os.path.expanduser ('~'), 'Data' )
if not R_BUF      :
    R_BUF       = os.path.join ( os.path.expanduser ('~'), 'Data'    )
if not R_FIG      :
    R_FIG       = os.path.join ( os.path.expanduser ('~'), 'Data'    )
    
if not STORAGE    :
    STORAGE     = ARCHIVE
if not R_IN       :
    R_IN        = os.path.join ( os.path.expanduser ('~'), 'Data', 'IGCM' )
if not R_GRAF or 'http' in R_GRAF :
    R_GRAF      = os.path.join ( os.path.expanduser ('~'), 'GRAF', 'DATA' )
if not DB         :
    DB          = os.path.join ( os.path.expanduser ('~'), 'marti', 'GRAF', 'DB' )
if not TmpDir     :
    TmpDir      = os.path.join ( os.path.expanduser ('~'), 'Scratch' )
