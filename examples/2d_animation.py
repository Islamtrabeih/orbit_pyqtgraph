#!/usr/bin/env python3
"""
Example: 2D Animated Orbit Visualization
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from islam_reda_orbit import OrbitPlot, tle_to_kepler6

class Example2DAnimated(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Animated Orbit - Islam Reda Orbit Library")
        self.setGeometry(100, 100, 1000, 800)
        
        # TLE for ISS
        L1 = "1 25544U 98067A   25229.18034946  .00009619  00000-0  17645-3 0  9996"
        L2 = "2 25544  51.6356   4.7550 0003499 229.5075 130.5609 15.49975761524621"
        
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
        
        # Start 2D animated visualization
        self.orbit_plot._2d(animation=True, accumulation=True, 
                           title="ISS Ground Track (Animated)", 
                           lncolor="#00ff00", revolves=3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Example2DAnimated()
    window.show()
    sys.exit(app.exec_())