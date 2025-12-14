"""
Visualization Library
A comprehensive orbit visualization toolkit using PyQt, OpenGL, and PIL.
"""

from .orbit import OrbitPlot, EarthGLWidget
from .orb_math import *

__version__ = "1.0.0"
__author__ = "Islam Trabeih"
__email__ = "islamtrabeih@azhar.edu.eg"

__all__ = [
    "OrbitPlot",
    "EarthGLWidget",
    "tle_to_kepler6",
    "propagate_orbit",
    "kepler_E",
    "oe_to_rv",
    "eci_to_ecef",
    "ecef_to_latlon"
]
