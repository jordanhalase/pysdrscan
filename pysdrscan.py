#!/usr/bin/python

from astropy.io import fits
from rtlsdr import RtlSdr
from time import strftime
import argparse
import math
import numpy
import os
import sys

version = "0.1.0"

parser = argparse.ArgumentParser(prog="PySDRScan", version=version,
        description="Use librtl-supported SDR devices to scan wide spectrum data over time")
parser.add_argument("startfreq", help="Starting frequency in MHz", type=float)
parser.add_argument("endfreq", help="Ending frequency in MHz", type=float)
parser.add_argument("-p", "--passes",
        help="Number of full spectrum passes",
        default=1,
        type=int)
parser.add_argument("-o", "--output-file",
        help="Output file name for FITS data (defaults to start date and time)",
        default=strftime("%Y-%m-%d %H:%M:%S.fits"),
        type=str)
parser.add_argument("--clobber",
        help="Automatically overwrite existing output file",
        action='store_true',
        default=False)
argv = parser.parse_args()

clobber = argv.clobber

out = fits.HDUList()
out.append(fits.PrimaryHDU())
out[0].header["PSSVER"] = (version, "PySDRScan version")

starting_freq = argv.startfreq * 1e6
out[0].header["FRQ_STRT"] = (starting_freq, "Start frequency (Hz)")
print("\nStarting frequency: %f MHz" % (starting_freq/1e6))

ending_freq = argv.endfreq * 1e6
if ending_freq < starting_freq:
    print("Ending frequency must be greater or equal to starting frequency.")
    sys.exit()
out[0].header["FRQ_END"] = (ending_freq, "End frequency (Hz)")
print("Ending frequency: %f MHz" % (ending_freq/1e6))

num_passes = argv.passes
if num_passes < 1:
    print("Number of passes cannot be less than one.")
    sys.exit()
out[0].header["PASSES"] = (num_passes, "Full passes")
print("Number of passes: %d\n" % num_passes)

print("Will write to output file '%s'" % argv.output_file)

# Initialize SDR
sdr = RtlSdr()
sdr.set_gain(200)
out[0].header["GAIN"] = (sdr.get_gain(), "SDR Gain")
print("Using a gain of %f" % sdr.get_gain())

# TODO: properly set the sampling rate and number of samples to read
sdr.sample_rate *= 2
sdr.set_center_freq(starting_freq)
out[0].header["BANDWD"] = (sdr.sample_rate, "Bandwidth (Hz)")
print("Device bandwidth: %f MHz" % ((sdr.sample_rate)/1e6))

fft_size = 2048
num_windows = int(math.ceil((ending_freq - starting_freq)/(sdr.get_sample_rate())))
print("Will sample %d windows per pass\n" % num_windows)

data = numpy.zeros(shape=(num_passes, num_windows, fft_size), dtype=numpy.float64)

for i in range(0, num_passes):
    freq = starting_freq
    print("\nBeginning pass %d of %d\n" % (i+1, num_passes))
    for j in range(0, num_windows):
        print("Scanning at %f MHz..." % (freq/1e6))

        # TODO: normalize, average over time, and allow for custom fft info
        samples = sdr.read_samples(fft_size)
        spectrum = numpy.absolute(numpy.fft.fft(samples))

        data[i][j] = spectrum

        freq += sdr.get_sample_rate()
        sdr.set_center_freq(freq)

# Collapse array of FFT data into one broad spectrum
data = data.reshape((num_passes, -1))

out.append(fits.ImageHDU())
out[1].data = data

if os.path.isfile(argv.output_file) and clobber == False:
    choice = ""
    while choice != ('y' or 'n'):
        print("File '%s' already exists. Overwrite? [y/N]:" % argv.output_file),
        choice = raw_input().lower()
        if choice == 'y':
            print("Overwriting")
            clobber = True
        elif choice == 'n':
            print("Abandoning all captured data (TODO: salvage)")
            sys.exit()

out.writeto(argv.output_file, clobber=clobber)

out.close()

