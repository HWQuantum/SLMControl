import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw
import sys

class MainWindow(qw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = qw.QHBoxLayout()
        button = qw.QPushButton("Add new qdock")
        button.clicked.connect(self.add_dock)
        layout.addWidget(button)
        w = qw.QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

    def add_dock(self):
        w = qw.QDockWidget(self)
        button = qw.QPushButton("Push me")
        w.setWidget(button)
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
