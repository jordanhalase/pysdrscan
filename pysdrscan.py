#!/usr/bin/python

from astropy.io import fits
from astropy import wcs
from rtlsdr import RtlSdr
from time import strftime
import argparse
import math
import numpy
import os
import signal
import sys

import scandata

def saveFits(header, data, clobber):
    # Collapse array of FFT data into one broad spectrum
    data = data.reshape((header['passes'], -1))

    out = fits.HDUList()
    out.append(fits.PrimaryHDU())
    out.append(fits.ImageHDU())
    out[1].data = data

    # Check if output file already exists
    if os.path.isfile(argv.output_file) and clobber == False:
        choice = ""
        while choice != ('y' or 'n'):
            print("File '%s' already exists. Overwrite? [y/N]:" % argv.output_file),
            choice = raw_input().lower()
            if choice == 'y':
                print("Overwriting")
                clobber = True
            elif choice == 'n':
                print("Abandoning all captured data")
                sys.exit()

    # TODO: Finish WCS
    coords = wcs.WCS(naxis=2)
    pixcoords = numpy.array([[2048,0], [2.048, 0]], numpy.float_)
    world = coords.wcs_pix2world(pixcoords, 1)
    print(world)

    print("Writing to file '%s'..." % argv.output_file)
    out[0].header.update(scandata.toFitsHeaderDict(header))
    out.writeto(argv.output_file, clobber=clobber)
    out.close()
    print("File '%s' written successfully" % argv.output_file)

def terminate(signal, frame):
    print "\nCaught SIGINT. Salvaging data."
    header['enddate'] = strftime("%Y-%m-%dT%H:%M:%S")
    saveFits(header, data, clobber)
    sys.exit(0)

def parse_arguments():
    parser = argparse.ArgumentParser(prog="PySDRScan", version=scandata.program_version,
            description="Use librtl-supported SDR devices to scan wide spectrum data over time")
    parser.add_argument("startfreq", help="Starting frequency in MHz", type=float)
    parser.add_argument("endfreq", help="Ending frequency in MHz", type=float)
    parser.add_argument("-p", "--passes",
            help="Number of full spectrum passes",
            default=1,
            type=int)
    parser.add_argument("-o", "--output-file",
            help="Output file name for FITS data (defaults to start date and time)",
            default=strftime("%Y-%m-%dT%H:%M:%S.fits"),
            type=str)
    parser.add_argument("--clobber",
            help="Automatically overwrite any existing output files",
            action='store_true',
            default=False)
    parser.add_argument("--silent",
            help="Do not report the status of the scanning phase",
            action='store_true',
            default=False)
    return parser.parse_args()

argv = parse_arguments()
clobber = argv.clobber

# Create new generic header
header = {
        'version': scandata.program_version,
        'startdate': strftime("%Y-%m-%dT%H:%M:%S"),
        'startfreq': argv.startfreq * 1e6,
        'endfreq': argv.endfreq * 1e6,
        'passes': argv.passes
        }

# Perform sanity check on the arguments
if header['endfreq'] < header['startfreq']:
    print("Ending frequency must be greater than or equal to starting frequency.")
    sys.exit()
if header['passes'] < 1:
    print("Number of passes cannot be less than one.")
    sys.exit()

print("\nStarting frequency: %f MHz" % (header['startfreq']/1e6))
print("Ending frequency: %f MHz" % (header['endfreq']/1e6))
print("Number of passes: %d\n" % header['passes'])
print("Will write to output file '%s'" % argv.output_file)

# Initialize SDR
sdr = RtlSdr()
sdr.set_gain(200)
header['gain'] = sdr.get_gain()
print("Using a gain of %f" % sdr.get_gain())

# TODO: properly set the sampling rate and number of samples to read
sdr.sample_rate *= 2
header['bandwidth'] = sdr.sample_rate
sdr.set_center_freq(header['startfreq'])
print("Device bandwidth: %f MHz" % ((sdr.sample_rate)/1e6))

fft_size = 2048
num_windows = int(math.ceil((header['endfreq'] - header['startfreq'])/(sdr.get_sample_rate())))
print("Sampling %d windows per %d passes\n" % (num_windows, header['passes']))

data = numpy.zeros(shape=(header['passes'], num_windows, fft_size), dtype=numpy.float64)

signal.signal(signal.SIGINT, terminate)
print("Press Ctrl+C to cancel scanning and save")

for i in range(0, header['passes']):
    freq = header['startfreq']

    if not argv.silent:
        print("\nBeginning pass %d of %d\n" % (i+1, header['passes']))

    for j in range(0, num_windows):
        sdr.set_center_freq(freq)

        if not argv.silent:
            print("Scanning window %d of %d at %f MHz..." %
                    (j+1, num_windows, (freq/1e6)))

        # TODO: normalize, average over time, and allow for custom fft info
        samples = sdr.read_samples(fft_size)
        spectrum = numpy.abs(numpy.fft.fft(samples))**2

        data[i][j] = spectrum

        freq += sdr.get_sample_rate()

header['enddate'] = strftime("%Y-%m-%dT%H:%M:%S")
saveFits(header, data, clobber)

