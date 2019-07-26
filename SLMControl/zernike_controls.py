from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg
import numpy as np


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
    indices = (0, 0)

    def __init__(self, indices, value=0):
        super().__init__()
        self.indices = indices
        layout = QVBoxLayout()

        self.coefficient = pg.SpinBox(value=value)
        self.coefficient.sigValueChanged.connect(self.value_changed.emit)

        layout.addWidget(self.coefficient)
        layout.addWidget(QLabel("({}, {})".format(indices[0], indices[1])))

        self.setLayout(layout)


class ZernikeSet(QWidget):
    '''A controller for the first n Zernike polynomials (default is 6)
    '''
    value_dict = {}

    value_changed = pyqtSignal()

    def __init__(self, X, Y, poly_set=None, poly_limit=6):
        '''If poly_set is not None, display only the given polynomials.
        poly_set should be of type: [(m, n)] - a list of m, n values
        Otherwise just generate up to poly_limit controls

        X, Y are the x and y positions to generate the set for,
        made from numpy's mgrid function
        '''
        super().__init__()
        layout = QHBoxLayout()

        if poly_set is not None:
            self.controls = [ZernikeControl(index) for index in poly_set]
        else:
            self.controls = [
                ZernikeControl(index) for index in coefficients(poly_limit)
            ]

        for c in self.controls:
            self.value_dict[c.indices] = zernike_cartesian(*c.indices)(X, Y)
            c.value_changed.connect(self.value_changed.emit)
            layout.addWidget(c)

        self.setLayout(layout)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    x = np.linspace(-1, 1, 100)
    y = np.linspace(-1, 1, 100)
    X, Y = np.meshgrid(x, y)
    a = ZernikeSet(X, Y)
    a.show()
    app.exec()
