# -*- coding: utf-8 -*-
'''
Utilitaires

author: olivier.marti@lsce.ipsl.fr

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
personal.
'''

from typing import Union, Literal

import numpy as np
import xarray as xr
import xrft
import statsmodels.api as sm

RPI:float   = np.pi
RAD:float   = np.deg2rad (1.0)
DAR:float   = np.rad2deg (1.0)
REPSI:float = np.finfo(np.float64).resolution.item()

def detrend (ztab:xr.DataArray, dim:str, detrend_type:str='linear') -> tuple[xr.DataArray, xr.DataArray] :
    '''
    Detrend a signal

    ztab       : multi-dimensionnal xarray data array
                    The data to be transformed
    dim        : str
                 The dimension along which to take the transformation.
                 If the inputs is a dask arrays, the array must not be
                    chunked along this dimension

    detrend_type: 'linear' or 'constant'

    Returns
    -------
    ztab_d      : the detrended signal
    ztab_t      : the trend (i.e. a line)
    '''
    ztab_d = xrft.detrend (ztab, dim=dim, detrend_type=detrend_type )
    ztab_t = ztab - ztab_d
    return ztab_d, ztab_t


def mirror ( ztab:xr.DataArray, dim:str, use_coord=False) -> xr.DataArray :
    '''
    Mirror a signal along a dimension.

    ztab       : xarray data array
                 The data to be mirrored
    dim        : str
                 The dimension along which to mirror the data
    use_coord  : bool
                 If True, use original coordinates; if False, use indices

    Returns
    -------
    ztab2      : mirrored data array
    '''
    ztab2  = xr.concat ( ( ztab.isel({dim:slice(None,None,-1)}), ztab, ), dim=dim)
    xxt   = ztab.coords[dim]
    if use_coord :
        xx2 = xr.concat ( ( (xxt-(xxt[-1]-xxt[0])), xxt), dim=dim)
    else :
        xx2 = np.arange ( -len(xxt), len(xxt) )
    ztab2  = ztab2.assign_coords ( {dim:xx2} )
    return ztab2

def fft_fft (tab:xr.DataArray, dim:str, fill_gap:bool=False, use_coord:bool=False, return_aux=True,
             Debug=False, chunks_to_segments=False) -> tuple[xr.DataArray,xr.DataArray]|xr.DataArray :
    '''
    Run a fft transform on a xarray DataArray
    Data are mirrored to force the periodicity of the signal

    tab        : multi-dimensionnal xarray data array
                    The data to be transformed
    dim        : str
                 The dimension along which to take the transformation.
                 If the inputs is a dask arrays, the array must not be
                    chunked along this dimension
    fill_gap   : if True, replace Nan values by interpolation. Default: False
    use_coord  : if True , frequencies and periods are the same units as dim
                 if False, frequencies and periods are in number of time steps
                 Default: False
    Returns
    -------
    power      : the power spectrum
    if return_aux==True, returns :
       freqs   : frequencies
    '''
    ztab  = tab
    xxt   = ztab.coords[dim]
    if fill_gap :
        if Debug : print (' fft_filter: Fill gaps')
        ztab = ztab.interpolate_na (dim=dim, method='linear', limit=None, use_coordinate=False,
                                    max_gap=None, keep_attrs=None)
        ztab = ztab.fillna (0.)
    if Debug : print (' fft_fft: Remove and store mean 1')
    ztab_mean = ztab.mean (dim=dim)
    if Debug : print (' fft_fft: Remove and store mean 2')
    ztab     -= ztab_mean
    if Debug : print ('  fft_fft: Detrend, and store trend' )
    ztab_d     = xrft.detrend (ztab, dim=dim, detrend_type='linear'  )
    ztab_trend = ztab - ztab_d
    ztab       = ztab_d
    if Debug : print (' fft_fft: Mirror data')
    ztab2  = xr.concat ( ( ztab.isel({dim:slice(None,None,-1)}), ztab, ), dim=dim)
    del ztab_d, ztab_trend
    if Debug : print ('  fft_fft: Create axis for the mirrored data')
    if use_coord :
        xx2 = xr.concat ( ( (xxt-(xxt[-1]-xxt[0])), xxt), dim=dim)
    else :
        xx2 = np.arange ( -len(xxt), len(xxt) )
    ztab2  = ztab2.assign_coords ( {dim:xx2} )
    if Debug : print (' fft_fft: Detrend')
    ztab2  = xrft.detrend (ztab2, dim=dim, detrend_type='linear'  )

    if Debug : print ('  fft_fft: Direct transform')
    power = xrft.fft (ztab2, dim=dim, true_phase=True, true_amplitude=True, prefix='freq_',
                      chunks_to_segments=chunks_to_segments)
    freqs = power.coords[f'freq_{dim}']
    del ztab2

    if return_aux :
        return power, freqs
    else :
        return power

## ============================================================================
def fft_filter ( tab:xr.DataArray, dim:str, fill_gap:bool=False, use_coord:bool=False,
                     detrend_type:bool=True,
                     min_freq:Union[float,None]=None, max_freq:Union[float,None]=None,
                     min_period:Union[float,None]=None, max_period:Union[float,None]=None,
                     keep_trend:bool=True, return_aux:bool=False, Debug:bool=False,
                     chunks_to_segments:bool=False
                     ) -> Union[xr.DataArray, tuple[xr.DataArray,xr.DataArray,xr.DataArray,xr.DataArray]] :
    '''
    Run a fft filter on a xarray DataArray
    Data are mirrored to force the periodicity of the signal

    tab        : multi-dimensionnal xarray data array
                    The data to be transformed
    dim        : str
                 The dimension along which to take the transformation.
                 If the inputs is a dask arrays, the array must not be
                    chunked along this dimension
    fill_gap   : if True, replace Nan values by ionterpolation. Default: False
    keep_trend : if True, keep the trend of the signal. Only for low pass filter. Default: True
    return_aux : if True, returns intermediate variables for debugging. Default: False
    use_coord  : if True , frequencies and periods are the same units as dim
                 if False, frequencies and periods are in number of time steps
                 Default: False
    min_freq   : minimum frequency for a high-pass filtering
    max_freq   : maximum frequency for a low-pass filtering
    min_period : minimum period for a low-pass filtering
    max_period : maximum period for a high-pass filtering
    min_freq and max_period are mutually exclusive. And max_freq and min_period.

    Returns
    -------
    ftab : `xarray.DataArray`
        The filtered tab, with same dimensions, coordinates and attributes

    if return_aux==True, returns :
       power      : the power spectrum
       power_filt : truncated power spectrum
       freqs      : frequencies
    '''
    #- Check parameters
    if min_freq and max_period :
        raise ValueError ( 'both min_freq and max_period are defined. Please choose one' )
    if max_freq and min_period :
        raise ValueError ( 'both max_freq and min_period are defined. Please choose one' )

    ztab  = tab
    xxt   = ztab.coords[dim]
    if fill_gap :
        if Debug : print (' fft_filter: Fill gaps')
        ztab = ztab.interpolate_na (dim=dim, method='linear', limit=None, use_coordinate=False,
                                    max_gap=None, keep_attrs=None)
        ztab = ztab.fillna (0.)
    if  Debug: print (' fft_filter: Remove and store mean')
    ztab_mean  = ztab.mean (dim=dim)
    ztab = ztab - ztab_mean

    ztab_d     = xrft.detrend (ztab, dim=dim, detrend_type='linear' )
    ztab_trend = ztab - ztab_d
    if detrend_type :
        if Debug : print (' fft_filter: Detrend, and store trend' )
        ztab   = ztab_d
    if Debug : print (' fft_filter: Mirror data')
    ztab2  = xr.concat ( ( ztab.isel({dim:slice(None,None,-1)}), ztab, ), dim=dim)
    if Debug : print (' fft_filter: Create axis for the mirrored data')
    if use_coord :
        xx2 = xr.concat ( ( (xxt-(xxt[-1]-xxt[0])), xxt), dim=dim)
    else :
        xx2 = np.arange ( -len(xxt), len(xxt) )
    ztab2  = ztab2.assign_coords ( {dim:xx2} )
    ztab2_mean = ztab2.mean (dim=dim)
    ztab2 = ztab2 - ztab2_mean
    if detrend_type :
        if Debug : print (' fft_filter: Detrend')
        ztab2  = xrft.detrend (ztab2, dim=dim, detrend_type='linear'  )

    if Debug : print (' fft_filter: Direct transform')
    power = xrft.fft (ztab2, dim=dim, true_phase=True, true_amplitude=True, prefix='freq_',
                      chunks_to_segments=chunks_to_segments)

    freqs = power.coords[f'freq_{dim}']

    if max_period and not min_freq : min_freq = 1./max_period
    if min_period and not max_freq :
        if min_period > 0. : max_freq = 1./min_period
    if min_freq and not max_period : max_period = 1./min_freq
    if max_freq and not min_period : min_period = 1./max_freq

    if Debug : print (f' fft_filter: {min_freq=} {max_freq=} {min_period=} {max_period=}')

    power_filt = power.copy()
    if min_freq : power_filt = xr.where (np.abs(freqs) < min_freq, 0., power_filt)
    if max_freq : power_filt = xr.where (np.abs(freqs) > max_freq, 0., power_filt)

    if Debug : print (' fft_filter: Inverse transform' )
    #nn = power_filt[f'freq_{dim}'].size
    ftab2 = xrft.ifft (power_filt, dim=f'freq_{dim}', true_phase=True, true_amplitude=True,
                           lag=0, chunks_to_segments=chunks_to_segments).compute().real
    ftab  = ftab2.isel ({dim:slice(len(xxt),None)}) + ztab2_mean
    ftab = ftab.assign_coords ( {dim:xxt} )

    if not min_freq and keep_trend and detrend_type :
        ftab = ftab + ztab_mean
        ftab = ftab + ztab_trend

    for attr in ztab.attrs : ftab.attrs[attr] = ztab.attrs[attr]

    ftab.attrs.update (
         {'Comment':f'{ztab.name} filtered with fft filter and mirroring',
          'min_freq':str(min_freq), 'max_freq':str(max_freq),
          'min_period':str(min_period), 'max_period':str(max_period)} )

    if return_aux :
        return ftab, power, power_filt, freqs
    else :
        return ftab

def lowess ( endog:xr.DataArray, exog:np.ndarray|xr.DataArray|None=None,
             frac:float|None=None, length:int|None|float=None, it:int=3,
             bounds:bool=False, N:int=200, confidence_interval=0.95,
             delta:float=0.0, xvals:float|np.ndarray|None=None,
             is_sorted:bool=False, missing:Literal["drop","none","raise"]="drop",
             return_sorted:bool=True, Debug:bool=False ) :
    '''
    Implement lowless filter for 1D xarray.

    Parameters
    ----------
    endog : 1-D xarray array
        The y-values of the observed points
    exog : 1-D xarray or numpy array
        The x-values of the observed points
    frac : float
        Between 0 and 1. The fraction of the data used
        when estimating each y-value.
    length : int
        Length of the filter. Use to compute an ad hoc value of frac
        as frac = length/len(endog)
    it : int
        The number of residual-based reweightings
        to perform.
    bounds : bool
        If true, use a boostrap method to evaluate the confidence interval
    N : int
        If bounds, number of draws for the boostrap method
    confidence_interval : float
        Confidence interval
    delta : float
        Distance within which to use linear-interpolation
        instead of weighted regression.
    xvals: 1-D numpy array
        Values of the exogenous variable at which to evaluate the regression.
        If supplied, cannot use delta.
    is_sorted : bool
        If False (default), then the data will be sorted by exog before
        calculating lowess. If True, then it is assumed that the data is
        already sorted by exog. If xvals is specified, then it too must be
        sorted if is_sorted is True.
    missing : str
        Available options are 'none', 'drop', and 'raise'. If 'none', no nan
        checking is done. If 'drop', any observations with nans are dropped.
        If 'raise', an error is raised. Default is 'drop'.
    return_sorted : bool
        If True (default), then the returned array is sorted by exog and has
        missing (nan or infinite) observations removed.
        If False, then the returned array is in the same length and the same
        sequence of observations as the input array.

    Returns
    -------
    If endog is an xarray, returns an xarray with proper coordinates
    If endog is a numpy array, sea documenation of sm.nonparametric.lowess for return values
    If bounds, return also upper and lower limits of the confidence interval

    '''
    ldebug = Debug

    if len (endog.shape) != 1 :
        raise ValueError ( f'Works only for 1D arrays. You have {len(endog.dims)} dimensions' )

    if frac is None :
        if length is None :
            frac = 2./3.
        else :
            frac = length / len(endog)
    else :
        if length is not None :
            raise ValueError ( 'Both frac and length are specified. Give only one value')

    if xvals is None : xvals = exog # pyright: ignore[reportAssignmentType]


    zz = sm.nonparametric.lowess (endog=endog, exog=exog, frac=frac, it=it, delta=delta, xvals=xvals,
                                  is_sorted=is_sorted, missing=missing, return_sorted=return_sorted)

    if bounds :
        # Perform bootstrap resamplings of the data
        # and  evaluate the smoothing at a fixed set of points
        smoothed_values = np.empty ((N, len(xvals))) # pyright: ignore[reportArgumentType]
        for ii in range(N):
            sample    = np.random.choice(len(endog), len(endog), replace=True)
            sampled_x = exog [sample] # pyright: ignore[reportOptionalSubscript]
            sampled_y = endog[sample]

            smoothed_values[ii] = sm.nonparametric.lowess (
                exog=sampled_x, endog=sampled_y,
                frac=frac, it=it, delta=delta, xvals=xvals, is_sorted=is_sorted,
                missing=missing, return_sorted=return_sorted )

        # Get the confidence interval
        sorted_values = np.sort (smoothed_values, axis=0)
        bound  = int (N * (1 - confidence_interval) / 2)
        zz_b = sorted_values[bound - 1]
        zz_t = sorted_values[-bound]

    if isinstance (endog, xr.DataArray) :
        if ldebug : print ( 'endog xarray' )
        if return_sorted :
            if ldebug : print ( '  return sorted' )
            if xvals is None :
                if ldebug : print ( '    xvals is None' )
                zz_x = zz[:,0]
                zz_y = xr.DataArray ( zz[:,1], dims=endog.dims, coords=[zz_x,])
                zz_x = xr.DataArray ( zz_x   , dims=endog.dims, coords=[zz_x,])
                if bounds :
                    zz_b = xr.DataArray ( zz_b, dims=endog.dims, coords=[zz_x,])
                    zz_t = xr.DataArray ( zz_t, dims=endog.dims, coords=[zz_x,])
            else :
                if ldebug : print ( 'xvals is not None' )
                zz_x = xvals
                zz_y = xr.DataArray ( zz  , dims=endog.dims, coords=[zz_x,]) # pyright: ignore[reportArgumentType]
                zz_x = xr.DataArray ( zz_x, dims=endog.dims, coords=[zz_x,]) # pyright: ignore[reportArgumentType]
                if bounds :
                    zz_b = xr.DataArray ( zz_b, dims=endog.dims, coords=[zz_x,])
                    zz_t = xr.DataArray ( zz_t, dims=endog.dims, coords=[zz_x,])
        else :
            if xvals is None :
                zz_x = exog
                zz_y = xr.DataArray ( zz  , dims=endog.dims, coords=[zz_x,]) # pyright: ignore[reportArgumentType]
                zz_x = xr.DataArray ( zz_x, dims=endog.dims, coords=[zz_x,]) # pyright: ignore[reportArgumentType]
                if bounds :
                    zz_b = xr.DataArray ( zz_b, dims=endog.dims, coords=[zz_x,])
                    zz_t = xr.DataArray ( zz_t, dims=endog.dims, coords=[zz_x,])
            else :
                zz_x = xvals
                zz_y = xr.DataArray ( zz  , dims=endog.dims, coords=[zz_x,]) # pyright: ignore[reportArgumentType]
                zz_x = xr.DataArray ( zz_x, dims=endog.dims, coords=[zz_x,]) # pyright: ignore[reportArgumentType]
                if bounds :
                    zz_b = xr.DataArray ( zz_b, dims=endog.dims, coords=[zz_x,])
                    zz_t = xr.DataArray ( zz_t, dims=endog.dims, coords=[zz_x,])
        if isinstance (endog, xr.DataArray) :
            zz_y.attrs.update ( endog.attrs )
            zt = f"{len(xvals)} values>" if xvals is not None else "None" # pyright: ignore[reportArgumentType]
            zz_y.attrs.update (
             {'LOWLESS':f'{frac=}, {it=}, {delta=}, xvals={zt}, {is_sorted=}, {missing=}, {return_sorted=}'} )

            name = zz_y.coords[zz_y.dims[0]].name
            if 'attrs' in dir(exog) :
                zz_y[name].attrs.update (exog.attrs)
            zz_r = zz_y

    else :
        if ldebug : print ( 'endog numpy' )
        if return_sorted :
            if ldebug : print ( 'return sorted' )
            if xvals is not None :
                if ldebug : print ( 'endog numpy' )
                zz_r = [ xvals, zz]
            else :
                if ldebug : print ( 'not return_sorted' )
                zz_r = [ exog, zz ]
        else :
            if xvals is not None :
                if ldebug : print ( 'xvals not None' )
                zz_r = [ xvals, zz ]
            else :
                if ldebug : print ( 'xvals None' )
                zz_r = zz


    if bounds :
        return zz_r, zz_t, zz_b
    else :
        return zz_r
