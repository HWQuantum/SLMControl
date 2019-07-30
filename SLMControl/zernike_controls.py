from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg
import numpy as np
from ast import literal_eval as make_tuple


def radial_coeff(m, n, l):
    '''Radial coefficient in the sum for the radial part of the Zernike polynomial
    '''
    if (n - m) % 2 == 0:
        return ((np.power(-1, l) * np.math.factorial(n - l)) /
                (np.math.factorial(l) * np.math.factorial(0.5 * (n + m) - l) *
                 np.math.factorial(0.5 * (n - m) - l)))
    else:
        return 0


def radial(m, n):
    '''Radial part of the Zernike polynomial
    '''
    return [(radial_coeff(m, n, l), n - 2 * l)
            for l in range(0,
                           int(round((n - m) / 2)) + 1)]


def coefficients(n):
    '''Generate the first n non-zero Zernike coefficient indices
    ie: (0, 0), (-1, 1), (1, 1), (-2, 2), (0, 2), (2, 2), ...
    '''
    c = 0
    i, j = 0, 0
    while c < n:
        c += 1
        yield (i, j)
        if i == j:
            j += 1
            i = -j
        else:
            i += 2


def zernike_cartesian(m, n):
    '''Zernike polynomial in cartesian coordinates
    '''
    abs_m = np.abs(m)
    rs = [(i, j) for (i, j) in radial(abs_m, n) if i != 0]
    if m == 0:
        norm = np.sqrt(n + 1)
    else:
        norm = np.sqrt(2 * (n + 1))
    if m < 0:

        def poly(x, y):
            r = np.sqrt(x**2 + y**2)
            theta = np.arctan2(y, x)
            return norm * np.sum([i * np.power(r, j) for (i, j) in rs],
                                 axis=0) * np.sin(abs_m * theta)

        return poly
    else:

        def poly(x, y):
            r = np.sqrt(x**2 + y**2)
            theta = np.arctan2(y, x)
            return norm * np.sum([i * np.power(r, j) for (i, j) in rs],
                                 axis=0) * np.cos(abs_m * theta)

        return poly


class ZernikeControl(QWidget):
    '''A controller for a single zernike coefficient
    '''
    value_changed = pyqtSignal()

    def __init__(self, indices, value=0):
        super().__init__()
        self.indices = indices
        layout = QVBoxLayout()

        self.coefficient = pg.SpinBox(value=value)
        self.coefficient.sigValueChanged.connect(self.value_changed.emit)

        layout.addWidget(self.coefficient)
        layout.addWidget(QLabel("({}, {})".format(indices[0], indices[1])))

        self.setLayout(layout)

    def get_value(self):
        return self.coefficient.value()

    def set_value(self, value):
        self.coefficient.setValue(value)


class ZernikeSet(QGroupBox):
    '''A controller for the first n Zernike polynomials (default is 6)

    value_dict contains the zernike polynomial evaluated over the given X, Y
    (from numpy.mgrid) at the indices
    '''

    value_changed = pyqtSignal()

    def __init__(self, X, Y, poly_set=None, poly_limit=6):
        '''If poly_set is not None, display only the given polynomials.
        poly_set should be of type: [(m, n)] - a list of m, n values
        Otherwise just generate up to poly_limit controls

        X, Y are the x and y positions to generate the set for,
        made from numpy's mgrid function
        '''
        super().__init__()
        self.setTitle("Zernike Controls")
        self.layout = QHBoxLayout()
        self.value_dict = {}
        self.controls = {}

        if poly_set is not None:
            for indices in poly_set:
                self.controls[indices] = ZernikeControl(indices)
        else:
            for indices in coefficients(poly_limit):
                self.controls[indices] = ZernikeControl(indices)

        self.generate_polynomials(X, Y)

        self.setLayout(self.layout)

    def generate_polynomials(self, X, Y):
        '''Generate the polynomials over the given X and Ys
        '''
        for indices, control in self.controls.items():
            self.value_dict[indices] = zernike_cartesian(*indices)(X, Y)
            control.value_changed.connect(self.value_changed.emit)
            self.layout.addWidget(control)

    def get_values(self):
        '''Get the values contained and return a dictionary of
        {indices, value} with indices a string instead of a tuple
        '''
        value_dict = {}
        for i, c in self.controls.items():
            value_dict["({},{})".format(*i)] = c.get_value()

        return value_dict

    def set_values(self, *args):
        '''Set the Zernike values from given dictionaries, converting string
        indices into values
        '''
        for dictionary in args:
            for key, value in dictionary.items():
                if type(key) == str:
                    key = make_tuple(key)
                if key in self.controls.keys():
                    self.controls[key].set_value(value)

    def get_pattern(self):
        '''Get the value of the pattern Σe^{iaZ}
        '''
        return np.exp(1j * np.sum([
            c.coefficient.value() * self.value_dict[i]
            for i, c in self.controls.items()
        ],
                                  axis=0))

    def reset_coefficients(self):
        '''Reset all coefficients to 0
        '''
        for control in self.controls.values():
            control.setValue(0)
