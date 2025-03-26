#
'''
Copyright (c) 2012 Michel Crucifix <michel.crucifix@uclouvain.be>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject
the following conditions:

The above copyright notice and this permission notice shall be
incluudedin all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND INFRINGEMENT
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

When using this package for actual applications, always
cite the authors of the original insolation solutions 
Berger, Loutre and/or Laskar, see details in man pages

----------------------------------------------------------------------
R Code developed for R version 2.15.2 (2012-10-26) -- "Trick or Treat"

https://www.rdocumentation.org/packages/palinsol/versions/0.93
https://cran.r-project.org/web/packages/palinsol/palinsol.pdf

Translated (partially) to Python/numpy by Olivier Marti
---------------------------------------------------------------------- 
'''

import numpy as np

# Utilities
deg2rad = np.deg2rad
rad2deg = np.rad2deg

pi = np.pi

## Deliberate difference with Berger et al. (2010), who consider the SIDERAL_YEAR
SIDERAL_YEAR = 365.25636 
TROPIC_YEAR  = 365.24219876
YEAR         = TROPIC_YEAR

# Default for 1950 CE
ECC   = 0.01588923
VARPI = deg2rad (135.6181)
EPS   = deg2rad (23.196057)
SOLAR = 1365.0

# ======================================================================================

def InsolFromDay (day, lat=deg2rad(45), eps=EPS, varpi=VARPI, ecc=ECC, S0=SOLAR) :
    '''Returns daily mean incoming solar insolation after Berger (1978) 
    eps     : obliquity (radians)
    varpi   : longitude of perihelion (radians)
    ecc     : eccentricity 
    day     : day of the year
    lat     : latitude
    S0      : Total solar irradiance
    unit    : unit if input angles
    returns : daily mean incoming solar radiation at the top of the atmosphere
               in the same unit as S0. 
    '''
    
    lon = day2lon (day=day, eps=eps, varpi=varpi, ecc=ecc)
    InsolFromDay = Insol (lat=lat, lon=lon, eps=eps, varpi=varpi, ecc=ecc, S0=S0)
    return InsolFromDay
 
def Insol (lat=deg2rad(45), lon=deg2rad(180), eps=EPS, varpi=VARPI, ecc=ECC, S0=SOLAR) :
    '''
    Returns daily mean incoming solar insolation after Berger (1978) 
    eps     : obliquity (radians)
    varpi   : longitude of perihelion (radians)
    ecc     : eccentricity 
    lon     : true solar longitude 
        (radians; = pi/2   for summer solstice )
                    pi     for autumn equinox  )
                    3.pi/2 for winter solstice )
                    0      for spring equinox  )
    lat     : latitude
    S0      : Total solar irradiance
    unit    : unit if input angles
    returns : daily mean incoming solar radiation at the top of the atmosphere
               in the same unit as S0. 
    '''
    nu             = lon - varpi
    rho            = (1.0-ecc*ecc) / (1.0+ecc*np.cos(nu))
    sindelta       = np.sin (eps) * np.sin (lon)
    cosdelta       = np.sqrt (1.0-sindelta*sindelta)
    
    sinlatsindelta = np.sin (lat) * sindelta
    coslatcosdelta = np.cos (lat) * cosdelta
    cosH0          = np.minimum (np.maximum (-1.0, -sinlatsindelta/coslatcosdelta), 1.0)
    sinH0          = np.sqrt (1.0-cosH0*cosH0)
    H0             = np.arccos (cosH0)

    Insol = S0 / (np.pi*rho*rho) * (H0*sinlatsindelta+coslatcosdelta*sinH0)
    return Insol
 
def dtdnu (lon, eps=EPS, varpi=VARPI, ecc=ECC) :
    '''Time increment corresponding a tsl increment'''
    nu    = lon - varpi
    xec   = ecc*ecc
    rho   = (1-xec)/(1+ecc*np.cos(nu))
    dtdnu = rho*rho/np.sqrt(1.-xec)
    return dtdnu
 
# Provides an insolation times series
# astrosol = astronomical solution (defaults to Ber78)
# times = times in yr epoch 1950.0
# ...   = any argument passed to Insol
#InsolWrapper <- function(times=times,astrosol=ber78,...)
#  sapply (times,function(tt)  Insol(astrosol(tt),...) )

def calins (lat=deg2rad(65), eps=EPS, varpi=VARPI, ecc=ECC) :
    ''' Caloric_insolation
    integrated insolation over the 180 days receiving above median insolation
    '''
    ins = list (map (lambda x:           Insol (lat=lat, lon=x, eps=eps, varpi=varpi, ecc=ecc) , L))
    dt  = list (map (lambda x: rad2deg ( dtdnu (         lon=x, eps=eps, varpi=varpi, ecc=ecc)), L))
    ins = np.array (ins)
    dt  = np.array (dt)
#
    # Reste à piger ce que fait MatLab sur les 3 instructions qui suivent
    # idx  = sort (ins,decreasing=TRUE,index.return=TRUE)$ix
    # cs   = cumsum (dt[idx])
    # idx  = which (cs <= 180)  ## The 180 days whose cumulative length is half total
                                ## year length, picking days by decreasing order of 
                                ## insolation. 
    XCORR = 86.4 *  YEAR / 360.
    calins = np.sum (ins[idx]*dt[idx]) * XCORR  ## Result in kJ

    return calins

def thrins (lat=deg2rad(65.), threshold=400, eps=EPS, varpi=VARPI, ecc=ECC) :
    '''
    Integrated insolation over the 360 days receiving insolation above a threshold
    Results in kJ
    '''
    L = deg2rad (np.linspace (1, 360, 360))
    ins = list (map (lambda x:           Insol (lat=lat, lon=x, eps=eps, varpi=varpi, ecc=ecc) , L))
    dt  = list (map (lambda x: rad2deg ( dtdnu (         lon=x, eps=eps, varpi=varpi, ecc=ecc)), L))
    ins = np.array (ins)
    dt  = np.array (dt)
    #    
    idx    = np.where (ins >= threshold)
    XCORR  = 86.4 * YEAR / 360.0
    thrins = np.sum (ins[idx] * dt[idx]) * XCORR   ## Result in kJ
    
    return thrins

def Insol_l1l2 (lon1=deg2rad(0.), lon2=deg2rad(360.), lat=deg2rad(65.), avg=False, ell=True,
                    eps=EPS, varpi=VARPI, ecc=ECC) :
    ''' Warning : dont work !!!
    Conversion from MatLab no finished

    Time-integrated between two true solar longitude bounds

    lon1 and lon2 : longitudes bonds in radians. Defaults to annual average.
    discretize longitude intreval in N intervals
    avg : supplies an average insolation
    ell : defaults to TRUE, use elliptic integrals for calculation (much faster)
          rather than trapeze rule integral.  Currently incompatible
          with avg=TRUE (this can be fixed later)
    '''
    if (ell) :
        # Use elliptic integrals
        if (lon1 < lon2) :
            INT = W (lat, lon2, eps=eps, ecc=ecc ) - \
                  W (lat, lon1, eps=eps, ecc=ecc )
        else :     
            INT = W (lat, 2.0*np.pi, eps=eps, ) - \
                  W (lat, lon1     , eps=eps, ) + \
                  W (lat, lon2     , eps=eps, )
                  
    if (avg) :
        DT = l2day (lon2, eps=eps, varpi=varpi, ecc=ecc) - l2day (lon1, eps=eps, varpi=varpi, ecc=ecc)
        if DT <= 0 : DT = DT+360.
        XCORR  = 86.4 *  YEAR / 360.0
        INT = INT / (DT*XCORR) ## result in W/m2
    else :
        ## Integration using trapeze rule
        Dl = np.mod (lon2-lon1, 2.0*np.pi)
        if Dl == 0 : Dl = 2.0*np.pi
        N =  np.int32 ( np.ceil (Dl* 180.0/np.pi))
        dl = Dl/N
        L  = np.linspace (lon1, lon2, N)

        ins = list (map (lambda x:           Insol (lat=lat, lon=x, eps=eps, varpi=varpi, ecc=ecc) , L ))
        dt  = list (map (lambda x: rad2deg ( dtdnu (         lon=x, eps=eps, varpi=varpi, ecc=ecc)), L )) 
        ins = np.array (ins)
        dt  = np.array (dt)
        iss = ins * dt
        XCORR = 86.4 * YEAR / 360.0
        INT = (np.sum(iss[1:N-1]) + 0.5 *iss[1] + 0.5 *iss[N-1]) * dl * XCORR  ## result in kJ
        
        if (avg) :
            DT =  (np.sum(dt[1:N-1]) + 0.5 * dt[0] + 0.5 * dt[N]) * dl * XCORR
            INT = INT / DT ## result in W/m2
      
    return INT

def day2lon (day, eps=EPS, varpi=VARPI, ecc=ECC) :
    '''
    Converts day to longitude.
    Source : Berger 78, from Brower and Clemence.
    day using a 360-d calendar
    here :  day of spring equinox is in fact conventionally 80
    '''
    
    # Definitions for speed-up
    xee = ecc*ecc
    xec = xee * ecc
    xse = np.sqrt (1.0-xee)
    # True anomaly of vernal equinox point 
    xlp = -varpi 
    # Mean anomaly  of the vernal equinox point
    lm =  xlp - 2.*((ecc/2 + xec/8)*(1+xse)*np.sin(xlp) - 
          xee/4.*(0.5+xse)*np.sin(2*xlp) +
          xec/8.*(1/3+xse)*np.sin(3*xlp) )

    # Mean anomaly  of the point considered
    M = (day - 80.) * np.pi/ 180. + lm 

    # TRUE anomaly of the point considered
    V = M + (2.0*ecc-xec/4.)*np.sin(M) + \
          5.0/4.0*xee*np.sin(2.*M) + \
          13.0/12.0*xec*np.sin(3.0*M)

    # True longitude of the point considered
    L = np.mod (V + varpi, 2.0*np.pi)
    return L

def lon2day (lon, eps=EPS, varpi=VARPI, ecc=ECC) :
    '''
    Converts true solar longitude to day
    source :  Brouwer and Clemence
    '''
    # Definitions for speed-up
    xee = ecc*ecc
    xec = xee * ecc
    xse = np.sqrt (1.-xee)
    # True anomaly
    xlp = - varpi 
    # Mean anomaly  of the vernal equinox point
    lm =  xlp - 2.*((ecc/2 + xec/8)*(1.0+xse)*np.sin(xlp) -  \
          xee/4*(0.5+xse)*np.sin(2*xlp) + \
          xec/8*(1/3+xse)*np.sin(3*xlp) )

    # True anomaly of the point considered
    V = np.mod (lon + xlp, 2.0*np.pi)

    # Mean anomaly  of the point considered
    M =  V - 2.*((ecc/2 + xec/8)*(1+xse)*np.sin(V) - \
          xee/4*(0.5+xse)*np.sin(2*V) + \
          xec/8*(1/3+xse)*np.sin(3*V) )

    # Anomaly in deg. elapsed between vernal equinox point and point

    day = np.mod (80.0 + (M - lm)  * 360.0/(2.0*np.pi), 360.0)
    return day

def date_of_perihelion (eps=EPS, varpi=VARPI, ecc=ECC) :
    # Definitions for speed-up
    xee = ecc*ecc
    xec = xee * ecc
    xse = np.sqrt(1.-xee)    # true anomaly
    xlp= - varpi 
    # mean anomaly  of the vernal equinox point
    lm =  xlp - 2.*((ecc/2 + xec/8)*(1+xse)*np.sin(xlp) - 
          xee/4*(0.5+xse)*np.sin(2*xlp) +
          xec/8*(1/3+xse)*np.sin(3*xlp) )

    # Mean anomaly  of the point considered
    M =  0.

    # Anomaly in deg. elapsed between vernal equinox point and perihelion passage

    DAY = np.mod ( 80 + (M - lm)  * 360.0/(2*np.pi) , 360.0)
    
    return DAY

def Insol_d1d2 (day1, day2, lat=65*np.pi/180., avg=False, eps=EPS, varpi=VARPI, ecc=ECC) :
      '''Like Insol but given days rather than longitudes'''
      lon1 = day2lon (day1, eps=eps, varpi=varpi, ecc=ecc)
      lon2 = day2lon (day2, eps=eps, varpi=varpi, ecc=ecc)
      Insol_d1d2 = Insol_l1l2 (lat=lat, lon1=lon1, lon2=lon2, avg=avg, eps=eps, varpi=varpi, ecc=ecc) 
      return Insol_d1d2

# if (isTrue(getOption('debug')) && interactive())
# { t <- seq(-1e6,0,by=1e3)
#   F <- InsolWrapper(t)

def W (xx, n=3, eps=EPS, varpi=VARPI, ecc=ECC, S0=SOLAR) :
    # Require(gsl) ## gnu scientific library ported by Robin Hankin. Thank you Robin !!!
    # Inb Python : require pygsl
    pi2  = np.pi/2.0
    H00  = pi2
    seps = np.sin (eps)
    ceps = np.cos (eps)
    sphi = np.sin (phi)
    cphi = np.cos (phi)
    tphi = sphi/cphi

    def eq34 (xx) :
      sxx    = np.sin(xx)
      cxx    = np.cos(xx)
      k      = seps/cphi
      sesl   = seps*sxx
      tdelta = sesl / np.sqrt(1-sesl*sesl)
      H0     = np.arccos(-tphi*tdelta)
      Flk    = ellint_F(xx,k)
      Elk    = ellint_E(xx,k)
      
      eq34 = sphi*seps*(H00-cxx*H0) + cphi*Elk + \
             sphi*tphi*Flk - sphi*tphi*ceps*ceps*ellint_P (xx, k, -seps*seps)

      return eq34
  
    def eq40 (xx) :
        ## The max(-1, min(1, 
        ## is to account for a numerical artefact when xx = xx1,2,3,4
      
        sxx = np.sin(xx)
        cxx = np.cos(xx)
      
        k =  seps/cphi
        k1 = cphi/seps
        psi  = np.arcsin(max(-1, np.minimum(1,k*sxx)))
      
        if cxx < 0 :
            psi = pi-psi
      
        sesl   = seps*sxx
        tdelta = sesl / np.sqrt(1-sesl*sesl)
        H0     = np.arccos (np.maximum (-1.0, np.minimum (1.0,-tphi*tdelta)))
        Fpk    = ellint_F (psi, k1)
        Epk    = ellint_E (psi, k1)
        Pipk   = ellint_P (psi, k1, -cphi*cphi)
        
        eq40 = ( sphi*seps*(H00-cxx*H0) + seps*Epk + \
            ceps* ceps/seps * Fpk - sphi*sphi*ceps*ceps/seps*Pipk)

        return eq40
      
    def eq38 (xx) :
          eq38 = np.pi * sphi*seps*np.cos(xx)
          return eq38


    T   = YEAR * 0.086400 * 1000.
    xes = np.sqrt (1.0-ecc*ecc)
    W0  = S0*T/(2.0*np.pi*np.pi*xes)

    if (phi >= (pi2-eps) or phi <= -(pi2-eps) ) :
        ## Above polar circle 
        xx1 = ( np.arcsin (cphi/seps) )
        xx2 = np.pi - xx1
        xx3 = np.pi + xx1
        xx4 = 2.0*np.pi - xx1
  
        WW=0

        if (xx > 0)   :
            WW = WW + eq40 (min(xx,xx1))
        if (xx > xx2) :
            WW = WW + eq40 (min(xx,xx3)) - eq40(xx2)
        if (xx > xx4) :
            WW = WW + eq40 (xx) - eq40(xx4)
              
        if phi >= (pi2-eps) :
            ## northern hemisphere
            if (xx > xx1) :
                WW = WW + eq38 (min(xx,xx2)) - eq38(xx1)
        else :
            ## Southern hemisphere
            if (xx > xx3) :
                WW = WW + eq38 (min(xx,xx4)) - eq38(xx3)
              
        WW = W0*WW 

    else :
          ## Outside polar circle
          WW = W0 * eq34(xx)
          
    return W
