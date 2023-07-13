def flatcombine(ffiles, bias = None, dark = None, trim = True, normframe = True,
                illumcor = True, threshold = 0.9,
                responsecor = True, smooth = False, npix = 11,
                Saxis = 0, Waxis = 1,
                EXPTIME = 'EXPTIME', DATASEC = 'DATASEC'  # header keywords
                ):
    """
    A general-purpose wrapper function to create a science-ready
    flatfield image.

    Parameters:

    ffiles: numpy ndarray
    Array of paths to the flat frame "fits" files.

    bias: CCDData object (optional), default = None
    Median bias frame to subtract from each flat image.

    trim: bool, default = True
    Trim the "bias section" out of each flat frame. Uses "fits" header field defined by the "DATASEC" keyword.

    normframe: bool, default = True
    If set to True, normalize each bias frame by its median value before combining.

    illumcor: bool, default = True
    Use the median-combined flat to determine the illuminated portion of the CCD. Runs "find_illum" function.

    threshold: float (optional), default = 0.9
    Passed to "find_illum" function.The fraction to clip to determine the illuminated portion (between 0 and 1).

    responsecor: bool, default = True
    Divide out the spatially-averaged spectrum response from the flat image. Runs "flat_response" function.

    smooth: bool, default = False
    Passed to "flat_response" function. If desired, the 1D mean-combined flat is smoothed before dividing out.

    npix: int, default = 11
    Passed to "flat_response" function.
    If "smooth=True", determines how big of a boxcar smooth kernel should be used (in pixels).

    EXPTIME: string (optional), default = "EXPTIME"
    "Fits" header field containing the exposure time in seconds.

    DATASEC: string (optional), default = "DATASEC"
    "Fits" header field containing the data section of the CCD (to remove the bias section). Used if trim = True.

    Saxis: int (optional), default is 0
    Set which axis is the spatial dimension. For DIS, Saxis = 0 (corresponds to "NAXIS"2" in the header).
    For KOSMOS, Saxis = 1.

    Waxis: int (optional), default is 1
    Set which axis is the wavelength dimension. For DIS, Waxis = 1 (corresponds to "NAXIS1" in the header).
    For KOSMOS, Waxis = 0.
    NOTE: if Saxis is changed, Waxis will be updated, and visa versa.

    Returns:

    flat: CCDData object
    Always returned, the final flat image object.

    ilum: array
    Returned if illumcor = True. The 1D array to use for trimming science images to the illuminated portion of the CCD.

    """

    # Old DIS default was Saxis=0, Waxis=1, shape = (1028,2048).
    # KOSMOS is swapped, shape = (4096, 2148).
    if (Saxis == 1) | (Waxis == 0):
        # If either axis is swapped, swap them both.
        Saxis = 1
        Waxis = 0
    # Initialize an empty list "flist" to append reduced and normalized flat frames to it.
    flist = []
    # Loop over all flat frames.
    for ind in range(len(ffiles)):
        # Reduce each flat frame using "apo_proc" defined above.
        img = apo_proc(ffiles[ind], bias = bias, dark = dark, EXPTIME = EXPTIME, DATASEC = DATASEC, trim = trim)
        # If desired, normalize each flat frame by its median.
        if normframe:
            img.data = img.data / np.nanmedian(img.data)
        # Append each resulting flat frame to "flist".
        flist.append(img)
    # Combine the flat frames with a median.
    medflat = Combiner(flist).median_combine()
    # If desired, the median flat is used to detect the illuminated portion of the CCD.
    if illumcor:
        ilum = kosmos.find_illum(medflat, threshold = threshold, Waxis = Waxis)
        # Trimming the median flat to only the illuminated portion.
        if Waxis == 1:
            medflat = trim_image(medflat[ilum[0]:(ilum[-1] + 1), :])
        if Waxis == 0:
            medflat = trim_image(medflat[:, ilum[0]:(ilum[-1] + 1)])
    # If desired, divide out the spatially-averaged spectrum response from the flat image.
    if responsecor:
        medflat = kosmos.flat_response(medflat, smooth = smooth, npix = npix, Saxis = Saxis)
    # If "illumcore" was set to True, return both the final flat image object
    # and the 1D array used for trimming science images to the illuminated portion of the CCD.
    if illumcor:
        return medflat, ilum
    else:
        return medflat
