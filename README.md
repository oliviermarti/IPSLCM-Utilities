# IPSLCM-Utilities
Python utilities to plot and analyse IPSL-CM outputs

Author : olivier.marti@lsce.ipsl.fr

git : https://github.com/oliviermarti/IPSLCM-Utilities

## ORCA\_Gallery.ipynb
An eclectic demo of various plots with ORCA outputs

## LMDZ\_Gallery.ipynb 
A demo of plots with LMDZ outputs

## libIGCM\_sys.py 
Defines libIGCM directories, depending of the computer

## libIGCM\_date.py
Handles date computations and convertions in different calendars. Mostly conversion of IGCM_date.ksh to python.

Dates format
 - Human format     : [yy]yy-mm-dd
 - Gregorian format : yymmdd
 - Julian format    : yyddd

  Types of calendars possible :
  - leap | gregorian |standard (other name leap) :
      The normal calendar. The time origin for the
      julian day in this case is 24 Nov -4713.
  - noleap | 365_day :
      A 365 day year without leap years.
  - all\_leap | 366_day :
      A 366 day year with only leap years.
  - 360d | 360\_day :
      Year of 360 days with month of equal length.

## lmdz.py
Utilities for LMDZ grid
- Lots of tests for xarray object
- Not much tested for numpy objects

## nemo.py
Utilities to plot NEMO ORCA fields. Handles periodicity and other stuff.
- Lots of tests for xarray object
- Not much tested for numpy objects

## oasis.py
A few fonctionnalities of the OASIS coupler in Python
