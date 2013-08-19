# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

""" cgs - Physical constants in CGS.

For reference: the esu has dimensions of g^1/2 cm^3/2 s^-1

E and B field have g^1/2 cm^-1/2 s^-1

esu * field = dyne
"""

# make e the electron charge
from numpy import pi, e as euler, exp, sqrt, log, log10

c = 2.99792458e10 # cm / s
h = 6.6260755e-27 # erg s
me = 9.1093897e-28 # g
mp = 1.6726231e-24 # g
e = 4.802e-10 # esu
G = 6.67259e-8 # cm^3 g^-1 s^-2
k = 1.3806505e-16 # erg / K
hbar = h / 2 / pi
alpha = e**2  / hbar / c # dimensionless
sigma = pi**2 * k ** 4 * hbar**-3 * c**-2 / 60 # g s^-3 K^-4
arad = 4 * sigma / c # radiation constant, erg cm^-3 K^-4
a0 = hbar**2 / (me * e**2) # cm
re = e**2 / (me * c**2) # cm
ryd1 = e**2 / (2 * a0) # erg
mue = e * hbar / (2 * me * c) # magnetic moment units, whatever those are
sigmat = 8 * pi * re**2 / 3 # cm^2
ergperev = 1.60e-12 # erg / eV [dimensionless]
evpererg = 1. / ergperev
conjaaev = 1e8 * c * h / ergperev # eV*Angstrom ; lambda(AA) = conjaaev/E(eV)
cmperpc = 3.08568025e18 # cm / pc [dimensionless]
pcpercm = 1. / cmperpc
cmperau = 1.49598e13 # cm / AU [dimensionless]
aupercm = 1. / cmperau
spersyr = 31558150. # s / sidereal yr [dimensionless]
syrpers = 1. / spersyr

# Astro
msun = 1.989e33 # g
rsun = 6.9599e10 # cm
lsun = 3.826e33 # erg s^-1
tsun = 5770 # K
mearth = 5.974e27 # g
rearth = 6.378e8 # cm
mjup = 1.8986e30 # g
rjup = 7.1492e9 # cm (equatorial)

jypercgs = 1e23 # jy per (erg s^-1 cm^-2 Hz^-1) [dimensionless]
cgsperjy = 1e-23

bnu = lambda nu, T: 2 * h * nu**3 * c**-2 / (exp (h * nu / k / T) - 1)
blambda = lambda lam, T: 2 * h * lam**-5 * c**2 / (exp (h * c / lam / k / T) - 1)
