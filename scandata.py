#!/usr/bin/python

program_name = "PySDRScan by Jordan Halase"
program_version = "0.1.3"

attributes = {
    'version', 'startdate', 'enddate', 'startfreq',
    'endfreq', 'passes', 'bandwidth', 'gain'
    }

def toFitsHeaderDict(header):
    if attributes.issubset(header.keys()):
        return {
                "PROG": (program_name),
                "VERSION": (header['version']),
                "STRTDATE": (header['startdate']),
                "ENDDATE": (header['enddate']),
                "FRQ_STRT": (header['startfreq'], "Start frequency (Hz)"),
                "FRQ_END": (header['endfreq'], "End frequency (Hz)"),
                "PASSES": (header['passes'], "Full spectrum passes"),
                "BNDWDTH": (header['bandwidth'], "Window bandwidth (Hz)"),
                "GAIN": (header['gain'], "SDR Gain")
                }
    else:
        raise KeyError("Required keys not found to construct a full header.")

