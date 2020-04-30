"""Widgets for screens
"""

import PyQt5.QtWidgets as qw
import PyQt5.QtCore as qc
import pyqtgraph as pg
from SLMControl.transform import Transform
from SLMControl.state import SLMState
from uuid import uuid4


class ViewReference(qw.QWidget):
    """This is a widget which controls a view reference
    """
    def __init__(self, reference_data, state):
        super().__init__()

        self._data = reference_data
        self._state = state

        self.name = qw.QLabel()
        self.pos_x = pg.SpinBox()
        self.pos_y = pg.SpinBox()
        self.size_x = pg.SpinBox()
        self.size_y = pg.SpinBox()

        self.pos_x.sigValueChanged.connect(self.pos_x_changed)
        self.pos_y.sigValueChanged.connect(self.pos_y_changed)
        self.size_x.sigValueChanged.connect(self.size_x_changed)
        self.size_y.sigValueChanged.connect(self.size_y_changed)

        layout = qw.QVBoxLayout()
        layout.addWidget(self.name)
        layout.addWidget(self.pos_x)
        layout.addWidget(self.pos_y)
        layout.addWidget(self.size_x)
        layout.addWidget(self.size_y)

        self.setLayout(layout)

        self.update_from_data()

    @qc.pyqtSlot()
    def update_from_data(self):
        self.pos_x.blockSignals(True)
        self.pos_x.setValue(self._data[1][0])
        self.pos_x.blockSignals(False)
        self.pos_y.blockSignals(True)
        self.pos_y.setValue(self._data[1][1])
        self.pos_y.blockSignals(False)
        self.size_x.blockSignals(True)
        self.size_x.setValue(self._data[2][0])
        self.size_x.blockSignals(False)
        self.size_y.blockSignals(True)
        self.size_y.setValue(self._data[2][1])
        self.size_y.blockSignals(False)
        self.update_name_from_data()

    @qc.pyqtSlot()
    def pos_x_changed(self):
        self._data[1][0] = self.pos_x.value()

    @qc.pyqtSlot()
    def pos_y_changed(self):
        self._data[1][1] = self.pos_y.value()

    @qc.pyqtSlot()
    def size_x_changed(self):
        self._data[2][0] = self.size_x.value()

    @qc.pyqtSlot()
    def size_y_changed(self):
        self._data[2][1] = self.size_y.value()

    @qc.pyqtSlot()
    def update_name_from_data(self):
        self.name.setText(self._state.get_view_name(self._data[0]))


class Screen(qw.QWidget):

    data_changed = qc.pyqtSignal()

    def __init__(self, screen_data, state):
        """We need the state reference to be able to get the names of views
        """
        super().__init__()
        self._data = screen_data
        self._state = state
        layout = qw.QVBoxLayout()

        self.name = qw.QLineEdit()
        self.name.textChanged.connect(self.update_name)

        layout.addWidget(self.name)

        self.view_references = []
        self.view_references_layout = qw.QVBoxLayout()

        view_references_box = qw.QGroupBox("View References")
        view_references_box.setLayout(self.view_references_layout)

        layout.addWidget(view_references_box)

        self.setLayout(layout)
        self.update_from_data()

    @qc.pyqtSlot()
    def update_from_data(self):
        """Update the data from the reference this widget has to it
        """
        self.update_pattern_references()

    @qc.pyqtSlot(str)
    def update_name(self, name: str):
        self._data["name"] = name

    @qc.pyqtSlot()
    def update_pattern_references(self):
        for v in self.view_references:
            v.update_from_data()
        while self.view_references_layout.count() > 0:
            self.view_references_layout.takeAt(0)
        self.view_references.clear()
        for vr in sorted(self._data["views"]):
            self.view_references.append(
                ViewReference(self._data["views"][vr], self._state))
            self.view_references_layout.addWidget(self.view_references[-1])
