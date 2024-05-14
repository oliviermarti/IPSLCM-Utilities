#!/usr/bin/env python3
'''
This library handles date computations and convertions in different calendars.

Mostly conversion of IGCM_date.ksh to python.

Dates format
 - Human format     : [yy]yy-mm-dd
 - Gregorian format : yymmdd
 - Julian format    : yyddd

  Types of avalaible calendars :

  - leap|gregorian|standard (other name leap) :
      The normal calendar. The time origin for the
      julian day in this case is 24 Nov -4713.
  - noleap|365_day :
      A 365 day year without leap years.
  - all_leap|366_day :
      A 366 day year with only leap years.
  - 360d|360_day :
      Year of 360 days with month of equal length.

  Warning, to install, configure, run, use any of included software or
  to read the associated documentation you'll need at least one (1)
  brain in a reasonably working order. Lack of this implement will
  void any warranties (either express or implied).  Authors assumes
  no responsability for errors, omissions, data loss, or any other
  consequences caused directly or indirectly by the usage of his
  software by incorrectly or partially configured personal

'''

import numpy as np
import cftime

# Stack depth
sdep = 1

# Characteristics of the gregorian calender
mth_length = np.array ( [31, 28, 31,  30,  31,  30,  31,  31,  30,  31,  30,  31] )
mth_start  = np.array ( [ 0, 31, 59,  90, 120, 151, 181, 212, 243, 273, 304, 334] )
#mth_end    = mth_start + mth_length + 1  # Because of upper bounds in Python

# Other calendars
mth_length365 = np.array ( [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] )
mth_length366 = np.array ( [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] )
mth_length360 = np.array ( [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30] )

# List of possible names for calendar types
Calendar_gregorian = [ 'Gregorian', 'GREGORIAN', 'leap', 'LEAP', 'Leap', 'gregorian',  ]
Calendar_360d      = [ '360d', '360_day', '360d', '360_days', '360D', '360_DAY', '360D', '360_DAYS' ]
Calendar_noleap    = [ 'noleap', '365_day', '365_days', 'NOLEAP', '365_DAY', '365_DAYS', '365d', '365D', '365_d', '365_D'  ]
Calendar_allleap   = [ 'all_leap', '366_day', 'allleap', '366_days', '336d', 'ALL_LEAP', '366_DAY', 'ALLLEAP', '366_DAYS', '336D',  ]

# List of possible names for day, month and year
YE_name = [ 'YE', 'YEAR'  , 'Years' , 'years' , 'YEAR' , 'Year' , 'year' , 'YE', 'ye', 'Y', 'y' ]
MO_name = [ 'MO', 'MONTHS', 'Months', 'months', 'MONTH', 'Month', 'month', 'MO', 'mo', 'M', 'm' ]
DA_name = [ 'DA', 'DAYS'  , 'Days'  , 'days'  , 'DAY'  , 'Day'  , 'day'  , 'DA', 'da', 'D', 'd' ]

# Still to do
# function IGCM_date_DaysInNextPeriod
# function IGCM_date_DaysInPreviousPeriod

# libIGCM_date internal options
import warnings
from typing import TYPE_CHECKING, Literal, TypedDict

stack = list()

if TYPE_CHECKING :
    Options = Literal [ "DefaultCalendarType", "Debug", "Stack", "Depth" ]

    class T_Options (TypedDict) :
        DefaultCalendarType: Literal['Gregorian', 'GREGORIAN', 'leap', 'LEAP', 'Leap', 'gregorian',
                                     '360d', '360_day', '360d', '360_days', '360D', '360_DAY', '360D', '360_DAYS', 
                                     'noleap', '365_day', '365_days', 'NOLEAP', '365_DAY', '365_DAYS',
                                     'all_leap', '366_day', 'allleap', '366_days', '336d', 'ALL_LEAP', '366_DAY', 'ALLLEAP', '366_DAYS', '336D',]
        Debug = bool
        Stack = bool
        Depth = -1

OPTIONS = { 'DefaultCalendarType':'Gregorian', 'Debug':False, 'Stack':False, 'Depth':-1 }

class set_options :
    """
    set options for libIGCM_date
    """
    def __init__ (self, **kwargs):
        self.old = {}
        for k, v in kwargs.items():
            if k not in OPTIONS:
                raise ValueError ( f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}" )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update (self, options_dict):
        OPTIONS.update (options_dict)

    def __enter__ (self):
        return

    def __exit__ (self, type, value, traceback):
        self._apply_update (self.old)

def get_options () -> dict :
    """
    Get options for libIGCM_date

    See Also
    ----------
    set_options

    """
    return OPTIONS

def PushStack (string:str) :
    OPTIONS['Depth'] += 1
    if OPTIONS['Stack'] : print ( '  '*OPTIONS['Depth'], '-->libIGCM_date: ', string)
    return

def PopStack (string:str) :
    if OPTIONS['Stack'] : print ( '  '*OPTIONS['Depth'], '<--libIGCM_date: ', string)
    OPTIONS['Depth'] -= 1
    return
    
def GetMonthsLengths ( year, CalendarType=OPTIONS['DefaultCalendarType'] ) :
    '''
    Returns the month lengths for a given year and calendar type
    '''
    PushStack ( f'GetMonthsLengths ( {year=}, {CalendarType=} )' )
        
    if CalendarType in Calendar_360d   : zlengths = mth_length360
    if CalendarType in Calendar_noleap : zlengths = mth_length365
    if CalendarType in Calendar_noleap : zlengths = mth_length366
    if CalendarType in Calendar_gregorian :
        if IsLeapYear (year, CalendarType) : zlengths = mth_length366
        else                               : zlengths = mth_length365

    PopStack ( f'GetMonthsLengths : {zlengths}' )
    return zlengths

def DaysInMonth (yy, mm=None, CalendarType=None) :
    '''
    Returns the number of days in a month
    
    Usage:  DaysInMonth ( yyyy    , mm, [CalendarType] )
         or DaysInMonth ( yyyymmdd, [CalendarType] )
         '''
    PushStack ( f'DaysInMonth ( {yy=}, {mm=}, {CalendarType=} )' )

    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    if mm : year = int(yy) ; month = int(mm)
    else  : year, month = GetYearMonth (yy)
        
    length = GetMonthsLengths ( year, CalendarType=CalendarType )[ np.mod(month-1, 12) ]

    PopStack ( f'DaysInMonth : {length}' )
    return length
    
def DaysSinceJC ( date, CalendarType=None ) -> int :
    '''
    Calculate the days difference between a date and 00010101

    Computation is splitted in three case for the sake of speed
    '''
    PushStack ( f'DaysSinceJC ( {date=}, {CalendarType=} )' )

    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    yy, mo, da = GetYearMonthDay (date)
    if yy < 500 :
        date0 = '0101-01-01'
        if CalendarType in Calendar_360d      : aux = -360
        if CalendarType in Calendar_noleap    : aux = -365           
        if CalendarType in Calendar_allleap   : aux = -366
        if CalendarType in Calendar_gregorian : aux = -366
            
    elif yy < 1500 :
        date0 = '1001-01-01'
        if CalendarType in Calendar_360d      : aux = 359640
        if CalendarType in Calendar_noleap    : aux = 364635           
        if CalendarType in Calendar_allleap   : aux = 365634
        if CalendarType in Calendar_gregorian : aux = 364877
            
    else :
        date0 = '1901-01-01'
        if CalendarType in Calendar_360d      : aux = 683640
        if CalendarType in Calendar_noleap    : aux = 693135           
        if CalendarType in Calendar_allleap   : aux = 695034
        if CalendarType in Calendar_gregorian : aux = 693595
            
    ndays = DaysBetweenDate ( date, date0 ) + aux
     
    PopStack ( f'DaysSinceJC : {ndays}' )
    return ndays

def IsLeapYear (year : [int, str], CalendarType=None) -> bool :
    '''
    True if Year is a leap year
    '''
    PushStack ( f'IsLeapYear ( {year=}, {CalendarType=} )' )

    yy = int ( year )
    zis_leap_year = None
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']

    if OPTIONS['Debug'] : print ( f'{year=} {CalendarType=}' )
    
    # What is the CalendarType :
    if CalendarType in Calendar_360d      :
        if OPTIONS['Debug'] : print ( f'{CalendarType=} 360d' )
        zis_leap_year = False
    if CalendarType in Calendar_noleap    :
        if OPTIONS['Debug'] : print ( f'{CalendarType=} noleap' )
        zis_leap_year = False
    if CalendarType in Calendar_allleap   :
        if OPTIONS['Debug'] : print ( f'{CalendarType=} allleap' )
        zis_leap_year = True
    if CalendarType in Calendar_gregorian :
        if OPTIONS['Debug'] : print ( f'{CalendarType=} gregorian' )
        # A year is a leap year if it is even divisible by 4
        # but not evenly divisible by 100
        # unless it is evenly divisible by 400
        
        # if it is evenly divisible by 400 it must be a leap year
        if not zis_leap_year and np.mod ( yy, 400 ) == 0 :
            zis_leap_year = True
            
        # if it is evenly divisible by 100 it must not be a leap year
        if not zis_leap_year and np.mod ( yy, 100 ) == 0 :
            zis_leap_year = False
            
        # if it is evenly divisible by 4 it must be a leap year
        if not zis_leap_year and np.mod ( yy, 4 ) == 0 :
            zis_leap_year = True
            
        if not zis_leap_year :
            zis_leap_year = False

    PopStack ( f'IsLeapYear : {zis_leap_year}' )
    return zis_leap_year

def DateFormat ( date ) -> str :
    '''
    Get date format. Could be 'human' or 'gregorian'

      [yy]yymmdd   is Gregorian
      [yy]yy-mm-dd is Human
    '''
    PushStack ( f'DateFormat ( {date=} )' )
        
    if OPTIONS['Debug'] : print ( f'{type(date)=}' )
    zdate_format = None
    if isinstance (date, str) :
        if '-' in date : zdate_format = 'Human'
        else           : zdate_format = 'Gregorian'
    if isinstance (date, int) : zdate_format = 'Gregorian'

    PopStack ( f'DateFormat : {zdate_format}' )
    return zdate_format

def PrintDate ( ye, mo, da, pformat ) :
    '''
    Return a date in the requested format
    '''
    PushStack ( f'PrintDate ( {ye=}, {mo=}, {da=}, {pformat=} )' )

    zPrintDate = None
    if pformat == 'Human'     : zPrintDate = f'{ye:04d}-{mo:02d}-{da:02d}'
    if pformat == 'Gregorian' : zPrintDate = f'{ye:04d}{mo:02d}{da:02d}'

    PopStack ( f'PrintDate : {zPrintDate}' )
    return zPrintDate

def ConvertFormatToGregorian ( date ) :
    '''
    From a yyyy-mm-dd or yyymmdd date format returns a yyymmdd date format
    '''
    PushStack ( f'ConvertFormatToGregorian ( {date=} )' )
        
    zz = PrintDate ( *GetYearMonthDay ( date ), 'Gregorian' )
    
    PopStack ( f'ConvertFormatToGregorian : {zz}' )
    return zz

def ConvertFormatToHuman ( date ) :
    '''
    From a yyyymmdd or yyymmdd date format returns a yyy-mm-dd date format
    '''
    PushStack ( f'ConvertFormatToHuman ( {date=} )' )
    zz = PrintDate ( *GetYearMonthDay ( date ), 'Human' )
    PopStack ( f'ConvertFormatToHuman : {zz}' )
    return 

def GetYearMonthDay  ( date ) :
    '''
    Split Date in format [yy]yymmdd or [yy]yy-mm-dd to yy, mm, dd
    '''
    PushStack ( f'GetYearMonthDay ( {date=} )' )
        
    if isinstance (date, str) :
        if '-' in date :
            zz = date.split ('-')
            if len(zz) == 3 :
                ye, mo, da = zz
            if len(zz) == 2 :
                ye, mo = zz
                da = 0
            if len(zz) == 1 :
                ye = zz
                da = 0 ; mo = 0
        else :
            date = int (date)
            
    if isinstance (date, int) :
        if date > 1000000 :
            da = np.mod ( date, 100)
            mo = np.mod ( date//100, 100)
            ye = date // 10000
        elif date > 100000 :
            mo = np.mod ( date, 100)
            ye = date // 100
            da = 0
        else :
            ye = date
            da = 0 ; mo = 0

    if ye : ye = int (ye)
    if mo : mo = int (mo)
    if da : da = int (da)

    PopStack ( f'GetYearMonthDay : {ye}, {mo}, {da}' )
    return ye, mo, da

def GetYearMonth ( date ) :
    '''
    Split Date in format [yy]yymmdd or [yy]yy-mm-dd to yy, mm
    '''
    PushStack ( f'GetYearMonth ( {date=} )' )

    ye, mo, da = GetYearMonthDay (date)
    
    PopStack ( f'GetYearMonth : {ye}, {mo}' )
    return ye, mo

def DateAddYear ( date, year_inc='1Y' ) :
    '''
    Add year(s) to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    PushStack ( f'DateAddYear ( {date=}, {year_inc=} )' )
    zformat = DateFormat ( date )
    ye, mo, da = GetYearMonthDay ( date )

    if isinstance ( year_inc, str) :
        PeriodType, PeriodLength = AnaPeriod ( year_inc )
        #print ( f"DateAddYear {PeriodType=} {PeriodLength=}" )
        if PeriodType == YE_name[0] :
            year_inc = PeriodLength
        else :
            raise AttributeError ( f'Parameter {year_inc=} is not a year period' )
            
    ye_new = ye + year_inc
    zz = PrintDate ( ye_new, mo, da, zformat)
    
    PopStack ( f'DateAddYear : {zz}' )
    return zz

def CorrectYearMonth ( ye, mo) :
    '''
    Correct month values outside [1,12]
    '''
    PushStack ( f'CorrectYearMonth ( {ye=}, {mo=} )' )

    mo_new = mo
    ye_new = ye

    while mo_new > 12 :
        mo_new = mo_new - 12
        ye_new = ye_new + 1

    while mo_new < 1 :
        mo_new = mo_new + 12
        ye_new = ye_new - 1
        
    PopStack ( 'CorrectYearMonth : {ye_new}, {mo_new}' )
    return ye_new, mo_new

def CorrectYearMonthDay (ye, mo, da, CalendarTypeNone) :
    '''
    Correct month values outside [1,12] and day outside month length
    '''
    PushStack ( f'CorrectYearMonthDay ( {ye=}, {mo=}, {da=}, {CalendarTypeNone=} )' )

    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    ye_new, mo_new = CorrectYearMonth ( ye, mo)
    da_new = da
    
    num_day = DaysInMonth (ye, mo, CalendarType)
    
    while da_new > num_day :
        da_new = da_new - num_day
        mo_new = mo_new + 1
        ye_new, mo_new = CorrectYearMonth ( ye_new, mo_new)
        num_day = DaysInMonth (ye_new, mo_new, CalendarType)
    while da_new < 1 :
        mo_new = mo_new - 1
        num_day = DaysInMonth (ye_new, mo_new, CalendarType)
        da_new = da_new + num_day
        ye_new, mo_new = CorrectYearMonth ( ye_new, mo_new)
        num_day = DaysInMonth (ye, mo, CalendarType)
        
    PopStack ( f'CorrectYearMonthDay : {ye_new}, {mo_new}, {da_new}' )
    return ye_new, mo_new, da_new

def DateAddMonth (date, month_inc=1, CalendarType=None) :
    '''
    Add on year(s) to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    PushStack ( f'DateAddMonth ( {date=}, {month_inc=}, {CalendarType=} )' )
        
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    zformat = DateFormat ( date )
    ye, mo, da = GetYearMonthDay ( date )

    if isinstance (month_inc, str) :
        PeriodType, PeriodLength = AnaPeriod ( month_inc )
        if PeriodType == MO_name[0] :
            month_inc = PeriodLength
        else :
            raise AttributeError ( f'Parameter {month} is not a month period' )

    if month_inc < 0 : ye_inc = -( -month_inc // 12)
    else             : ye_inc = month_inc // 12

    ye_new = ye + ye_inc
    mo_new = mo + month_inc # - ye_inc*12
    ye_new, mo_new = CorrectYearMonth (ye_new, mo_new)
    lday1 = DaysInMonth ( ye    , mo    , CalendarType=CalendarType )
    lday2 = DaysInMonth ( ye_new, mo_new, CalendarType=CalendarType )
    if OPTIONS['Debug'] : print ( f'{ye=} {mo=} {da=} {ye_inc=} {month_inc=} {ye_new=} {mo_new=} {lday1=} {lday2=}' )
    da_new = da
    if da == lday1 : da_new = lday2
    da_new = np.minimum ( da_new, lday2)

    if OPTIONS['Debug'] : print ( f'{ye=} {mo=} {da=} {ye_new=} {mo_new=} {lday1=} {lday2=} {da_new=}' )

    PopStack ( 'DateAddMonth : {ye_new}, {mo_new, {da_new}, {zformat}' )
    return PrintDate ( ye_new, mo_new, da_new, zformat)

def DateAddPeriod ( date, period='1YE', CalendarType=None ) :
    '''
    Add a period to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    PushStack ( f'DateAddPeriod ( {date=}, {period=}, {CalendarType=} )' )
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    zformat = DateFormat ( date )
   
    PeriodType, PeriodLength = AnaPeriod ( period )

    if PeriodType == YE_name[0] :
        new_date = DateAddYear ( date, year_inc=period )
    if PeriodType == MO_name[0] :
        new_date = DateAddMonth ( date, month_inc=period, CalendarType=OPTIONS['DefaultCalendarType'] )
    if PeriodType == DA_name[0] :
        new_date = AddDaysToDate ( date, ndays=period, CalendarType=OPTIONS['DefaultCalendarType'] )
    if PeriodType == 'Unknown' :
        raise AttributeError ( f"DateAddPeriod : period syntax {period=} not understood" )

    ye, mo, da = GetYearMonthDay ( new_date )
    zz = PrintDate ( ye, mo, da, zformat )
    
    PopStack ( f'DateAddPeriod : {zz}' )
    return zz
    
def SubOneDayToDate (date, CalendarType=None) :
    '''
    Substracts one day to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    PushStack ( f'SubOneDayToDate ( {date=}, {CalendarType=} )' )

    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    zformat = DateFormat ( date )
    ye, mo, da = GetYearMonthDay ( date )
    zlength = GetMonthsLengths ( ye, CalendarType )

    ye = int(ye) ; mo = int(mo) ; da=int(da)
    if da ==  1 :
        if mo == 1 :
            da_new, mo_new, ye_new = zlength[-1  ], 12    , ye - 1
        else       :
            da_new, mo_new, ye_new = zlength[mo-2], mo - 1, ye
    else :
        da_new, mo_new, ye_new = da - 1, mo, ye

    zz = PrintDate ( ye_new, mo_new, da_new, zformat)
    PopStack ( f'SubOneDayToDate : {zz}' )
    return zz

def AddOneDayToDate ( date, CalendarType=None ) :
    '''
    Add one day to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    PushStack ( f'AddOneDayToDate ( {date=}, {CalendarType=} )' )
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    if OPTIONS['Debug'] : print ( f'AddOneDayToDate : {date=}' )
    zformat = DateFormat ( date )
    ye, mo, da = GetYearMonthDay ( date )
    zlength = GetMonthsLengths ( ye, CalendarType )

    ye_new = ye
    mo_new = mo
    da_new = da+1
    if da_new > zlength [mo_new-1] :
        da_new = 1
        mo_new = mo_new + 1
        if mo_new == 13 :
            mo_new =  1
            ye_new += 1

    zz = PrintDate ( ye_new, mo_new, da_new, zformat )
    PopStack ( 'AddOneDayToDate : {zz}' )
    return zz

def AddDaysToDate ( date, ndays='1D', CalendarType=None ) :
    '''
    Add days to date in format [yy]yymmdd or [yy]yy-mm-dd
    Number of days migth be negative
    '''
    PushStack ( f'AddDaysToDate ( {date=}, {ndays=}, {CalendarType=} )' )
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    zformat = DateFormat ( date )
     
    # Break it into pieces
    yy, mm, dd = GetYearMonthDay ( date )

    if isinstance (ndays, str) :
        PeriodType, PeriodLength = AnaPeriod (ndays )
        if PeriodType == DA_name[0] :
            ndays=PeriodLength
        else :
            raise AttributeError ( f'{ndays=} is not a day period' )
       
    zdate0 = date
    
    if ndays > 0 :
        for nn in np.arange (ndays) :
            zdate0 = AddOneDayToDate ( zdate0, CalendarType )

    if ndays < 0 :
        for nn in np.arange (-ndays) :
            zdate0 = SubOneDayToDate ( zdate0, CalendarType )

    yy, mm, dd = GetYearMonthDay ( zdate0 )

    zz = PrintDate ( yy, mm, dd, zformat )
    PopStack ( f'AddDaysToDate : {zz}' )
    return zz

def AddPeriodToDate ( date, period, CalendarType=None ) :
    '''
    Add a period to a date.
    period is specified as '1D', '5YE', '3DA', etc ...
    '''
    PushStack ( f'AddPeriodToDate ( {date=}, {period=}, {CalendarType=} )' )

    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    ndays = DaysInCurrentPeriod ( date, period, CalendarType=CalendarType)
    new_date = AddDaysToDate ( date, ndays=1, CalendarType=CalendarType )

    PopStack ( f'AddPeriodToDate : {new_date}' )
    return new_date

def DaysInYear (year, CalendarType=None ) -> int :
    '''
    Return the number of days in a year
    '''
    PushStack ( f'DaysInYear ( {year=}, {CalendarType=} )' )
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']

    if CalendarType in Calendar_360d :
        ndays = 360
  
    if  CalendarType in Calendar_noleap :
        ndays = 365

    if  CalendarType in Calendar_allleap :
        ndays = 366

    if CalendarType in Calendar_gregorian :
        if IsLeapYear ( year, CalendarType ) :
            ndays = 366
        else :
            ndays = 365

    PopStack ( 'DaysInYear : {ndays}' )
    return ndays

def DaysBetweenDate ( pdate1, pdate2, CalendarType=None ) -> int :
  '''
  Calculates the days difference between two dates

  This process subtracts pdate2 from pdate1. If pdate2 is larger
  than pdate1 then reverse the arguments. The calculations are done
  and then the sign is reversed.
  '''
  PushStack ( f'DaysBetweenDate ( {pdate1=}, {pdate2=}, {CalendarType=} )' )
  if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
    
  if pdate1 < pdate2 :
    date1=pdate2 ; date2=pdate1
  if pdate1 > pdate2 :
    date1=pdate1 ; date2=pdate2
    
  if pdate1 == pdate2 : 
    res = 0
  else :
    res = 0
    zdate1 = date2
    
    while zdate1 < date1  :
      zdate1 = AddOneDayToDate ( zdate1, CalendarType)
      res += 1
    
    # if argument 2 was larger than argument 1 then
    # the arguments were reversed before calculating
    # adjust by reversing the sign
    if pdate1 < pdate2 : 
      res = -res 

  # and output the results
  PopStack ( 'DaysBetweenDate : {res}' )
  return res

def ConvertGregorianDateToJulian (date, CalendarType=None) :
    '''
    Convert yyyymmdd to yyyyddd
    '''
    PushStack ( f'ConvertGregorianDateToJulian ( {date=}, {CalendarType} )' )
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    ye, mo, da = GetYearMonthDay (date)
    ndays = DaysBetweenDate ( PrintDate (ye,mo,da, 'Human'), PrintDate (ye,1,1, 'Human'), CalendarType=CalendarType )
    zz = int ( f'{ye}{ndays+1:03d}' )
    if OPTIONS['Stack'] : print ( '--> ConvertGregorianDateToJulian' )
    return zz
    
def ConvertJulianDateToGregorian (date, CalendarType=None) : 
    '''
    Convert yyyyddd to yyyymmdd
    '''
    PushStack ( f'ConvertJulianDateToGregorian ( {date=}, {CalendarType} )' )
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
   
    # Break apart the year and the days
    zdate = int (date)
    yy = zdate // 1000
    dd = np.mod (zdate, 1000 )
    
    # subtract the number of days in each month starting from 1
    # from the days in the date. When the day goes below 1, you
    # have the current month. Add back the number of days in the
    # month to get the correct day of the month
    mm=1
    while dd > 0 :
        #print ( f'ConvertJulianDateToGregorian {yy=} {mm=} {dd=}' )
        md = DaysInMonth ( yy, mm, CalendarType=CalendarType)
        dd = dd - md
        mm = mm + 1

    # The loop steps one past the correct month, so back up the month
    dd = dd + md
    mm = mm - 1 
    
    # Assemble the results into a gregorian date
    zz = PrintDate ( yy, mm, dd, 'Gregorian')

    PushStack ( f'ConvertJulianDateToGregorian : {zz}' )
    return zz

def DaysInCurrentPeriod ( startdate, period, CalendarType=None ) :
    ''' 
    Give the numbers of days during the period from startdate date
    '''
    PushStack ( f'DaysInCurrentPeriod ( {startdate=}, {period=}, {CalendarType=} )' )
    if not CalendarType : CalendarType=OPTIONS['DefaultCalendarType']
        
    year, month, day = GetYearMonthDay ( startdate )
    PeriodType, PeriodLength = AnaPeriod ( period )

    if PeriodType == YE_name[0] :
        PeriodLengthInYears = PeriodLength
    
        dateend = DateAddYear ( startdate, PeriodLengthInYears )
        Length = DaysBetweenDate ( dateend, startdate )
        
    elif PeriodType == MO_name[0] :
        PeriodLengthInMonths = PeriodLength

        year0       = year
        treatedYear = 0
        Length      = 0
        for i in np.arange ( PeriodLengthInMonths ) :
            Length = Length + DaysInMonth ( year, month + i-12*treatedYear, CalendarType=CalendarType)
            if month + i >= 12 * (treatedYear + 1) :
                year = year0 + 1
                treatedYear = treatedYear + 1

    elif PeriodType == DA_name[0] :
        PeriodLengthInDays = PeriodLength
        Length = PeriodLengthInDays

    else :
      Length = None

    PopStack ( 'DaysInCurrentPeriod : {Length}' )
    return Length

def AnaPeriod ( period ) :
    '''
    Decodes a period definition like '1Y', ''1MO', 'DA', etc ...
    Return period types (string) and period length (integer)
    '''
    PushStack ( f'AnaPeriod ( {period=} )' )

    periodName   = rmDigits  (period)
    periodLength = getDigits (period)

    if '-' in periodName : 
        Neg = True
    else :
        Neg = False

    periodName = periodName.replace ( '-', '')
    
    if periodName in YE_name : 
        PeriodType = YE_name[0]
        if periodLength == '' :
            PeriodLength = 1
        else : 
            PeriodLength = int ( periodLength )
        
    elif periodName in MO_name :
        PeriodType = MO_name[0]
        if periodLength == '' :
            PeriodLength = 1
        else : 
            PeriodLength = int ( periodLength )

    elif periodName in DA_name :
        PeriodType = DA_name[0]
        if periodLength == '' :
            PeriodLength = 1
        else : 
            PeriodLength = int ( periodLength )

    else :
        PeriodType   = 'Unknown'
        PeriodLength = 0

    if Neg : PeriodLength = -PeriodLength

    PopStack ( 'AnaPeriod' )
    return PeriodType, PeriodLength

def getDigits ( s: str ) -> str :
    '''Extract digits in a string'''
    PushStack ( f'getDigits ( {s=} )' )
    zz = ''.join (i for i in s if i.isdigit())
    PopStack ( f'getDigits : {zz}' )
    return zz

def rmDigits ( s:str ) -> str :
    '''Removes digits from a string'''
    PushStack ( f'rmDigits ( {s=} )' )
    zz =  ''.join (i for i in s if not i.isdigit())
    PopStack ( f'rmDigits : {zz}' )
    return zz
