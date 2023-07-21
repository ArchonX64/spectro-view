#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 11:47:49 2018

@author: babychirp

Peak picker and constant difference finder, using peak pick routine lifted
straight from UVA's Autofit v.15c

"""
import numpy
import math
import scipy
import scipy.interpolate


def cubic_spline(spectrum, new_resolution):  # Cubic spline of spectrum to
    # new_resolution; used pre-peak-picking.  Assumes the spectrum is already
    # in order of increasing frequency.

    x = spectrum[:, 0]
    y = spectrum[:, 1]

    old_resolution = (x[-1] - x[0]) / len(spectrum)
    scale_factor = old_resolution / new_resolution

    new_length = int(math.floor(scale_factor * len(spectrum)))

    tck = scipy.interpolate.splrep(x, y, s=0)
    xnew = numpy.arange(x[0], x[-1], new_resolution)
    ynew = scipy.interpolate.splev(xnew, tck, der=0)

    output_spectrum = numpy.column_stack((xnew, ynew))

    return output_spectrum


def peakpicker(spectrum, thresh_l,
               thresh_h):  # Code taken from Cristobal's peak-picking script; assumes spectrum is in increasing frequency order
    peaks = []
    for i in range(1, len(spectrum) - 1):
        if spectrum[i, 1] > thresh_l and spectrum[i, 1] < thresh_h and spectrum[i, 1] > spectrum[(i - 1), 1] and \
                spectrum[i, 1] > spectrum[(i + 1), 1]:
            peaks.append(spectrum[i])

    peakpicks = numpy.zeros((len(peaks), 2))
    for i, row in enumerate(peaks):
        peakpicks[i, 0] = row[0]
        peakpicks[i, 1] = row[1]
    freq_low = spectrum[0, 0]
    freq_high = spectrum[-1, 0]
    return peakpicks, freq_low, freq_high


def intensity_filter(full_list, peaklist, inten_low,
                     filter_level):  # Intensity filter to give more efficient triples searches for isotopologues.

    filtered_peaklist = []
    filtered_full_list = []
    comparison_level = filter_level * float(inten_low)

    for peak in peaklist:
        if peak[1] >= comparison_level:  # Only keep experimental peaks more intense than the lower cutoff.
            filtered_peaklist.append(peak)

    for entry in full_list:
        for peak in filtered_peaklist:
            temp_freq_diff = abs(float(entry[1]) - float(peak[0]))
            if temp_freq_diff <= 0.5:  # Looking for a strong NS peak within 0.5 MHz of its predicted value.  Too coarse, too tight, OK?
                filtered_full_list.append(entry)
                break  # Only need to find one; no need to continue searching through the full experimental peak list after a hit has been found.

    if filter_level == 0:
        filtered_full_list = full_list

    if len(filtered_full_list) < 3:
        print(
            "There aren't enough transitions of appropriate intensity close to predicted positions for an isotopologue search.  Check your NS constants, your scale factor, or your spectral data file.")
        quit()

    return filtered_full_list


def deltanus(peaklist):  # Calculates frequency differences between all peak picked lines
    totaltrans = numpy.size(peaklist[:, 0])  # total number of transitions in peak pick file
    freqh1 = numpy.zeros((totaltrans, 1))
    freql1 = numpy.zeros((totaltrans, 1))
    for n in range(totaltrans):
        freqh1[n] = peaklist[n, 0]  # 1st column of mr_peaky file
        freql1[n] = peaklist[n, 0]  # 1st column of mr_peaky file
    #    delta_nu_1=numpy.zeros((totaltrans,1))
    print(totaltrans)
    # set up two separate 1D arrays that are just the frequency column
    #    print(freqh1,freql1)
    for j in range(totaltrans):
        for i in range(j, totaltrans):
            delta_nu_1 = freqh1[i] - freql1[j]
        print(freqh1, freql1, delta_nu_1)
    return (freqh1, freql1, delta_nu_1)


if __name__ == "main":
    # def looper(): # calculates differences in differences and finds pairs of lines separated by same (within a threshold)
    #    return(freqh1,freql1,delta_nu_1,deltadelta_nu_1)

    numpy.set_printoptions(threshold=999999, formatter={
        'float': '{: 0.5f}'.format})  # bodge to make output pretty as numpy returns scientific notation

    # Define high and low intensity to define range for peak picking
    inten_high = 0.300  # was 0.5
    inten_low = 0.005  # was 0.005

    #    fh = numpy.loadtxt(fileopenbox(msg="Enter the spectrum file in two column format: frequency intensity")) #loads full experimental data file, not just list of peaks

    # Read spectrum data (currently hard-coded input file name)
    spectrum_file = numpy.loadtxt("spectrum.ft")
    # Interpolate expt spectrum to a 2 kHz resolution with a cubic spline.  Gives better peak-pick values.
    spectrum_2kHz = cubic_spline(spectrum_file, 0.002)
    # Call slightly modified version of Cristobal's routine to pick peaks instead of forcing user to do so.
    (peaklist, freq_low, freq_high) = peakpicker(spectrum_2kHz, inten_low, inten_high)
    mr_peaky = open("mr_peaky.dat", "w")
    output_file = open("diffyduck.dat", "w")
    print("{0:7.5f},{1:7.5f}".format(freq_low, freq_high))
    print("Output peaks:\n")
    print(peaklist)
    print(peaklist, file=mr_peaky)
    mr_peaky.close()

    (freqh1, freql1, delta_nu_1) = deltanus(peaklist)
    # print(,file=output_file)