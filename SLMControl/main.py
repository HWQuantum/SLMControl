import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw
import sys
from SLMControl.view import View
from SLMControl.screen import Screen
from SLMControl.state import SLMState
from uuid import uuid4


class MainWindow(qw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = SLMState()
        self.state.add_view({
            "id": uuid4(),
            "name": "test_view",
            "patterns": {},
            "transform": {
                "position": [0, 0],
                "size": [0, 0],
                "rotation": 0
            }
        })
        self.state.add_screen({
            "id": uuid4(),
            "name": "test_screen",
            "offset": [0, 0],
            "views": {}
        })
        layout = qw.QHBoxLayout()
        button = qw.QPushButton("Add new qdock")
        button.clicked.connect(self.add_dock)
        layout.addWidget(button)
        button = qw.QPushButton("Add new screen")
        button.clicked.connect(self.add_screen)
        layout.addWidget(button)
        w = qw.QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

    def add_dock(self):
        w = qw.QDockWidget(self)

        v = View(self.state.get_view_by_name("test_view"), self.state)
        w.setWidget(v)
        self.addDockWidget(qc.Qt.RightDockWidgetArea, w)

    def add_screen(self):
        w = qw.QDockWidget(self)

        v = Screen(self.state.get_screen_by_name("test_screen"), self.state)
        w.setWidget(v)
        self.addDockWidget(qc.Qt.RightDockWidgetArea, w)


class buttonThing(qw.QDockWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = qw.QHBoxLayout()
        button = qw.QPushButton("This is a button")
        layout.addWidget(button)
        self.setLayout(layout)


app = qw.QApplication(sys.argv)

w = MainWindow()

w.show()

sys.exit(app.exec())
