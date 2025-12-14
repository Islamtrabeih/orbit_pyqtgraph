#!/usr/bin/env python3
"""
Example: 3D Animated Orbit Visualization
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from islam_reda_orbit import OrbitPlot, tle_to_kepler6

class Example3DAnimated(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Animated Orbit - Islam Reda Orbit Library")
        self.setGeometry(100, 100, 1000, 800)
        
        # TLE for Molniya orbit
        L1 = "1 24652U 96063A   25230.12195618  .00000257  00000-0  39011-4 0  9990"
        L2 = "2 24652  63.7979 189.2201 7280347 270.0591  16.1348  2.00609021  1809"
        
        # Convert TLE to Keplerian elements
        a_km, e, i_deg, raan_deg, argp_deg, M0_deg, epoch_time_s = tle_to_kepler6(L1, L2)
        kepler_elems = [a_km, e, i_deg, raan_deg, argp_deg, M0_deg, epoch_time_s]
        
        # Get earth texture path
        earth_texture = os.path.join(os.path.dirname(__file__), '..', 'islam_reda_orbit', 'assets', 'earth.jpg')
        
        # Create orbit plot widget
        self.orbit_plot = OrbitPlot(kepler_elems, earth_texture=earth_texture)
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.orbit_plot)
        self.setCentralWidget(central_widget)
        
        # Start 3D animated visualization
        self.orbit_plot._3d(animation=True, accumulation=True, 
                           title="Molniya Orbit 3D (Animated)",
                           bgcolor="#000010", lncolor="#ff9900", revolves=2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Example3DAnimated()
    window.show()
    sys.exit(app.exec_())