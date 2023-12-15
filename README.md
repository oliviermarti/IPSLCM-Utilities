# IPSLCM-Utilities
Python utilities to plot and analyse IPSL-CM outputs

Author : olivier.marti@lsce.ipsl.fr

git : https://github.com/oliviermarti/IPSLCM-Utilities

## ORCA\_Gallery.ipynb 

## libIGCM\_sys.py 
Defines libIGCM directories, depending of the computer

## libIGCM\_date.py
Handles date calculs and convertions in different calendars. Mostly conversion of IGCM_date.ksh to python.

Dates  format
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

  Warning, to install, configure, run, use any of included software or
  to read the associated documentation you'll need at least one (1)
  brain in a reasonably working order. Lack of this implement will
  void any warranties (either express or implied).  Authors assumes
  no responsability for errors, omissions, data loss, or any other
  consequences caused directly or indirectly by the usage of his
  software by incorrectly or partially configured personal

## lmdz.py
Utilities for LMDZ grid

- Lots of tests for xarray object
- Not much tested for numpy objects

## nemo.py
Utilities to plot NEMO ORCA fields,

Handles periodicity and other stuff

- Lots of tests for xarray object
- Not much tested for numpy objects

## oasis.py
A few fonctionnalities of the OASIS coupler in Python
