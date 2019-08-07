from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGridLayout, QTabWidget
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import pyqtgraph as pg
from time import sleep
import numpy as np


class TestThread(QObject):
    measurement_done = pyqtSignal(np.ndarray, np.ndarray, list)

    def __init__(self):
        super().__init__()

    @pyqtSlot(int)
    def run_measurement(self):
        sleep(1)
        self.measurement_done.emit(*(np.random.rand(9), np.random.rand(9),
                                     [np.random.rand(9) for _ in range(9)]))


class DeviceSetup(QWidget):
    '''Widget which controls the initialisation of a counting device
    '''
    device_initialised = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.initialise = QPushButton("Initialise Device")

        self.initialise.clicked.connect(self.init_device)
        self.device_initialised.connect(lambda: self.setEnabled(True))

        self.layout.addWidget(self.initialise, 0, 0)
        self.setLayout(self.layout)

    @pyqtSlot()
    def init_device(self):
        self.setEnabled(False)
        self.device_initialised.emit(2)


class DeviceMeasurement(QWidget):
    '''Widget which displays and orders measurements from
    a counting device
    

    The measurement_button_first_push keeps track of whether 
    it's the first time the toggle has been pushed, to stop
    queueing up measurements in the measurement thread
    '''
    # run a measurement for a given number of ms
    run_measurement = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        # for queueing of measurements
        self.measurement_queued = False

        self.layout = QGridLayout()

        self.histogram_plot = pg.PlotWidget()
        self.histogram = self.histogram_plot.plot([0, 1], [1],
                                                  stepMode=True,
                                                  fillLevel=0,
                                                  brush=(0, 0, 255, 150))

        self.run_measurement_button = QPushButton("Run measurement")

        self.run_measurement_button.setCheckable(True)
        self.run_measurement_button.clicked.connect(self.try_run_measurement)
        self.measurement_button_first_push = True

        self.measurement_thread = QThread()
        self.test = TestThread()
        self.test.moveToThread(self.measurement_thread)
        self.test.measurement_done.connect(self.update_data)
        self.run_measurement.connect(self.test.run_measurement)
        self.measurement_thread.start()
        self.measure = True

        self.layout.addWidget(self.histogram_plot, 0, 0)
        self.layout.addWidget(self.run_measurement_button, 1, 0)

        self.setLayout(self.layout)

    @pyqtSlot(np.ndarray, np.ndarray, list)
    def update_data(self, singles, coincs, hists):
        '''Update the plots based on the counts data'''
        self.histogram.setData(np.linspace(0, 1, 10), hists[0])
        if self.run_measurement_button.isChecked():
            self.run_measurement.emit(1000)
        else:
            self.measurement_button_first_push = True

    @pyqtSlot(bool)
    def try_run_measurement(self, checked):
        if checked:
            # the measurement button has been toggled on
            if self.measurement_button_first_push:
                self.run_measurement.emit(1000)
                self.measurement_button_first_push = False


class CoincidenceWidget(QWidget):
    run_measurement = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.device_measurement = DeviceMeasurement()
        self.device_setup = DeviceSetup()

        self.tab_widget.addTab(self.device_measurement, "Plot")
        self.tab_widget.addTab(self.device_setup, "Device Setup")

        self.layout.addWidget(self.tab_widget)

        self.setLayout(self.layout)


class DeviceSettings(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = CoincidenceWidget()
    window.show()
    app.exec()
