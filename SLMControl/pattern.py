import numpy as np
from numba import njit
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg


@njit()
def point_in_slice(x, y, r, R, theta_1, theta_2):
    '''Check if the given point is inside the given pizza slice
    The pizza slice is defined by two angles (theta_1, theta_2),
    which the angle of the point must be inside.
    r gives a limit to the inside of the circle and
    R gives a limit to the outside of the circle
    '''
    theta = (np.arctan2(y, x)) % (np.pi * 2)
    mag = x**2 + y**2
    return (theta_1 <= theta) & (theta < theta_2) & (r**2 < mag) & (mag < R**2)


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


class PizzaPattern(QWidget):
    """Class which gives a widget for controlling 'pizza slice' patterns
    """

    value_changed = pyqtSignal()
    name = "Pizza Pattern"

    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self.circle_inner_radius = pg.SpinBox(value=0)
        self.circle_outer_radius = pg.SpinBox(value=1)
        self.slice_fraction = pg.SpinBox(value=1)
        self.circle_fraction = pg.SpinBox(value=1)

        self.circle_inner_radius.sigValueChanged.connect(
            self.value_changed.emit)
        self.circle_outer_radius.sigValueChanged.connect(
            self.value_changed.emit)
        self.slice_fraction.sigValueChanged.connect(self.value_changed.emit)
        self.circle_fraction.sigValueChanged.connect(self.value_changed.emit)

        self.layout.addWidget(QLabel("Circle inner radius:"), 0, 0)
        self.layout.addWidget(self.circle_inner_radius, 0, 1)
        self.layout.addWidget(QLabel("Circle outer radius:"), 1, 0)
        self.layout.addWidget(self.circle_outer_radius, 1, 1)
        self.layout.addWidget(QLabel("Slice fraction:"), 2, 0)
        self.layout.addWidget(self.slice_fraction, 2, 1)
        self.layout.addWidget(QLabel("Circle fraction:"), 3, 0)
        self.layout.addWidget(self.circle_fraction, 3, 1)

        self.setLayout(self.layout)

    def pizza_pattern(X,
                      Y,
                      components,
                      circle_inner_radius=0,
                      circle_outer_radius=1,
                      slice_fraction=1,
                      circle_fraction=1):
        """Draw a pizza pattern over X and Y

        Keyword arguments:
        circle_inner_radius -- The inner radius that the circle making up the pizza has
        circle_outer_radius -- The outer radius of the circle
        clice_fraction -- The amount of space the individual slices of pizza actually take up
        circle_fraction -- The amount of a whole circle that is filled by the pizza

        returns a complex array with shape X.shape or Y.shape
        """
        dim = len(components)
        rotational_span = 2 * np.pi * circle_fraction
        slice_spacing_rads = rotational_span * (1 - slice_fraction) / (2 * dim)
        lower_angle = np.linspace(0, rotational_span - (rotational_span / dim),
                                  dim) + slice_spacing_rads

        upper_angle = np.linspace(rotational_span / dim, rotational_span,
                                  dim) - slice_spacing_rads

        field = np.zeros(X.shape, dtype=np.complex128)
        if dim > 1:
            for i, p in enumerate(components):
                field += p * point_in_slice(X, Y, circle_inner_radius,
                                            circle_outer_radius,
                                            lower_angle[i], upper_angle[i])
        else:
            field += components[0] * point_in_slice(
                X, Y, circle_inner_radius, circle_outer_radius, lower_angle[i],
                upper_angle[i])

        return field

    def get_pattern(self, X, Y, components):
        """Get the pattern described by this controller.
        Extracts the values from the sliders
        """
        return PizzaPattern.pizza_pattern(
            X,
            Y,
            components,
            circle_inner_radius=self.circle_inner_radius.value(),
            circle_outer_radius=self.circle_outer_radius.value(),
            slice_fraction=self.slice_fraction.value(),
            circle_fraction=self.circle_fraction.value())


class OAMPattern(QWidget):
    """Class which gives a widget for controlling 'OAM' patterns
    """

    value_changed = pyqtSignal()
    name = "OAM Pattern"

    def __init__(self):
        super().__init__()

    def oam_pattern(X, Y, components):
        """Draw an exp(ilθ) pattern over X and Y

        returns a complex array with shape X.shape or Y.shape
        """
        dim = len(components)
        ang_mom_limit = (dim - 1) * (1 / 2)

        amplitude = np.abs(components)
        phase = np.angle(components)
        angular_momentum = np.linspace(-ang_mom_limit, ang_mom_limit, dim)
        theta = np.arctan2(Y, X)
        return np.sum([
            amplitude[i] * np.exp(1j * (l * theta + phase[i]))
            for i, l in enumerate(angular_momentum)
        ],
                      axis=0)

    def get_pattern(self, X, Y, components):
        """Get the pattern described by this controller.
        This just returns the oam_pattern function because
        the OAM has no controls
        """
        return OAMPattern.oam_pattern(X, Y, components)


def PatternContainer(QWidget):
    """Container for all the different types of patterns
    """
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()

        patterns = [PizzaPattern, OAMPattern]

        self.setLayout(self.layout)


def draw_plot():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 1)
    X, Y = np.mgrid[-1:1:512j, -1:1:512j]
    rot = 2 * np.pi
    rotX, rotY = np.cos(rot) * X + np.sin(rot) * Y, -np.sin(rot) * X + np.cos(
        rot) * Y
    p = oam_pattern(rotX, rotY, [1, 1j, 1j, -1])
    ax.imshow(np.angle(p))
    plt.show()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = PizzaPattern()
    w.show()
    app.exec()
