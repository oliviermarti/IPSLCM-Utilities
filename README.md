# IPSLCM-Utilities
Python utilities to plot and analyse IPSL-CM outputs

Author : <mailto:olivier.marti@lsce.ipsl.fr>

git : <https://github.com/oliviermarti/IPSLCM-Utilities>

## Jupyter notebooks

### ORCA\_Gallery.ipynb
An eclectic demo of various plots with ORCA outputs, using `nemo.py`.

### LMDZ\_Gallery.ipynb 
A demo of plots with LMDZ outputs, using `lmdz.py`.

### coastline.ipynb
From an ORCA geometry, computes the coastline. Output as shapefile and Cartopy feature.

# Python modules

## libIGCM
Some functionnalities from the ksh libIGCM used for running the IPSL models. Dedicated to post processing in Python.

### sys.py 
Defines `libIGCM` directories, depending of the computer.

### post.py
A layer above `sys.py` that read a json catalog file (by defaults `IGCM_catalog.json`) to automatically get informations about key simulations.

### date.py
Handles date computations and convertions in different calendars. Mostly conversion of `IGCM_date.ksh` to python.

#### Dates formats :
- Human format     : `[yy]yy-mm-dd`
- Gregorian format : `yymmdd`
- Julian format    : `yyddd`

#### Available calendars :
- `leap | gregorian |standard` :
      The normal calendar. The time origin for the
      julian day in this case is 24 Nov -4713.
- `noleap | 365_day` :
      A 365 day year without leap years.
- `all_leap | 366_day` :
      A 366 day year with only leap years.
- `360d | 360_day` :
      Year of 360 days with months of equal length.

## plotIGCM
Utilities for post processing of IPSL models outputs. Uses `xarray`.

### lmdz.py
Utilities for LMDZ grid

### nemo.py
Utilities to plot NEMO ORCA fields. Handles periodicity and other stuff.

### oasis.py
A few fonctionnalities of the OASIS coupler in Python : interpolation.

### interp1d.py
One-dimensionnal interpolation of a multi-dimensionnal field. Obsolete, as xcdat or xgcm handles the 1D interpolation.

### sphere.py
Some computations on the sphere : angles, distances, surfaces, changes of referential, etc ...

### utils.py
Miscelaneaous, see internal documentation.

## Miscellaneous
### IPCC.py
Defines colors recommanded by IPCC, from IPCC Visual Style Guide for Authors
IPCC WGI Technical Support Unit.

<https://www.ipcc.ch/site/assets/uploads/2019/04/IPCC-visual-style-guide.pdf>

### `ephemerides.py`
Compute time of sun rise and sun set, given a day and a geographical position

(<http://www.softrun.fr/index.php/bases-scientifiques/heure-de-lever-et-de-coucher-du-soleil>)

All computations are approximate, with an error of a few minutes.

More details here : <http://jean-paul.cornec.pagesperso-orange.fr/heures_lc.htm>

Details for exact computation : <https://www.imcce.fr/en/grandpublic/systeme/promenade/pages3/367.html>

### `DailyInso.py`
Compute daily insolation. From Didier Paillard. Adapted to python by Olivier Marti.

### `couleurs.py`
Some useful variables for pretty printing

### `climM.py`
Compute some climatologies.

Obsolete : using `xcdat` directly is simpler and safer.

### `palinsol.py`
Copyright (c) 2012 Michel Crucifix <michel.crucifix@uclouvain.be>. When using this package for actual applications, always cite the authors of the original insolation solutions Berger, Loutre and/or Laskar, see details in man pages.

R Code developed for R version 2.15.2 (2012-10-26) -- "Trick or Treat"

- https://www.rdocumentation.org/packages/palinsol/versions/0.93
- https://cran.r-project.org/web/packages/palinsol/palinsol.pdf

Translated  (partially) to `Python/numpy/xarray` by Olivier Marti

