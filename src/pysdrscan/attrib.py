#!/usr/bin/python

from __init__ import __title__

attributes = {
    'version', 'startdate', 'enddate', 'startfreq',
    'endfreq', 'passes', 'bandwidth', 'gain'
    }

def to_fits_header_dict(header):
    if attributes.issubset(header.keys()):
        return {
                "PROG": (__title__),
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

