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
        layout = qw.QHBoxLayout()
        layout.addWidget(self.pos_x)
        layout.addWidget(self.pos_y)
        layout.addWidget(self.size_x)
        layout.addWidget(self.size_y)
        self.setLayout(layout)

    @qc.pyqtSlot()
    def update_from_data(self):
        self.pos_x.setValue(self._data[0][0])
        self.pos_y.setValue(self._data[0][1])
        self.size_x.setValue(self._data[1][0])
        self.size_y.setValue(self._data[1][1])


class Screen(qw.QWidget):

    data_changed = qc.pyqtSignal()

    def __init__(self, screen_data, state):
        """We need the state reference to be able to get the names of views
        """
        super().__init__()
        self._data = screen_data
        self._state = state
        layout = qw.QHBoxLayout()
        self.view_references = []
        self.setLayout(layout)

    @qc.pyqtSlot()
    def update_from_data(self):
        """Update the data from the reference this widget has to it
        """
        pass

    @qc.pyqtSlot()
    def update_pattern_references(self):
        for v in self.view_references:
            v.update_from_data()
