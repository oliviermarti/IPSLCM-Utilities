#!/usr/bin/env python3
'''
This library handles date calculs and convertions in different calendars.

Mostly conversion of IGCM_date.ksh to python.

Dates  formar
 - Human format     : [yy]yy-mm-dd
 - Gregorian format : yymmdd
 - Julian format    : yyddd

  Types of calendars are possible :

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

 SVN information
 $Author:  $
 $Date:  $
 $Revision:  $
 $Id:  $
 $HeadURL:  $
'''

import numpy as np
debug = False

DefaultCalendarType = 'Gregorian'

# Characteristics of the gregorian calender
mth_length = np.array ( [31, 28, 31,  30,  31,  30,  31,  31,  30,  31,  30,  31] )
mth_start  = np.array ( [ 0, 31, 59,  90, 120, 151, 181, 212, 243, 273, 304, 334] )
mth_end    = mth_start + mth_length + 1  # A cause des bornes superieures de Python

# Other caalendars
mth_length365 = np.array ( [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] )
mth_length366 = np.array ( [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] )
mth_length360 = np.array ( [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30] )

# List of possible names for calendar types
Calendar_gregorian = [ 'leap', 'LEAP', 'Leap', 'gregorian', 'Gregorian', 'GREGORIAN' ]
Calendar_360d      = [ '360d', '360_day', '360d', '360_days', '360D', '360_DAY', '360D', '360_DAYS' ]
Calendar_noleap    = [ 'noleap', '365_day', '365_days', 'NOLEAP', '365_DAY', '365_DAYS',  ]
Calendar_allleap   = [ 'all_leap', '366_day', 'allleap', '366_days', '336d', 'ALL_LEAP', '366_DAY', 'ALLLEAP', '366_DAYS', '336D',  ]

# List of possible names for day, month and year
YE_name = [ 'YE', 'YEAR', 'Years', 'years', 'YEAR', 'Year', 'year', 'YE', 'ye', 'Y', 'y' ]
MO_name = [ 'MO', 'MONTHS', 'Months', 'months', 'MONTH', 'Month', 'month', 'MO', 'mo', 'M', 'm' ]
DA_name = [ 'DA', 'DAYS', 'Days', 'days', 'DAY', 'Day', 'day', 'DA', 'da', 'D', 'd' ]

# Still to do
# function IGCM_date_DaysInNextPeriod
# function IGCM_date_DaysInPreviousPeriod

def GetMonthsLengths ( year, CalendarType=DefaultCalendarType ) :
    '''
    Returns the month lengths for a given year and calendar type
    '''
    if CalendarType in Calendar_360d :
        zlengths = mth_length360
        
    if  CalendarType in Calendar_noleap :
        zlengths = mth_length365
        
    if  CalendarType in Calendar_noleap :
        zlengths = mth_length366

    if CalendarType in Calendar_gregorian :
        if IsLeapYear ( year, CalendarType) :
           zlengths = mth_length366
        else :
           zlengths = mth_length365

    return zlengths

def DaysInMonth ( yy, mm=None, CalendarType=DefaultCalendarType) :
    '''
    Returns the number of days in a month
    
    Usage:  DaysInMonth ( yyyy    , mm, [CalendarType] )
         or DaysInMonth ( yyyymmdd, [CalendarType] )
         '''
    if mm :
        year = int(yy) ; month = int(mm)
    else :
        year, month = GetYearMonth (yy)
        
    length = GetMonthsLengths ( year, CalendarType=CalendarType )[ np.mod(month-1, 12) ]
    return length
    
def DaysSinceJC ( date, CalendarType=DefaultCalendarType ) :
    '''
    Calculate the days difference between a date and 00010101

    Computation is splitted in three case for the sake of speed
    '''
    yy, mo, da = GetYearMonthDay (date)
    if yy < 500 :
        date0 = '0101-01-01'
        if CalendarType in Calendar_360d :
            aux = -360
        if CalendarType in Calendar_noleap :
            aux = -365           
        if CalendarType in Calendar_allleap :
            aux = -366
        if CalendarType in Calendar_gregorian :
            aux = -366
            
    elif yy < 1500 :
        date0 = '1001-01-01'
        if CalendarType in Calendar_360d :
           aux = 359640
        if CalendarType in Calendar_noleap :
            aux = 364635           
        if CalendarType in Calendar_allleap :
            aux = 365634
        if CalendarType in Calendar_gregorian :
            aux = 364877
            
    else :
        date0 = '1901-01-01'
        if CalendarType in Calendar_360d :
           aux = 683640
        if CalendarType in Calendar_noleap :
            aux = 693135           
        if CalendarType in Calendar_allleap :
            aux = 695034
        if CalendarType in Calendar_gregorian :
            aux = 693595
            
    ndays = DaysBetweenDate ( date, date0 ) + aux
     
    return ndays

def IsLeapYear ( year, CalendarType=DefaultCalendarType ) :
    '''
    True if Year is a leap year
    '''
    yy = int ( year )
    zis_leap_year = None

    # What is the CalendarType :
    if CalendarType in Calendar_360d :
        zis_leap_year = False
    if CalendarType in Calendar_noleap :
        zis_leap_year = False

    if CalendarType in Calendar_allleap :
        zis_leap_year = True
        
    if CalendarType in Calendar_gregorian :
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

    return zis_leap_year

def DateFormat ( date ) :
    '''
    Get date format. Could be human or gregorian

      [yy]yymmdd   is Gregorian
      [yy]yy-mm-dd is Human
    '''
    if isinstance (date, str) :
        if '-' in date :
            zdate_format = 'Human'
        else :
            zdate_format = 'Gregorian'
    if isinstance (date, int) : zdate_format = 'Gregorian'
    return zdate_format

def PrintDate ( ye, mo, da, pformat ) :
    '''
    Return a date in the requested format
    '''
    zPrintDate = None
    if pformat == 'Human'     : zPrintDate = f'{ye:04d}-{mo:02d}-{da:02d}'
    if pformat == 'Gregorian' : zPrintDate = f'{ye:04d}{mo:02d}{da:02d}'
    return zPrintDate

def ConvertFormatToGregorian ( date ) :
    '''
    From a yyyy-mm-dd or yyymmdd date format returns a yyymmdd date format
    '''
    return PrintDate ( *GetYearMonthDay ( date ), 'Gregorian' )

def ConvertFormatToHuman ( date ) :
    '''
    From a yyyymmdd or yyymmdd date format returns a yyy-mm-dd date format
    '''
    return PrintDate ( *GetYearMonthDay ( date ), 'Human' )

def GetYearMonthDay  ( date ) :
    '''
    Split Date in format [yy]yymmdd or [yy]yy-mm-dd to yy, mm, dd
    '''
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
    return ye, mo, da

def GetYearMonth ( date ) :
    '''
    Split Date in format [yy]yymmdd or [yy]yy-mm-dd to yy, mm, dd
    '''
    ye, mo, da = GetYearMonthDay (date)
    return ye, mo

def DateAddYear ( date, year_inc='1Y' ) :
    '''
    Add year(s) to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    zformat = DateFormat ( date )
    ye, mo, da = GetYearMonthDay ( date )

    if isinstance ( year_inc, str) :
        PeriodType, PeriodLength = AnaPeriod ( year_inc )
        print ( f"DateAddYear {PeriodType=} {PeriodLength=}" )
        if PeriodType == YE_name[0] :
            year_inc = PeriodLength
        else :
            raise AttributeError ( f'Parameter {year_inc=} is not a year period' )
            
    ye_new = ye + year_inc
    return PrintDate ( ye_new, mo, da, zformat)

def CorrectYearMonth ( ye, mo) :
    '''
    Correct month values outside [1,12]
    '''
    mo_new = mo
    ye_new = ye

    while mo_new > 12 :
        mo_new = mo_new - 12
        ye_new = ye_new + 1

    while mo_new < 1 :
        mo_new = mo_new + 12
        ye_new = ye_new - 1

    return ye_new, mo_new

def CorrectYearMonthDay (ye, mo, da, CalendarType=DefaultCalendarType) :
    '''
    Correct month values outside [1,12] and day outside month length
    '''
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

    return ye_new, mo_new, da_new

def DateAddMonth ( date, month_inc=1, CalendarType=DefaultCalendarType ) :
    '''
    Add on year(s) to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    zformat = DateFormat ( date )
    ye, mo, da = GetYearMonthDay ( date )

    if isinstance ( month_inc, str) :
        PeriodType, PeriodLength = AnaPeriod ( month_inc )
        if PeriodType == MO_name[0] :
            month_inc = PeriodLength
        else :
            raise AttributeError ( f'Parameter {month} is not a month period' )

    if month_inc < 0 :
        ye_inc = -( -month_inc // 12)
    else : 
        ye_inc = month_inc // 12

    ye_new = ye + ye_inc
    mo_new = mo + month_inc# - ye_inc*12
    ye_new, mo_new = CorrectYearMonth (ye_new, mo_new)
    lday = DaysInMonth ( ye_new, mo_new, CalendarType=DefaultCalendarType )
    da_new = np.minimum ( da, lday)
       
    return PrintDate ( ye_new, mo_new, da_new, zformat)

def DateAddPeriod ( date, period='1YE', CalendarType=DefaultCalendarType ) :
    '''
    Add a period to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    zformat = DateFormat ( date )
   

    PeriodType, PeriodLength = AnaPeriod ( period )

    if PeriodType == YE_name[0] :
        new_date = DateAddYear ( date, year_inc=period )
    if PeriodType == MO_name[0] :
        new_date = DateAddMonth ( date, month_inc=period, CalendarType=DefaultCalendarType )
    if PeriodType == DA_name[0] :
        new_date = AddDaysToDate ( date, ndays=period, CalendarType=DefaultCalendarType )
    if PeriodType == 'Unknow' :
        raise AttributeError ( f"DateAddPeriod : period syntax {period=} not understood" )

    ye, mo, da = GetYearMonthDay ( new_date )
    return PrintDate ( ye, mo, da, zformat )
    
def SubOneDayToDate ( date, CalendarType=DefaultCalendarType) :
    '''
    Substracts one day to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
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

    return PrintDate ( ye_new, mo_new, da_new, zformat)

def AddOneDayToDate ( date, CalendarType=DefaultCalendarType ) :
    '''
    Add one day to date in format [yy]yymmdd or [yy]yy-mm-dd
    '''
    if debug : print ( f'AddOneDayToDate : {date=}' )
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

    return PrintDate ( ye_new, mo_new, da_new, zformat )

def AddDaysToDate ( date, ndays='1D', CalendarType=DefaultCalendarType ) :
    '''
    Add days to date in format [yy]yymmdd or [yy]yy-mm-dd
    Number of days migth be negative
    '''
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
    
    return PrintDate ( yy, mm, dd, zformat )

def AddPeriodToDate ( date, period, CalendarType=DefaultCalendarType ) :
    '''
    Add a period to a date.
    period is specified as '1D', '5YE', '3DA', etc ...
    '''
    ndays = DaysInCurrentPeriod ( date, period, CalendarType=CalendarType)
    new_date = AddDaysToDate ( date, ndays=1, CalendarType=CalendarType )

    return new_date

def DaysInYear (year, CalendarType=DefaultCalendarType ) :
    '''
    Return the number of days in a year
    '''
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

    return ndays

def DaysBetweenDate ( pdate1, pdate2, CalendarType=DefaultCalendarType ) :
  '''
  Calculates the days difference between two dates

  This process subtracts pdate2 from pdate1. If pdate2 is larger
  than pdate1 then reverse the arguments. The calculations are done
  and then the sign is reversed.
  '''
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
  return res

def ConvertGregorianDateToJulian (date, CalendarType=DefaultCalendarType) :
    '''
    Convert yyyymmdd to yyyyddd
    '''
    ye, mo, da = GetYearMonthDay (date)
    ndays = DaysBetweenDate ( PrintDate (ye,mo,da, 'Human'), PrintDate (ye,1,1, 'Human'), CalendarType=CalendarType )

    return int ( f'{ye}{ndays+1:03d}' )
    
def ConvertJulianDateToGregorian (date, CalendarType=DefaultCalendarType) : 
    '''
    Convert yyyyddd to yyyymmdd
    '''
   
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
    return PrintDate ( yy, mm, dd, 'Gregorian')

def DaysInCurrentPeriod ( startdate, period, CalendarType=DefaultCalendarType ) :
    ''' 
    Give the numbers of days during the period from startdate date
    '''
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
      
    return Length

def AnaPeriod ( period ) :
    '''
    Decodes a period definition like '1Y', ''1MO', 'DA', etc ...
    Return period types (string) and period length (integer)
    '''
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
      
    return PeriodType, PeriodLength

def getDigits ( s ) :
    '''Extract digits in a string'''
    return ''.join (i for i in s if i.isdigit())

def rmDigits ( s ) :
    '''Removes digits from aa string'''
    return ''.join (i for i in s if not i.isdigit())
