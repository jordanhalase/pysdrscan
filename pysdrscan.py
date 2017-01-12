#!/usr/bin/python

from astropy.io import fits
from astropy import wcs
from rtlsdr import RtlSdr
from time import strftime
import numpy as np
import argparse
import os
import signal
import sys

import scandata

def save_fits(header, data, overwrite):
    # Collapse array of FFT data into one broad spectrum
    data = data.reshape((header['passes'], -1))

    hdulist = fits.HDUList()
    hdulist.append(fits.PrimaryHDU())
    hdulist.append(fits.ImageHDU())
    hdulist[1].data = data

    # Check if output file already exists
    if os.path.isfile(argv.output_file) and overwrite == False:
        choice = ""
        while choice != ('y' or 'n'):
            print("File '%s' already exists. Overwrite? [y/N]:" % argv.output_file),
            choice = raw_input().lower()
            if choice == 'y':
                print("Overwriting")
                overwrite = True
            elif choice == 'n':
                print("Abandoning all captured data")
                sys.exit()

    # TODO: Finish WCS
    w = wcs.WCS(naxis=2)
    w.wcs.crpix = [0, 0]
    w.wcs.crval = [header['startfreq'] - header['bandwidth']/2.0, 0]
    w.wcs.cdelt = [header['bandwidth']/argv.fft_size, 1]
    w.wcs.ctype = ['FREQ', '']
    w.wcs.cunit = ['Hz', '']

    print("Writing to file '%s'..." % argv.output_file)
    hdulist[0].header.update(scandata.toFitsHeaderDict(header))
    hdulist[0].header.update(w.to_header())
    hdulist.writeto(argv.output_file, overwrite=overwrite)
    hdulist.close()
    print("File '%s' written successfully" % argv.output_file)

def terminate(signal, frame):
    print "\nCaught SIGINT. Salvaging data."
    header['enddate'] = strftime("%Y-%m-%dT%H:%M:%S")
    save_fits(header, data, argv.overwrite)
    sys.exit(0)

def secs_to_segments(secs, fft_size, sample_rate):
    return int(np.floor(sample_rate * secs / fft_size))

def parse_arguments():
    parser = argparse.ArgumentParser(prog="PySDRScan", version=scandata.program_version,
            description="Use librtl-supported SDR devices to scan wide spectrum data over time")
    parser.add_argument("startfreq",
            help="Starting center frequency in MHz", type=float)
    parser.add_argument("endfreq",
            help="Ending center frequency in MHz", type=float)
    parser.add_argument("-fs", "--sample_rate",
            help="SDR sampling rate in Hz (negative for default)",
            default=-1,
            type=int)
    parser.add_argument("-p", "--passes",
            help="Number of full spectrum passes",
            default=1,
            type=int)
    parser.add_argument("-g", "--gain",
            help="SDR device gain (negative for auto)",
            default=-1,
            type=int)
    parser.add_argument("-t", "--time-per-segment",
            help="Time in seconds to average per segment",
            default=0,
            type=int)
    parser.add_argument("-fft", "--fft-size",
            help="FFT size per segment",
            default=256,
            type=int)
    parser.add_argument("-w", "--window",
            help="Window function for FFT",
            choices=['rectangular', 'hanning', 'hamming', 'bartlett', 'blackman', 'kaiser'],
            default='hanning',
            type=str)
    parser.add_argument("-o", "--output-file",
            help="Output file name for FITS data (defaults to start date and time)",
            default=strftime("%Y-%m-%dT%H:%M:%S.fits"),
            type=str)
    parser.add_argument("--overwrite",
            help="Automatically overwrite any existing output files",
            action='store_true',
            default=False)
    parser.add_argument("--silence",
            help="Do not report the status of the scanning phase",
            choices=['none', 'segments', 'passes', 'all'],
            default='none')
    return parser.parse_args()

argv = parse_arguments()

# Create new generic header
header = {
        'version': scandata.program_version,
        'startdate': strftime("%Y-%m-%dT%H:%M:%S"),
        'startfreq': argv.startfreq*1e6,
        'endfreq': argv.endfreq*1e6,
        'passes': argv.passes
        }

# Perform sanity check on the arguments
if header['endfreq'] < header['startfreq']:
    print("Ending frequency must be greater than or equal to starting frequency.")
    sys.exit()
if header['passes'] < 1:
    print("Number of passes cannot be less than one.")
    sys.exit()

print("\nStarting center frequency: %f MHz" % (header['startfreq']/1e6))
print("Ending center frequency: %f MHz" % (header['endfreq']/1e6))
print("Number of passes: %d\n" % header['passes'])
print("Will write to output file '%s'" % argv.output_file)

if argv.window == 'rectangular':
    windowfunc = np.ones
    header['winfunc'] = 'rectangular'
else:
    windowfunc = getattr(np, argv.window)
    header['winfunc'] = argv.window

print("Will use a %s window" % header['winfunc'])
header['fftsize'] = argv.fft_size
print("Using an FFT size of %f" % header['fftsize'])

# Initialize SDR
sdr = RtlSdr()
if argv.gain < 0:
    sdr.set_gain('auto')
    header['gain'] = 'auto'
    print("Using an automatic gain")
else:
    sdr.set_gain(argv.gain)
    header['gain'] = sdr.get_gain()
    print("Using a gain of %f" % sdr.get_gain())

if argv.sample_rate > 0:
    sdr.set_sample_rate(argv.sample_rate)
header['bandwidth'] = sdr.sample_rate
sdr.set_center_freq(header['startfreq'])
print("Device bandwidth: %f MHz" % ((sdr.sample_rate)/1e6))

num_segments = int(np.ceil((header['endfreq'] - header['startfreq'])/(sdr.get_sample_rate())))
print("Sampling %d segments per %d passes\n" % (num_segments, header['passes']))

data = np.zeros(shape=(header['passes'], num_segments, argv.fft_size), dtype=np.float64)

signal.signal(signal.SIGINT, terminate)
print("Press Ctrl+C to cancel scanning and save")

# A 'primer' pass may need to be done
for i in range(0, 8):
    sdr.read_samples(argv.fft_size)

segments = secs_to_segments(argv.time_per_segment, argv.fft_size, sdr.sample_rate)
header['segavg'] = segments

for i in range(0, header['passes']):
    freq = header['startfreq']

    if argv.silence != 'passes' and argv.silence != 'all':
        print("\nBeginning pass %d of %d\n" % (i+1, header['passes']))

    for j in range(0, num_segments):
        sdr.set_center_freq(freq)

        if argv.silence != 'segments' and argv.silence != 'all':
            print("Scanning segment %d of %d at %f MHz..." %
                    (j+1, num_segments, (freq/1e6)))

        samples = sdr.read_samples(argv.fft_size)
        samples = windowfunc(len(samples)) * samples
        spectrum = np.fft.fft(samples)
        spectrum = np.fft.fftshift(spectrum)
        power = np.abs(spectrum)**2.0
        data[i][j] = power

        for k in range(1, segments):
            samples = sdr.read_samples(argv.fft_size)
            samples = windowfunc(len(samples)) * samples
            spectrum = np.fft.fft(samples)
            spectrum = np.fft.fftshift(spectrum)
            power = np.abs(spectrum)**2.0
            data[i][j] = (data[i][j] + power)/2.0

        freq += sdr.get_sample_rate()

header['enddate'] = strftime("%Y-%m-%dT%H:%M:%S")
save_fits(header, data, argv.overwrite)

