#!/usr/bin/env python

# -----------------------------------------------------------
# The following is a wrapper that calls several functions
# written in python (and other languages) in order to estimate
# the RM produced by the Ionosphere for a given date/time and
# a line of sight.
# @version 1.0
# @author carlos <sotomayor@astro.rub.de>
# Updates of IGRF and angles by Charlotte Sobey
# The source transits the sky, changing its coordinates of
# latitude and longitude every sec, min, hr, etc. As a
# consequence of this the coordinates of the intersection
# of the line of sight direction with thin Ionospheric shell
# also changes.
#
# This program calculates the coordinates at the piercing
# point during 24 hr, one point per every hour.
# Each coordinate is then used to calulate the TEC and B values
# for every hour. Remember that there should be 25 coordinates,
# each one corresponding to every hour during a day (from 00~24).
#
# NOTE: Actually due to problems with the 'sidereal' package we only
# obtain 24 RM values (from 00~23)
# -----------------------------------------------------------

# `path` is the variable describing where the ionFR code is. Determine this
# automatically.
from __future__ import annotations

import sys
from datetime import datetime
from math import cos, pi, sin
from typing import NamedTuple

import pandas as pd
import pyIGRF

from ionfr.ionex import ionheight, teccalc, tecrmscalc
from ionfr.puncture_ionosphere_coord import ippcoor_v1 as ippcoor
from ionfr.sidereal_package import rdalaz
from ionfr.sidereal_package.rdalaz import usage

# Defining some variables for further use
TECU = 1e16  # Total Electron Content Unit
TEC2m2 = 0.1 * TECU 
EarthRadius = 6371000.0  # in meters
Tesla2Gauss = 1e4  # Conversion factor from Tesla to Gauss

class RMResult(NamedTuple):
    hour: int
    tec_path: float
    tot_field: float
    ifr: float
    rms_ifr: float

class Args(NamedTuple):
    latitude: str
    longitude: str
    datetime: str
    ionex: str

def cli():
    argList  =  sys.argv[1:]
    if  len(argList) != 5:
        usage ("Incorrect command line argument count.")
    rawRAscencionDeclination, rawLatitude, rawLongitude, rawDTime, nameIONEX  =  argList
    return Args(
        latitude=rawLatitude,
        longitude=rawLongitude,
        datetime=rawDTime,
        ionex=nameIONEX,
    )
    


def main():
    args = cli()
    rm_results = compute_rm(
        rawLatitude=args.latitude,
        rawLongitude=args.longitude,
        rawDTime=args.datetime,
        nameIONEX=args.ionex,
    )
    save_results(rm_results)


def compute_rm(
    rawLatitude: str,
    rawLongitude: str,
    rawDTime: str,
    nameIONEX: str,
) -> pd.DataFrame:
    # predict the ionospheric RM for every hour within a day
    rm_results: list[RMResult] = []
    for h in range(24):
        if h < 10:
            rawtime = str(rawDTime.split("T")[0] + "T0" + str(h) + ":00:00")
        else:
            rawtime = str(rawDTime.split("T")[0] + "T" + str(h) + ":00:00")

        hour = rawtime.split("T")[1].split(":")[0]
        date = rawtime.split("T")[0].split("-")
        year = rawtime.split("T")[0].split("-")[0]
        month = rawtime.split("T")[0].split("-")[1]
        day = rawtime.split("T")[0].split("-")[2]

        # RA and Dec (of the source in degrees) to Alt and Az (radians)
        # NB only rawtime is passed to rdalaz.alaz because
        # source RA and Dec are obtained by alaz from sys.argv
        AzS, AlS, HA, LatO, LonO = rdalaz.alaz(rawtime)
        ZenS = (pi / 2.0) - AlS

        # output data only when the altitude of the source is above 0 degrees
        if not AlS * (180.0 / pi) > 0:
            continue

        # Reading the altitude of the Ionosphere in km (from IONEX file)
        AltIon = ionheight.calcionheight(nameIONEX)
        AltIon = AltIon * 1000.0  # km to m

        # Alt and AZ coordinates of the Ionospheric piercing point
        # Lon and Lat distances wrt the location of the antenna are also
        # calculated (radians)
        offLat, offLon, AzPunct, ZenPunct = ippcoor.PuncIonOffset(LatO, AzS, ZenS, AltIon)
        AlSPunct = (pi / 2.0) - ZenPunct

        # Calculate offset lat and lon in degrees
        if rawLatitude[-1] == "s":
            if rawLongitude[-1] == "e":
                lat = -(LatO + offLat) * 180.0 / pi
                lon = (LonO + offLon) * 180.0 / pi
            if rawLongitude[-1] == "w":
                lat = -(LatO + offLat) * 180.0 / pi
                lon = -(LonO + offLon) * 180.0 / pi
        if rawLatitude[-1] == "n":
            if rawLongitude[-1] == "e":
                lat = (LatO + offLat) * 180.0 / pi
                lon = (LonO + offLon) * 180.0 / pi
            if rawLongitude[-1] == "w":
                lat = (LatO + offLat) * 180.0 / pi
                lon = -(LonO + offLon) * 180.0 / pi

        # Calculation of TEC path value for the indicated 'hour' and therefore
        # at the IPP
        TECarr = teccalc.calcTEC(
            lat,
            lon,
            nameIONEX,
        )
        VTEC = TECarr[int(hour)]
        TECpath = VTEC * TEC2m2 / cos(ZenPunct)  # from vertical TEC to line of sight TEC

        # Calculation of RMS TEC path value (same as the step above)
        RMSTECarr = tecrmscalc.calcRMSTEC(
            lat,
            lon,
            nameIONEX,
        )
        VRMSTEC = RMSTECarr[int(hour)]
        RMSTECpath = (
            VRMSTEC * TEC2m2 / cos(ZenPunct)
        )  # from vertical RMS TEC to line of sight RMS TEC

        # Calculation of the total magnetic field along the line of sight at the IPP
        date = datetime(int(year), int(month), int(day))
        decimalyear = int(year) + (
            date.timetuple().tm_yday / 365.0
            if int(year) % 4
            else date.timetuple().tm_yday / 366.0
        ) # +/- 1 day fine for this purpose.
        Xfield, Yfield, Zfield, _ = pyIGRF.calculate.igrf12syn(
            date=decimalyear,
            itype=2, # assume sphere (not WGS84 spheroid)
            alt=(EarthRadius + AltIon) / 1000.0, # from Earth centre in km
            lat=lat, # deg
            elong=lon, # deg
        )
        Xfield = abs(Xfield) * pow(10, -9) * Tesla2Gauss
        Yfield = abs(Yfield) * pow(10, -9) * Tesla2Gauss
        Zfield = abs(Zfield) * pow(10, -9) * Tesla2Gauss
        Totfield = (
            Zfield * cos(ZenPunct)
            + Yfield * sin(ZenPunct) * sin(AzPunct)
            - Xfield * sin(ZenPunct) * cos(AzPunct)
        )

        # Saving the Ionosheric RM and its corresponding
        # rms value to a file for the given 'hour' value
        IFR = 2.6 * pow(10, -17) * Totfield * TECpath
        RMSIFR = 2.6 * pow(10, -17) * Totfield * RMSTECpath

        rm_result = RMResult(
            hour=int(hour),
            tec_path=TECpath,
            tot_field=Totfield,
            ifr=IFR,
            rms_ifr=RMSIFR,
        )
        rm_results.append(rm_result)

    return pd.DataFrame(rm_results)

def save_results(rm_results: pd.DataFrame):
    rm_results.to_csv("IonRM.csv", index=False)

if __name__ == "__main__":
    main()