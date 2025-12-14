# earth_orbit_viewer.py
import sys
import numpy as np
from PyQt5 import QtWidgets, QtOpenGL, QtCore
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image


class EarthOrbitViewer(QtOpenGL.QGLWidget):
    def __init__(self,
                 orbit_true_anomaly=None,
                 orbit_radius=None,
                 earth_diameter=1.0,
                 space_color=(0.0, 0.0, 0.0),
                 texture_path="earth.jpg",
                 orbit_color=(1.0, 1.0, 0.0),
                 satellite_period=90.0,   # seconds
                 parent=None):
        super(EarthOrbitViewer, self).__init__(parent)

        # Parameters (public)
        self.earth_radius = float(earth_diameter) / 2.0
        self.space_color = tuple(space_color)
        self.texture_path = texture_path
        self.orbit_color = tuple(orbit_color)
        self.satellite_period = float(satellite_period)

        # Orbit arrays (must be same length)
        if orbit_true_anomaly is not None:
            self.orbit_true_anomaly = np.asarray(orbit_true_anomaly, dtype=float)
        else:
            self.orbit_true_anomaly = None

        if orbit_radius is not None:
            self.orbit_radius = np.asarray(orbit_radius, dtype=float)
        else:
            self.orbit_radius = None

        # GL resources
        self.earthTexture = None

        # View controls
        self.xRot = 20.0
        self.yRot = -30.0
        self.lastPos = None

        # Timing for animation
        self.start_time = QtCore.QTime.currentTime()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)  # call paintGL via update()
        self.timer.start(16)  # ~60 FPS

    # ---------------------------
    # OpenGL setup
    # ---------------------------
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glClearColor(self.space_color[0], self.space_color[1], self.space_color[2], 1.0)

        # load texture
        try:
            img = Image.open(self.texture_path).transpose(Image.FLIP_TOP_BOTTOM).convert("RGB")
            img_data = np.array(img, dtype=np.uint8)
            self.earthTexture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.earthTexture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        except Exception as e:
            print("Failed to load texture:", e)
            self.earthTexture = None

        # lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 10.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.25, 0.25, 0.25, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

    def resizeGL(self, w, h):
        h = max(1, h)
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / float(h), 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    # ---------------------------
    # Main render
    # ---------------------------
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # camera distance scales with Earth radius so Earth is visible
        cam_dist = max(5.0, 6.0 * self.earth_radius)
        glTranslatef(0.0, 0.0, -cam_dist)

        # rotate scene by user mouse
        glRotatef(self.xRot, 1.0, 0.0, 0.0)
        glRotatef(self.yRot, 0.0, 1.0, 0.0)

        # draw Earth
        if self.earthTexture:
            glBindTexture(GL_TEXTURE_2D, self.earthTexture)

        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE if self.earthTexture else GL_FALSE)
        gluSphere(quad, self.earth_radius, 64, 64)
        gluDeleteQuadric(quad)

        # draw orbit
        if self.orbit_true_anomaly is not None and self.orbit_radius is not None and len(self.orbit_true_anomaly) >= 2:
            self.draw_orbit()

        # draw animated satellite marker (modern)
        if self.orbit_true_anomaly is not None and self.orbit_radius is not None and len(self.orbit_true_anomaly) >= 2:
            self.draw_satellite_marker()

    # ---------------------------
    # Orbit drawing (line)
    # ---------------------------
    def draw_orbit(self):
        glDisable(GL_LIGHTING)
        glColor3f(*self.orbit_color)
        glLineWidth(2.0)
        glBegin(GL_LINE_STRIP)
        for ta, r in zip(self.orbit_true_anomaly, self.orbit_radius):
            x = r * np.cos(np.radians(ta))
            y = r * np.sin(np.radians(ta))
            z = 0.0
            glVertex3f(x, y, z)
        glEnd()
        glEnable(GL_LIGHTING)

    # ---------------------------
    # Satellite animation interpolation
    # ---------------------------
    def get_satellite_position(self):
        """Return (x,y,z) interpolated along the provided orbit arrays based on current time and satellite_period."""
        N = len(self.orbit_true_anomaly)
        if N < 2:
            return (0.0, 0.0, 0.0)

        elapsed_s = self.start_time.msecsTo(QtCore.QTime.currentTime()) / 1000.0
        if self.satellite_period <= 0:
            fraction = 0.0
        else:
            fraction = (elapsed_s % self.satellite_period) / self.satellite_period

        # continuous index across the orbit points
        idx_float = fraction * (N - 1)
        idx0 = int(np.floor(idx_float)) % N
        idx1 = (idx0 + 1) % N
        t = idx_float - np.floor(idx_float)

        ta0 = float(self.orbit_true_anomaly[idx0])
        ta1 = float(self.orbit_true_anomaly[idx1])
        # handle wrap-around of angle (e.g., 350 -> 10 deg)
        dta = ((ta1 - ta0 + 180.0) % 360.0) - 180.0
        ta = ta0 + dta * t

        r0 = float(self.orbit_radius[idx0])
        r1 = float(self.orbit_radius[idx1])
        r = r0 + (r1 - r0) * t

        x = r * np.cos(np.radians(ta))
        y = r * np.sin(np.radians(ta))
        z = 0.0
        return (x, y, z)

    # ---------------------------
    # Satellite marker (modern: cube + solar panels)
    # ---------------------------
    def draw_satellite_marker(self):
        x, y, z = self.get_satellite_position()

        glPushMatrix()
        glTranslatef(x, y, z)

        # optionally orient marker to velocity or radial direction in future; for now it's axis-aligned

        # disable textures + lighting for flat colors, then re-enable after
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)

        # satellite body (cube)
        size = max(0.01 * self.earth_radius, self.earth_radius * 0.03)  # scale with Earth
        self._draw_colored_cube(size, (0.85, 0.85, 0.85))

        # solar panels (two thin rectangles)
        panel_w = size * 2.6
        panel_h = size * 0.45
        panel_thickness = 0.002 * self.earth_radius
        self._draw_solar_panel(-size - panel_w/2.0, 0.0, 0.0, panel_w, panel_h, panel_thickness, (0.12, 0.18, 0.55))
        self._draw_solar_panel(size + panel_w/2.0, 0.0, 0.0, panel_w, panel_h, panel_thickness, (0.12, 0.18, 0.55))

        # small antenna or bus detail
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_LINES)
        glVertex3f(0.0, size, 0.0)
        glVertex3f(0.0, size + size*0.6, 0.0)
        glEnd()

        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glPopMatrix()

    def _draw_colored_cube(self, size, color):
        """Draw a cube centered at origin with face color"""
        hs = size * 0.5
        glColor3f(*color)
        glBegin(GL_QUADS)
        # +Z face
        glVertex3f(-hs, -hs, hs)
        glVertex3f(hs, -hs, hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(-hs, hs, hs)
        # -Z face
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(-hs, hs, -hs)
        glVertex3f(hs, hs, -hs)
        glVertex3f(hs, -hs, -hs)
        # +Y face
        glVertex3f(-hs, hs, -hs)
        glVertex3f(-hs, hs, hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(hs, hs, -hs)
        # -Y face
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(hs, -hs, -hs)
        glVertex3f(hs, -hs, hs)
        glVertex3f(-hs, -hs, hs)
        # +X face
        glVertex3f(hs, -hs, -hs)
        glVertex3f(hs, hs, -hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(hs, -hs, hs)
        # -X face
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(-hs, -hs, hs)
        glVertex3f(-hs, hs, hs)
        glVertex3f(-hs, hs, -hs)
        glEnd()

    def _draw_solar_panel(self, cx, cy, cz, width, height, thickness, color):
        """Draws a thin rectangular panel centered at (cx,cy,cz) oriented in Y-Z plane (flat along X)."""
        hw = width * 0.5
        hh = height * 0.5
        ht = thickness * 0.5
        glColor3f(*color)
        # front face
        glBegin(GL_QUADS)
        glVertex3f(cx - hw, cy - hh, cz + ht)
        glVertex3f(cx + hw, cy - hh, cz + ht)
        glVertex3f(cx + hw, cy + hh, cz + ht)
        glVertex3f(cx - hw, cy + hh, cz + ht)
        # back face
        glVertex3f(cx - hw, cy - hh, cz - ht)
        glVertex3f(cx - hw, cy + hh, cz - ht)
        glVertex3f(cx + hw, cy + hh, cz - ht)
        glVertex3f(cx + hw, cy - hh, cz - ht)
        # sides
        glVertex3f(cx - hw, cy - hh, cz - ht)
        glVertex3f(cx - hw, cy - hh, cz + ht)
        glVertex3f(cx - hw, cy + hh, cz + ht)
        glVertex3f(cx - hw, cy + hh, cz - ht)

        glVertex3f(cx + hw, cy - hh, cz - ht)
        glVertex3f(cx + hw, cy + hh, cz - ht)
        glVertex3f(cx + hw, cy + hh, cz + ht)
        glVertex3f(cx + hw, cy - hh, cz + ht)

        glVertex3f(cx - hw, cy + hh, cz - ht)
        glVertex3f(cx - hw, cy + hh, cz + ht)
        glVertex3f(cx + hw, cy + hh, cz + ht)
        glVertex3f(cx + hw, cy + hh, cz - ht)

        glVertex3f(cx - hw, cy - hh, cz - ht)
        glVertex3f(cx + hw, cy - hh, cz - ht)
        glVertex3f(cx + hw, cy - hh, cz + ht)
        glVertex3f(cx - hw, cy - hh, cz + ht)
        glEnd()

    # ---------------------------
    # Mouse interaction
    # ---------------------------
    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        if self.lastPos is None:
            self.lastPos = event.pos()
            return
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        if event.buttons() & QtCore.Qt.LeftButton:
            self.xRot += dy * 0.5
            self.yRot += dx * 0.5
            self.update()
        self.lastPos = event.pos()


class EarthOrbitWindow(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        super().__init__()
        self.setWindowTitle("Textured Earth with Animated Satellite")
        self.glWidget = EarthOrbitViewer(**kwargs)
        self.setCentralWidget(self.glWidget)
        self.resize(1000, 700)


# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # example: circular orbit with radius 2.7 * Earth radius
    true_anomaly = np.linspace(0, 360, 400)  # degrees
    radius = np.ones_like(true_anomaly) * (2.7 * 1.0)  # units are arbitrary: relative to earth_diameter used below

    window = EarthOrbitWindow(
        orbit_true_anomaly=true_anomaly,
        orbit_radius=radius,
        earth_diameter=2.0,                     # full diameter (you control)
        space_color=(0.02, 0.02, 0.06),         # dark space
        texture_path="earth.jpg",               # path to texture
        orbit_color=(0.2, 1.0, 0.2),            # orbit color
        satellite_period=30.0                   # seconds per orbit
    )
    window.show()
    sys.exit(app.exec_())
