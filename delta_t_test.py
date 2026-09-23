from skyfield.api import load, GREGORIAN_START
import ephempath as p
import deltatnew as deltat

eph = load(p.EPHEM_PATH)
ts = load.timescale()
ts.julian_calendar_cutoff = GREGORIAN_START
t = ts.ut1(2027, 1, 1, 0, 0, 0)
delta_t_skyfield: float = t.delta_t
delta_t_new: float = deltat.calc_delta_t_float(2027, 1)
print(f"skyfield = {delta_t_skyfield}s, new = {delta_t_new}s")

t = ts.ut1(1600, 1, 1, 0, 0, 0)
delta_t_skyfield: float = t.delta_t
delta_t_new: float = deltat.calc_delta_t_float(1600, 1)
print(f"skyfield = {delta_t_skyfield}s, new = {delta_t_new}s")

t = ts.ut1(2600, 1, 1, 0, 0, 0)
delta_t_skyfield: float = t.delta_t
delta_t_new: float = deltat.calc_delta_t_float(2600, 1)
print(f"skyfield = {delta_t_skyfield}s, new = {delta_t_new}s")

