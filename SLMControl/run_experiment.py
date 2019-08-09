'''This file contains a widget which wraps up the slm and coincidence counting widgets
and controls them itself to allow taking a run of measurements
'''

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject
from slm_display import MultiSLMController
from coincidence_counting import CoincidenceWidget
from time import sleep
import pickle
import numpy as np


class ExperimentController(QWidget):
    def __init__(self, screens, application):
        super().__init__()
        self.application = application
        self.layout = QGridLayout()
        self.run_experiment_button = QPushButton("Run EXPERIMENT")
        self.slm_controller = MultiSLMController(screens, [(500, 500),
                                                           (500, 500)])

        self.coincidence_widget = CoincidenceWidget()

        self.run_experiment_button.clicked.connect(self.run_experiment)

        self.layout.addWidget(self.slm_controller, 0, 0)
        self.layout.addWidget(self.coincidence_widget, 0, 1)
        self.layout.addWidget(self.run_experiment_button, 1, 0, 1, 2)
        self.setLayout(self.layout)

    def closeEvent(self, e):
        self.slm_controller.close()

    @pyqtSlot()
    def run_experiment(self):
        ''' Runs the experiment, using values set on the device measurement
        page
        '''
        integration_time = 1000  # integration time in ms
        coincidence_window = 3000  # coincidence window in ps
        histogram_bins = 300  # number of bins for the histogram
        sync_channel = 0  # the channel the values should be compared with

        self.measurement_receiver = MeasurementReceiver()
        angle_a = np.arange(0, np.pi / 2, np.pi / 8)
        angle_b = np.linspace(0, 2 * np.pi, 200)

        self.measurement_receiver.set_key('coincidence_counter_values')
        self.measurement_receiver.add_data(
            self.coincidence_widget.device_setup.get_values())
        self.measurement_receiver.set_key('measurement_parameters')
        self.measurement_receiver.add_data({
            "integration_time": integration_time,
            "coincidence_window": coincidence_window,
            "histogram_bins": histogram_bins,
            "sync_channel": sync_channel,
        })

        for i, a in enumerate(angle_a):
            for j, b in enumerate(angle_b):
                self.measurement_receiver.set_key(("angle_a_b", a, b))
                self.slm_controller.set_values([{
                    "oam_controller": [{
                        "amplitude": 1,
                        "ang_mom": 2,
                        "phase": 0,
                    }, {
                        "amplitude": 1,
                        "ang_mom": -2,
                        "phase": a,
                    }]
                }, {
                    "oam_controller": [{
                        "amplitude": 1,
                        "ang_mom": 2,
                        "phase": 0,
                    }, {
                        "amplitude": 1,
                        "ang_mom": -2,
                        "phase": b,
                    }]
                }])
                self.application.processEvents()
                sleep(0.3)
                self.measurement_receiver.add_data(
                    self.coincidence_widget.measurement_thread.
                    run_measurement_once(integration_time, coincidence_window,
                                         histogram_bins, sync_channel))

            print("Done {}/{}".format(i + 1, len(angle_a)))

        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "")
        if filename:
            with open(filename, 'wb') as f:
                self.measurement_receiver.save_data(f)


class MeasurementReceiver(QObject):
    '''Class used to receive measurement data
    Stores the received data in a dictionary, with a given key
    The dictionary is of the form {key: [data]}
    Where each key has a list of data associated with it
    '''
    def __init__(self):
        self.data = {}

    def set_key(self, new_key):
        '''Sets the key to store in, converting any lists or dicts to tuples
        with the tuplise function
        '''
        self.key = tuplise(new_key)
        if self.key not in self.data:
            self.data[self.key] = []

    def add_data(self, new_data):
        '''Adds data to the associated key
        '''
        self.data[self.key].append(new_data)

    def save_data(self, file):
        pickle.dump(self.data, file)


def tuplise(data):
    '''Recursively converts any lists/dicts in data into tuples
    '''
    if type(data) == list:
        return tuple(tuplise(i) for i in data)
    elif type(data) == dict:
        return tuple((":key:", k, tuplise(v)) for k, v in data.items())
    else:
        return data


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = ExperimentController(app.screens(), app)
    window.show()
    app.exec()
