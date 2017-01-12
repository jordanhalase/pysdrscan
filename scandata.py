#!/usr/bin/python

program_name = "PySDRScan by Jordan Halase"
program_version = "0.1.4"

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
                "BNDWDTH": (header['bandwidth'], "Segment bandwidth (Hz)"),
                "GAIN": (header['gain'], "SDR Gain"),
                "FFTSIZE": (header['fftsize'], "FFT Size"),
                "SEGAVG": (header['segavg'], "Segments to average"),
                "WINFUNC": (header['winfunc'], "FFT window function")
                }
    else:
        raise KeyError("Required keys not found to construct a full header.")

