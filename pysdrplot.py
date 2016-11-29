#!/usr/bin/python

from astropy.io import fits
from astropy import wcs
from matplotlib import pyplot
import argparse
import pylab

parser = argparse.ArgumentParser(prog="PySDRPlot",
        description="Plot graphs saved by PySDRScan")
parser.add_argument("file", help="File to plot", type=str)
parser.add_argument("aspect", help="Aspect", type=float)
argv = parser.parse_args()

hdulist = fits.open(argv.file)
w = wcs.WCS(hdulist[0].header)

figure = pyplot.figure()
pylab.imshow(hdulist[1].data, aspect=argv.aspect)
pyplot.show()

