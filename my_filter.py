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

from typing import Union

import numpy as np
import xarray as xr
import xrft

RPI   = np.pi
RAD   = np.deg2rad (1.0)
DAR   = np.rad2deg (1.0)
REPSI = np.finfo (1.0).eps

def detrend (ztab:xr.DataArray, dim:str, detrend_type:str='linear') :
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
    ztab_d      : the trend (i.e. a line)
    '''
    ztab_d = xrft.detrend (ztab, dim=dim, detrend_type=detrend_type )
    ztab_t = ztab - ztab_d
    return ztab_d, ztab_t


def mirror ( ztab:xr.DataArray, dim:str, use_coord=False) :
             
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
    if Debug : print (' fft_fft: Remove and store mean')
    ztab_mean = ztab.mean (dim=dim)
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
def fft_filter ( tab:xr.DataArray, dim:str, fill_gap:bool=False, use_coord:bool=False, detrend:bool=True,
                     min_freq:Union[float,None]=None, max_freq:Union[float,None]=None, 
                     min_period:Union[float,None]=None, max_period:Union[float,None]=None,
                     keep_trend:bool=True, return_aux:bool=False, Debug:bool=False,
                     chunks_to_segments:bool=False) :
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
    if detrend : 
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
    if detrend :
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
    nn = power_filt[f'freq_{dim}'].size
    ftab2 = xrft.ifft (power_filt, dim=f'freq_{dim}', true_phase=True, true_amplitude=True,
                           lag=0, chunks_to_segments=chunks_to_segments).compute().real
    ftab  = ftab2.isel ({dim:slice(len(xxt),None)}) + ztab2_mean
    ftab = ftab.assign_coords ( {dim:xxt} )

    if not min_freq and keep_trend and detrend :
        ftab = ftab + ztab_mean
        ftab = ftab + ztab_trend

    for attr in ztab.attrs : ftab.attrs[attr] = ztab.attrs[attr]

    ftab.attrs.update ( {'Comment':f'{ztab.name} filtered with fft filter and mirroring',
        'min_freq':str(min_freq), 'max_freq':str(max_freq), 'min_period':str(min_period), 'max_period':str(max_period)} )

    if return_aux : 
        return ftab, power, power_filt, freqs
    else :
        return ftab

