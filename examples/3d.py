#!/usr/bin/env python3
"""
Example: 3D Static Orbit Visualization
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from islam_reda_orbit import OrbitPlot

class Example3DStatic(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Static Orbit - Islam Reda Orbit Library")
        self.setGeometry(100, 100, 1000, 800)
        
        # Example Keplerian elements (LEO orbit)
        kepler_elems = [
            6787.0,      # a_km (LEO semi-major axis)
            0.001,       # e (slightly elliptical)
            45.0,        # i_deg (inclination)
            30.0,        # Ω_deg (RAAN)
            60.0,        # ω_deg (argument of perigee)
            120.0,       # M0_deg (mean anomaly)
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
        
        # Start 3D static visualization (multiple revolutions)
        self.orbit_plot._3d(animation=False, accumulation=True, 
                           title="LEO Orbit 3D (Static - 6 Revolutions)",
                           bgcolor="#000020", lncolor="#00ccff", revolves=6)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Example3DStatic()
    window.show()
    sys.exit(app.exec_())