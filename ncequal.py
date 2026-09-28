#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Compare two netcdf files for equality. """

import sys
import argparse
import os
import xarray as xr
import numpy as np
from sty import fg, Style, RgbFg

def define_color(color: bool) -> tuple[Style, Style]:
    '''
    Define colors for the output of the script.

    Parameters:
    color (bool): flag to activate or deactivate colored output

    Returns:
    the colors for the output
    '''
    if color:
        fg.customred=Style(RgbFg(189,55,55))
        fg.customblue=Style(RgbFg(73,96,156))
    else:
        fg.customred=fg.rs
        fg.customblue=fg.rs

    return fg.customred, fg.customblue

def compare_files(file1: str, file2: str ,randvarnum: int,
                  randtimenum: int, color: bool) -> tuple[str,int]:
    '''
    Compare two netcdf files for equality. The function checks whether the two files contain
    the same variables. For variables that depend on the time/TIME dimension, values are
    compared at randomly selected time steps; all other variables are compared in full. The number of
    variables and time steps to be checked can be specified by the user. The function returns
    a message that indicates whether the files are equal or not, and an exit code that can be
    used to exit the program with sys.exit(exit_code).

    Parameters:
    file1 (str): path to the first file
    file2 (str): path to the second file
    randvarnum (int): number of variables to be checked
    randtimenum (int): number of time steps to be checked
    color (bool): flag to activate or deactivate colored output

    Returns:
    tuple[str,int]: message indicating whether the files are equal or not, and an exit code
    '''

    #define colors for the output
    fg.error, fg.success = define_color(color)

    ds1 = xr.open_dataset(file1, decode_times=False)
    ds2 = xr.open_dataset(file2, decode_times=False)

    #do inital checks, are the same variables saved in the two files, and do
    #their coordinates have the same sizes?
    exit_code = 1

    # Check if the two files contain the same variables
    # no need to use list comprehension here
    if set(ds1.variables) != set(ds2.variables):
        message = f"{fg.error}the two files do not contain the same variables - files not equal.{fg.rs}"
        return message, exit_code

    # Check if the coordinates have the same sizes
    # you can create the dictionay in one line, no need to use zip
    if {cd: ds1[cd].shape for cd in ds1.coords} != {cd: ds2[cd].shape for cd in ds2.coords}:
        message = f"{fg.error}the coordinates within the two files have different sizes - files not equal.{fg.rs}"
        return message, exit_code

    # Check the time dimension. Variables that depend on it are spot checked
    # at random time steps (cheap even for large time series). Variables
    # that don't (e.g. static fields, or files without a time axis) are
    # compared in full, so they still get a real equality check.
    if 'time' in ds1.coords:
        time = 'time'
    elif 'TIME' in ds1.coords:
        time = 'TIME'
    else:
        time = None

    #create list that contains data variables that could be checked
    # use data_vars to only get the data variables and safe the additional checks
    varlist = list(ds1.data_vars)

    if not varlist:
        message = f"{fg.error}no comparable data variables found - can't verify equality.{fg.rs}"
        return message, exit_code

    #draw random fields: (draw at most as many fields as exist in files)
    randvarnum = min(randvarnum, len(varlist))
    # use random choice to recreate the possibility of choosing the same variable multiple times,
    # but remove list comprehension for readability
    randvars = np.random.choice(varlist, size=randvarnum, replace=True)

    # split the picked variables into time-dependent and static ones
    timevars = [var for var in randvars if time is not None and time in ds1[var].dims]
    staticvars = [var for var in randvars if var not in timevars]

    #draw random times only if needed (at most as many as exist in files)
    if timevars:
        randtimenum = min(randtimenum, ds1[time].shape[0])
        randtimes = np.random.choice(range(ds1[time].shape[0]), size=randtimenum, replace=True)

    #for every variable, check whether all matrix entries (for the selected time
    #steps, if time-dependent) are equal, then count the number of different variables.
    # use xarray equals method to compare the data arrays, which takes care of the nans
    ndifferences = 0
    for var in timevars:
        ndifferences += not ds1[var].isel({time: randtimes}).equals(ds2[var].isel({time: randtimes}))
    for var in staticvars:
        ndifferences += not ds1[var].equals(ds2[var])

    # describe what was checked, for the output message
    checked = []
    if timevars:
        checked.append(f"variables {', '.join(timevars)} at time steps {', '.join(map(str, randtimes))}")
    if staticvars:
        checked.append(f"variables {', '.join(staticvars)} (compared in full)")
    checked = '; '.join(checked)

    if ndifferences == 0:
        exit_code = 0
        message = f"{fg.success}{file1} and {file2} are equal in {checked}.{fg.rs}"

    else:
        message = (
            f"{fg.error}{file1} and {file2} contain at least {ndifferences} data variables with different values - files not equal.\n{fg.rs}"
            f"{fg.error}(picked {checked}).{fg.rs}"
            )
        if color:
            message = fg.customred + message + fg.rs

    return message, exit_code

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='check files for equality')
    parser.add_argument('file1', metavar='file_1', type=str,
                                            help='first file')
    parser.add_argument('file2', metavar='file_2', type=str,
                                            help='second file to be compared to first file')
    parser.add_argument('--nocolors',dest='colorbool',action='store_false',
                                            help='use this flag to deactivate colors')
    parser.add_argument('--variable_number',dest='randvarnum',default=3,type=int,
                                            help='specify the number of variables to check, default is 3')
    parser.add_argument('--time_step_number',dest='randtimenum',default=3,type=int,
                                            help='specify the number of time steps to check, default is 3')

    args = parser.parse_args()
    FILE1 = args.file1
    FILE2 = args.file2
    COLOR = args.colorbool
    RANDVARNUM = args.randvarnum
    RANDTIMENUM = args.randtimenum

    # if the files exists, execute compare files, if not raise error.
    if os.path.exists(FILE1) and os.path.exists(FILE2):
        out = compare_files(FILE1, FILE2, RANDVARNUM, RANDTIMENUM, COLOR)
        print(out[0])
        sys.exit(out[1])
    else:
        fg.error, _ = define_color(COLOR)
        MESSAGE = f"{fg.error}files not found.{fg.rs}"
        print(MESSAGE)
        sys.exit(1)
