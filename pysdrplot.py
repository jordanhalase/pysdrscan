#!/usr/bin/python

from astropy.io import fits
from astropy.wcs import WCS
from matplotlib.colors import LogNorm
from matplotlib import pyplot
import argparse

parser = argparse.ArgumentParser(prog="PySDRPlot",
        description="Plot graphs saved by PySDRScan")
parser.add_argument("file", help="File to plot", type=str)
argv = parser.parse_args()

hdu = fits.open(argv.file)
wcs = WCS(hdu[0].header)

figure = pyplot.figure()
figure.add_subplot(111, projection=wcs)
pyplot.imshow(hdu[1].data,
        origin='lower',
        aspect='auto',
        norm=LogNorm())
        # cmap='PuBu_r')
pyplot.xlabel('Frequency')
pyplot.ylabel('Passes')
pyplot.show()

