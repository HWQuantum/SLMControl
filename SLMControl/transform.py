"""Contains the transform widget
"""
import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw
import pyqtgraph as pg


class Transform(qw.QWidget):
    """A widget which modifys a transform
    The transform is specified in the state module
    """

    data_changed = qc.pyqtSignal()

    def __init__(self, data):
        super().__init__()
        self._data = data
        layout = qw.QHBoxLayout()
        p_box = qw.QGroupBox("Position")
        p_grid = qw.QGridLayout()
        self.x = pg.SpinBox()
        self.y = pg.SpinBox()

        p_grid.addWidget(qw.QLabel("x:"), 0, 0)
        p_grid.addWidget(self.x, 0, 1)
        p_grid.addWidget(qw.QLabel("y:"), 1, 0)
        p_grid.addWidget(self.y, 1, 1)

        p_box.setLayout(p_grid)

        s_box = qw.QGroupBox("Size")
        s_grid = qw.QGridLayout()
        self.size_x = pg.SpinBox()
        self.size_y = pg.SpinBox()

        s_grid.addWidget(qw.QLabel("x:"), 0, 0)
        s_grid.addWidget(self.size_x, 0, 1)
        s_grid.addWidget(qw.QLabel("y:"), 1, 0)
        s_grid.addWidget(self.size_y, 1, 1)

        s_box.setLayout(s_grid)

        self.rotation = pg.SpinBox()
        r_box = qw.QGroupBox("Rotation")
        r_layout = qw.QHBoxLayout()
        r_layout.addWidget(self.rotation)
        r_box.setLayout(r_layout)

        layout.addWidget(p_box)
        layout.addWidget(s_box)
        layout.addWidget(r_box)

        # connect the signals
        self.x.sigValueChanged.connect(self.x_changed)
        self.y.sigValueChanged.connect(self.y_changed)
        self.size_x.sigValueChanged.connect(self.size_x_changed)
        self.size_y.sigValueChanged.connect(self.size_y_changed)
        self.rotation.sigValueChanged.connect(self.rotation_changed)

        self.setLayout(layout)

        self.update_from_data()

    @qc.pyqtSlot()
    def update_from_data(self):
        """Update from data, blocking signals for each update"""
        self.x.blockSignals(True)
        self.x.setValue(self._data["position"][0])
        self.x.blockSignals(False)
        self.y.blockSignals(True)
        self.y.setValue(self._data["position"][1])
        self.y.blockSignals(False)
        self.size_x.blockSignals(True)
        self.size_x.setValue(self._data["size"][0])
        self.size_x.blockSignals(False)
        self.size_y.blockSignals(True)
        self.size_y.setValue(self._data["size"][1])
        self.size_y.blockSignals(False)
        self.rotation.blockSignals(True)
        self.rotation.setValue(self._data["rotation"])
        self.rotation.blockSignals(False)

    @qc.pyqtSlot()
    def x_changed(self):
        self._data["position"][0] = self.x.value()

    @qc.pyqtSlot()
    def y_changed(self):
        self._data["position"][1] = self.y.value()

    @qc.pyqtSlot()
    def size_x_changed(self):
        self._data["size"][0] = self.size_x.value()

    @qc.pyqtSlot()
    def size_y_changed(self):
        self._data["size"][1] = self.size_y.value()

    @qc.pyqtSlot()
    def rotation_changed(self):
        self._data["rotation"] = self.rotation.value()
