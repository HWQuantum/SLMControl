"""Contains the transform widget
"""
import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw
import pyqtgraph as pg

class Transform(qw.QWidget):
    """A widget which modifys a transform
    The transform is specified in the state module
    """
    def __init__(self, data):
        self._data = data
        layout = qw.QVBoxLayout()
        self.x = pg.SpinBox()
        self.y = pg.SpinBox()
        self.scale_x = pg.SpinBox()
        self.scale_y = pg.SpinBox()
        self.rotation = pg.SpinBox()

        layout.addWidget(self.x)
        layout.addWidget(self.y)
        layout.addWidget(self.scale_x)
        layout.addWidget(self.scale_y)
        layout.addWidget(self.rotation)

        self.setLayout(layout)

        self.update_from_data()

    def update_from_data(self):
        self.x.setValue(data["position"][0])
        self.y.setValue(data["position"][1])
        self.scale_x.setValue(data["scale"][0])
        self.scale_y.setValue(data["position"][1])
