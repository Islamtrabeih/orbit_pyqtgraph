import sys, os
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from orbit import OrbitPlot
from orb_math import *

# Example classical elements (rough LEO):
# a_km, e, i_deg, raan_deg, argp_deg, M0_deg
# This example is ~6500 km semi-major axis (~129 km altitude unrealistic but for demo).
L1 = "1 25544U 98067A   25229.18034946  .00009619  00000-0  17645-3 0  9996"
L2 = "2 25544  51.6356   4.7550 0003499 229.5075 130.5609 15.49975761524621"
x= tle_to_kepler6(L1, L2)
example_elems = x[:-1]
'''[
    6787.00,     # a_km  (semi-major axis, approx.)
    0.0003440,   # e     (eccentricity)
    51.6370,     # i_deg (inclination)
    11.0151,     # Ω_deg (RAAN)
    221.9962,    # ω_deg (argument of perigee)
    280.8086     # M0_deg (mean anomaly at epoch)
]'''
def main():
    app = QApplication(sys.argv)
    w = QWidget()
    w.setWindowTitle("OrbitPlot Demo")
    layout = QHBoxLayout(w)

    # Create an OrbitPlot instance
    op = OrbitPlot(example_elems, earth_texture='earth.jpg')

    # Left: 3D widget
    left_col = QVBoxLayout()
    btn3d_anim = QPushButton("Show 3D Animated")
    btn3d_static = QPushButton("Show 3D Static (2 revs)")
    left_col.addWidget(btn3d_anim)
    left_col.addWidget(btn3d_static)
    left_col.addStretch()
    layout.addLayout(left_col)

    # Right: the orbit widget (embedded)
    layout.addWidget(op, 1)

    def on_3d_anim():
        op._3d(animation=True, accumulation=True, title="3D Animated Orbit",
               bgcolor="#FFFFFF", lncolor="#00ff00", revolves=2)

    def on_3d_static():
        op._3d(animation=False, accumulation=True, title="3D Static 2 revs",
               bgcolor="#000010", lncolor="#ff9900", revolves=6)

    def on_2d_anim():
        # op._2d(animation=False, accumulation=True, title="2D Ground Track", lncolor="#ff00ff", revolves=6)
        op.liveorbit(epoch_time=x[-1])

    btn3d_anim.clicked.connect(on_3d_anim)
    btn3d_static.clicked.connect(on_3d_static)

    # extra button to show 2D
    btn2d = QPushButton("Show 2D Animated")
    left_col.addWidget(btn2d)
    btn2d.clicked.connect(on_2d_anim)

    w.resize(1200, 700)
    w.show()
    # start with 3D animation
    on_3d_anim()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
