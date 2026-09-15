# sedategenerator_v2

A solar eclipse date generator that returns a csv style formatting. The format is:
Datetime in UT1,Datetime in TT,Delta T in seconds,Datetime T0 in TT,x0,x1,x2,x3,y0,y1,y2,y3,d0,d1,d2,d3,l10,l11,l12,l13,l20,l21,l22,l23,u0,u1,u2,u3,tanf1,tanf2

To run the script, type `python (or python3 depending on your machine) main.py --start {start year in int} --end {end year in int and not the same as start year} --step {step to find eclipses in seconds in int} --ttm {TT Mode 0 or 1}`
*Note that if you change the TT mode, sometimes the Eclipse Times will yield different results
