#!/usr/bin/env python3
"""
Example: 2D Static Orbit Visualization
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from islam_reda_orbit import OrbitPlot

class Example2DStatic(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Static Orbit - Islam Reda Orbit Library")
        self.setGeometry(100, 100, 1000, 800)
        
        # Example Keplerian elements (GEO orbit)
        kepler_elems = [
            42164.0,     # a_km (GEO semi-major axis)
            0.0001,      # e (near-circular)
            0.0,         # i_deg (equatorial)
            0.0,         # Ω_deg (RAAN)
            0.0,         # ω_deg (argument of perigee)
            45.0,        # M0_deg (mean anomaly)
            0.0          # epoch_time_s
        ]
        
        # Get earth texture path
        earth_texture = os.path.join(os.path.dirname(__file__), '..', 'islam_reda_orbit', 'assets', 'earth.jpg')
        
        # Create orbit plot widget
        self.orbit_plot = OrbitPlot(kepler_elems, earth_texture=earth_texture)
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.orbit_plot)
        self.setCentralWidget(central_widget)
        
        # Start 2D static visualization
        self.orbit_plot._2d(animation=False, accumulation=True, 
                           title="GEO Satellite Ground Track (Static)", 
                           lncolor="#ff00ff", revolves=6)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Example2DStatic()
    window.show()
    sys.exit(app.exec_())