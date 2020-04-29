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
        layout = qw.QHBoxLayout()
        self.transform = Transform(self._data["transform"])
        self.pattern_references = []
        layout.addWidget(self.transform)
        self.setLayout(layout)

    @qc.pyqtSlot()
    def update_from_data(self):
        """Update the data from the reference this widget has to it
        """
        self.transform.update_from_data()

    @qc.pyqtSlot()
    def update_pattern_references(self):
        pass


import sys
app = qw.QApplication(sys.argv)
s = SLMState()
s.add_view({
    "id": uuid4(),
    "name": "test_view",
    "transform": {
        "position": (0, 0),
        "size": (0, 0),
        "rotation": 0
    },
    "patterns": {}
})
v = View(s.get_view_by_name("test_view"))
v.show()
w = qw.QWidget()
l = qw.QHBoxLayout()
w.setLayout(l)
b = qw.QPushButton("Hi")
l.addWidget(b)


def update_s():
    s.get_view_by_name("test_view")["transform"]["position"] = (20, 10)
    v.transform.update_from_data()


b.clicked.connect(update_s)
w.show()
sys.exit(app.exec())
