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

import itertools

import numpy as np
import xarray as xr

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patheffects import Stroke, Normal
from matplotlib.projections import PolarAxes
import mpl_toolkits.axisartist.floating_axes as FA
import mpl_toolkits.axisartist.grid_finder   as GF

from libIGCM.options import push_stack as push_stack
from libIGCM.options import pop_stack  as pop_stack

RPI   = np.pi
RAD   = np.deg2rad (1.0)
DAR   = np.rad2deg (1.0)
REPSI = np.finfo (1.0).eps


def distance (lat1, lon1, lat2, lon2, radius:float=1) :
    '''
    Compute distance on the sphere
    '''
    arg      = ( np.sin (RAD*lat1) * np.sin (RAD*lat2)
               + np.cos (RAD*lat1) * np.cos (RAD*lat2) *
                 np.cos(RAD*(lon1-lon2)) )
    
    zdistance = np.arccos (arg) * radius
    
    return zdistance

def aire_triangle (lat0, lon0, lat1, lon1, lat2, lon2) :
    '''
    Aire of a triangle on the sphere
    Girard's formula
    '''
    a = distance (lat0 , lon0, lat1 , lon1)
    b = distance (lat1 , lon1, lat2 , lon2)
    c = distance (lat2 , lon2, lat0 , lon0)

    arg_alpha = (np.cos(a) - np.cos(b)*np.cos(c)) / ( np.sin(b)*np.sin(c) ) 
    arg_beta  = (np.cos(b) - np.cos(a)*np.cos(c)) / ( np.sin(a)*np.sin(c) ) 
    arg_gamma = (np.cos(c) - np.cos(a)*np.cos(b)) / ( np.sin(a)*np.sin(b) ) 

    alpha = np.arccos ( arg_alpha ) 
    beta  = np.arccos ( arg_beta  ) 
    gamma = np.arccos ( arg_gamma )

    S = (alpha + beta + gamma - np.pi)

    return S

def aire_maille (bounds_lat:xr.DataArray, bounds_lon:xr.DataArray, vertex:str|None=None ) :
    '''
    Aire of a grid box on the sphere
    '''
    push_stack ( 'aire_maille')
    if not vertex : vertex = bounds_lat.dims[-1]
        
    S1 = aire_triangle ( bounds_lat[{vertex:0}], bounds_lon[{vertex:0}],
                         bounds_lat[{vertex:1}], bounds_lon[{vertex:1}],
                         bounds_lat[{vertex:2}], bounds_lon[{vertex:2}] )
    S2 = aire_triangle ( bounds_lat[{vertex:2}], bounds_lon[{vertex:2}],
                         bounds_lat[{vertex:3}], bounds_lon[{vertex:3}],
                         bounds_lat[{vertex:0}], bounds_lon[{vertex:0}] )
    pop_stack ('aire_maille')
    return S1 + S2

def cmap_long (cmap, ncolors:int) :
    '''
    Cycle sur une palette de couleur pour en créer une plus longue par répétition
    '''
    push_stack ('cmap_long')

    # Longueur de la colormap (nombre de couleurs disponibles)
    nc = len (cmap.colors)

    # Création d'une liste de couleurs bidon (juste pour avoir le bon type d'objet)
    colors = cmap.resampled (ncolors) (np.linspace (0, 1, ncolors))

    # Remplacement des couleurs
    for nn in range (ncolors) : colors[nn,:]= cmap (nn%nc)

    # Creation d'un objet colormap
    cmap_long =  matplotlib.colors.ListedColormap (colors)

    pop_stack ('cmap_long')
    return cmap_long

def rgb2hex (r,g,b) :
    '''Converti du RGB décimal (valeurs dans [0,255]) vers HEXA [#00,#FF]'''
    push_stack ( 'rgb2hex')
    zres =  "#{:02x}{:02x}{:02x}".format(r,g,b)
    pop_stack  ( f'rgb2hex : {zres = }')
    return zres

def hex2rgb (hexcode) :
    '''Converti RGB HEXA [#00,#FF] vers RGB décimal [0-255]'''
    push_stack ( ' ')
    zres = tuple (map(ord,hexcode[1:].decode('hex')))
    pop_stack  ( f'{zres = }')
    return zres

def color2hex (r, g, b) :
    '''Converti du RGB fraactionaire (valeurs dans [0,1]) vers HEXA'''
    push_stack ( 'color2hex')
    zres = "#{:02X}{:02X}{:02X}".format( int(r*255), int(g*255), int(b*255) )
    pop_stack  ( f'color2hex: {zres =}')
    return

def total_seconds (timedelta):
    """Convert timedeltas to seconds
    In Python, time differences can take many formats. This function can take
    timedeltas in any format and return the corresponding number of seconds, as
    a float.
    Beware! Representing timedeltas as floats is not as precise as representing
    them as a timedelta object in datetime, numpy, or pandas.
    Parameters
    ----------
    timedelta : various
        Time delta from python's datetime library or from numpy or pandas. If
        it is from numpy, it can be an ndarray with dtype datetime64. If it is
        from pandas, it can also be a Series of datetimes. However, this
        function cannot operate on entire pandas DataFrames. To convert a
        DataFrame, do df.apply(to_seconds)
    Returns
    -------
    seconds : various
        Returns the total seconds in the input timedelta object(s) as float.
        If the input is a numpy ndarray or pandas Series, the output is the
        same, but with a float datatype.

    From https://gist.github.com/MichaelStetner
    """
    try:
        seconds = timedelta.total_seconds()
    except AttributeError:  # no method total_seconds
        one_second = np.timedelta64(1000000000, 'ns')
        # use nanoseconds to get highest possible precision in output
        seconds = timedelta / one_second
    return seconds


def zebra_frame(self, lw:int=3, crs=None, zorder:int|None=None, iFlag_outer_frame_in:bool|None=None) -> None :    
    # Alternate black and white line segments
    bws = itertools.cycle(["k", "w"])
    self.spines["geo"].set_visible(False)
    
    if iFlag_outer_frame_in is not None:
        #get the map spatial reference        
        left, right, bottom, top = self.get_extent()
        crs_map = self.projection
        xticks  = np.arange(left, right+(right-left)/9, (right-left)/8)
        yticks  = np.arange(bottom, top+(top-bottom)/9, (top-bottom)/8)
        #check spatial reference are the same           
        pass
    else:        
        crs_map =  crs
        xticks  = sorted([*self.get_xticks()])
        xticks  = np.unique(np.array(xticks))        
        yticks  = sorted([*self.get_yticks()])
        yticks  = np.unique(np.array(yticks))        
        
    for ticks, which in zip([xticks, yticks], ["lon", "lat"]):
        for idx, (start, end) in enumerate(zip(ticks, ticks[1:])):
            bw = next(bws)
            if which == "lon":
                xs = [[start, end], [start, end]]
                ys = [[yticks[0], yticks[0]], [yticks[-1], yticks[-1]]]
            else:
                xs = [[xticks[0], xticks[0]], [xticks[-1], xticks[-1]]]
                ys = [[start, end], [start, end]]
                
                # For first and last lines, used the "projecting" effect
                capstyle = "butt" if idx not in (0, len(ticks) - 2) else "projecting"
                for (xx, yy) in zip(xs, ys):
                    self.plot(xx, yy, color=bw, linewidth=max(0, lw - self.spines["geo"].get_linewidth()*2), clip_on=False,
                        transform=crs_map, zorder=zorder, solid_capstyle=capstyle,
                        # Add a black border to accentuate white segments
                        path_effects=[
                            Stroke(linewidth=lw, foreground="black"),
                            Normal(),
                        ],
                    )

class TaylorDiagram (object) :
    """
    Taylor diagram (Taylor, 2001) test implementation.
    Plot model standard deviation and correlation to reference (data)
    sample in a single-quadrant polar plot, with r=stddev and
    theta=arccos(correlation).
    
    Based on Copin's implementation in Python.
    Co-authors : 
    - "Yannick Copin <yannick.copin@laposte.net>"
    - "Pritthijit Nath <pritthijit.nath@icloud.com>"

    Useful links : 
    - https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2000JD900719
    - http://www-pcmdi.llnl.gov/about/staff/Taylor/CV/Taylor_diagram_primer.htm
    - https://gist.github.com/ycopin/3342888
    - https://zenodo.org/record/5548061
    - https://gist.github.com/nathzi1505/1d9e879881605a91e05f9afc1089e53f
    """

    def __init__(self, refstd,
                 fig=None, rect=111, label='_', srange=(0, 1.5), extend=False):
        """
        Set up Taylor diagram axes, i.e. single quadrant polar
        plot, using `mpl_toolkits.axisartist.floating_axes`.
        Parameters:
        * refstd: reference standard deviation to be compared to
        * fig: input Figure or None
        * rect: subplot definition
        * label: reference label
        * srange: stddev axis extension, in units of *refstd*
        * extend: extend diagram to negative correlations
        """
        
        self.refstd = refstd            # Reference standard deviation

        tr = PolarAxes.PolarTransform ()

        # Correlation labels
        rlocs = np.array ([0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1])
        if extend :
            # Diagram extended to negative correlations
            self.tmax = np.pi
            rlocs = np.concatenate ((-rlocs[:0:-1], rlocs))
        else :
            # Diagram limited to positive correlations
            self.tmax = np.pi/2
        tlocs = np.arccos (rlocs)        # Conversion to polar angles
        gl1 = GF.FixedLocator (tlocs)    # Positions
        tf1 = GF.DictFormatter (dict(zip(tlocs, map(str, rlocs))))

        # Standard deviation axis extent (in units of reference stddev)
        self.smin = srange[0] * self.refstd
        self.smax = srange[1] * self.refstd

        ghelper = FA.GridHelperCurveLinear (
            tr,
            extremes=(0, self.tmax, self.smin, self.smax),
            grid_locator1=gl1, tick_formatter1=tf1)

        if fig is None:
            fig = plt.figure()

        ax = FA.FloatingSubplot (fig, rect, grid_helper=ghelper)
        fig.add_subplot(ax)

        # Adjust axes
        ax.axis["top"].set_axis_direction("bottom")   # "Angle axis"
        ax.axis["top"].toggle(ticklabels=True, label=True)
        ax.axis["top"].major_ticklabels.set_axis_direction("top")
        ax.axis["top"].label.set_axis_direction("top")
        ax.axis["top"].label.set_text("Correlation")

        ax.axis["left"].set_axis_direction("bottom")  # "X axis"
        ax.axis["left"].label.set_text("Standard deviation")

        ax.axis["right"].set_axis_direction("top")    # "Y-axis"
        ax.axis["right"].toggle(ticklabels=True)
        ax.axis["right"].major_ticklabels.set_axis_direction (
            "bottom" if extend else "left")

        if self.smin:
            ax.axis["bottom"].toggle(ticklabels=False, label=False)
        else:
            ax.axis["bottom"].set_visible(False)          # Unused

        self._ax = ax                   # Graphical axes
        self.ax = ax.get_aux_axes (tr)  # Polar coordinates

        # Add reference point and stddev contour
        ll, = self.ax.plot([0], self.refstd, 'k*',
                          ls='', ms=10, label=label)
        tt = np.linspace(0, self.tmax)
        rr = np.zeros_like(tt) + self.refstd
        self.ax.plot (tt, rr, 'k--', label='_')

        # Collect sample points for latter use (e.g. legend)
        self.samplePoints = [ll]

    def add_sample (self, stddev, corrcoef, *args, **kwargs) :
        """
        Add sample (*stddev*, *corrcoeff*) to the Taylor
        diagram. *args* and *kwargs* are directly propagated to the
        `Figure.plot` command.
        """
        push_stack ('add_sample')
        ll, = self.ax.plot (np.arccos(corrcoef), stddev,
                          *args, **kwargs)  # (theta, radius)
        self.samplePoints.append(ll)

        pop_stack  ('add_sample')
        return ll

    def add_grid (self, *args, **kwargs) :
        """Add a grid."""
        self._ax.grid (*args, **kwargs)

    def add_contours (self, levels=5, **kwargs) :
        """
        Add constant centered RMS difference contours, defined by *levels*.
        """
        push_stack ('add_contours ')
        rs, ts = np.meshgrid (np.linspace(self.smin, self.smax),
                              np.linspace(0, self.tmax))
        # Compute centered RMS difference
        rms = np.sqrt (self.refstd**2 + rs**2 - 2*self.refstd*rs*np.cos(ts))

        contours = self.ax.contour(ts, rs, rms, levels, **kwargs)

        pop_stack ('add_contours')
        return contours

    def test1 (self) :
        """Display a Taylor diagram in a separate axis."""
        push_stack ('test1')
        # Reference dataset
        x = np.linspace (0, 4*np.pi, 100)
        data = np.sin (x)
        refstd = data.std (ddof=1)           # Reference standard deviation
        
        # Generate models
        m1 = data + 0.2*np.random.randn (len(x))     # Model 1
        m2 = 0.8*data + .1*np.random.randn (len(x))  # Model 2
        m3 = np.sin (x-np.pi/10)                     # Model 3
        
        # Compute stddev and correlation coefficient of models
        samples = np.array ([ [m.std(ddof=1), np.corrcoef (data, m)[0, 1]]
                            for m in (m1, m2, m3)])
        
        fig = plt.figure (figsize=(10, 4))
        
        ax1 = fig.add_subplot (1, 2, 1, xlabel='X', ylabel='Y')
        # Taylor diagram
        dia = TaylorDiagram (refstd, fig=fig, rect=122, label="Reference",
                            srange=(0.5, 1.5))
        
        colors = plt.matplotlib.cm.jet (np.linspace(0, 1, len(samples)))
        
        ax1.plot(x, data, 'ko', label='Data')
        for i, m in enumerate ([m1, m2, m3]):
            ax1.plot (x, m, c=colors[i], label=f'Model {i+1}' )
            ax1.legend (numpoints=1, prop=dict(size='small'), loc='best')
        
        # Add the models to Taylor diagram
        for i, (stddev, corrcoef) in enumerate (samples):
            dia.add_sample (stddev, corrcoef,
                        marker='$%d$' % (i+1), ms=10, ls='',
                        mfc=colors[i], mec=colors[i],
                        label=f"Model {i+1}" )
            
        # Add grid
        dia.add_grid ()
        
        # Add RMS contours, and label them
        contours = dia.add_contours (colors='0.5')
        plt.clabel (contours, inline=1, fontsize=10, fmt='%.2f')
        
        # Add a figure legend
        fig.legend (dia.samplePoints,
                [ p.get_label() for p in dia.samplePoints ],
                numpoints=1, prop=dict(size='small'), loc='upper right')

        pop_stack  ('test1')
        return 
    
    def test2 (self) :
        """
        Climatology-oriented example (after iteration w/ Michael A. Rawlins).
        """
        push_stack ('test2')
        
        # Reference std
        stdref = 48.491

        # Samples std,rho,name
        samples = [[25.939, 0.385, "Model A"],
                   [29.593, 0.509, "Model B"],
                   [33.125, 0.585, "Model C"],
                   [29.593, 0.509, "Model D"],
                   [71.215, 0.473, "Model E"],
                   [27.062, 0.360, "Model F"],
                   [38.449, 0.342, "Model G"],
                   [35.807, 0.609, "Model H"],
                   [17.831, 0.360, "Model I"]]
            
        fig = plt.figure ()
        
        dia = TaylorDiagram (stdref, fig=fig, label='Reference', extend=True)
        dia.samplePoints[0].set_color('r')  # Mark reference point as a red star
        
        # Add models to Taylor diagram
        for i, (stddev, corrcoef, name) in enumerate (samples):
            dia.add_sample(stddev, corrcoef,
                        marker='$%d$' % (i+1), ms=10, ls='',
                        mfc='k', mec='k',
                        label=name)
            
        # Add RMS contours, and label them
        contours = dia.add_contours(levels=5, colors='0.5')  # 5 levels in grey
        plt.clabel (contours, inline=1, fontsize=10, fmt='%.0f')
        
        dia.add_grid ()                                  # Add grid
        dia._ax.axis[:].major_ticks.set_tick_out (True)  # Put ticks outward
        
        # Add a figure legend and title
        fig.legend (dia.samplePoints,
                [ p.get_label() for p in dia.samplePoints ],
                numpoints=1, prop=dict(size='small'), loc='upper right')
        fig.suptitle ("Taylor diagram", size='x-large')  # Figure title

        pop_stack  ('test2')
        return dia
