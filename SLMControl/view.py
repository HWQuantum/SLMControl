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
        self.coefficient.setValue(reference_data[1])
        self.coefficient.sigValueChanged.connect(self.update_coefficient_from_gui)
        
        self.transform = Transform(reference_data[2])
        layout = qw.QVBoxLayout()
        layout.addWidget(self.name)
        layout.addWidget(self.coefficient)
        layout.addWidget(self.transform)
        self.setLayout(layout)

        self.update_from_data()

    @qc.pyqtSlot()
    def update_from_data(self):
        self.update_name_from_data()
        self.coefficient.setValue(self._data[1])
        self.transform.update_from_data()

    @qc.pyqtSlot()
    def update_name_from_data(self):
        self.name.setText(self._state.get_pattern_name(self._data[0]))

    @qc.pyqtSlot()
    def update_coefficient_from_gui(self):
        self._data[1] = self.coefficient.value()


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

        self.pattern_references_layout = qw.QVBoxLayout()

        layout.addWidget(self.name)
        layout.addWidget(self.transform)

        pattern_references_box = qw.QGroupBox("Pattern References")
        pattern_references_box.setLayout(self.pattern_references_layout)

        layout.addWidget(pattern_references_box)

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
        self.update_pattern_references()

    @qc.pyqtSlot()
    def update_pattern_references(self):
        while self.pattern_references_layout.count() > 0:
            self.pattern_references_layout.takeAt(0)
        self.pattern_references.clear()
        for pr in sorted(self._data["patterns"]):
            self.pattern_references.append(
                PatternReference(self._data["patterns"][pr], self._state))
            self.pattern_references_layout.addWidget(
                self.pattern_references[-1])

    @qc.pyqtSlot(str)
    def update_name(self, name: str):
        self._data["name"] = name
