'''This file contains the functions that load the pixel entanglement stuff
The circle packings come from http://hydra.nat.uni-magdeburg.de/packing/csq/csq.html
The coordinates give the centres of the circles, and they all have the same radius, given in the radii array.

The circles fit into a square with coordinates (-0.5, -0.5) -> (0.5, 0.5) 
or a circle with radius 1
'''

import numpy as np
from numba import njit, jit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
# from slm_display import SLMDisplay, FullScreenPlot
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QGroupBox, QComboBox, QScrollArea, QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
from slm_display import FullScreenPlot, SLMDisplay
from lut_control import LUTWidget
from zernike_controls import ZernikeSet
from oam_pattern_controls import XYController

radii_sq = np.loadtxt(
    'circle_packing/radius_square.txt'
)[:, 1]  # the radius array for packing circles into a square

radii_ci = np.loadtxt(
    'circle_packing/radius_circle.txt'
)[:, 1]  # the radius array for packing circles into a circle


def get_coords_square(i):
    '''Get the coordinates of i circles packed into a square
    '''
    if i == 1:
        return np.loadtxt('circle_packing/csq{}.txt'.format(i))
    else:
        return np.loadtxt('circle_packing/csq{}.txt'.format(i))[:, 1:]


def get_coords_circle(i):
    '''Get the coordinates of i circles packed into a circle
    '''
    if i == 1:
        return np.loadtxt('circle_packing/cci{}.txt'.format(i))[1:]
    else:
        return np.loadtxt('circle_packing/cci{}.txt'.format(i))[:, 1:]


@njit()
def point_in_circle(x, y, c):
    '''Check if the given point is inside the given circle
    p is a tuple (x, y) - the point you want to check
    c is a tuple (r, (x, y)) containing the radius of the circle and the x and y
    '''
    return ((x - c[1][0])**2 + (y - c[1][1])**2) < c[0]**2


def complex_field(components,
                  X,
                  Y,
                  pixel_radius=1,
                  circle_radius=1,
                  circle_position=(0, 0)):
    '''Take the components of a vector, the X and Y matrices (from meshgrid)
    the radius of the pixel bases, the radius of the circle containing the pixels
    and the positions of the containing circle
    return the complex field over X and Y which represents this vector
    '''
    n_pixels = len(components)
    coords = get_coords_circle(n_pixels)
    field = np.zeros(X.shape, dtype=np.complex128)
    if n_pixels > 1:
        for i, p in enumerate(coords):
            field += components[i] * point_in_circle(
                X / circle_radius - circle_position[0],
                Y / circle_radius - circle_position[1],
                (pixel_radius * radii_ci[n_pixels], p))
    else:
        field += components[0] * point_in_circle(
            X / circle_radius - circle_position[0],
            Y / circle_radius - circle_position[1],
            (pixel_radius * radii_ci[n_pixels], coords))

    return field


def basis(dim, a, n):
    '''Generate the basis vectors of the mutually unbiased bases in dim = 2j+1
    dimensions
    The index a ∈ (0, 2j+1) (dim+1 bases) denotes which MUB the vector is drawn from
    a=0 gives the computational basis
    The index n ∈ (0, 2j) denotes which vector is chosen
    Taken from the paper: https://arxiv.org/pdf/quant-ph/0601092.pdf
    '''
    if a == 0:
        v = np.zeros(dim, dtype=np.complex128)
        v[n] = 1
        return v
    else:
        j = (dim - 1) / 2
        q = np.exp(1j * 2 * np.pi / dim)
        return 1 / np.sqrt(dim) * np.array([
            np.power(q, 0.5 * (j + m) * (j - m + 1) * (a - 1) + (j + m) * n)
            for m in np.linspace(-j, j, dim)
        ],
                                           dtype=np.complex128)


def check_prod(dim, a, va, b, vb):
    '''Get the absolute value of the scalar product between MUB basis vectors
    '''
    return np.abs(basis(dim, a, va).conj() @ basis(dim, b, vb))


def check_all(dim):
    '''Check the product between all MUB basis vectors of dimension dim
    and return the number that are incorrect
    '''
    errors = 0
    for a in range(dim + 1):
        for b in range(a, dim + 1):
            for via in range(dim):
                for vib in range(dim):
                    val = check_prod(dim, a, via, b, vib)
                    if a == b:
                        if via == vib:
                            errors += not np.isclose(val, 1)
                        else:
                            errors += not np.isclose(val, 0)
                    else:
                        errors += not np.isclose(val, 1 / np.sqrt(dim))

    return errors


def plot_circles(i, ax):
    '''Pack i circles into the unit circle and plot them
    '''
    coords = get_coords_circle(i)
    for row in coords:
        ax.add_patch(mpatches.Circle(row, radii_ci[i]))


def nice_circles_plot():
    fig, axs = plt.subplots(5, 5)
    for i, ax in enumerate(axs.flatten()):
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        plot_circles(i + 2, ax)
    plt.show()


class PixelEntanglementController(QWidget):
    '''Controls for pixel entanglement
    '''
    def __init__(self, window_title, screens, slm_size):
        self.screens = screens

        layout = QGridLayout()
        self.x, self.y = np.mgrid[-1:1:(slm_size[0] * 1j), -1:1:(slm_size[1] *
                                                                 1j)]
        self.slm_size = slm_size

        screen_selector = QComboBox()
        position_zernike_scroll_area = QScrollArea()
        slm_zernike_scroll_area = QScrollArea()

        self.position = XYController("Pixel Centre")
        self.diffraction_grating = XYController("Diffraction Grating")
        self.pixel_radius = pg.SpinBox()
        self.circle_radius = pg.SpinBox()
        self.dim = pg.SpinBox(int=True, step=1, bounds=(2, None))
        self.mub_selection = pg.SpinBox(int=True, step=1)
        self.basis_selection = pg.SpinBox(int=True, step=1)

        self.position_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(2, 2), (0, 2), (-2, 2)],
            title="Position Zernike Controller")
        self.slm_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(2, 2), (0, 2), (-2, 2)],
            title="SLM Zernike Controller")

        self.plot = FullScreenPlot(slm_size, slm_size)

        self.slm_window = SLMDisplay(window_title,
                                     screens[screen_selector.currentIndex()],
                                     slm_size)

        screen_selector.currentIndexChanged.connect(
            lambda _: self.slm_window.set_screen(self.screens[screen_selector.
                                                              currentIndex()]))


class PixelEntanglementSLMController(QWidget):
    '''A controller for pixel entanglement in a single SLM
    '''
    def __init__(self, window_title, screens, slm_size):
        '''Pass a list of screens to allow this to select what screen a
        pattern is displayed on
        Pass slm_size to set the size of the slm to display on
        (how many pixels it has)
        There are two zernike controls: one for position and one for the slm
        '''
        super().__init__()
        self.screens = screens

        layout = QGridLayout()
        self.x, self.y = np.mgrid[-1:1:(slm_size[0] * 1j), -1:1:(slm_size[1] *
                                                                 1j)]
        self.slm_size = slm_size

        # this is an overlay that can be added to the slm display
        # it can be used for eg. entanglement concentration
        self.overlay = None
        screen_selector = QComboBox()
        oam_scroll_area = QScrollArea()
        position_zernike_scroll_area = QScrollArea()
        slm_zernike_scroll_area = QScrollArea()
        add_controller_button = QPushButton("Add OAM control")

        self.oam_controller = OAMControlSet()
        self.plot = FullScreenPlot(slm_size, slm_size)
        self.position_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(2, 2), (0, 2), (-2, 2)],
            title="Position Zernike Controller")
        self.slm_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(2, 2), (0, 2), (-2, 2)],
            title="SLM Zernike Controller")
        self.position_controller = XYController("Position")

        self.lut_control = None
        self.lut_control_button = QPushButton("Open LUT controls")
        self.diffraction_grating = XYController("Diffraction grating")
        self.lut_list = [(-np.pi, 0), (np.pi, 255)]

        oam_scroll_area.setWidget(self.oam_controller)
        oam_scroll_area.setWidgetResizable(True)
        position_zernike_scroll_area.setWidget(
            self.position_zernike_controller)
        position_zernike_scroll_area.setWidgetResizable(True)
        slm_zernike_scroll_area.setWidget(self.slm_zernike_controller)
        slm_zernike_scroll_area.setWidgetResizable(True)

        for i, screen in enumerate(screens):
            screen_selector.addItem("Screen {}".format(i))

        self.slm_window = SLMDisplay(window_title,
                                     screens[screen_selector.currentIndex()],
                                     slm_size)

        screen_selector.currentIndexChanged.connect(
            lambda _: self.slm_window.set_screen(self.screens[screen_selector.
                                                              currentIndex()]))

        self.oam_controller.value_changed.connect(self.update_image)
        self.position_zernike_controller.value_changed.connect(
            self.update_image)
        self.slm_zernike_controller.value_changed.connect(self.update_image)
        self.diffraction_grating.value_changed.connect(self.update_image)
        self.position_controller.value_changed.connect(self.update_image)
        self.position_controller.value_changed.connect(
            self.change_zernike_position)
        add_controller_button.clicked.connect(
            self.oam_controller.add_new_oam_pattern)
        self.lut_control_button.clicked.connect(self.open_lut_control)

        layout.addWidget(QLabel("Display on:"), 0, 1)
        layout.addWidget(screen_selector, 0, 2)
        layout.addWidget(add_controller_button, 0, 0)
        layout.addWidget(self.diffraction_grating, 0, 3)
        layout.addWidget(oam_scroll_area, 1, 0, 1, 3)
        layout.addWidget(self.plot, 1, 3, 1, 1)
        layout.addWidget(self.lut_control_button, 3, 0, 1, 1)
        layout.addWidget(self.position_controller, 3, 1, 1, 3)
        layout.addWidget(position_zernike_scroll_area, 4, 0, 1, 2)
        layout.addWidget(slm_zernike_scroll_area, 4, 2, 1, 2)

        self.setLayout(layout)

        self.oam_controller.add_new_oam_pattern()

    def change_zernike_position(self):
        x, y = self.position_controller.get_values()
        self.position_zernike_controller.change_position(
            self.x - x, self.y - y)

    def open_lut_control(self):
        '''Open the LUT control if it's not open already
        '''
        if self.lut_control is None:
            self.lut_control = LUTWidget(self.lut_list)
            self.lut_control.value_changed.connect(self.update_LUT)
            self.lut_control.closed.connect(self.remove_lut_control)
            self.lut_control.show()

    def remove_lut_control(self):
        self.lut_control = None

    @pyqtSlot(list)
    def update_LUT(self, new_lut):
        if len(new_lut) >= 2:
            self.lut_list = new_lut
            new_lut = points_to_lut(self.lut_list)
            self.plot.update_LUT(new_lut)
            self.slm_window.window.update_LUT(new_lut)

    def update_image(self):
        '''Update the image displayed on the oam plot and the
        gui plot
        '''
        diff_x, diff_y = self.diffraction_grating.get_values()
        position_zernike_image = self.position_zernike_controller.get_pattern()
        slm_zernike_image = self.slm_zernike_controller.get_pattern()
        x, y = self.position_controller.get_values()
        oam_image = np.sum([
            p["amplitude"] *
            np.exp(1j * ((p["ang_mom"] * np.arctan2(self.y - y, self.x - x)) +
                         (diff_x * self.x + diff_y * self.y) + p["phase"]))
            for p in self.oam_controller.get_values()
        ],
                           axis=0)
        if self.overlay is None:
            new_image = np.angle(slm_zernike_image * position_zernike_image *
                                 oam_image)
        else:
            new_image = np.angle(slm_zernike_image * position_zernike_image *
                                 oam_image * self.overlay)
        self.plot.set_and_update_image(new_image)
        self.slm_window.set_image(new_image)

    def set_slm_size(self, size):
        '''Set the size of the slm to display on in pixels
        size is a tuple, eg: (500, 500)
        '''
        self.x, self.y = np.mgrid[-1:1:(size[0] * 1j), -1:1:(size[1] * 1j)]
        delta_x, delta_y = self.position_controller.get_values()
        self.slm_window.window.update_SLM_size(size)
        self.plot.screen_size = size
        self.plot.update_SLM_size(size)
        self.position_zernike_controller.generate_polynomials(
            self.x - delta_x, self.y - delta_y)
        self.slm_zernike_controller.generate_polynomials(self.x, self.y)

    def close_slm_window(self):
        self.slm_window.window.close()
        if self.lut_control is not None:
            self.lut_control.close()

    def get_values(self):
        '''Get a dictionary of values for the contained widgets
        '''
        return {
            "oam_controller":
            self.oam_controller.get_values(),
            "position_zernike_controller":
            self.position_zernike_controller.get_values(),
            "slm_zernike_controller":
            self.slm_zernike_controller.get_values(),
            "diffraction_grating":
            self.diffraction_grating.get_values(),
            "position_controller":
            self.position_controller.get_values(),
            "lut_list":
            self.lut_list,
            "overlay":
            self.overlay,
        }

    def set_values(self, *args, **kwargs):
        '''Set the values of the SLM display from a set of args and kwargs
        Expects values for:
        oam_controller,
        position_zernike_controller,
        slm_zernike_controller,
        position_controller,
        diffraction_grating,
        overlay,
        lut_list,
        '''
        for dictionary in args:
            for key, value in dictionary.items():
                if key == 'lut_list':
                    self.update_LUT(value)
                else:
                    try:
                        getattr(self, key).set_values(value)
                    except AttributeError:
                        pass

        for key, value in kwargs.items():
            if key == 'lut_list':
                self.update_LUT(value)
            else:
                try:
                    getattr(self, key).set_values(value)
                except AttributeError:
                    pass
