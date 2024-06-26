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
Utilitaires
'''
def aire_maille ( bounds_lat, bounds_lon, vertex=None ) :
    '''
    Aire of a grid box on the sphere
    '''
    if not vertex : vertex = bounds_lat.dims[-1]
        
    S1 = aire_triangle ( bounds_lat[{vertex:0}], bounds_lon[{vertex:0}],
                         bounds_lat[{vertex:1}], bounds_lon[{vertex:1}],
                         bounds_lat[{vertex:2}], bounds_lon[{vertex:2}] )
    S2 = aire_triangle ( bounds_lat[{vertex:2}], bounds_lon[{vertex:2}],
                         bounds_lat[{vertex:3}], bounds_lon[{vertex:3}],
                         bounds_lat[{vertex:0}], bounds_lon[{vertex:0}] )
    return S1 + S2

def cmap_long ( cmap, ncolors ) :
    '''
    Cycle sur une palette de couleur pour en créer une plus longue par répétition
    '''
    import numpy as np, matplotlib as mpl

    # Longueur de la colormap (nombre de couleurs disponibles)
    nc = len (cmap.colors)

    # Création d'une liste de couleurs bidon (juste pour avoir le bon type d'objet)
    colors = cmap.resampled (ncolors) (np.linspace (0, 1, ncolors))

    # Remplacement des couleurs
    for nn in range (ncolors) : colors[nn,:]= cmap (nn%nc)

    # Creation d'un objet colormap
    cmap_long =  mpl.colors.ListedColormap (colors)

    return cmap_long

def rgb2hex (r,g,b) :
    '''Converti du RGB décimal (valeurs dans [0,255]) vers HEXA [#00,#FF]'''
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

def hex2rgb (hexcode) :
    '''Converti RGB HEXA [#00,#FF] vers RGB décimal [0-255]'''
    return tuple (map(ord,hexcode[1:].decode('hex')))

def color2hex ( r, g, b ) :
    '''Converti du RGB fraactionaire (valeurs dans [0,1]) vers HEXA'''
    return "#{:02X}{:02X}{:02X}".format( int(r*255), int(g*255), int(b*255) )


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
        
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.projections import PolarAxes
        import mpl_toolkits.axisartist.floating_axes as FA
        import mpl_toolkits.axisartist.grid_finder as GF

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
        l, = self.ax.plot([0], self.refstd, 'k*',
                          ls='', ms=10, label=label)
        t = np.linspace(0, self.tmax)
        r = np.zeros_like(t) + self.refstd
        self.ax.plot (t, r, 'k--', label='_')

        # Collect sample points for latter use (e.g. legend)
        self.samplePoints = [l]

    def add_sample (self, stddev, corrcoef, *args, **kwargs) :
        """
        Add sample (*stddev*, *corrcoeff*) to the Taylor
        diagram. *args* and *kwargs* are directly propagated to the
        `Figure.plot` command.
        """
        import numpy as np
        l, = self.ax.plot (np.arccos(corrcoef), stddev,
                          *args, **kwargs)  # (theta, radius)
        self.samplePoints.append(l)

        return l

    def add_grid (self, *args, **kwargs) :
        """Add a grid."""
        import numpy as np
        self._ax.grid (*args, **kwargs)

    def add_contours (self, levels=5, **kwargs) :
        """
        Add constant centered RMS difference contours, defined by *levels*.
        """
        import numpy as np
        rs, ts = np.meshgrid (np.linspace(self.smin, self.smax),
                              np.linspace(0, self.tmax))
        # Compute centered RMS difference
        rms = np.sqrt (self.refstd**2 + rs**2 - 2*self.refstd*rs*np.cos(ts))

        contours = self.ax.contour(ts, rs, rms, levels, **kwargs)

        return contours


    def test1 () :
        """Display a Taylor diagram in a separate axis."""
        import numpy as np
        import matplotlib.pyplot as plt
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
            ax1.plot (x, m, c=colors[i], label=f'Model {i+1}'
        ax1.legend (numpoints=1, prop=dict(size='small'), loc='best')
        
        # Add the models to Taylor diagram
        for i, (stddev, corrcoef) in enumerate (samples):
            dia.add_sample (stddev, corrcoef,
                        marker='$%d$' % (i+1), ms=10, ls='',
                        mfc=colors[i], mec=colors[i],
                        label=f"Model {i+1}"
            
        # Add grid
        dia.add_grid ()
        
        # Add RMS contours, and label them
        contours = dia.add_contours (colors='0.5')
        plt.clabel (contours, inline=1, fontsize=10, fmt='%.2f')
        
        # Add a figure legend
        fig.legend (dia.samplePoints,
                [ p.get_label() for p in dia.samplePoints ],
                numpoints=1, prop=dict(size='small'), loc='upper right')
        
        return dia
    
    
    def test2 () :
        """
        Climatology-oriented example (after iteration w/ Michael A. Rawlins).
        """
        import numpy as np
        import matplotlib.pyplot as plt
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
        
        return dia
