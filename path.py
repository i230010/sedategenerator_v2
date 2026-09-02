import math
from skyfield.units import Angle
import constants as c
import asdatetime as dt

def polynize(a, x):
    return a[0] + a[1]*x + a[2]*x*x + a[3]*x*x*x

def coords(Xa: list, Ya: list, Da: list, Ma: list, delta_t: float, T: float) -> tuple:
    X = polynize(Xa, T)
    Y = polynize(Ya, T)
    d = Angle(degrees=polynize(Da, T)).radians
    m = Angle(degrees=polynize(Ma, T)).radians
    e2 = c.E_SQUARED
    one_minus_f = c.ONE_MINUS_F
    omega = 1.0 / math.sqrt(1 - e2 * (math.cos(d) ** 2))
    y1 = omega * Y
    b1 = omega * math.sin(d)
    b2 = (one_minus_f * omega * math.cos(d))
    Bsq = 1 - X**2 - y1**2
    if Bsq < 0:
        return None, None
    B = math.sqrt(Bsq)
    sinphi1 = B * b1 + y1 * b2
    phi1 = math.asin(sinphi1)
    phi = math.atan(c.ELLIPSOID_CORRECTION * math.tan(phi1))
    sinH = X / math.cos(phi1)
    cosH = (B * b2 - y1 * b1) / math.cos(phi1)
    H = math.atan2(sinH, cosH)
    lambda_geo = (m - H - c.DELTA_LAMBDA_FACTOR * delta_t * math.pi / 180) % (2 * math.pi)
    lat_uncorrected, lon_uncorrected = (Angle(radians=phi).degrees, (Angle(radians=lambda_geo).degrees * -1))
    lat = ((lat_uncorrected + 90) % 180) - 90
    lon = ((lon_uncorrected + 180) % 360) - 180
    return lat, lon

t_tt = dt.datetime(2027, 8, 2, 10, 7, 50)
t0 = dt.datetime(2027, 8, 2, 10, 0, 0)
delta_t = 73

x = [-0.0201069306, 0.5451545354, -0.0000443799, -0.0000092310]
y = [0.1600239032, -0.2100149805, -0.0001226392, 0.0000037396]
d = [17.8638727486, -0.0101032228, -0.0000039108, -0.0000000079]
l1 = [0.5305090721, 0.0000140661, -0.0000128242, 0.0000000002]
l2 = [ -0.0155706871, 0.0000139960, -0.0000127603, 0.0000000002]
u = [328.5025789761, 15.0020558215, 0.0000000000, 0.0000000000]
tanf1 = 0.0046044725
tanf2 = 0.0045815319