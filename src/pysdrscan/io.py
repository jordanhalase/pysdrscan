#!/usr/bin/python

from astropy.io import fits
from astropy import wcs
import numpy as np

import attrib
from __init__ import __version__, __title__

def save_fits(filename, header, data, overwrite=False):
    # Collapse array of FFT data into one broad spectrum
    data = data.reshape((header['passes'], -1))

    hdulist = fits.HDUList()
    hdulist.append(fits.PrimaryHDU())
    hdulist.append(fits.ImageHDU())
    hdulist[1].data = data

    # Check if output file already exists
    # if os.path.isfile(argv.output_file) and overwrite == False:
        # choice = ""
        # while choice != ('y' or 'n'):
            # print("File '%s' already exists. Overwrite? [y/N]:" % argv.output_file),
            # choice = raw_input().lower()
            # if choice == 'y':
                # print("Overwriting")
                # overwrite = True
            # elif choice == 'n':
                # print("Abandoning all captured data")
                # sys.exit()

    # TODO: Finish WCS
    w = wcs.WCS(naxis=2)
    w.wcs.crpix = [0, 0]
    w.wcs.crval = [header['startfreq'] - header['bandwidth']/2.0, 0]
    w.wcs.cdelt = [header['bandwidth']/header['fftsize'], 1]
    w.wcs.ctype = ['FREQ', '']
    w.wcs.cunit = ['Hz', '']

    hdulist[0].header.update(attrib.to_fits_header_dict(header))
    hdulist[0].header.update(w.to_header())
    hdulist.writeto(filename, overwrite=overwrite)
    hdulist.close()

