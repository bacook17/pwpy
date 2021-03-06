# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""srctable - flexible table of astronomical source information

The main API is the stmapping() function, which creates a Mapping
object for reading a flatdb as a source table.

readst() is a convenience function analogous to flatdb.readtable()
that uses stmapping() as its Mapping.

sfindcols is the list of columns that we can extract by parsing
the output of MIRIAD sfind with parseSFind().

nvsscols is likewise the list of columns that we can extract
by parsing the output of the NVSS query program with parseNVSS().
"""

from astutil import *
import flatdb

__all__ = ('Holder readtable writetable stmapping readst '
           'sfindcols nvsscols parseSFind parseNVSS').split ()


from flatdb import Holder, readtable, writetable # convenience


def stmapping ():
    # TODO: tunable precision in flux, position, etc. Maybe I should
    # put the definition of the sfind and NVSS columns with the rest
    # of the sfind and NVSS bits. I dunno.

    m = flatdb.Mapping ()
    m.add ('ident', str, 20)
    m.add ('ra', object, 12, parse=parsehours, format=fmthours) # rad
    m.addfloat ('ra_uc', '%.3f', 8, A2R) # rad
    m.add ('dec', object, 12, parse=parsedeglat, format=fmtdeglat) # rad
    m.addfloat ('dec_uc', '%.2f', 8, A2R) # rad
    m.addfloat ('totflux', '%.5f', 12) # jy
    m.addfloat ('totflux_uc', '%.7f', 12) # jy
    m.add ('totflux_is_ul', bool, 1)
    m.addfloat ('pkflux', '%.5f', 12) # jy
    m.addfloat ('pkflux_uc', '%.7f', 12) # jy
    m.add ('pkflux_is_ul', bool, 1)
    m.addfloat ('bgrms', '%.5f', 12) # jy
    m.addfloat ('major', '%.2f', 7, A2R) # rad
    m.addfloat ('major_uc', '%.2f', 12, A2R) # rad
    m.add ('major_is_ul', bool, 1)
    m.addfloat ('minor', '%.2f', 7, A2R) # rad
    m.addfloat ('minor_uc', '%.2f', 12, A2R) # rad
    m.add ('minor_is_ul', bool, 1)
    m.addfloat ('pa', '%+.2f', 7, D2R) # rad
    m.addfloat ('pa_uc', '%.2f', 12, D2R) # rad

    m.addfloat ('sfind_fitrms', '%9.5f', 12) # jy

    m.addfloat ('nvss_dist', '%f', 12)
    m.addfloat ('nvss_angle', '%f', 12)
    m.add ('nvss_resid_code', str, 2)
    m.addfloat ('nvss_resid_val', '%f', 12)
    m.addfloat ('nvss_lpflux', '%f', 12)
    m.addfloat ('nvss_lpflux_uc', '%f', 12)
    m.addfloat ('nvss_lppa', '%f', 12)
    m.addfloat ('nvss_lppa_uc', '%f', 12)
    m.add ('nvss_field', str, 8)
    m.addfloat ('nvss_pixel_x', '%f', 12)
    m.addfloat ('nvss_pixel_y', '%f', 12)

    # these are used by precastro:
    m.addfloat ('promora', '%.3f', 9) # mas/yr
    m.addfloat ('promodec', '%.3f', 9) # mas/yr
    m.addfloat ('promoepoch', '%.4f', 12) # JD TDB
    m.addfloat ('parallax', '%.3f', 9) # mas
    m.addfloat ('vradial', '%.2f', 10) # km/s

    return m


def readst (source, recfactory=Holder, **kwargs):
    return readtable (source, stmapping (**kwargs), recfactory=recfactory)


# Parsing output of MIRIAD sfind

_sfindMiscColumns = ('ra_uc dec_uc pkflux pkflux_uc totflux major '
                     'minor pa bgrms sfind_fitrms').split ()
_sfindMiscOffsets = [24, 32, 40, 50, 58, 68, 74, 80, 86, 92, 100]
_sfindUnits= [A2R, A2R, 1e-3, 1e-3, 1e-3, A2R,
              A2R, D2R, 1e-3, 1e-3]

def parseSFind (lines, pristine=False):
    for linenum, line in enumerate (lines):
        if line[0] == '#':
            continue

        a = line.strip ().split ()
        source = Holder ()
        source.ra = parsehours (a[0])
        source.dec = parsedeglat (a[1])

        if a[1][0] in '+-':
            ofs = 1
        else:
            ofs = 0

        for i, name in enumerate (_sfindMiscColumns):
            substr = line[_sfindMiscOffsets[i]+ofs:_sfindMiscOffsets[i+1]+ofs]

            if '*' in substr:
                val = None
            else:
                val = float (substr) * _sfindUnits[i]

            setattr (source, name, val)

        if (not pristine and source.totflux is not None and
            source.pkflux is not None and source.totflux < source.pkflux):
            # Sfind docs say you can occasionally get this for
            # unresolved sources if the fitted Gaussian parameters are
            # smaller than the beamsize.
            source.totflux = source.pkflux

        if source.pkflux_uc == 0.:
            # Sometimes the precision in the text output is
            # insufficient; be conservative.
            source.pkflux_uc = 0.0005 * 1e-3

        if source.pkflux_uc is None:
            source.totflux_uc = None
        else:
            source.totflux_uc = abs (source.totflux * source.pkflux_uc / source.pkflux)

        if source.ra_uc == 0.: # as with pkflux_uc
            source.ra_uc = 0.0005 * A2R

        if source.dec_uc == 0.:
            source.dec_uc = 0.005 * A2R

        yield source


sfindcols = ('ra ra_uc dec dec_uc pkflux pkflux_uc totflux '
             'totflux_uc major minor pa bgrms sfind_fitrms').split ()


# Parsing the NVSS textual catalog
# NOTE: if non-deconvolved source parameters are requested, peak fluxes are
# returned, not total fluxes! We don't detect this (you'd have to poke at
# the comment lines).

nvss_columns1 = {
    # Each tuple gives the Python slice info for extracting that column:
    # for tuple t, take text[t[0]:t[1]].
    'ra': (0, 11), # [hr] space-separated sexigesimal
    'dec': (12, 23), # [deg] space-separated signed sexigesimal
    'nvss_dist': (24, 30), # [arcsec] dist of src from search origin
    'totflux': (31, 37), # [mjy]
    'major': (38, 43), # [arcsec]; (bool, float), bool indicating if upper limit
    'minor': (44, 49), # ditto
    'pa': (50, 55), # [deg], poss. absent
    'nvss_resid_code': (56, 59), # P*=high pk, R*=high rms, S*=high sum
    'nvss_lpflux': (60, 65), # [mjy] linear polarized flux
    'nvss_lppa': (66, 71), # [deg] lin. pol E vector PA
    'nvss_field': (72, 80),
    'nvss_pixel_x': (81, 88),
    'nvss_pixel_y': (89, 96),
}

nvss_columns2 = {
    'ra_uc': (0, 11), # [time-sec]
    'dec_uc': (12, 23), # [arcsec]
    'nvss_angle': (24, 30), # [deg] PA of src *location* relative to search origin
    'totflux_uc': (31, 37), # [mjy]
    'major_uc': (38, 43), # [arcsec], poss. absent
    'minor_uc': (44, 49), # [arcsec], poss. absent
    'pa_uc': (50, 55), # [deg], poss. absent
    'nvss_resid_val': (56, 59), # [100s of ujy] value triggering residual flag
    'nvss_lpflux_uc': (60, 65), # [mjy]
    'nvss_lppa_uc': (66, 71), # [deg] poss. absent
}


def nvss_parsera (t):
    chars = list (t)
    chars[2] = ':'
    chars[5] = ':'
    return parsehours (''.join (chars))


def nvss_parsedec (t):
    chars = list (t)
    chars[3] = ':'
    chars[6] = ':'
    return parsedeglat (''.join (chars))


nvss_asec2rad = lambda t: float (t) * A2R
nvss_tsec2rad = lambda t: float (t) * A2R * 15
nvss_mjy2jy = lambda t: float (t) * 1e-3

def nvss_maybeulasec (t):
    if t[0] == '<':
        return (True, float (t[1:]) * A2R)
    return (False, float (t) * A2R)


def nvss_strornone (t):
    t = t.strip ()
    if not len (t):
        return None
    return t

def nvss_scaleornone (scale):
    def f (t):
        t = t.strip ()
        if not len (t):
            return None
        return float (t) * scale
    return f

nvss_floatornone = nvss_scaleornone (1)
nvss_degornone = nvss_scaleornone (D2R)
nvss_asecornone = nvss_scaleornone (A2R)
nvss_mjyornone = nvss_scaleornone (1e-3)
nvss_hujyornone = nvss_scaleornone (1e-4)

nvss_parsers = {
    # default parser is float()
    'ra': nvss_parsera,
    'ra_uc': nvss_tsec2rad,
    'dec': nvss_parsedec,
    'dec_uc': nvss_asec2rad,
    'nvss_dist': nvss_asec2rad,
    'nvss_angle': nvss_degornone,
    'totflux': nvss_mjy2jy,
    'totflux_uc': nvss_mjy2jy,
    'major': nvss_maybeulasec,
    'major_uc': nvss_asecornone,
    'minor': nvss_maybeulasec,
    'minor_uc': nvss_asecornone,
    'pa': nvss_degornone,
    'pa_uc': nvss_degornone,
    'nvss_resid_code': nvss_strornone,
    'nvss_resid_val': nvss_hujyornone,
    'nvss_lpflux': nvss_mjy2jy,
    'nvss_lpflux_uc': nvss_mjyornone,
    'nvss_lppa': nvss_degornone,
    'nvss_lppa_uc': nvss_degornone,
    'nvss_field': str,
}


def parseNVSS (stream):
    linenum = 0
    datalinenum = 0
    source = None

    for line in stream:
        linenum += 1

        if line[0] == '#':
            continue

        if datalinenum % 2 == 0:
            assert source is None, 'NVSS internal logic error 1'
            source = Holder ()
            colspec = nvss_columns1
        else:
            colspec = nvss_columns2

        try:
            for key, (b0, b1) in colspec.iteritems ():
                parser = nvss_parsers.get (key, float)
                setattr (source, key, parser (line[b0:b1]))
        except Exception as e:
            raise Exception ('line %d, item %s: %s' % (linenum, key, e))

        if datalinenum % 2 == 1:
            # Fixups
            source.major_is_ul = source.major[0]
            source.major = source.major[1]
            source.minor_is_ul = source.minor[0]
            source.minor = source.minor[1]
            # Done
            yield source
            source = None

        datalinenum += 1

    assert source is None, 'NVSS internal logic error 2'




nvsscols = ('ra ra_uc dec dec_uc totflux totflux_uc major major_uc '
            'major_is_ul minor minor_uc minor_is_ul pa pa_uc '
            'nvss_dist nvss_angle nvss_resid_code nvss_resid_val '
            'nvss_lpflux nvss_lpflux_uc nvss_lppa '
            'nvss_lppa_uc nvss_field nvss_pixel_x nvss_pixel_y').split ()


# Transformations on sources

has = lambda s, f: getattr (s, f, None) is not None

def deconvolve (source, bmaj, bmin, bpa, minaxprod=0, preserve=True):
    if not (has (source, 'major') and has (source, 'minor')
            and has (source, 'pa')):
        source.deconvolve_error = 'missing shape information'
        return source

    if preserve:
        source.c_major = source.major
        source.c_minor = source.minor
        source.c_pa = source.pa

    dmaj, dmin, dpa, status = gaussianDeconvolve (source.major,
                                                  source.minor,
                                                  source.pa,
                                                  bmaj, bmin, bpa)

    if status == 'fail':
        dmaj = dmin = dpa = None
        source.deconvolve_error = 'deconvolution failed'
    elif status == 'pointlike':
        dmaj = dmin = dpa = None
        source.deconvolve_error = None
    elif status == 'ok':
        source.deconvolve_error = None
    else:
        raise Exception ('unexpected deconvolution status ' + status)

    if dmaj is not None and dmaj * dmin < minaxprod:
        dmaj = dmin = dpa = None

    if has (source, 'major_uc'):
        if dmaj is None:
            source.major_uc = None
        else:
            source.major_uc *= dmaj / source.major

    if has (source, 'minor_uc'):
        if dmin is None:
            source.minor_uc = None
        else:
            source.minor_uc *= dmin / source.minor

    assert not has (source, 'pkflux'), ('need more info to update pkflux; '
                                        'clear it if info not needed')

    source.major = dmaj
    source.minor = dmin
    source.pa = dpa
    return source


# Overlays for ndshow. This is kind of an awkward place for this, but
# ndshow shouldn't depend on srctable, and I might want to reuse this
# functionality interactively, so it shouldn't go in pwshow.

def loadAsOverlay (source, topixel, imgheight):
    headers, cols, recs = readtable (source, stmapping ())
    compact = []

    for rec in recs:
        y, x = topixel ([rec.dec, rec.ra])

        if not hasattr (rec, 'major') or rec.major is None or rec.major == 0:
            compact.append ((x, y))
            continue

        # TODO: draw Gaussians with the right shape
        compact.append ((x, y))

    def drawoverlay (ctxt, width, height, x0, y0, d2p):
        ctxt.set_source_rgb (255, 0, 0)

        for dx, dy in compact:
            cx = (dx + 0.5 - x0) * d2p
            cy = (imgheight - dy - 0.5 - y0) * d2p

            ctxt.move_to (cx - 5, cy)
            ctxt.line_to (cx + 5, cy)
            ctxt.stroke ()
            ctxt.move_to (cx, cy - 5)
            ctxt.line_to (cx, cy + 5)
            ctxt.stroke ()

    return drawoverlay
