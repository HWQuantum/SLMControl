"""Widgets for views
"""

import PyQt5.QtWidgets as qw
import PyQt5.QtCore as qc
import pyqtgraph as pg
from SLMControl.transform import Transform
from SLMControl.state import SLMState
from uuid import uuid4


class PatternReference(qw.QWidget):
    """This is a widget which controls a pattern reference
    """
    def __init__(self, reference_data, state):
        super().__init__()

        self._data = reference_data
        self._state = state
        self.name = qw.QLabel()
        self.coefficient = pg.SpinBox()
        self.coefficient.setValue(reference_data[0])
        self.transform = Transform(reference_data[1])
        layout = qw.QHBoxLayout()
        layout.addWidget(self.coefficient)
        layout.addWidget(self.transform)
        self.setLayout(layout)

    @qc.pyqtSlot()
    def update_from_data(self):
        self.coefficient.setValue(self._data[0])
        self.transform.update_from_data()


class View(qw.QWidget):

    data_changed = qc.pyqtSignal()

    def __init__(self, view_data, state):
        """We need the state reference to be able to get the names of patterns
        """
        super().__init__()
        self._data = view_data
        self._state = state
        layout = qw.QVBoxLayout()
        self.name = qw.QLineEdit()
        self.name.textChanged.connect(self.update_name)
        self.transform = Transform(self._data["transform"])
        self.pattern_references = []
        layout.addWidget(self.name)
        layout.addWidget(self.transform)
        self.setLayout(layout)
        self.update_from_data()

    @qc.pyqtSlot()
    def update_from_data(self):
        """Update the data from the reference this widget has to it
        """
        self.name.blockSignals(True)
        self.name.setText(self._data["name"])
        self.name.blockSignals(False)
        self.transform.update_from_data()

    @qc.pyqtSlot()
    def update_pattern_references(self):
        pass

    @qc.pyqtSlot(str)
    def update_name(self, name: str):
        self._data["name"] = name
