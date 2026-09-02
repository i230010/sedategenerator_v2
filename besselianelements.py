import math
import numpy as np
import vector
from skyfield.api import load, GREGORIAN_START
from skyfield.units import Angle
from typing import Tuple
import constants as c
import ephempath as p
import asdatetime as dt
import deltatnew as deltat

def km_to_earth_radii(km: float) -> float:
    return km / c.EARTH_RADIUS_KM

def find_coeffs_tt(
    t: dt.datetime,
) -> Tuple[float, float, float, float, float, float, float, float]:
    planets = load(p.EPHEM_PATH)
    earth, sun, moon = planets["earth"], planets["sun"], planets["moon"]

    ts = load.timescale(delta_t = deltat.calc_delta_t(t.year, t.month))
    ts.julian_calendar_cutoff = GREGORIAN_START
    t_sf = ts.tt(t.year, t.month, t.day, t.hour, t.minute, t.second)

    obs_sun = earth.at(t_sf).observe(sun)
    obs_moon = earth.at(t_sf).observe(moon)

    sun_ra, sun_dec, sun_dist = obs_sun.radec()
    moon_ra, moon_dec, moon_dist = obs_moon.radec()

    sun_radius_r: float = km_to_earth_radii(sun_dist.km)
    moon_radius_r: float = km_to_earth_radii(moon_dist.km)

    sun_ra_rad: float = sun_ra.radians
    sun_dec_rad: float = sun_dec.radians
    moon_ra_rad: float = moon_ra.radians
    moon_dec_rad: float = moon_dec.radians

    sun_vec: vector.VectorObject3D = vector.obj(
        x=sun_radius_r * math.cos(sun_dec_rad) * math.cos(sun_ra_rad),
        y=sun_radius_r * math.cos(sun_dec_rad) * math.sin(sun_ra_rad),
        z=sun_radius_r * math.sin(sun_dec_rad),
    )
    moon_vec: vector.VectorObject3D = vector.obj(
        x=moon_radius_r * math.cos(moon_dec_rad) * math.cos(moon_ra_rad),
        y=moon_radius_r * math.cos(moon_dec_rad) * math.sin(moon_ra_rad),
        z=moon_radius_r * math.sin(moon_dec_rad),
    )

    shadow_vec = sun_vec - moon_vec
    shadow_dist: float = abs(shadow_vec)  
    shadow_axis_angle: float = math.atan2(shadow_vec.y, shadow_vec.x) 
    shadow_decl: float = math.asin(shadow_vec.z / shadow_dist)
    sun_hour_angle: float = (
        Angle(degrees=t_sf.gmst * 15).radians - shadow_axis_angle
    ) % (2.0 * math.pi)

    moon_x: float = moon_radius_r * (
        math.cos(moon_dec_rad) * math.sin(moon_ra_rad - shadow_axis_angle)
    )
    moon_y: float = moon_radius_r * (
        math.sin(moon_dec_rad) * math.cos(shadow_decl)
        - math.cos(moon_dec_rad)
        * math.sin(shadow_decl)
        * math.cos(moon_ra_rad - shadow_axis_angle)
    )
    moon_z: float = moon_radius_r * (
        math.sin(moon_dec_rad) * math.sin(shadow_decl)
        + math.cos(moon_dec_rad)
        * math.cos(shadow_decl)
        * math.cos(moon_ra_rad - shadow_axis_angle)
    )

    sun_radius: float = km_to_earth_radii(c.SUN_RADIUS_KM)
    kp, ku = c.K_PENUMBRA, c.K_UMBRA

    sin_angle_north: float = (sun_radius + kp) / shadow_dist
    sin_angle_south: float = (sun_radius - ku) / shadow_dist

    z_north: float = moon_z + (kp / sin_angle_north)
    z_south: float = moon_z - (ku / sin_angle_south)

    tangent_north: float = math.tan(math.asin(sin_angle_north))
    tangent_south: float = math.tan(math.asin(sin_angle_south))

    northern_limit: float = z_north * tangent_north
    southern_limit: float = z_south * tangent_south

    return (
        moon_x,
        moon_y,
        Angle(radians=shadow_decl).degrees,
        northern_limit,
        southern_limit,
        Angle(radians=sun_hour_angle).degrees,
        tangent_north,
        tangent_south,
    )  

def micro_find(
    val_0h: float,
    val_p1h: float
) -> Tuple[float, float, float, float]:
    mc0: float = val_0h
    mc1: float = val_p1h
    fit: float = (mc1 - mc0 + 180.0) % 360.0 - 180.0 
    return mc0, fit, 0.0, 0.0

def find_3rd_degree_polynomial(
    val_m2h: float,
    val_m1h: float,
    val_0h: float,
    val_p1h: float,
    val_p2h: float,
) -> tuple[float, float, float, float]:
    t = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=float)
    b = np.array([val_m2h, val_m1h, val_0h, val_p1h, val_p2h], dtype=float)
    A = np.column_stack([np.ones_like(t), t, t * t, t * t * t])

    coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

    return tuple(coeffs)


t_tt: dt.datetime = dt.datetime(2027, 8, 2, 10, 7, 50)
deltatnew: int = deltat.calc_delta_t(t_tt.year, t_tt.month)

tround: dt.datetime = t_tt.copy()

if tround.minute >= 30:
    tround.sub_minutes(t_tt.minute)
    tround.sub_seconds(t_tt.second)
    tround.add_hour()
else:
    tround.sub_minutes(t_tt.minute)
    tround.sub_seconds(t_tt.second)
        
tm2: dt.datetime = tround.copy()
tm2.sub_hours(2)
tm1: dt.datetime = tround.copy()
tm1.sub_hours(1)
t0: dt.datetime = tround.copy()
tp1: dt.datetime = tround.copy()
tp1.add_hours(1)
tp2: dt.datetime = tround.copy()
tp2.add_hours(2)

dm2 = find_coeffs_tt(tm2)
dm1 = find_coeffs_tt(tm1)
d0 = find_coeffs_tt(t0)
dp1 = find_coeffs_tt(tp1)
dp2 = find_coeffs_tt(tp2)

x = find_3rd_degree_polynomial(dm2[0], dm1[0], d0[0], dp1[0], dp2[0])
y = find_3rd_degree_polynomial(dm2[1], dm1[1], d0[1], dp1[1], dp2[1])
d = find_3rd_degree_polynomial(dm2[2], dm1[2], d0[2], dp1[2], dp2[2])
l1 = find_3rd_degree_polynomial(dm2[3], dm1[3], d0[3], dp1[3], dp2[3])
l2 = find_3rd_degree_polynomial(dm2[4], dm1[4], d0[4], dp1[4], dp2[4])
u: float = micro_find(d0[5], dp1[5])
tanf1: float = d0[6]
tanf2: float= d0[7]

print(f"Eclipse on {t_tt.isoformat()} TT")
print(f"{'n':<3} {'x':>12} {'y':>14} {'d':>14} {'l1':>14} {'l2':>14} {'u':>14}")

for n, values in enumerate(
    zip(x, y, d, l1, l2, u)
):
    print(
            f"{n} "
            f"{values[0]:14.10f} {values[1]:14.10f} {values[2]:14.10f} "
            f"{values[3]:14.10f} {values[4]:14.10f} {values[5]:14.10f}"
        )

print(f"tan(f1) = {tanf1:14.10f}  tan(f2) = {tanf2:14.10f}")
print(f"T0 = {t0.isoformat()} TT")
print(f"delta_t = {deltatnew}s")