import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from orbit_pyqtgraph import OrbitPlot, tle_to_kepler6

# TLE for ISS
L1 = "1 25544U 98067A   25229.18034946  .00009619  00000-0  17645-3 0  9996"
L2 = "2 25544  51.6356   4.7550 0003499 229.5075 130.5609 15.49975761524621"

# Convert TLE to Keplerian elements
kepler_elems = tle_to_kepler6(L1, L2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.orbit_plot = OrbitPlot(kepler_elems[:-1])
        self.setCentralWidget(self.orbit_plot)

        # Show 3D animated orbit
        self.orbit_plot._3d(animation=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
