'''This file contains the functions that load the pixel entanglement stuff
The circle packings come from http://hydra.nat.uni-magdeburg.de/packing/csq/csq.html
The coordinates give the centres of the circles, and they all have the same radius, given in the radii array.

The circles fit into a square with coordinates (-0.5, -0.5) -> (0.5, 0.5)
or a circle with radius 1
'''

import numpy as np
from numba import njit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QGroupBox, QComboBox, QScrollArea, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
from slm_display import FullScreenPlot, SLMDisplay, points_to_lut
from lut_control import LUTWidget
from zernike_controls import ZernikeSet
from oam_pattern_controls import XYController
import json

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


@njit()
def point_in_slice(x, y, r, R, theta_1, theta_2, rotation, c):
    '''Check if the given point is inside the given pizza slice
    The pizza slice is defined by two angles (theta_1, theta_2),
    which the angle of the point must be inside.
    The centre of the circle is given by c
    r gives a limit to the inside of the circle and
    R gives a limit to the outside of the circle
    '''
    theta = (np.arctan2(y - c[1], x - c[0]) + rotation) % (np.pi * 2)
    mag = (x - c[0])**2 + (y - c[1])**2
    return (theta_1 <= theta) & (theta < theta_2) & (r**2 < mag) & (mag < R**2)


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


def pizza_field(components,
                X,
                Y,
                circle_inner_radius=0,
                circle_outer_radius=1,
                circle_position=(0, 0),
                slice_angle_spacing=0,
                rotation=0):
    '''Take the components of a vector, the X and Y matrices (from meshgrid)
    and return the pizza representing the state.
    slice_angle_spacing gives the separation between slices in radians

    returns the complex field over X and Y which represents this vector
    '''
    n_slices = len(components)
    lower_angle = np.linspace(0, 2 * np.pi - (2 / n_slices * np.pi),
                              n_slices) + slice_angle_spacing
    upper_angle = np.linspace(2 / n_slices * np.pi, 2 * np.pi,
                              n_slices) - slice_angle_spacing
    field = np.zeros(X.shape, dtype=np.complex128)
    if n_slices > 1:
        for i, p in enumerate(components):
            field += p * point_in_slice(
                X, Y, circle_inner_radius, circle_outer_radius, lower_angle[i],
                upper_angle[i], rotation, circle_position)
    else:
        field += components[0] * point_in_slice(
            X, Y, circle_inner_radius, circle_outer_radius, lower_angle[i],
            upper_angle[i], rotation, circle_position)

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
        v[n % dim] = 1
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


class PizzaEntanglementController(QWidget):
    '''Controls for pizza entanglement
    '''
    def __init__(self, window_title, screens, slm_size):
        super().__init__()
        self.screens = screens

        layout = QGridLayout()
        self.x, self.y = np.mgrid[-1:1:(slm_size[0] * 1j), -1:1:(slm_size[1] *
                                                                 1j)]
        self.slm_size = slm_size

        self.overlay = None

        screen_selector = QComboBox()
        position_zernike_scroll_area = QScrollArea()
        slm_zernike_scroll_area = QScrollArea()

        # pizza pattern controls
        self.position = XYController("Pixel Centre")
        self.diffraction_grating = XYController("Diffraction Grating")
        self.circle_inner_radius = pg.SpinBox(value=0)
        self.circle_outer_radius = pg.SpinBox(value=1)
        self.slice_spacing = pg.SpinBox()
        self.rotation = pg.SpinBox()
        self.dim = pg.SpinBox(value=2, int=True, step=1, bounds=(2, None))
        self.mub_selection = pg.SpinBox(value=0, int=True, step=1)
        self.basis_selection = pg.SpinBox(value=0, int=True, step=1)

        # Lookup table controls
        self.lut_control = None
        self.lut_control_button = QPushButton("Open LUT controls")
        self.lut_list = [(-np.pi, 0), (np.pi, 255)]

        self.position_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(2, 2), (0, 2), (-2, 2)],
            title="Position Zernike Controller")
        self.slm_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(0, 0), (2, 2), (0, 2), (-2, 2)],
            title="SLM Zernike Controller")

        position_zernike_scroll_area.setWidget(
            self.position_zernike_controller)
        position_zernike_scroll_area.setWidgetResizable(True)
        slm_zernike_scroll_area.setWidget(self.slm_zernike_controller)
        slm_zernike_scroll_area.setWidgetResizable(True)

        for i, screen in enumerate(screens):
            screen_selector.addItem("Screen {}".format(i))

        self.plot = FullScreenPlot(slm_size, slm_size)

        self.slm_window = SLMDisplay(window_title,
                                     screens[screen_selector.currentIndex()],
                                     slm_size)

        screen_selector.currentIndexChanged.connect(
            lambda _: self.slm_window.set_screen(self.screens[screen_selector.
                                                              currentIndex()]))

        self.circle_inner_radius.sigValueChanged.connect(self.update_image)
        self.circle_outer_radius.sigValueChanged.connect(self.update_image)
        self.rotation.sigValueChanged.connect(self.update_image)
        self.slice_spacing.sigValueChanged.connect(self.update_image)
        self.dim.sigValueChanged.connect(self.update_image)
        self.mub_selection.sigValueChanged.connect(self.update_image)
        self.basis_selection.sigValueChanged.connect(self.update_image)
        self.position_zernike_controller.value_changed.connect(
            self.update_image)
        self.slm_zernike_controller.value_changed.connect(self.update_image)
        self.diffraction_grating.value_changed.connect(self.update_image)
        self.position.value_changed.connect(self.update_image)
        self.position.value_changed.connect(self.change_zernike_position)
        self.lut_control_button.clicked.connect(self.open_lut_control)

        layout.addWidget(QLabel("Display on:"), 0, 1)
        layout.addWidget(screen_selector, 0, 2)
        layout.addWidget(self.diffraction_grating, 0, 3)
        layout.addWidget(self.plot, 1, 3, 10, 1)
        layout.addWidget(QLabel("Circle inner radius:"), 1, 0, 1, 1)
        layout.addWidget(self.circle_inner_radius, 1, 1, 1, 1)
        layout.addWidget(QLabel("Circle outer radius:"), 2, 0, 1, 1)
        layout.addWidget(self.circle_outer_radius, 2, 1, 1, 1)
        layout.addWidget(QLabel("Slice spacing:"), 3, 0)
        layout.addWidget(self.slice_spacing, 3, 1)
        layout.addWidget(QLabel("Rotation:"), 4, 0)
        layout.addWidget(self.rotation, 4, 1)
        layout.addWidget(QLabel("Dimension:"), 5, 0, 1, 1)
        layout.addWidget(self.dim, 5, 1, 1, 1)
        layout.addWidget(QLabel("MUB:"), 6, 0, 1, 1)
        layout.addWidget(self.mub_selection, 6, 1, 1, 1)
        layout.addWidget(QLabel("Basis:"), 7, 0, 1, 1)
        layout.addWidget(self.basis_selection, 7, 1, 1, 1)
        layout.addWidget(self.lut_control_button, 8, 0, 1, 1)
        layout.addWidget(self.position, 8, 1, 1, 1)
        layout.addWidget(position_zernike_scroll_area, 9, 0, 1, 2)
        layout.addWidget(slm_zernike_scroll_area, 10, 0, 1, 2)

        self.setLayout(layout)
        self.update_image()

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

    def change_zernike_position(self):
        x, y = self.position.get_values()
        self.position_zernike_controller.change_position(
            self.x - x, self.y - y)

    def update_image(self):
        '''Update the image displayed on the oam plot and the
        gui plot
        '''
        diff_x, diff_y = self.diffraction_grating.get_values()
        position_zernike_image = self.position_zernike_controller.get_pattern()
        slm_zernike_image = self.slm_zernike_controller.get_pattern()
        x, y = self.position.get_values()
        pixel_image = pizza_field(
            basis(self.dim.value(), self.mub_selection.value(),
                  self.basis_selection.value()), self.x, self.y,
            self.circle_inner_radius.value(), self.circle_outer_radius.value(),
            (x, y), self.slice_spacing.value(),
            self.rotation.value()) * np.exp(
                1j * (diff_x * self.x + diff_y * self.y))
        if self.overlay is None:
            new_image = np.angle(slm_zernike_image * position_zernike_image *
                                 pixel_image) * np.abs(pixel_image)
        else:
            new_image = np.angle(
                slm_zernike_image * position_zernike_image * pixel_image *
                self.overlay) * np.abs(pixel_image)
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
            "position_zernike_controller":
            self.position_zernike_controller.get_values(),
            "pixel_radius":
            self.pixel_radius.value(),
            "circle_radius":
            self.circle_radius.value(),
            "dim":
            self.dim.value(),
            "mub_selection":
            self.mub_selection.value(),
            "basis_selection":
            self.basis_selection.value(),
            "slm_zernike_controller":
            self.slm_zernike_controller.get_values(),
            "diffraction_grating":
            self.diffraction_grating.get_values(),
            "position":
            self.position.get_values(),
            "lut_list":
            self.lut_list,
            "overlay":
            self.overlay,
        }

    def set_values(self, *args, **kwargs):
        '''Set the values of the SLM display from a set of args and kwargs
        Expects values for:
        position_zernike_controller,
        slm_zernike_controller,
        position,
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


class PixelEntanglementController(QWidget):
    '''Controls for pixel entanglement
    '''
    def __init__(self, window_title, screens, slm_size, flip=False):
        super().__init__()
        self.screens = screens

        layout = QGridLayout()
        if flip:
            self.x, self.y = np.mgrid[1:-1:(slm_size[0] *
                                            1j), -1:1:(slm_size[1] * 1j)]
        else:
            self.x, self.y = np.mgrid[-1:1:(slm_size[0] *
                                            1j), -1:1:(slm_size[1] * 1j)]
        self.slm_size = slm_size

        self.overlay = None

        screen_selector = QComboBox()
        position_zernike_scroll_area = QScrollArea()
        slm_zernike_scroll_area = QScrollArea()

        # Pixel pattern controls
        self.position = XYController("Pixel Centre")
        self.diffraction_grating = XYController("Diffraction Grating")
        self.pixel_radius = pg.SpinBox(value=1)
        self.circle_radius = pg.SpinBox(value=1)
        self.dim = pg.SpinBox(value=2, int=True, step=1, bounds=(2, None))
        self.mub_selection = pg.SpinBox(value=0, int=True, step=1)
        self.basis_selection = pg.SpinBox(value=0, int=True, step=1)

        # Lookup table controls
        self.lut_control = None
        self.lut_control_button = QPushButton("Open LUT controls")
        self.lut_list = [(-np.pi, 0), (np.pi, 255)]

        self.position_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(2, 2), (0, 2), (-2, 2)],
            title="Position Zernike Controller")
        self.slm_zernike_controller = ZernikeSet(
            self.x,
            self.y, [(2, 2), (0, 2), (-2, 2)],
            title="SLM Zernike Controller")

        position_zernike_scroll_area.setWidget(
            self.position_zernike_controller)
        position_zernike_scroll_area.setWidgetResizable(True)
        slm_zernike_scroll_area.setWidget(self.slm_zernike_controller)
        slm_zernike_scroll_area.setWidgetResizable(True)

        for i, screen in enumerate(screens):
            screen_selector.addItem("Screen {}".format(i))

        self.plot = FullScreenPlot(slm_size, slm_size)

        self.slm_window = SLMDisplay(window_title,
                                     screens[screen_selector.currentIndex()],
                                     slm_size)

        screen_selector.currentIndexChanged.connect(
            lambda _: self.slm_window.set_screen(self.screens[screen_selector.
                                                              currentIndex()]))

        self.pixel_radius.sigValueChanged.connect(self.update_image)
        self.circle_radius.sigValueChanged.connect(self.update_image)
        self.dim.sigValueChanged.connect(self.update_image)
        self.mub_selection.sigValueChanged.connect(self.update_image)
        self.basis_selection.sigValueChanged.connect(self.update_image)
        self.position_zernike_controller.value_changed.connect(
            self.update_image)
        self.slm_zernike_controller.value_changed.connect(self.update_image)
        self.diffraction_grating.value_changed.connect(self.update_image)
        self.position.value_changed.connect(self.update_image)
        self.position.value_changed.connect(self.change_zernike_position)
        self.lut_control_button.clicked.connect(self.open_lut_control)

        layout.addWidget(QLabel("Display on:"), 0, 1)
        layout.addWidget(screen_selector, 0, 2)
        layout.addWidget(self.diffraction_grating, 0, 3)
        layout.addWidget(self.plot, 1, 3, 8, 1)
        layout.addWidget(QLabel("Pixel radius:"), 1, 0, 1, 1)
        layout.addWidget(self.pixel_radius, 1, 1, 1, 1)
        layout.addWidget(QLabel("Circle radius:"), 2, 0, 1, 1)
        layout.addWidget(self.circle_radius, 2, 1, 1, 1)
        layout.addWidget(QLabel("Dimension:"), 3, 0, 1, 1)
        layout.addWidget(self.dim, 3, 1, 1, 1)
        layout.addWidget(QLabel("MUB:"), 4, 0, 1, 1)
        layout.addWidget(self.mub_selection, 4, 1, 1, 1)
        layout.addWidget(QLabel("Basis:"), 5, 0, 1, 1)
        layout.addWidget(self.basis_selection, 5, 1, 1, 1)
        layout.addWidget(self.lut_control_button, 6, 0, 1, 1)
        layout.addWidget(self.position, 6, 1, 1, 1)
        layout.addWidget(position_zernike_scroll_area, 7, 0, 1, 2)
        layout.addWidget(slm_zernike_scroll_area, 8, 0, 1, 2)

        self.setLayout(layout)
        self.update_image()

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

    def change_zernike_position(self):
        x, y = self.position.get_values()
        self.position_zernike_controller.change_position(
            self.x - x, self.y - y)

    def update_image(self):
        '''Update the image displayed on the oam plot and the
        gui plot
        '''
        diff_x, diff_y = self.diffraction_grating.get_values()
        position_zernike_image = self.position_zernike_controller.get_pattern()
        slm_zernike_image = self.slm_zernike_controller.get_pattern()
        x, y = self.position.get_values()
        pixel_image = complex_field(
            basis(self.dim.value(), self.mub_selection.value(),
                  self.basis_selection.value()), self.x, self.y,
            self.pixel_radius.value(), self.circle_radius.value(),
            (x, y)) * np.exp(1j * (diff_x * self.x + diff_y * self.y))
        if self.overlay is None:
            new_image = np.angle(slm_zernike_image * position_zernike_image *
                                 pixel_image) * np.abs(pixel_image)
        else:
            new_image = np.angle(
                slm_zernike_image * position_zernike_image * pixel_image *
                self.overlay) * np.abs(pixel_image)
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
            "position_zernike_controller":
            self.position_zernike_controller.get_values(),
            "pixel_radius":
            self.pixel_radius.value(),
            "circle_radius":
            self.circle_radius.value(),
            "dim":
            self.dim.value(),
            "mub_selection":
            self.mub_selection.value(),
            "basis_selection":
            self.basis_selection.value(),
            "slm_zernike_controller":
            self.slm_zernike_controller.get_values(),
            "diffraction_grating":
            self.diffraction_grating.get_values(),
            "position":
            self.position.get_values(),
            "lut_list":
            self.lut_list,
            "overlay":
            self.overlay,
        }

    def set_values(self, *args, **kwargs):
        '''Set the values of the SLM display from a set of args and kwargs
        Expects values for:
        position_zernike_controller,
        slm_zernike_controller,
        position,
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


class MultiPixelController(QWidget):
    '''Controls for pixel entanglement on two slms
    '''
    def __init__(self, screens, slm_sizes):
        super().__init__()
        self.layout = QGridLayout()
        save_button = QPushButton("Save values")
        load_button = QPushButton("Load values")

        self.slms = [
            PizzaEntanglementController("SLM {}".format(i),
                                        screens,
                                        size,
                                        flip=bool(i))
            for i, size in enumerate(slm_sizes)
        ]

        self.layout.addWidget(save_button, 0, 0)
        self.layout.addWidget(load_button, 0, 1)
        for i, slm in enumerate(self.slms):
            self.layout.addWidget(slm, i + 1, 0, 1, 2)

        self.setLayout(self.layout)

        save_button.clicked.connect(self.save_file)
        load_button.clicked.connect(self.open_file)

    def closeEvent(self, event):
        for slm in self.slms:
            slm.close_slm_window()

    def get_values(self):
        '''Returns a list of slm settings
        ready and prepared to be tucked in a json
        '''
        return [slm_screen.get_values() for slm_screen in self.slms]

    def set_values(self, slm_list):
        '''Accepts a list of slm settings
        '''
        for i, slm in enumerate(slm_list):
            if i < len(self.slms):
                self.slms[i].set_values(slm)

    def save_values_to_json_file(self, filename):
        '''Save the values to a given filename
        doesn't catch any errors
        '''
        values = self.get_values()
        with open(filename, 'w') as f:
            json.dump(values, f)

    def read_values_from_json_file(self, filename):
        '''Read the values from a given filename
        doesn't catch any errors
        '''
        with open(filename, 'r') as f:
            self.set_values(json.load(f))

    def try_read_values_from_json_file(self, filename):
        '''wraps reading values in a try except thing,
        so it doesn't fail when reading a naughty file
        '''
        try:
            self.read_values_from_json_file(filename)
        except:
            pass

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "")
        if filename:
            self.try_read_values_from_json_file(filename)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "")
        if filename:
            self.save_values_to_json_file(filename)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = MultiPixelController(app.screens(), [(512, 512), (512, 512)])
    # w = PizzaEntanglementController("hi", app.screens(), (512, 512))
    w.show()
    app.exec()
