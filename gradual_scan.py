#!/usr/bin/python

# COMMAND LINE USAGE
#   ./gradual_scan.py starting_freq ending_freq num_passes
#
# frequencies are in MHz
#
# num_passes is the number of times the entire spectrum is
# scanned and added to the time information of the FITS file

from rtlsdr import RtlSdr
from astropy.io import fits
import numpy
import sys

out = fits.HDUList()
out.append(fits.PrimaryHDU())
output_file = "out.fits"

# Parse arguments
if len(sys.argv) < 4:
    # TODO: print some INFOUSAGE instead of this vague statement
    print("Please supply the needed arguments. Read this file for information.")
    sys.exit()

starting_freq = float(sys.argv[1]) * 1e6
out[0].header["FRQ_STRT"] = (starting_freq, "Start frequency (Hz)")
print("\nStarting frequency: %f MHz" % (starting_freq/1e6))

ending_freq = float(sys.argv[2]) * 1e6
if ending_freq < starting_freq:
    print("Ending frequency must be greater or equal to starting frequency.")
    sys.exit()
out[0].header["FRQ_END"] = (ending_freq, "End frequency (Hz)")
print("Ending frequency: %f MHz" % (ending_freq/1e6))

num_passes = int(sys.argv[3])
if num_passes < 1:
    print("Number of passes cannot be less than one.")
    sys.exit()
out[0].header["PASSES"] = (num_passes, "Full passes")
print("Number of passes: %d\n" % num_passes)

if len(sys.argv) > 4:
    output_file = sys.argv[4]
print("Will write to output file '%s'" % output_file)

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

data = numpy.zeros(shape=(num_passes, fft_size), dtype=numpy.float64)

for i in range(0, num_passes):
    freq = starting_freq
    while freq <= ending_freq:
        print("Scanning at %f MHz..." % (freq/1e6))

        # TODO: normalize, average over time, and allow for custom fft info
        samples = sdr.read_samples(fft_size)
        spectrum = numpy.absolute(numpy.fft.fft(samples))

        data[i] = spectrum

        freq += sdr.get_sample_rate()
        sdr.set_center_freq(freq)

# TODO: Handle exception where output file already exists
out.append(fits.ImageHDU())
out[1].data = data
out.writeto(output_file)

