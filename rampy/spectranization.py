# -*- coding: utf-8 -*-
import numpy as np
from scipy import interpolate
from scipy import signal
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import interp1d

import rampy

# SPECIFIC FUNCTIONS FOR TREATMENT OF SPECTRA

def spectrarray(name,sh,sf,x):
    """Construct a general array that contain common X values in first columns and all Y values in the subsequent columns.

    Parameters
    ----------
    name : ndarray
        Array containing the names of the files (should work with a dataframe too).
    sh : int
        Number of header line in files to skip.
    sf : int
        Number of footer lines in files to skip.
    x : ndarray
        The common x axis.

    Returns
    -------
    out
        An array with the common X axis in first column and all the spectra in the subsequent columns.
    """
    for i in range(len(name)):
        rawspectre = np.genfromtxt(name[i],skip_header=sh, skip_footer=sf)
        rawspectre = rawspectre[~np.isnan(rawspectre).any(1)] # check for nan

        y = resample(rawspectre[:,0],rawspectre[:,1],x) # resample the signal

        # Now we construct the output matrix
        # 1st column is the x axis
        # then others are the spectra in the order provided in the list of names input array
        if i == 0:
            out = np.zeros((len(x),len(name)+1))
            out[:,0]=x
            out[:,i+1]=y
        else:
            out[:,i+1]=y

    return out

def spectrataux(spectres):
    """Calculate the increase/decrease rate of each frequencies in a set of spectra.

    Parameters
    ----------
    spectres : ndarray
        An array of spectra containing the common X axis in first column and all the spectra in the subsequent columns. (see spectrarray function)

    Returns
    -------
    taux : ndarray
        The rate of change of each frequency, fitted by a 2nd order polynomial functions.
    """
    # we need an organized function before calling the curve_fit algorithm
    freq = spectres[:,0]
    # output array
    taux = np.zeros((len(freq),4));
    taux[:,0] = freq[:]

    # We look a each frequency, we sort y data and fit them with a second order polynomial
    for i in range(len(freq)):
        y = spectres[i,1::]
        popt, pcov = curve_fit(fun2,x,y,[0.5e-3,0.5e-4,1e-6])
        taux[i,1:len(x)]=popt

    return taux

def spectraoffset(spectre,oft):
    """Offset your spectra with values in offsets

    Parameters
    ----------
    spectre : ndarray
        array of spectra constructed with the spectrarray function
    oft : ndarray
        array constructed with numpy and containing the coefficient for the offset to apply to spectra

    Returns
    -------
    out : ndarray
        Array with spectra separated by offsets defined in oft

    """

    out = np.zeros(spectre.shape) # we already say what is the output array
    for i in range(len(oft)): # and we offset the spectra
        out[:,i+1] = spectre[:,i+1] + oft[i]
    return out

#
# Simple data treatment functions
#
def flipsp(sp):
    """Flip an array along the row dimension (dim = 1) if the row values are in decreasing order.

    Parameters
    ----------
    sp : ndarray
        An array with n columns
    Returns
    -------
    sp : ndarray
        The same array but sorted such that the values in the first column are in increasing order.
    """
    if sp[-1,0] < sp[0,0]:
        sp = np.flip(sp,0)
        return sp
    else:
        return sp

def resample(x,y,x_new):
    """Resample a y signal associated with x, along the x_new values.

    Parameters
    ----------
    x : ndarray
        The x values
    y : ndarray
        The y values
    x_new : ndarray
        The new X values

    Returns
    -------
    y_new : ndarray
        y values interpolated at x_new.

    Remarks
    -------
    Uses scipy.interpolate.interp1d
    """
    f = interp1d(x,y)
    return f(x_new)

def normalise(y,x=0,method="intensity"):
    """normalisation of the y signal
    Parameters
    ==========
    x : ndarray
        x values
    y : ndarray
        y values
    method : string
        method used, choose between area, intensity, minmax
    Returns
    =======
    y_norm : Numpy array
        Normalised signal
    """
    if method == "area":
        if x == 0:
            raise TypeError("Input x values for area normalisation")
        y = y/np.trapz(y,x)
    if method == "intensity":
        y = y/np.max(y)
    if method == "minmax":
        y = (y-np.min(y))/(np.max(y)-np.min(y))

def centroid(x,y,smoothing=False,**kwargs):
    """calculation of the y signal centroid
    
    as np.sum(y/np.sum(y)*x)
    if smoothing == 1:
    
    Parameters
    ==========
    x: Numpy array
        x values
    y: Numpy array
        y values, 1 spectrum

    Options
    =======
    smoothing : bool
        True or False. Smooth the signals with arguments provided as kwargs. Default method is whittaker smoothing. See the rampy.smooth function for smoothing options and arguments.
        
    Returns
    =======
    centroid : float
        signal centroid
    """
    
    # for safety, we reshape the x array    
    x = x.reshape(-1)
    y = y.reshape(-1)
    
    if smoothing == True:
        y_ = rampy.smooth(x,y,**kwargs)
    else: 
        y_ = y.copy()
        
    return np.sum(y_/np.sum(y_)*x)