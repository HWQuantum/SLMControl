from PyQt5.QtWidgets import QWidget, QGroupBox, QGridLayout, QLabel
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg


class OAMControls(QWidget):
    '''Contains the controls for one OAM pattern
    the amplitude, the m, the position and the phase
    '''

    value_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.amplitude = pg.SpinBox(value=1)
        self.ang_mom = pg.SpinBox(int=True, step=1)
        self.phase = pg.SpinBox()
        self.position = XYController("Position")

        self.amplitude.sigValueChanged.connect(self.value_changed.emit)
        self.ang_mom.sigValueChanged.connect(self.value_changed.emit)
        self.phase.sigValueChanged.connect(self.value_changed.emit)
        self.position.value_changed.connect(self.value_changed.emit)

        self.layout.addWidget(QLabel("Amplitude:"), 0, 0)
        self.layout.addWidget(self.amplitude, 0, 1, 1, 2)
        self.layout.addWidget(QLabel("Angular Momentum:"), 1, 0)
        self.layout.addWidget(self.ang_mom, 1, 1, 1, 2)
        self.layout.addWidget(QLabel("Phase:"), 2, 0)
        self.layout.addWidget(self.phase, 2, 1, 1, 2)
        self.layout.addWidget(self.position, 0, 3, 3, 1)
        self.setLayout(self.layout)

    def get_values(self):
        '''Get all of the values and return a dictionary containing them
        '''
        return {
            "amplitude": self.amplitude.value(),
            "ang_mom": self.ang_mom.value(),
            "phase": self.phase.value(),
            "position": self.position.get_values(),
        }

    def set_values(self, *args, **kwargs):
        for arg in args:
            for key, value in arg.items():
                if key == "amplitude":
                    self.amplitude.setValue(value)
                elif key == "ang_mom":
                    self.ang_mom.setValue(value)
                elif key == "phase":
                    self.phase.setValue(value)
                elif key == "position":
                    self.position.set_values(value)
        for key, value in kwargs.items():
            if key == "amplitude":
                self.amplitude.setValue(value)
            elif key == "ang_mom":
                self.ang_mom.setValue(value)
            elif key == "phase":
                self.phase.setValue(value)
            elif key == "position":
                self.position.set_values(value)


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
            elif type(arg) == tuple:
                self.x.setValue(arg[0])
                self.y.setValue(arg[1])

        for key, value in kwargs.items():
            if key == 'x':
                self.x.setValue(value)
            elif key == 'y':
                self.y.setValue(value)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    a = QApplication([])
    c = OAMControls()
    c.set_values(position=(2, 3), phase=30, ang_mom=3.124)
    c.show()
    a.exec()
