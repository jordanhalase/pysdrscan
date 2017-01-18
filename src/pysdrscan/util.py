#!/usr/bin/python

from numpy import floor

def secs_to_segments(secs, fft_size, sample_rate):
    return int(floor(sample_rate * secs / fft_size))

