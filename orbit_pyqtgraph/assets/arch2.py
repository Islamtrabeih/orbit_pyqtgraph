import sys
import numpy as np
from PyQt5 import QtWidgets, QtOpenGL, QtCore
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image


class EarthOrbitViewer(QtOpenGL.QGLWidget):
    def __init__(self, earth_diameter=1.0, space_color=(0.0, 0.0, 0.0), texture_path="earth.jpg",
                 orbit_true_anomaly=None, orbit_radius=None, orbit_color=(1.0, 1.0, 0.0),
                 parent=None):
        super(EarthOrbitViewer, self).__init__(parent)

        # Parameters
        self.earth_radius = earth_diameter / 2.0
        self.space_color = space_color
        self.texture_path = texture_path
        self.orbit_true_anomaly = np.array(orbit_true_anomaly) if orbit_true_anomaly is not None else None
        self.orbit_radius = np.array(orbit_radius) if orbit_radius is not None else None
        self.orbit_color = orbit_color

        # View rotation
        self.xRot = 0
        self.yRot = 0
        self.lastPos = None

        # GL resources
        self.earthTexture = None

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glClearColor(*self.space_color, 1.0)  # background color

        # Load Earth texture
        img = Image.open(self.texture_path).transpose(Image.FLIP_TOP_BOTTOM).convert("RGB")
        img_data = np.array(img, dtype=np.uint8)

        self.earthTexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.earthTexture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 10, 1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / float(h or 1), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.xRot, 1.0, 0.0, 0.0)
        glRotatef(self.yRot, 0.0, 1.0, 0.0)

        # Draw Earth
        glBindTexture(GL_TEXTURE_2D, self.earthTexture)
        quadric = gluNewQuadric()
        gluQuadricTexture(quadric, GL_TRUE)
        gluSphere(quadric, self.earth_radius, 50, 50)
        gluDeleteQuadric(quadric)

        # Draw orbit and satellite
        if self.orbit_true_anomaly is not None and self.orbit_radius is not None:
            self.draw_orbit()
            self.draw_satellite_marker()

    def draw_orbit(self):
        glDisable(GL_LIGHTING)  # orbit not affected by lighting
        glColor3f(*self.orbit_color)
        glBegin(GL_LINE_LOOP)
        for ta, r in zip(self.orbit_true_anomaly, self.orbit_radius):
            x = r * np.cos(np.radians(ta))
            y = r * np.sin(np.radians(ta))
            z = 0
            glVertex3f(x, y, z)
        glEnd()
        glEnable(GL_LIGHTING)

    def draw_satellite_marker(self):
        # Last orbit point
        ta_last = self.orbit_true_anomaly[-1]
        r_last = self.orbit_radius[-1]
        x = r_last * np.cos(np.radians(ta_last))
        y = r_last * np.sin(np.radians(ta_last))
        z = 0

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.0, 0.0)  # red marker
        quadric = gluNewQuadric()
        gluSphere(quadric, self.earth_radius * 0.05, 20, 20)  # small sphere marker
        glPushMatrix()
        glTranslatef(x, y, z)
        gluSphere(quadric, self.earth_radius * 0.05, 20, 20)
        glPopMatrix()
        gluDeleteQuadric(quadric)
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        if event.buttons() & QtCore.Qt.LeftButton:
            self.xRot += dy
            self.yRot += dx
            self.update()
        self.lastPos = event.pos()


class EarthOrbitWindow(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        super().__init__()
        self.setWindowTitle("Textured Earth with Orbit")
        self.glWidget = EarthOrbitViewer(**kwargs)
        self.setCentralWidget(self.glWidget)
        self.resize(800, 600)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Example orbit data
    true_anomaly = np.linspace(0, 360, 200)  # degrees
    radius = np.ones_like(true_anomaly) * 2.5

    window = EarthOrbitWindow(
        earth_diameter=2.0,
        space_color=(0.0, 0.0, 0.1),       # dark blue background
        texture_path="earth.jpg",
        orbit_true_anomaly=true_anomaly,
        orbit_radius=radius,
        orbit_color=(0.0, 1.0, 0.0)        # green orbit line
    )
    window.show()
    sys.exit(app.exec_())
