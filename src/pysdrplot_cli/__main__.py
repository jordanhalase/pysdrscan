#!/usr/bin/python

from astropy.io import fits
from astropy.wcs import WCS
from matplotlib.colors import Normalize, LogNorm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import argparse

parser = argparse.ArgumentParser(prog="PySDRPlot",
        description="Plot graphs saved by PySDRScan")
parser.add_argument("file", help="File to plot", type=str)
parser.add_argument("-o", "--output-file",
        help="Output file",
        default=None,
        type=str)
parser.add_argument("-n", "--norm",
        help="Value normalization",
        choices=['none', 'linear', 'logarithmic'],
        default='logarithmic')

argv = parser.parse_args()
if argv.norm == 'none':
    imnorm = None
elif argv.norm == 'linear':
    imnorm = Normalize()
elif argv.norm == 'logarithmic':
    imnorm = LogNorm()

hdu = fits.open(argv.file)
wcs = WCS(hdu[0].header)

fig = plt.figure()
ax = fig.add_subplot(111, projection=wcs)

# TODO: Wait for wcsaxes to get their act together and implement this
# mhz_fmt = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x*1e-6))
# ax.coords[0].set_major_formatter(mhz_fmt)

img = ax.imshow(hdu[1].data,
        origin='lower',
        aspect='auto',
        norm=imnorm)
# cmap='PuBu_r')
plt.colorbar(img)

plt.xlabel('Frequency')
plt.ylabel('Passes')
plt.subplots_adjust(right=1.0)
if argv.output_file == None:
    plt.show()
else:
    plt.savefig(argv.output_file)

