# 🚀 Orbit PyQtGraph: Satellite Visualization Library

## 🌟 Overview

**Orbit PyQtGraph** is a Python library that transforms satellite orbit data into breathtaking interactive visualizations. Whether you're tracking the ISS, planning satellite missions, or teaching orbital mechanics, this library brings space to your screen with cinematic quality.

<div align="center">
  <img src="" width="800" height="400" alt="3D Orbit Demo">
  <p><em>Real-time 3D visualization of satellite orbits around Earth</em></p>
</div>

## ✨ Features

### 🎨 **Visual Excellence**
- **Cinematic 3D Rendering** - Photorealistic Earth with cloud textures
- **Interactive Controls** - Rotate, zoom, and pan with mouse gestures
- **Real-time Animation** - Watch satellites move in real-time
- **Multiple View Modes** - 3D, 2D ground track, and hybrid views

### 🛰️ **Orbital Accuracy**
- **TLE Integration** - Direct support for Two-Line Element sets
- **Precise Propagation** - SGP4/SDP4 algorithms for accurate predictions
- **Multiple Orbit Types** - LEO, MEO, GEO, Molniya, and more
- **Earth Rotation** - Proper accounting for Earth's rotation and axial tilt

Works on Windows, macOS, and Linux

## 📦 Installation

```bash
# Install from PyPI (Recommended)
pip install orbit-pyqtgraph

# Install from GitHub (Latest features)
pip install git+https://github.com/Islamtrabeih/orbit_pyqtgraph.git

# For development
git clone https://github.com/Islamtrabeih/orbit_pyqtgraph.git
cd orbit_pyqtgraph
pip install -e .
```

### Requirements
- Python 3.7+
- PyQt5 5.15+
- PyOpenGL 3.1+
- NumPy 1.21+
- Pillow 9.0+

## 🚀 Quick Start

### Basic 3D Visualization

```python
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from orbit_pyqtgraph import OrbitPlot, tle_to_kepler6

# ISS TLE (Two-Line Element)
L1 = "1 25544U 98067A   25229.18034946  .00009619  00000-0  17645-3 0  9996"
L2 = "2 25544  51.6356   4.7550 0003499 229.5075 130.5609 15.49975761524621"

# Convert TLE to orbital elements
kepler_elems = tle_to_kepler6(L1, L2)

class SpaceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Real-time ISS Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create orbit visualization
        self.orbit_plot = OrbitPlot(kepler_elems[:-1])
        self.setCentralWidget(self.orbit_plot)
        
        # Launch in 3D mode
        self.orbit_plot._3d(
            animation=True,
            title="International Space Station",
            bgcolor="#0a0a23",  # Space black with blue tint
            lncolor="#00ff88",  # Neon green orbit
            revolves=3
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern UI style
    window = SpaceApp()
    window.show()
    sys.exit(app.exec_())
```

### Advanced Example: Multi-Satellite Display

```python
from orbit_pyqtgraph import OrbitPlot
import numpy as np

# Create a constellation of satellites
satellites = {
    "ISS": [6778, 0.0004, 51.64, 11.02, 221.99, 280.81],
    "Hubble": [6928, 0.0003, 28.47, 76.88, 354.91, 12.45],
    "GPS": [26560, 0.001, 55.0, 0.0, 0.0, 45.0],
    "Starlink": [6920, 0.001, 53.0, 30.0, 90.0, 180.0]
}

# Create multi-view dashboard
plot = OrbitPlot(satellites["ISS"])
plot.create_dashboard(
    satellites=satellites,
    mode="multi_view",
    theme="dark_space",
    show_controls=True,
    show_info_panel=True
)
```

**Methods:**
```python
# 3D Visualization
plot._3d(
    animation=True,           # Animate satellite motion
    accumulation=True,        # Show full orbit path
    title="Orbit View",       # Window title
    bgcolor="#000010",        # Background color
    lncolor="#ff9900",        # Orbit line color
    revolves=2                # Number of revolutions
)

# 2D Ground Track
plot._2d(
    animation=True,
    accumulation=True,
    title="Ground Track",
    lncolor="#00ff00",
    revolves=6
)

# Live Orbit Tracking
plot.liveorbit(
    lncolor="#ff0000",
    epoch_time=None,          # Custom epoch time
    realtime=True            # Real-time propagation
)
```

#### Orbital Mathematics Module
```python
from orbit_pyqtgraph import (
    tle_to_kepler6,      # Convert TLE to orbital elements
    propagate_orbit,     # Propagate orbit over time
    eci_to_ecef,         # Convert coordinate systems
    ecef_to_latlon,      # Get latitude/longitude
    calculate_visibility # Compute ground station visibility
)
```

### Advanced Features

#### Custom Earth Textures
```python
# Use custom Earth texture
plot = OrbitPlot(
    kepler_elems,
    earth_texture="path/to/custom_earth.jpg"
)

# Use high-resolution NASA Blue Marble
plot = OrbitPlot(
    kepler_elems,
    earth_texture="nasa_blue_marble.jpg"
)
```

## 🔧 Configuration

### Themes
```python
# Available themes
themes = {
    "dark_space": {
        "bgcolor": "#0a0a23",
        "earth_color": "#1e3a8a",
        "orbit_color": "#00ff88"
    },
    "scientific": {
        "bgcolor": "#000000",
        "earth_color": "#2563eb",
        "orbit_color": "#f59e0b"
    },
    "night_vision": {
        "bgcolor": "#000000",
        "earth_color": "#00ff00",
        "orbit_color": "#ff0000"
    }
}

plot.set_theme("dark_space")
```

### Project Structure
```
orbit_pyqtgraph/
├── orbit_pyqtgraph/          # Main package
│   ├── __init__.py
│   ├── orbit.py             # Main visualization class
│   ├── orb_math.py          # Orbital calculations
│   ├── utils.py             # Utilities
│   └── assets/              # Textures and resources
└── examples/                # Example scripts
```

## 📈 Roadmap

- [x] **v1.0** - Basic 2D/3D visualization
- [x] **v1.1** - TLE support and real-time updates
- [ ] **v1.2** - Multiple satellite display
- [ ] **v1.3** - Ground station visibility
- [ ] **v1.4** - Mission planning tools
