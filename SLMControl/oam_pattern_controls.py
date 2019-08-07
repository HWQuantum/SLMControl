from PyQt5.QtWidgets import QWidget, QGroupBox, QGridLayout, QLabel, QPushButton, QFormLayout, QHBoxLayout, QSpacerItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import pyqtgraph as pg


class OAMControls(QWidget):
    '''Contains the controls for one OAM pattern
    the amplitude, the m, and the phase
    '''

    value_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.amplitude = pg.SpinBox(value=1)
        self.ang_mom = pg.SpinBox(int=True, step=1)
        self.phase = pg.SpinBox()

        self.amplitude.sigValueChanged.connect(self.value_changed.emit)
        self.ang_mom.sigValueChanged.connect(self.value_changed.emit)
        self.phase.sigValueChanged.connect(self.value_changed.emit)

        self.layout.addWidget(QLabel("Amplitude:"), 0, 0)
        self.layout.addWidget(self.amplitude, 0, 1, 1, 2)
        self.layout.addWidget(QLabel("Angular Momentum:"), 1, 0)
        self.layout.addWidget(self.ang_mom, 1, 1, 1, 2)
        self.layout.addWidget(QLabel("Phase:"), 2, 0)
        self.layout.addWidget(self.phase, 2, 1, 1, 2)
        self.setLayout(self.layout)

    def get_values(self):
        '''Get all of the values and return a dictionary containing them
        '''
        return {
            "amplitude": self.amplitude.value(),
            "ang_mom": self.ang_mom.value(),
            "phase": self.phase.value(),
        }

    def set_values(self, *args, **kwargs):
        '''Set the values from an args dictionary or kwargs
        '''
        for arg in args:
            for key, value in arg.items():
                if key == "amplitude":
                    self.amplitude.setValue(value)
                elif key == "ang_mom":
                    self.ang_mom.setValue(value)
                elif key == "phase":
                    self.phase.setValue(value)
        for key, value in kwargs.items():
            if key == "amplitude":
                self.amplitude.setValue(value)
            elif key == "ang_mom":
                self.ang_mom.setValue(value)
            elif key == "phase":
                self.phase.setValue(value)
        self.value_changed.emit()


class CloseWrapper(QGroupBox):
    close = pyqtSignal()

    def __init__(self, other_widget):
        super().__init__()
        self.wrapped = other_widget

        layout = QHBoxLayout()
        close = QPushButton("Close")

        close.clicked.connect(self.close.emit)

        layout.addWidget(self.wrapped, 6)
        layout.addWidget(close, 1)

        self.setLayout(layout)


class OAMControlSet(QWidget):
    value_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QFormLayout()
        self.setLayout(self.layout)

    @pyqtSlot()
    def add_new_oam_pattern(self, args=None):
        '''Add a new OAM pattern to the set
        args is optionally the set of values to put into the SLM control
        '''
        controller = OAMControls()
        if args is not None:
            controller.set_values(args)
        controller.value_changed.connect(self.value_changed.emit)

        wrapped_controller = CloseWrapper(controller)
        wrapped_controller.close.connect(
            lambda: self.remove_pattern(wrapped_controller))

        self.layout.addRow(wrapped_controller)
        self.value_changed.emit()

    def remove_pattern(self, pattern):
        '''Remove the given pattern from the set
        '''
        self.layout.removeRow(pattern)
        self.value_changed.emit()

    def remove_all_rows(self):
        '''Self explanatory
        '''
        while self.layout.rowCount() > 0:
            self.layout.removeRow(0)
        self.value_changed.emit()

    def get_values(self):
        '''Get the values of the contained OAM patterns and return
        them in a list
        '''
        return [
            self.layout.itemAt(i).widget().wrapped.get_values()
            for i in range(self.layout.count())
        ]

    def set_values(self, patterns):
        '''This function takes a list of dictionaries containing
        OAM pattern values.
        It removes the current patterns and creates new patterns
        according to the given values
        '''
        self.remove_all_rows()
        for args in patterns:
            self.add_new_oam_pattern(args)


class XYController(QGroupBox):
    '''Define a control for x and y position
    '''
    value_changed = pyqtSignal()

    def __init__(self, name):
        super().__init__()
        self.setTitle(name)
        self.layout = QGridLayout()
        self.x = pg.SpinBox()
        self.y = pg.SpinBox()
        self.x.sigValueChanged.connect(self.value_changed.emit)
        self.y.sigValueChanged.connect(self.value_changed.emit)
        self.layout.addWidget(QLabel("x:"), 0, 0)
        self.layout.addWidget(QLabel("y:"), 0, 5)
        self.layout.addWidget(self.x, 0, 1, 1, 4)
        self.layout.addWidget(self.y, 0, 6, 1, 4)
        self.setLayout(self.layout)

    def get_values(self):
        '''Get the x and y values and return in a tuple
        '''
        return (self.x.value(), self.y.value())

    def set_values(self, *args, **kwargs):
        '''Set the values from some dictionaries
        '''
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
