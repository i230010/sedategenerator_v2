import math
import numpy as np
import vector
from skyfield.api import load, GREGORIAN_START
from skyfield.units import Angle
import argparse
from typing import Tuple, List
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

def narrow(
    start: dt.datetime,
    end: dt.datetime,
    tt_mode: bool
) -> None:
    
    if start > end:
        raise ValueError("start must be earlier than or equal to end")
    
    eph = load(p.EPHEM_PATH)
    ts = load.timescale()
    ts.julian_calendar_cutoff = GREGORIAN_START

    earth, sun, moon = eph["earth"], eph["sun"], eph["moon"]

    current_time: dt.datetime = start.copy()
    
    separations: List[float] = []
    timestamps: List[dt.datetime] = []
    
    while current_time <= end:
        delta_t_new: int = deltat.calc_delta_t(current_time.year, current_time.month)

        sf_time = ts.ut1(
            current_time.year,
            current_time.month,
            current_time.day,
            current_time.hour,
            current_time.minute,
            current_time.second
        )
            
        if(tt_mode == True):
            sf_time = ts.tt(
                current_time.year,
                current_time.month,
                current_time.day,
                current_time.hour,
                current_time.minute,
                current_time.second
            )

        sf_time.delta_t = delta_t_new

        sun_pos = earth.at(sf_time).observe(sun)
        moon_pos = earth.at(sf_time).observe(moon)

        sep_angle: float = moon_pos.separation_from(sun_pos).radians

        sun_dist_km: float = sun_pos.distance().km
        moon_dist_km: float = moon_pos.distance().km

        threshold: float = math.asin(
            (c.MOON_RADIUS_KM + c.EARTH_RADIUS_KM) / moon_dist_km
        ) + math.asin(
            (c.SUN_RADIUS_KM - c.EARTH_RADIUS_KM) / sun_dist_km
        )

        if sep_angle <= threshold:
            separations.append(sep_angle)
            timestamps.append(current_time.copy())
            current_time.add_second()
        else:
            current_time.add_second()
        
    if not separations:
        print("None")
            
    min_sep: float = min(separations)
    min_index: int = separations.index(min_sep)
    min_time: dt.datetime = timestamps[min_index]

    delta_t_new: int = deltat.calc_delta_t(current_time.year, current_time.month)

    ut1: dt.datetime = min_time.copy()
    tt: dt.datetime = min_time.copy()
    tt = tt + dt.timedelta(0, 0, 0, delta_t_new)

    if(tt_mode == True):
        tt: dt.datetime = min_time.copy()
        ut1: dt.datetime = min_time.copy()
        ut1 = ut1 - dt.timedelta(0, 0, 0, delta_t_new)
    
    tround: dt.datetime = tt.copy()

    if tround.minute >= 30:
        tround.sub_minutes(tt.minute)
        tround.sub_seconds(tt.second)
        tround.add_hour()
    else:
        tround.sub_minutes(tt.minute)
        tround.sub_seconds(tt.second)

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

    print( f"{ut1.isoformat()} UT1,{tt.isoformat()} TT,{delta_t_new}s,{tround.isoformat()} TT,{x[0]:.10f},{x[1]:.10f},{x[2]:.10f},{x[3]:.10f},{y[0]:.10f},{y[1]:.10f},{y[2]:.10f},{y[3]:.10f},{d[0]:.10f},{d[1]:.10f},{d[2]:.10f},{d[3]:.10f},{l1[0]:.10f},{l1[1]:.10f},{l1[2]:.10f},{l1[3]:.10f},{l2[0]:.10f},{l2[1]:.10f},{l2[2]:.10f},{l2[3]:.10f},{u[0]:.10f},{u[1]:.10f},{u[2]:.10f},{u[3]:.10f},{tanf1:.10f},{tanf2:.10f}" )

def find(
    start: dt.datetime,
    end: dt.datetime,
    step: dt.timedelta,
    tt_mode: bool
) -> None:
    
    if start > end:
        raise ValueError("start must be earlier than or equal to end")
    
    eph = load(p.EPHEM_PATH)
    ts = load.timescale()
    ts.julian_calendar_cutoff = GREGORIAN_START

    earth, sun, moon = eph["earth"], eph["sun"], eph["moon"]

    current_time: dt.datetime = start.copy()

    while current_time <= end:
        delta_t_new: int = deltat.calc_delta_t(current_time.year, current_time.month)
        
        sf_time = ts.ut1(
            current_time.year,
            current_time.month,
            current_time.day,
            current_time.hour,
            current_time.minute,
            current_time.second
        )
            
        if(tt_mode == True):
            sf_time = ts.tt(
                current_time.year,
                current_time.month,
                current_time.day,
                current_time.hour,
                current_time.minute,
                current_time.second
            )
            
        sf_time.delta_t = delta_t_new

        sun_pos = earth.at(sf_time).observe(sun)
        moon_pos = earth.at(sf_time).observe(moon)

        sep_angle: float = moon_pos.separation_from(sun_pos).radians

        sun_dist_km: float = sun_pos.distance().km
        moon_dist_km: float = moon_pos.distance().km

        threshold: float = math.asin(
            (c.MOON_RADIUS_KM + c.EARTH_RADIUS_KM) / moon_dist_km
        ) + math.asin(
            (c.SUN_RADIUS_KM - c.EARTH_RADIUS_KM) / sun_dist_km
        )

        if sep_angle <= threshold:
            t1: dt.datetime = current_time.copy()
            t2: dt.datetime = t1.copy()
            t2.add_hours(4)
            narrow(t1, t2, tt_mode)
            current_time.add_days(27)
        else:
            current_time: dt.datetime = current_time + step    

def main():
    parser = argparse.ArgumentParser(
        description="Process start and end year values"
    )

    parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="Start year (int)",
    )

    parser.add_argument(
        "--end", 
        type=int, 
        required=True, 
        help="End year (int)"
    )

    parser.add_argument(
        "--step", 
        type=int, 
        required=True, 
        help="Step (in seconds)(int)"
    )
    
    parser.add_argument(
        "--ttm", 
        type=int, 
        required=True, 
        help="Step (in seconds)(int)"
    )

    args = parser.parse_args()
    
    tt_mode = False
    
    if(args.ttm == 1):
        tt_mode = True

    t1: dt.datetime = dt.datetime(int(args.start), 1, 1, 0, 0, 0)
    t2: dt.datetime = dt.datetime(int(args.end), 3, 1, 0, 0, 0)
    step = dt.timedelta(0, 0, 0, int(args.step))
    find(t1, t2, step, tt_mode)

if(__name__ == "__main__"):
    main()