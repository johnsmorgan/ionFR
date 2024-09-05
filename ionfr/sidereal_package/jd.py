#!/usr/bin/env python
# ================================================================
# jd:  Convert date and time to Julian date
#   For documentation, see:
#     http://www.nmt.edu/tcc/help/lang/python/examples/sidereal/ims/
# ----------------------------------------------------------------
# ================================================================
# Imports
# ----------------------------------------------------------------
from __future__ import annotations

import sys

from . import sidereal

# - - -   m a i n


def main():
    """jd main program."""

    # -- 1 --
    # [ if the arguments in sys.argv are valid ->
    #     dt  :=  a datetime.datetime instance representing the
    #             date and time expressed in those arguments ]
    dt = argCheck()

    # -- 2 --
    # [ jd  :=  a JulianDate instance representing dt ]
    jd = sidereal.JulianDate.fromDatetime(dt)

    # -- 3 --
    print(float(jd))


# - - -   a r g C h e c k


def argCheck():
    """Check and convert the command line argument(s)."""
    # -- 1 --
    # [ argList  :=  the command line arguments ]
    argList = sys.argv[1:]

    # -- 2 --
    # [ if (len(argList)==1) and argList[0] is a valid
    #   date-time string ->
    #     dt  :=  that date-time as a datetime.datetime instance
    #   else if (len(argList)==2) and (argList[0] is a valid
    #   date) and (argList[1] is a valid time) ->
    #     dt  :=  a datetime.datetime representing that date
    #             and time
    #   else ->
    #     sys.stderr  +:=  error message
    #     stop execution ]
    if len(argList) == 1:
        try:
            dt = sidereal.parseDatetime(argList[0])
        except SyntaxError as detail:
            usage("Invalid date-time: %s" % detail)
    elif len(argList) == 2:
        try:
            date = sidereal.parseDate(argList[0])
        except SyntaxError as detail:
            usage("Invalid date: %s" % detail)
        try:
            time = sidereal.parseTime(argList[1])
        except SyntaxError as detail:
            usage("Invalid time: %s" % detail)
        dt = date.combine(date, time)
    else:
        usage("Incorrect number of arguments.")

    # -- 3 --
    return dt


# - - -   u s a g e


def usage(*L):
    """Print a usage message and stop.

    [ L is a list of strings ->
        sys.stderr  +:=  (usage message) + (elements of L,
                         concatenated)
        stop execution ]
    """
    print("*** Usage:", file=sys.stderr)
    print("***   jd yyyy-mm-dd[Thh[:mm[:ss]]]", file=sys.stderr)
    print("*** or:", file=sys.stderr)
    print("***   jd yyyy-mm-dd hh[:mm[:ss]]", file=sys.stderr)
    print("*** Error: %s" % "".join(L), file=sys.stderr)
    raise SystemExit


# ================================================================
# Epilogue
# ----------------------------------------------------------------

if __name__ == "__main__":
    main()
