# IPSLCM-Utilities
Python utilities to plot and analyse IPSL-CM outputs

Author : <mailto:olivier.marti@lsce.ipsl.fr>

git : <https://github.com/oliviermarti/IPSLCM-Utilities>

# Jupyter notebooks

## ORCA\_Gallery.ipynb
An eclectic demo of various plots with ORCA outputs, using `nemo.py`

## LMDZ\_Gallery.ipynb 
A demo of plots with LMDZ outputs, using `lmdz.py`

# Usage notes
In `plotIGCM/utils/__init__.py`, there is a decorator that allows to dynamically check paramaters for functions that are correctly documented (with proper python 'hints'). This fully experimental. The parameter Check at the beginning allows to activate/deactivate this checkins phase.

# Python modules

## libIGCM
Some functionnalities of the ksh libIGCM used for running the IPSL models. Dedicated to post processing in Python.

### utils
Utilities for the following modules.

### sys.py 
Defines libIGCM directories, depending of the computer.

### date.py
Handles date computations and convertions in different calendars. Mostly conversion of `IGCM_date.ksh` to python. In the ksh version, most date arithmetic functions are duplicated for use with dates either in Gregorian or Human format. Here, the functions guess the input date format, and returns the result in the same format.

Dates format :

- Human format     : `[yy]yy-mm-dd`
- Gregorian format : `yymmdd`
- Julian format    : `yyddd`

Available calendars :

- `leap | gregorian |standard` :
      The normal calendar. The time origin for the
      julian day in this case is 24 Nov -4713.
- `noleap | 365_day` :
      A 365 day year without leap years.
- `all_leap | 366_day` :
      A 366 day year with only leap years.
- `360d | 360_day` :
      Year of 360 days with month of equal length.

### post.py
A layer above `sys.py` that read `IGCM_catalog.json` to automatically get information about key simulations. You can specify your own catalog.

## plotIGCM
Utilities for post processing of IPSL models outputs

### lmdz.py
Utilities for LMDZ grid

- Lots of tests for `xarray` object
- Support `numpy` objects is now obsolete

### nemo.py
Utilities to plot NEMO ORCA fields. Handles periodicity and other stuff.
- Lots of tests for `xarray` object
- Not much tested for `numpy` objects

### oasis.py
A few fonctionnalities of the OASIS coupler in Python : interpolation.

### interp1d.py
One-dimensionnal interpolation of a multi-dimensionnal field. Used for vertical interpolation on regular levels or pressure levels by `nemo.py` and `lmdz.py`.


## Miscellaneous
### IPCC.py
Defines colors recommanded by IPCC

IPCC Visual Style Guide for Authors. IPCC WGI Technical Support Unit. <https://www.ipcc.ch/site/assets/uploads/2019/04/IPCC-visual-style-guide.pdf>

### ephemerides.py
Compute time of sun rise and sun set, given a day and a geographical position.

(<http://www.softrun.fr/index.php/bases-scientifiques/heure-de-lever-et-de-coucher-du-soleil>)

All computations are approximate, with an error of a few minutes

More details here : <http://jean-paul.cornec.pagesperso-orange.fr/heures_lc.htm>

Details for exact computation : <https://www.imcce.fr/en/grandpublic/systeme/promenade/pages3/367.html>

### DailyInso.py
Compute daily insolation. Created on Thu Jun 17 15:20:13 2021. @Author: Didier Paillard. Adapted by Olivier Marti.

### couleurs.py
Some useful variables for pretty printing

### climM.py
Compute some climatologies

Obsolete : using `xcdat` directly is simpler and safer

### interp1d.py

Intended to interpolate on standard pressure level. All inputs shoud be `xarray` data arrays.

Obsolete : `xgcm` is way faster ... 

### palinsol.py
Copyright (c) 2012 Michel Crucifix <michel.crucifix@uclouvain.be>. When using this package for actual applications, always cite the authors of the original insolation solutions Berger, Loutre and/or Laskar, see details in man pages.

R Code developed for R version 2.15.2 (2012-10-26) -- "Trick or Treat"

- https://www.rdocumentation.org/packages/palinsol/versions/0.93
- https://cran.r-project.org/web/packages/palinsol/palinsol.pdf

Translated  (partially) to `Python/numpy` by Olivier Marti

