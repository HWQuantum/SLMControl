import numpy as np
import matplotlib.pyplot as plt
from numba import njit
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QComboBox, QGroupBox, QScrollArea, QVBoxLayout, QFormLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import pyqtgraph as pg

from zernike_controls import ZernikeSet


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
                X, Y, circle_inner_radius, circle_outer_radius, lower_angle[0],
                upper_angle[0])

        return field

    def get_values(self):
        return {
            "circle_innder_radius": self.circle_inner_radius.value(),
            "circle_outer_radius": self.circle_outer_radius.value(),
            "slice_fraction": self.slice_fraction.value(),
            "circle_fraction": self.circle_fraction.value(),
        }

    def set_values(self, values):
        self.blockSignals(True)
        for k in [
                "circle_inner_radius", "circle_outer_radius",
                "slice_fraction", "circle_fraction"
        ]:
            try:
                getattr(self, k).setValue(values[k])
            except KeyError:
                pass
        self.blockSignals(False)
        self.value_changed.emit()

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
        if dim % 2 != 0:
            # if dimension is odd, then we want to make it so the 0 component
            # corresponds to the l=0 mode
            # we do this by rolling the array
            angular_momentum = np.roll(
                np.linspace(-ang_mom_limit, ang_mom_limit, dim),
                int(-((dim - 1) / 2)))
        else:
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

    def get_values(self):
        return None

    def set_values(self, values):
        pass


class XYController(QGroupBox):
    '''Define a control for x and y position
    Has some functions for getting and setting the value as a 
    complex number
    '''
    value_changed = pyqtSignal()

    def __init__(self, name, x_name='x:', y_name='y:'):
        super().__init__()
        self.setTitle(name)
        self.layout = QGridLayout()
        self.x = pg.SpinBox()
        self.y = pg.SpinBox()
        self.x.sigValueChanged.connect(self.value_changed.emit)
        self.y.sigValueChanged.connect(self.value_changed.emit)
        self.layout.addWidget(QLabel(x_name), 0, 0)
        self.layout.addWidget(QLabel(y_name), 0, 5)
        self.layout.addWidget(self.x, 0, 1, 1, 4)
        self.layout.addWidget(self.y, 0, 6, 1, 4)
        self.setLayout(self.layout)

    def get_values(self):
        '''Get the x and y values and return in a tuple
        '''
        return (self.x.value(), self.y.value())

    def get_values_complex(self):
        '''Get the values as a complex number
        '''
        return self.x.value() + 1j * self.y.value()

    def set_values_complex(self, c):
        """Set the values from a complex number
        """
        self.blockSignals(True)
        self.x.setValue(c.real)
        self.y.setValue(c.imag)
        self.blockSignals(False)
        self.value_changed.emit()

    def get_values_complex_polar(self):
        '''Get the values as a complex number with polar decomposition
        '''
        return self.x.value() * np.exp(1j * self.y.value())

    def set_values_complex_polar(self, c):
        """Set the values from a complex number with polar decomposition
        """
        self.blockSignals(True)
        self.x.setValue(np.abs(c))
        self.y.setValue(np.angle(c))
        self.blockSignals(False)
        self.value_changed.emit()

    def set_values(self, *args, **kwargs):
        """Set the values from some dictionaries
        """
        self.blockSignals(True)
        for arg in args:
            if type(arg) == dict:
                for key, value in arg.items():
                    if key == 'x':
                        self.x.setValue(value)
                    elif key == 'y':
                        self.y.setValue(value)
            elif type(arg) == tuple or type(arg) == list:
                self.x.setValue(arg[0])
                self.y.setValue(arg[1])

        for key, value in kwargs.items():
            if key == 'x':
                self.x.setValue(value)
            elif key == 'y':
                self.y.setValue(value)
        self.blockSignals(False)
        self.value_changed.emit()


class Vector(QWidget):
    """A QWidget controller which allows control over the components of a vector
    The components are in polar form: r, θ; v_j = r_j*exp(iθ_j)
    """

    value_changed = pyqtSignal()

    def __init__(self, dim=0):
        super().__init__()
        self.layout = QFormLayout()
        self.components = []

        for _ in range(dim):
            self.add_component(0)

        self.setLayout(self.layout)

    def remove_end_component(self):
        """Remove the widget at the end of the components list
        """
        if len(self.components) > 0:
            self.layout.removeRow(self.components.pop())

    def add_component(self, c=0):
        """Add a component to the end of the components list
        Optionally, you can pass in a complex number to set it to
        """
        new_component = XYController("v_{}".format(len(self.components) + 1),
                                     "R:", "θ:")
        new_component.set_values_complex_polar(c)
        new_component.value_changed.connect(self.value_changed.emit)

        self.layout.addRow(new_component)
        self.components.append(new_component)

    @pyqtSlot(int)
    def set_dimension(self, dim):
        """Set the dimension of the vector
        """
        self.blockSignals(True)
        if dim > len(self.components):
            for _ in range(dim - len(self.components)):
                self.add_component()
        else:
            for _ in range(len(self.components) - dim):
                self.remove_end_component()

        self.blockSignals(False)
        self.value_changed.emit()

    def set_to_vector(self, v):
        """Set the controllers to the given vector, adding and removing
        controllers as needed
        v is a vector of complex numbers
        """
        dim = len(v)
        self.blockSignals(True)

        if dim <= len(self.components):
            for _ in range(len(self.components) - dim):
                self.remove_end_component()

            for i, component in enumerate(self.components):
                component.set_values_complex_polar(v[i])
        else:
            for i, c in enumerate(v[:len(self.components)]):
                self.components[i].set_value_complex_polar(c)
            for c in v[len(self.components):]:
                self.add_component(c)

        self.blockSignals(False)
        self.value_changed.emit()

    def get_vector(self):
        """Get the vector contained in this controller
        """
        return np.array(
            [c.get_values_complex_polar() for c in self.components])


class MUBController(QWidget):
    """A controller for MUBs
    Contains spinboxes for mub selection and basis selection.

    There's not a "get_vector" function in here because the MUBController
    doesn't know about the dimension that's wanted, so to get the vector,
    you need to be in the parent widget.
    """

    value_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()

        self.mub = pg.SpinBox(int=True, step=1)
        self.basis = pg.SpinBox(int=True, step=1)

        self.mub.sigValueChanged.connect(self.value_changed.emit)
        self.basis.sigValueChanged.connect(self.value_changed.emit)

        self.layout.addWidget(QLabel("MUB:"), 0, 0)
        self.layout.addWidget(self.mub, 0, 1)
        self.layout.addWidget(QLabel("basis:"), 1, 0)
        self.layout.addWidget(self.basis, 1, 1)

        self.setLayout(self.layout)

    def get_values(self):
        """Get the tuple (mub, basis)
        """
        return (self.mub.value(), self.basis.value())

    def set_values(self, mub, basis):
        """Set the values from a MUB and a basis
        """
        self.blockSignals(True)
        self.mub.setValue(mub)
        self.basis.setValue(basis)
        self.blockSignals(False)
        self.value_changed.emit()


class PatternContainer(QWidget):
    """Container for all the different types of patterns
    """

    value_changed = pyqtSignal()

    def __init__(self, base_x, base_y):
        """base_X and base_Y are the base ranges to calculate the 
        complex field over. They're created with the numpy mgrid function
        (or meshgrid if you're a numpty)
        """
        super().__init__()

        # Add all the member variables
        self.base_x, self.base_y = base_x, base_y
        self.x, self.y = base_x, base_y

        self.layout = QGridLayout()

        self.patterns = [PizzaPattern(), OAMPattern()]
        self.pattern_selector = QComboBox()
        self.vector_selector = QComboBox()
        self.pattern_control_scroll_area = QScrollArea()
        self.vector_control_scroll_area = QScrollArea()
        self.slm_zernike_scroll_area = QScrollArea()
        self.position_zernike_scroll_area = QScrollArea()
        self.slm_zernike = ZernikeSet(self.base_x,
                                      self.base_y, [(-2, 2), (0, 2), (2, 2)],
                                      title="SLM Zernike Controls")
        self.position_zernike = ZernikeSet(self.x,
                                           self.y, [(-2, 2), (0, 2), (2, 2)],
                                           title="Position Zernike Controls")
        self.position = XYController("Position")
        self.scaling = XYController("Scaling")
        self.grating = XYController("Diffraction Grating")
        self.dimension = pg.SpinBox(int=True,
                                    step=1,
                                    value=2,
                                    bounds=(1, None))
        self.rotation = pg.SpinBox()
        self.vector_component_control = Vector(self.dimension.value())
        self.vector_mub_control = MUBController()

        # Add settings and setup n that

        self.scaling.set_values((1, 1))

        self.pattern_control_scroll_area.setWidgetResizable(True)
        self.vector_control_scroll_area.setWidgetResizable(True)
        self.slm_zernike_scroll_area.setWidgetResizable(True)
        self.position_zernike_scroll_area.setWidgetResizable(True)

        self.pattern_selector.addItems([p.name for p in self.patterns])
        self.pattern_control_scroll_area.setWidget(
            self.patterns[self.pattern_selector.currentIndex()])
        self.vector_selector.addItems(["MUB controls", "vector controls"])
        self.slm_zernike_scroll_area.setWidget(self.slm_zernike)
        self.position_zernike_scroll_area.setWidget(self.position_zernike)

        # Connect up signals

        self.pattern_selector.currentIndexChanged.connect(
            self.change_pattern_widget)
        self.vector_selector.currentIndexChanged.connect(
            self.change_vector_widget)
        self.dimension.sigValueChanged.connect(self.set_dimension)
        self.rotation.sigValueChanged.connect(self.change_transform)
        self.position.value_changed.connect(self.change_transform)
        self.scaling.value_changed.connect(self.change_transform)
        self.grating.value_changed.connect(self.value_changed.emit)
        for pattern in self.patterns:
            pattern.value_changed.connect(self.value_changed.emit)

        self.slm_zernike.value_changed.connect(self.value_changed.emit)
        self.position_zernike.value_changed.connect(self.value_changed.emit)
        self.vector_mub_control.value_changed.connect(self.value_changed.emit)
        self.vector_component_control.value_changed.connect(
            self.value_changed.emit)
        # Add widgets to layout

        self.layout.addWidget(self.pattern_selector, 0, 0, 1, 2)
        self.layout.addWidget(self.pattern_control_scroll_area, 1, 0, 1, 2)
        self.layout.addWidget(self.vector_selector, 0, 2, 1, 2)
        self.layout.addWidget(self.vector_control_scroll_area, 1, 2, 1, 2)
        self.layout.addWidget(QLabel("Dimension:"), 2, 2)
        self.layout.addWidget(self.dimension, 2, 3)
        self.layout.addWidget(QLabel("Rotation:"), 2, 0)
        self.layout.addWidget(self.rotation, 2, 1)
        self.layout.addWidget(self.grating, 3, 0, 1, 2)
        self.layout.addWidget(self.position, 3, 2, 1, 2)
        self.layout.addWidget(self.slm_zernike_scroll_area, 4, 0, 1, 2)
        self.layout.addWidget(self.position_zernike_scroll_area, 5, 0, 1, 2)
        self.layout.addWidget(self.scaling, 4, 2, 1, 2)

        self.setLayout(self.layout)

        self.change_vector_widget(0)
        self.previous_pos = self.position.get_values()

    @pyqtSlot(int)
    def change_pattern_widget(self, index):
        """Change the scroll widget in self.pattern_control_scroll_area
        to the given index
        """
        self.pattern_control_scroll_area.takeWidget()
        self.pattern_control_scroll_area.setWidget(self.patterns[index])

        self.value_changed.emit()

    @pyqtSlot(int)
    def change_vector_widget(self, index):
        """Change the vector selection widget to either MUBs or components
        """
        self.blockSignals(True)
        if index == 0:
            self.vector_control_scroll_area.takeWidget()
            self.vector_control_scroll_area.setWidget(self.vector_mub_control)
        if index == 1:
            self.vector_control_scroll_area.takeWidget()
            self.vector_control_scroll_area.setWidget(
                self.vector_component_control)
            self.vector_component_control.set_to_vector(
                basis(self.dimension.value(),
                      *self.vector_mub_control.get_values()))
        self.blockSignals(False)

        self.value_changed.emit()

    def set_pattern_by_name(self, name: str):
        """Set the current pattern by the name defined in the pattern class
        The name is pattern.name
        """
        for index, pattern in enumerate(self.patterns):
            if pattern.name == name:
                self.change_pattern_widget(index)
                break

    def set_dimension(self):
        """Set the dimension of the vector components widget
        """
        self.vector_component_control.set_dimension(self.dimension.value())

    def change_transform(self):
        """Change the transform of the coordinates
        This looks at the rotation, the scaling and the position
        """
        new_position = self.position.get_values()
        scale = self.scaling.get_values()
        rot = self.rotation.value()

        self.blockSignals(True)

        translate_scale_x = (self.base_x + new_position[0]) * scale[0]
        translate_scale_y = (self.base_y + new_position[1]) * scale[1]

        self.x = np.cos(rot) * translate_scale_x + np.sin(
            rot) * translate_scale_y
        self.y = -np.sin(rot) * translate_scale_x + np.cos(
            rot) * translate_scale_y

        if new_position != self.previous_pos:
            self.position_zernike.change_position(self.x, self.y)

        self.previous_pos = new_position

        self.blockSignals(False)

        self.value_changed.emit()

    def get_vector_components(self):
        """Get the vector components defined by this widget
        """
        if self.vector_selector.currentIndex() == 0:
            return basis(self.dimension.value(),
                         *self.vector_mub_control.get_values())
        else:
            return self.vector_component_control.get_vector()

    def get_pattern(self):
        """Get the phase pattern defined by this controller
        """
        d_x, d_y = self.grating.get_values()
        position_zernike_image = self.position_zernike.get_pattern()
        slm_zernike_image = self.slm_zernike.get_pattern()
        pattern_image = self.pattern_control_scroll_area.widget().get_pattern(
            self.x, self.y, self.get_vector_components())

        return pattern_image * np.exp(
            1j *
            (d_x * self.base_x +
             d_y * self.base_y)) * position_zernike_image * slm_zernike_image

    def get_values(self):
        """Get the contained values
        """
        return {
            "pattern_selector":
            self.pattern_selector.currentIndex(),
            "vector_selector":
            self.vector_selector.currentIndex(),
            "vector_control":
            self.vector_mub_control.get_values()
            if self.vector_selector.currentIndex() == 0 else
            [str(c) for c in self.vector_component_control.get_vector()],
            "dimension":
            self.dimension.value(),
            "rotation":
            self.rotation.value(),
            "grating":
            self.grating.get_values(),
            "position":
            self.position.get_values(),
            "scaling":
            self.scaling.get_values(),
            "slm_zernike":
            self.slm_zernike.get_values(),
            "position_zernike":
            self.position_zernike.get_values(),
            "pattern_control":
            self.pattern_control_scroll_area.widget().get_values(),
        }

    def set_values(self, values):
        """Set the values
        """

        self.blockSignals(True)
        try:
            self.pattern_selector.setCurrentIndex(values["pattern_selector"])
            self.patterns[values["pattern_selector"]].set_values(
                values["pattern_control"])
        except KeyError:
            pass

        try:
            self.vector_selector.setCurrentIndex(values["vector_selector"])
            if values["vector_selector"] == 0:
                self.vector_mub_control.set_values(*values["vector_control"])
            else:
                self.vector_component_control.set_to_vector(
                    [complex(c) for c in values["vector_control"]])
        except KeyError:
            pass

        for c in ["dimension", "rotation"]:
            try:
                getattr(self, c).setValue(values[c])
            except KeyError:
                pass

        for c in [
                "grating", "position", "scaling", "slm_zernike",
                "position_zernike"
        ]:
            try:
                getattr(self, c).set_values(values[c])
            except KeyError:
                pass

        self.blockSignals(False)
        self.value_changed.emit()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    x, y = np.mgrid[-1:1:512j, -1:1:512j]
    w = PatternContainer(x, y)
    w.show()
    app.exec()
