from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGridLayout
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import pyqtgraph as pg
from time import sleep
import numpy as np


class TestThread(QObject):
    measurement_done = pyqtSignal(np.ndarray, np.ndarray, list)

    def __init__(self):
        super().__init__()

    def run_measurement(self):
        sleep(1)
        self.measurement_done.emit(np.random.rand(9), np.random.rand(9), [np.random.rand(9) for _ in range(9)])


class CoincidenceWidget(QWidget):
    run_measurement = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.plot = pg.PlotWidget()
        self.hist = self.plot.plot([0, 1], [1], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
        self.layout.addWidget(self.plot)
        p = TestWindow()
        self.layout.addWidget(p)
        p.setEnabled(False)
        self.measurement_thread = QThread()
        self.test = TestThread()
        self.test.moveToThread(self.measurement_thread)
        self.measurement_thread.started.connect(self.test.run_measurement)
        self.test.measurement_done.connect(self.update_plot)
        self.run_measurement.connect(self.test.run_measurement)
        self.measurement_thread.start()
        self.measure = True

    @pyqtSlot(np.ndarray, np.ndarray, list)
    def update_plot(self, singles, coincs, hists):
            self.hist.setData(np.linspace(0, 1, 10), hists[0])
            self.run_measurement.emit()

class DeviceSettings(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.addWidget(QPushButton("Hi"))
        self.layout.addWidget(QPushButton("Ho"))
        self.layout.addWidget(QPushButton("He"))
        self.setLayout(self.layout)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = CoincidenceWidget()
    window.show()
    app.exec()
