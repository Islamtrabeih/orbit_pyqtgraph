import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np, math, os, time, datetime
from PyQt5 import QtWidgets, QtCore, QtGui, QtOpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
from .orb_math import *



class EarthGLWidget(QtOpenGL.QGLWidget):
    """
    A QGLWidget that draws a textured Earth sphere and the satellite path/marker.
    We avoid pyqtgraph GLMeshItem for textured Earth to reduce API incompatibilities.
    """
    def __init__(self, parent=None, earth_texture_path="earth.jpg"):

        fmt = QtOpenGL.QGLFormat()
        fmt.setDoubleBuffer(True)
        super().__init__(fmt, parent)
        if not os.path.isabs(earth_texture_path):
            # Try to find the texture relative to the orbit.py file
            orbit_dir = os.path.dirname(os.path.abspath(__file__))

            # Check if earth.jpg exists in assets folder
            possible_paths = [
                earth_texture_path,  # Original path
                os.path.join(orbit_dir, earth_texture_path),
                os.path.join(orbit_dir, 'assets', earth_texture_path),
                os.path.join(orbit_dir, '..', 'assets', earth_texture_path),
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    earth_texture_path = path
                    break
            else:
                # If still not found, use a fallback
                print(f"Warning: Earth texture not found at {earth_texture_path}")
                # You could create a default texture here

        self.earth_texture_path = earth_texture_path
        # print(f"Using earth texture: {self.earth_texture_path}")  # Debug
        self.parent = parent
        self.earth_texture_path = earth_texture_path
        self.satellite_positions = np.zeros((0,3))  # in ECEF km
        self.show_accum = True
        self.marker_index = 0
        self.bgcolor = (0, 0, 0, 1)
        self.line_color = (1.0, 0.0, 0.0)
        self.zoom = 1.0
        self.angle_x = -20.0
        self.angle_y = -40.0
        self.last_wheel = 0
        self.texture_id = None
        self.setMinimumSize(600, 600)
        self.revolves = None
        # satellite marker size in km (visual)
        self.marker_size_km = 200.0
        self.rot_x = 0.0   # vertical rotation (pitch)
        self.rot_y = 0.0   # horizontal rotation (yaw)
        self.last_mouse_pos = None


    def initializeGL(self):
        # Enable depth testing so nearer objects hide farther ones
        glEnable(GL_DEPTH_TEST)
        # Enable 2D texture mapping in OpenGL
        glEnable(GL_TEXTURE_2D)
        # Enable smooth shading (interpolates colors across surfaces)
        glShadeModel(GL_SMOOTH)
        # Set the background (clear) color to whatever is stored in self.bgcolor
        # This color is used when the frame buffer is cleared
        glClearColor(*self.bgcolor)
        # Enable lighting calculations
        glEnable(GL_LIGHTING)
        # Enable light source #0 (OpenGL supports multiple lights)
        glEnable(GL_LIGHT0)
        # Define ambient light color (global fill light, same in all directions)
        ambient_light = [0.4, 0.4, 0.4, 1.0]  # RGBA
        # Define diffuse light color (light that varies with surface angle)
        diffuse_light = [0.9, 0.9, 0.9, 1.0]  # RGBA
        # Define the position/direction of light0
        # Last value 0.0 means it’s a directional light (like sunlight)
        light_position = [1.0, 1.0, 1.0, 0.0]
        # Send ambient light settings to light0
        glLightfv(GL_LIGHT0, GL_AMBIENT, ambient_light)
        # Send diffuse light settings to light0
        glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse_light)
        # Send position/direction to light0
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        # Create one OpenGL texture ID and store it
        self.texture_id = glGenTextures(1)
        # Load and bind the Earth texture from the provided file path
        self.bind_texture(self.earth_texture_path)


    def bind_texture(self, path):
        # Check if the texture file exists
        if not os.path.exists(path):
            print(f"Earth texture not found at {path}. Earth will be untextured.")
            return
        # Load the image into a QImage object and mirror it vertically
        # (This fixes the flipped orientation caused by OpenGL coordinate system)
        img = QtGui.QImage(path).mirrored()
        # Convert the image to 32-bit RGBA format so OpenGL understands it
        img = img.convertToFormat(QtGui.QImage.Format_RGBA8888)
        # Get image dimensions
        w = img.width()
        h = img.height()
        # Get the raw pointer to the pixel data
        ptr = img.bits()
        # Set the size of the pointer to match the full byte size of the image
        ptr.setsize(img.byteCount())
        # Convert pointer data to a Python bytes object
        data = ptr.asstring()
        # Bind our pre-created OpenGL texture ID as the current texture
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        # Set texture minification filter (scaling down)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        # Set texture magnification filter (scaling up)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # Upload the texture data to GPU memory
        glTexImage2D(
            GL_TEXTURE_2D,  # Target: 2D texture
            0,              # Level of detail (0 = base)
            GL_RGBA,        # Internal format (GPU storage format)
            w, h,           # Width and height
            0,              # Border (must be 0)
            GL_RGBA,        # Format of the provided data
            GL_UNSIGNED_BYTE, # Data type of the provided data
            data            # The actual pixel data
        )


    def resizeGL(self, w, h):
        # Define the portion of the window to use for rendering (entire window)
        glViewport(0, 0, w, h)
        # Switch to modifying the projection matrix
        glMatrixMode(GL_PROJECTION)
        # Reset the projection matrix to the identity
        glLoadIdentity()
        # Set up a perspective projection:
        # - 45° field of view
        # - Aspect ratio based on window width/height
        # - Near clipping plane: 1.0
        # - Far clipping plane: 500,000 (so we can see far orbits)
        gluPerspective(45.0, w / float(h or 1), 1.0, 500000.0)
        # Switch back to modifying the modelview matrix
        glMatrixMode(GL_MODELVIEW)


    def wheelEvent(self, ev):
        # Get the wheel rotation in 'steps' (120 units per step in Qt)
        delta = ev.angleDelta().y() / 120.0
        # Apply exponential zoom scaling (0.9 per step forward, >1 for backward)
        self.zoom *= (0.9 ** delta)
        # Clamp zoom factor so you can’t zoom too far in or out
        self.zoom = max(0.3, min(self.zoom, 3.0))
        # Trigger a repaint so zoom change is visible immediately
        self.update()


    def mousePressEvent(self, event):
        # Store the mouse position when a button is pressed
        self.last_mouse_pos = event.pos()


    def mouseMoveEvent(self, event):
        # If we never stored the last position (mouse not pressed), ignore movement
        if self.last_mouse_pos is None:
            return
        # Calculate horizontal movement (delta x)
        dx = event.x() - self.last_mouse_pos.x()
        # Calculate vertical movement (delta y)
        dy = event.y() - self.last_mouse_pos.y()
        # Adjust vertical rotation angle (pitch) based on vertical mouse movement
        self.rot_x += dy * 0.5
        # Adjust horizontal rotation angle (yaw) based on horizontal mouse movement
        self.rot_y += dx * 0.5
        # Update stored mouse position for next movement calculation
        self.last_mouse_pos = event.pos()
        # Trigger a repaint to show new rotation
        self.update()


    def paintGL(self):
        # Clear the color and depth buffers so we start fresh each frame
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Reset the current modelview matrix to the identity (no transformation)
        glLoadIdentity()
        # Calculate how far the virtual camera should be from the Earth
        # 18000 is a base distance in km; self.zoom changes this distance
        cam_dist = 18000 * self.zoom
        # Position and aim the camera:
        # gluLookAt(eye_x, eye_y, eye_z,  center_x, center_y, center_z,  up_x, up_y, up_z)
        # Here: camera is at (0,0,cam_dist), looking at the origin (Earth's center),
        # with the 'up' direction being the +Y axis
        gluLookAt(0, 0, cam_dist,
                0, 0, 0,
                0, 1, 0)
        # Apply mouse-controlled rotation around the X axis (tilt up/down)
        glRotatef(self.rot_x, 1, 0, 0)
        # Apply mouse-controlled rotation around the Z axis (spin around the vertical axis)
        # This replaces the usual Y-axis rotation for a globe, to match your intended behavior
        glRotatef(self.rot_y, 0, 0, 1)
        # Apply Earth's axial tilt (23.44 degrees) around the Y axis
        # This tilts the planet so the poles are angled correctly relative to the orbit plane
        glRotatef(23.44, 0, 1, 0)

        # Draw the textured sphere representing Earth, with radius = 6371 km
        self.draw_textured_earth(radius=6371.0)
        # Draw path (only if we actually have satellite position data)
        if self.satellite_positions.size:
            # Short alias for positions array (ECEF coordinates in km)
            pts = self.satellite_positions
            # Set the line width for the orbital path
            glLineWidth(2.0)
            # Begin drawing a continuous line strip (connects each vertex in sequence)
            glBegin(GL_LINE_STRIP)
            # Set the current drawing color for the path
            glColor3f(*self.line_color)
            # If show_accum is True, draw the entire accumulated path of the satellite
            if self.show_accum:
                for p in pts:
                    # Plot each point in 3D space (x, y, z in km)
                    glVertex3f(p[0], p[1], p[2])
            else:
                # Otherwise, only draw the current marker position (single vertex)
                idx = max(0, min(self.marker_index, len(pts)-1))
                glVertex3f(*pts[idx])
            # End the line strip drawing
            glEnd()
            # Draw the satellite marker at the current index position
            idx = max(0, min(self.marker_index, len(pts)-1))
            self.draw_satellite_marker(pts[idx])
            # Draw satellite marker
            idx = max(0, min(self.marker_index, len(pts)-1))
            self.draw_satellite_marker(pts[idx])


    def draw_textured_earth(self, radius=6371.0, stacks=40, slices=80):
        # Enable 2D texturing so that vertices can be mapped to texture coordinates
        glEnable(GL_TEXTURE_2D)
        # If we have already loaded a texture, bind it so OpenGL uses it for drawing
        if self.texture_id is not None:
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
        # Save current transformation matrix so we can restore after tilt
        glPushMatrix()
        # Apply an axial tilt to match Earth's obliquity so that the texture lines up correctly
        glRotatef(180, 0, 0, 1)
        glRotatef(-OBLIQUITY_DEG, 1, 0, 0)
        # Loop through horizontal bands of the sphere (latitude)
        for i in range(stacks):
            # lat0 and lat1 are the start and end latitudes of the current band
            lat0 = math.pi * (-0.5 + i / stacks)
            lat1 = math.pi * (-0.5 + (i+1) / stacks)
            # y0, y1 are the vertical positions (sin of latitude)
            y0 = math.sin(lat0)
            y1 = math.sin(lat1)
            # r0, r1 are the radius of the horizontal cross section at each latitude
            r0 = math.cos(lat0)
            r1 = math.cos(lat1)
            # Start defining a horizontal strip (quad strip) for the current latitude band
            glBegin(GL_QUAD_STRIP)
            for j in range(slices+1):  # slices+1 so the strip closes fully
                # Compute longitude for this slice
                lon = 2 * math.pi * (j / slices)
                # x0, z0 are the horizontal positions on the sphere's surface
                x0 = math.cos(lon)
                z0 = math.sin(lon)
                # Map 3D longitude/latitude to 2D texture coordinates
                u = j / slices
                v0 = 0.5 + lat0 / math.pi
                v1 = 0.5 + lat1 / math.pi
                # First vertex of the quad strip segment
                glTexCoord2f(u, v0)         # texture coordinates (u, v)
                glNormal3f(r0*x0, r0*z0, y0) # normal vector for lighting
                glVertex3f(radius*r0*x0, radius*r0*z0, radius*y0)  # position
                # Second vertex of the quad strip segment
                glTexCoord2f(u, v1)
                glNormal3f(r1*x0, r1*z0, y1)
                glVertex3f(radius*r1*x0, radius*r1*z0, radius*y1)
            glEnd()
        # Restore the transformation matrix (removes tilt for the rest of the scene)
        glPopMatrix()
        # Disable texturing after drawing
        glDisable(GL_TEXTURE_2D)


    def draw_satellite_marker(self, pos_km, scale=1.0):
        """
        Draw a small sphere (silver) at pos_km (km) and simple solar panels (navy-blue).
        pos_km: [x,y,z] in km ECEF
        """
        glPushMatrix()
        glTranslatef(pos_km[0], pos_km[1], pos_km[2])
        # satellite body
        glColor3f(0.75, 0.75, 0.75)  # silver
        quad = gluNewQuadric()
        gluSphere(quad, 50.0, 20, 20)  # 50 km visual scale (adjust if too large)
        gluDeleteQuadric(quad)
        # solar panels (two rectangles)
        glDisable(GL_LIGHTING)
        glColor3f(0.0, 0.0, 0.5)
        # draw your panel
        glEnable(GL_LIGHTING)
        glBegin(GL_QUADS)
        # left panel
        glVertex3f(-144.0, -10.0, 10.0)
        glVertex3f(-144.0,  10.0, 10.0)
        glVertex3f(-60.0,   10.0, 10.0)
        glVertex3f(-60.0,  -10.0, 10.0)
        # right panel
        glVertex3f(60.0, -10.0, 10.0)
        glVertex3f(60.0,  10.0, 10.0)
        glVertex3f(144.0,  10.0, 10.0)
        glVertex3f(144.0, -10.0, 10.0)
        glEnd()
        glPopMatrix()


    def set_positions_ecef(self, positions_km, show_accum=True, marker_index=0, lncolor=(1,0,0)):
        # Store the satellite positions in ECEF coordinates (convert to numpy array for performance)
        self.satellite_positions = np.array(positions_km, dtype=float)
        # Whether to show the entire accumulated path or only the marker
        self.show_accum = show_accum
        # The index of the "current" marker along the path
        self.marker_index = int(marker_index)
        # Set the color of the orbit line (RGB values in range 0–1)
        self.line_color = lncolor
        # Request a repaint of the OpenGL widget
        self.update()


    def set_bgcolor(self, hexcolor):
        # Convert the hex color (e.g. "#000000") into a QColor object
        c = QtGui.QColor(hexcolor)
        # Store the background color as a tuple of floats (0–1 range)
        self.bgcolor = (c.redF(), c.greenF(), c.blueF(), c.alphaF())
        # Immediately tell OpenGL to use this as the clear color
        glClearColor(*self.bgcolor)



class OrbitPlot(QtWidgets.QWidget):
    """
    Main class to be embedded.
    Constructor: OrbitPlot(elems_array, parent=None, earth_texture='earth.jpg')
    """
    def __init__(self, elems, parent=None, earth_texture='earth.jpg'):
        super().__init__(parent)
        self.elems = elems
        self.earth_texture = earth_texture
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)
        # Two subwidgets (we will add/replace depending on which method is called)
        self.gl_widget = EarthGLWidget(self, earth_texture_path=self.earth_texture)
        self.pg_plot = pg.PlotWidget()
        self.pg_plot.setAspectLocked(False)
        self.animation_timer = None
        # cached propagated data
        self._cached_times = None
        self._cached_r_eci = None
        self._cached_r_ecef = None
        self._epoch = elems[-1]


    def _prepare_propagation(self, animation=True, revolves=None, sample_points_per_orbit=2000, orbit_time_scale=1.0):
        """
        Precompute a time array and propagated positions.
        N is always per orbit, so animation speed stays consistent regardless of revolves.
        """
        a = float(self.elems[0])
        # orbital period (seconds)
        T = 2 * math.pi * math.sqrt(a**3 / 398600.4418)
        if self.animation_timer:
            self.animation_timer.stop()
            self.animation_timer.deleteLater()
            self.animation_timer = None
        if not animation and revolves is not None:
            total_time = T * revolves
            N = max(300, int(sample_points_per_orbit * revolves))
            times = np.linspace(0, total_time, N)
        else:
            # Animation mode: generate multiple orbits if needed, but keep sample rate per orbit fixed
            total_time = T * (revolves if revolves is not None else 2.0)
            N = int(sample_points_per_orbit * (revolves if revolves is not None else 2.0))
            times = np.linspace(0, total_time, N)
        r_eci = propagate_orbit(self.elems, times)
        r_ecef = eci_to_ecef(r_eci, times)
        self._cached_times = times
        self._cached_r_eci = r_eci
        self._cached_r_ecef = r_ecef
        return times, r_eci, r_ecef, T


    def _3d(self, animation=True, accumulation=True, title='3D Orbit', bgcolor='#000000', lncolor='#ff0000', revolves=None):
        """
        Show a 3D textured Earth + orbit.
        animation: True -> animated (revolves is ignored), False -> static (must supply revolves int)
        accumulation: True -> accumulate path, False -> show only current location
        bgcolor: hex background for space
        lncolor: hex for line color
        revolves: if animation False, number of revolutions to compute and display (int)
        """
        # clear layout and place GL widget
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.layout.addWidget(self.gl_widget)
        # prepare propagation
        times, r_eci, r_ecef, period = self._prepare_propagation(animation=animation, revolves=revolves)
        # set widget colors/background
        self.gl_widget.set_bgcolor(bgcolor)
        rgb = tuple(int(lncolor.lstrip('#')[i:i+2], 16)/255.0 for i in (0,2,4))
        self.gl_widget.line_color = rgb
        self.gl_widget.show_accum = accumulation
        self.gl_widget.revolves = revolves
        # update positions (in ECEF) into GL widget
        self.gl_widget.set_positions_ecef(r_ecef, show_accum=accumulation, marker_index=0, lncolor=rgb)
        if animation:
            if self.animation_timer:
                self.animation_timer.stop()
                self.animation_timer.deleteLater()
            self.animation_timer = QtCore.QTimer(self)
            N = len(times)
            orbits_to_show = revolves if revolves else 2
            points_per_orbit = max(1, N // orbits_to_show)
            interval_ms = max(1, int((period / points_per_orbit) * 1000))
            index = {'i': 0}
            def update_frame():
                index['i'] = (index['i'] + 1) % N
                self.gl_widget.marker_index = index['i']
                self.gl_widget.update()
            self.animation_timer.timeout.connect(update_frame)
            self.animation_timer.start(interval_ms)
        else:
            # static: set marker to last index
            self.gl_widget.marker_index = len(times)-1
            self.gl_widget.update()


    def _2d(self, animation=True, accumulation=True, title='2D Ground Track', lncolor='#ff0000', revolves=None):
        """
        Show a 2D ground track over equirectangular earth.jpg.
        animation: animate current location moving along track
        accumulation: show full track or only current point
        lncolor: color of track
        revolves: if animation False, int number of revolutions to plot
        """
        # Clear layout and add pyqtgraph widget
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.layout.addWidget(self.pg_plot)
        self.pg_plot.clear()
        self.pg_plot.setTitle(title)
        # Get satellite positions
        times, r_eci, r_ecef, period = self._prepare_propagation(animation=animation, revolves=revolves)
        lat, lon, alt = ecef_to_latlon(r_ecef)
        # ---- Load background image ----
        img_path = os.path.join(os.path.dirname(__file__), self.earth_texture)
        if os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path).convert("RGBA")
                # Correct orientation
                pil_img = pil_img.rotate(90, expand=True)
                pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
                pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
                bgarr = np.array(pil_img)
                bgitem = pg.ImageItem(bgarr)
                bgitem.setRect(QtCore.QRectF(-180, -90, 360, 180))
                self.pg_plot.addItem(bgitem)
                self.pg_plot.setLimits(xMin=-180, xMax=180, yMin=-90, yMax=90)
                self.pg_plot.setRange(xRange=(-180, 180), yRange=(-90, 90))
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")
        # ---- Prepare pen ----
        rgb = tuple(int(lncolor.lstrip('#')[i:i+2], 16)/255.0 for i in (0, 2, 4))
        pen = pg.mkPen(color=tuple([int(255*c) for c in rgb]), width=2)
        # ---- Function to avoid horizontal line at dateline ----
        def add_wrapped_segments(plot_widget, lon_arr, lat_arr):
            if len(lon_arr) < 2:
                return []
            segments = []
            seg_lon = [lon_arr[0]]
            seg_lat = [lat_arr[0]]
            for i in range(1, len(lon_arr)):
                if abs(lon_arr[i] - lon_arr[i-1]) > 180:
                    seg = pg.PlotCurveItem(seg_lon, seg_lat, pen=pen)
                    plot_widget.addItem(seg)
                    segments.append(seg)
                    seg_lon = [lon_arr[i]]
                    seg_lat = [lat_arr[i]]
                else:
                    seg_lon.append(lon_arr[i])
                    seg_lat.append(lat_arr[i])
            seg = pg.PlotCurveItem(seg_lon, seg_lat, pen=pen)
            plot_widget.addItem(seg)
            segments.append(seg)
            return segments
        # ---- Marker for current position ----
        marker = pg.ScatterPlotItem([lon[0]], [lat[0]], size=10, brush=pg.mkBrush(200, 200, 200))
        self.pg_plot.addItem(marker)
        N = len(times)
        if animation:
            # Keep real-time orbit speed regardless of revolves
            orbits_to_show = revolves if revolves else 2
            points_per_orbit = max(1, N // orbits_to_show)
            interval_ms = max(1, int((period / points_per_orbit) * 1000))
            if self.animation_timer:
                self.animation_timer.stop()
                self.animation_timer.deleteLater()
            self.animation_timer = QtCore.QTimer(self)
            index = {'i': 0}
            current_segments = []

            def update2d():
                nonlocal current_segments
                index['i'] = (index['i'] + 1) % N
                # Remove old track segments
                for seg in current_segments:
                    self.pg_plot.removeItem(seg)
                current_segments.clear()
                if accumulation:
                    current_segments = add_wrapped_segments(self.pg_plot, lon[:index['i']+1], lat[:index['i']+1])
                else:
                    current_segments = add_wrapped_segments(self.pg_plot, [lon[index['i']]], [lat[index['i']]])
                # Move marker
                marker.setData([lon[index['i']]], [lat[index['i']]])

            self.animation_timer.timeout.connect(update2d)
            self.animation_timer.start(interval_ms)
        else:
            # Static mode
            if accumulation:
                add_wrapped_segments(self.pg_plot, lon, lat)
            else:
                add_wrapped_segments(self.pg_plot, [lon[-1]], [lat[-1]])
            marker.setData([lon[-1]], [lat[-1]])


    def liveorbit(self, lncolor='#ff0000', epoch_time=None):
        """
        Live ground track: 1 revolution total around 'now', satellite centered,
        ends fade to transparent, moves in sync with actual orbital motion.
        This version aligns Earth orientation with GMST at epoch (GPredict-style).
        """
        # --- Resolve epoch timestamp (float seconds since UNIX epoch) ---
        if epoch_time is not None:
            epoch_ts = float(epoch_time) if isinstance(epoch_time, (int, float)) \
                    else datetime.datetime.fromisoformat(epoch_time).timestamp()
        else:
            epoch_ts = float(self._epoch) if isinstance(self._epoch, (int, float)) \
                    else datetime.datetime.fromisoformat(self._epoch).timestamp()
        # --- GMST at epoch (radians) ---
        def gmst_rad(unix_ts: float) -> float:
            # Convert UNIX -> UTC datetime
            dt = datetime.datetime.utcfromtimestamp(unix_ts)
            # Julian Date
            Y, M, D = dt.year, dt.month, dt.day
            h, m, s = dt.hour, dt.minute, dt.second + dt.microsecond*1e-6
            if M <= 2:
                Y -= 1
                M += 12
            A = math.floor(Y/100)
            B = 2 - A + math.floor(A/4)
            JD0 = math.floor(365.25*(Y + 4716)) + math.floor(30.6001*(M + 1)) + D + B - 1524.5
            frac_day = (h + (m + s/60.0)/60.0)/24.0
            JD = JD0 + frac_day
            T = (JD - 2451545.0)/36525.0  # centuries since J2000.0

            # IAU 1982 expression for GMST in seconds of time
            GMST_sec = (67310.54841
                        + (876600.0*3600 + 8640184.812866)*T
                        + 0.093104*(T**2)
                        - 6.2e-6*(T**3))
            # Convert to radians in [0, 2π)
            GMST_deg = (GMST_sec/240.0) % 360.0
            return math.radians(GMST_deg)
        gst0 = gmst_rad(epoch_ts)
        # --- Clear layout and set plot ---
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if w: w.setParent(None)
        self.layout.addWidget(self.pg_plot)
        self.pg_plot.clear()
        self.pg_plot.setTitle("Live Orbit Ground Track")
        # --- Orbital period ---
        a = float(self.elems[0])
        period = 2 * math.pi * math.sqrt(a**3 / 398600.4418)  # s
        # --- Background map (your orientation) ---
        img_path = os.path.join(os.path.dirname(__file__), self.earth_texture)
        if os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path).convert("RGBA")
                pil_img = pil_img.rotate(90, expand=True)
                pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
                pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
                bgarr = np.array(pil_img)
                bgitem = pg.ImageItem(bgarr)
                bgitem.setRect(QtCore.QRectF(-180, -90, 360, 180))
                self.pg_plot.addItem(bgitem)
                self.pg_plot.setLimits(xMin=-180, xMax=180, yMin=-90, yMax=90)
                self.pg_plot.setRange(xRange=(-180, 180), yRange=(-90, 90))
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")
        # --- Satellite marker ---
        marker = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255, 255, 255))
        marker.setZValue(1_000_000)
        self.pg_plot.addItem(marker)
        # --- Animation timer ---
        if self.animation_timer:
            self.animation_timer.stop()
            self.animation_timer.deleteLater()
        self.animation_timer = QtCore.QTimer(self)
        # --- Parameters ---
        sample_points = 2000
        half_window_time = period / 2
        base_rgb = tuple(int(lncolor.lstrip('#')[k:k+2], 16) for k in (0, 2, 4))
        current_segments = []

        def add_wrapped_gradient(plot_widget, lon_seg, lat_seg, base_rgb):
            if len(lon_seg) < 2:
                return []
            # split on dateline
            segs, seg_lon, seg_lat = [], [lon_seg[0]], [lat_seg[0]]
            for j in range(1, len(lon_seg)):
                if abs(lon_seg[j] - lon_seg[j-1]) > 180:
                    segs.append((seg_lon, seg_lat))
                    seg_lon, seg_lat = [lon_seg[j]], [lat_seg[j]]
                else:
                    seg_lon.append(lon_seg[j]); seg_lat.append(lat_seg[j])
            segs.append((seg_lon, seg_lat))
            N = len(lon_seg); half = N // 2
            alpha_profile = np.concatenate([
                np.linspace(0, 255, half, endpoint=False),
                np.linspace(255, 0, N - half, endpoint=True)])
            items, start_idx = [], 0
            for seg_lon, seg_lat in segs:
                seg_len = len(seg_lon)
                alphas = alpha_profile[start_idx:start_idx + seg_len]
                start_idx += seg_len
                for k in range(seg_len - 1):
                    pen = pg.mkPen(color=(base_rgb[0], base_rgb[1], base_rgb[2], int(alphas[k])), width=2)
                    seg_item = pg.PlotCurveItem([seg_lon[k], seg_lon[k+1]], [seg_lat[k], seg_lat[k+1]], pen=pen)
                    seg_item.setZValue(100)
                    plot_widget.addItem(seg_item)
                    items.append(seg_item)
            return items

        def update_live():
            nonlocal current_segments
            for seg in current_segments:
                self.pg_plot.removeItem(seg)
            current_segments.clear()
            now = time.time()
            # Centered time window and RELATIVE time since epoch for propagation/rotation
            times_abs = np.linspace(-half_window_time, half_window_time, sample_points) + now
            t_rel = times_abs - epoch_ts  # seconds since epoch
            # Propagate with relative time (epoch is when M0 is defined)
            r_eci = propagate_orbit(self.elems, t_rel)  # M0_epoch_time=0 by design with t_rel
            # Rotate Earth using GMST(epoch) + omega * (t - epoch)
            r_ecef = eci_to_ecef(r_eci, t_rel, gst0=gst0)
            # Convert to lat/lon
            lat, lon, _ = ecef_to_latlon(r_ecef)
            # Normalize lon to [-180,180] for plotting
            lon = ((lon + 180) % 360) - 180
            current_segments = add_wrapped_gradient(self.pg_plot, lon, lat, base_rgb)
            # Marker at actual "now"
            idx_now = np.argmin(np.abs(times_abs - now))
            marker.setData([lon[idx_now]], [lat[idx_now]])

        interval_ms = max(1, int((period / sample_points) * 1000))
        self.animation_timer.timeout.connect(update_live)
        self.animation_timer.start(interval_ms)
