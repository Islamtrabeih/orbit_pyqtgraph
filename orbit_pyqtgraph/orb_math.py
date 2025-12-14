import math, datetime
import numpy as np

"""
Orbital math utilities.
Input orbital elements (classical):
    elems = [a_km, e, i_deg, raan_deg, argp_deg, M0_deg]
Functions:
    kepler_E(M, e) -> E (rad)
    oe_to_rv(a, e, i, raan, argp, M) -> r_eci (km), v_eci (km/s)  [at given mean anomaly M]
    propagate_orbit(elems, times_s) -> positions_eci (N x 3) in km
    eci_to_ecef(r_eci, t_sec, gst0=0.0) -> r_ecef (km)
    ecef_to_latlon(r_ecef) -> lat (deg), lon (deg), alt_km
"""

# Physical constants
MU_EARTH = 398600.4418  # km^3 / s^2
OMEGA_EARTH = 7.2921150e-5  # rad/s
# OBLIQUITY_DEG = 23.439281  # Earth's axial tilt in degrees
OBLIQUITY_DEG = 0             # Earth's axial tilt in degrees
def deg2rad(d): return np.deg2rad(d)
def rad2deg(r): return np.rad2deg(r)


def kepler_E(M, e, tol=1e-10, maxiter=100):
    """
    Solve Kepler's equation M = E - e sin E for eccentric anomaly E (radians)
    using Newton-Raphson.
    M may be scalar or numpy array.
    """
    M = np.array(M, dtype=float)
    # normalize M to [-pi, pi]
    M = (M + np.pi) % (2*np.pi) - np.pi
    E = M.copy()
    # better initial guess for high e
    mask = np.abs(e) > 0.8
    if np.any(mask):
        E[mask] = np.pi
    for _ in range(maxiter):
        f = E - e*np.sin(E) - M
        fp = 1 - e*np.cos(E)
        dE = -f / fp
        E += dE
        if np.all(np.abs(dE) < tol):
            break
    return E


def oe_to_rv(a, e, i_deg, raan_deg, argp_deg, M_deg):
    """
    Convert classical orbital elements at a given mean anomaly to ECI position vector.
    Returns r_eci (km), v_eci (km/s)
    """
    i = deg2rad(i_deg)
    raan = deg2rad(raan_deg)
    argp = deg2rad(argp_deg)
    M = deg2rad(M_deg)
    n = np.sqrt(MU_EARTH / (a**3))  # mean motion rad/s, but a in km => n in rad/s if MU in km^3/s^2
    E = kepler_E(M, e)
    # True anomaly
    cosf = (np.cos(E) - e) / (1 - e*np.cos(E))
    sinf = (np.sqrt(1 - e**2) * np.sin(E)) / (1 - e*np.cos(E))
    f = np.arctan2(sinf, cosf)
    # distance
    r = a * (1 - e*np.cos(E))
    # Perifocal coordinates
    rx_pf = r * np.cos(f)
    ry_pf = r * np.sin(f)
    rz_pf = 0.0
    # Velocity in perifocal frame
    h = np.sqrt(MU_EARTH * a * (1 - e**2))
    vx_pf = -MU_EARTH / h * np.sin(f)
    vy_pf = MU_EARTH / h * (e + np.cos(f))
    vz_pf = 0.0
    # Rotation matrix from perifocal to ECI
    Rz_raan = np.array([[np.cos(raan), -np.sin(raan), 0], [np.sin(raan),  np.cos(raan), 0], [0, 0, 1]])
    Rx_i = np.array([[1, 0, 0], [0, np.cos(i), -np.sin(i)], [0, np.sin(i),  np.cos(i)]])
    Rz_argp = np.array([[np.cos(argp), -np.sin(argp), 0], [np.sin(argp),  np.cos(argp), 0], [0, 0, 1]])
    Q_pX = Rz_raan @ Rx_i @ Rz_argp
    r_pf = np.array([rx_pf, ry_pf, rz_pf])
    v_pf = np.array([vx_pf, vy_pf, vz_pf])
    r_eci = Q_pX @ r_pf
    v_eci = Q_pX @ v_pf
    return r_eci, v_eci


def propagate_orbit(elems, times_s, M0_epoch_time=0.0):
    """
    Propagate orbit for array of times (seconds since epoch).
    elems = [a_km, e, i_deg, raan_deg, argp_deg, M0_deg]
    M0_epoch_time is time of M0 (s). times_s is array-like of seconds since that epoch.
    Returns array of r_eci positions (N x 3) in km.
    """
    a, e, i_deg, raan_deg, argp_deg, M0_deg = elems
    a = float(a)
    times = np.array(times_s, dtype=float)
    # mean motion (rad/s)
    n = np.sqrt(MU_EARTH / (a**3))
    # Mean anomaly at each time
    M0 = deg2rad(M0_deg)
    M = M0 + n * (times - M0_epoch_time)
    # reduce to [-pi, pi]
    M = (M + np.pi) % (2*np.pi) - np.pi
    # solve E for each M
    E = kepler_E(M, e)
    # compute true anomalies
    cosf = (np.cos(E) - e) / (1 - e*np.cos(E))
    sinf = (np.sqrt(1 - e**2) * np.sin(E)) / (1 - e*np.cos(E))
    f = np.arctan2(sinf, cosf)
    r = a * (1 - e*np.cos(E))
    # generate positions in perifocal then rotate
    rx_pf = r * np.cos(f)
    ry_pf = r * np.sin(f)
    rz_pf = np.zeros_like(rx_pf)
    r_pf = np.vstack([rx_pf, ry_pf, rz_pf])  # 3 x N
    # rotation matrix from perifocal to ECI (same for all times)
    i = deg2rad(i_deg)
    raan = deg2rad(raan_deg)
    argp = deg2rad(argp_deg)
    Rz_raan = np.array([[np.cos(raan), -np.sin(raan), 0], [np.sin(raan),  np.cos(raan), 0], [0, 0, 1]])
    Rx_i = np.array([[1, 0, 0], [0, np.cos(i), -np.sin(i)], [0, np.sin(i),  np.cos(i)]])
    Rz_argp = np.array([[np.cos(argp), -np.sin(argp), 0], [np.sin(argp),  np.cos(argp), 0], [0, 0, 1]])
    Q_pX = Rz_raan @ Rx_i @ Rz_argp
    r_eci_all = (Q_pX @ r_pf).T  # N x 3
    return r_eci_all


def eci_to_ecef(r_eci, t_sec, gst0=0.0):
    """
    Convert ECI positions to ECEF by rotating around z-axis by Earth's rotation angle:
    theta = gst0 + omega_earth * t_sec
    r_eci is (N x 3) or (3,)
    returns r_ecef in same shape (km)
    gst0 default 0.0 (radians) — user can set initial Greenwich sidereal time if desired.
    """
    r = np.array(r_eci, dtype=float)
    scalar = False
    if r.ndim == 1:
        r = r[np.newaxis, :]
        scalar = True
    theta = gst0 + OMEGA_EARTH * np.array(t_sec, dtype=float)
    # if theta is scalar or array broadcastable to (N,)
    theta = np.asarray(theta)
    N = r.shape[0]
    if theta.size == 1:
        theta = np.full(N, theta.item())
    out = np.empty_like(r)
    for idx in range(N):
        ct = np.cos(theta[idx]); st = np.sin(theta[idx])
        Rz = np.array([[ct,  st, 0],
                       [-st, ct, 0],
                       [0,   0,  1]])
        out[idx] = Rz @ r[idx]
    if scalar:
        return out[0]
    return out


def ecef_to_latlon(r_ecef):
    """
    Convert ECEF coordinates (N x 3) in km to lat, lon in degrees and altitude (km).
    Uses simple spherical conversion (WGS84 flattening ignored for simplicity; accurate to few km).
    """
    r = np.array(r_ecef, dtype=float)
    scalar = False
    if r.ndim == 1:
        r = r[np.newaxis, :]
        scalar = True
    x = r[:,0]; y = r[:,1]; z = r[:,2]
    lon = np.arctan2(y, x)
    rxy = np.hypot(x, y)
    lat = np.arctan2(z, rxy)
    alt = np.linalg.norm(r, axis=1) - 6371.0  # km (earth mean radius)
    if scalar:
        return rad2deg(lat[0]), rad2deg(lon[0]), alt[0]
    return rad2deg(lat), rad2deg(lon), alt


def tle_to_kepler6(line1: str, line2: str):
    """
    Convert TLE (2 lines) -> (a_km, e, i_deg, raan_deg, argp_deg, M0_deg, epoch_time_s)
    Returns:
        a_km (float)
        e (float)
        i_deg (float)
        raan_deg (float)
        argp_deg (float)
        M0_deg (float)
        epoch_time_s (float, UNIX seconds)
    """
    # ----- Parse epoch from line1 -----
    # Columns: epoch YYDDD.DDDDDDDD at positions 19-32 (0-based slice [18:32])
    epoch_str = line1[18:32].strip()
    yy = int(epoch_str[:2])
    day_of_year = float(epoch_str[2:])
    year = 2000 + yy if yy < 57 else 1900 + yy  # NORAD convention threshold ~ 57
    jan1 = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc)
    epoch_dt = jan1 + datetime.timedelta(days=day_of_year - 1.0)
    epoch_time_s = epoch_dt.timestamp()
    # ----- Parse elements from line2 -----
    # Inclination (deg) cols 9-16 -> [8:16]
    i_deg = float(line2[8:16])
    # RAAN (deg) cols 18-25 -> [17:25]
    raan_deg = float(line2[17:25])
    # Eccentricity (unitless, implied decimal) cols 27-33 -> [26:33]
    e = float("0." + line2[26:33].strip())
    # Argument of perigee (deg) cols 35-42 -> [34:42]
    argp_deg = float(line2[34:42])
    # Mean anomaly (deg) cols 44-51 -> [43:51]
    M0_deg = float(line2[43:51])
    # Mean motion (rev/day) cols 53-63 -> [52:63]
    n_rev_per_day = float(line2[52:63])
    # Semi-major axis from mean motion: a = (μ)^(1/3) / ( (2π n/86400)^(2/3) )
    n_rad_s = 2.0 * math.pi * n_rev_per_day / 86400.0
    a_km = (MU_EARTH ** (1.0/3.0)) / (n_rad_s ** (2.0/3.0))
    return a_km, e, i_deg, raan_deg, argp_deg, M0_deg, epoch_time_s
