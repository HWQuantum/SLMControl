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
        super().__init__()
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

    @qc.pyqtSlot()
    def update_from_data(self):
        self.x.setValue(self._data["position"][0])
        self.y.setValue(self._data["position"][1])
        self.scale_x.setValue(self._data["size"][0])
        self.scale_y.setValue(self._data["size"][1])
        self.rotation.setValue(self._data["rotation"])
