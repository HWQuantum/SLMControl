'''This file contains a widget which wraps up the slm and 
coincidence counting widgets
and controls them itself to allow taking a run of measurements
'''

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QFileDialog, QComboBox
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from slm_controller import MultiSLMController
from coincidence_counting import CoincidenceWidget
from experiments import coincidences_3x3_with_correction, two_mub_17x17
import os
import json
import experiments
import inspect
from pixel_entanglement import MultiPixelController


class OAMExperimentController(QWidget):
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
        self.measurement_receiver = coincidences_3x3_with_correction(
            self.slm_controller, self.coincidence_widget, self.application)

        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "")
        if filename:
            with open(filename, 'wb') as f:
                self.measurement_receiver.save_data(f)


class PizzaExperimentController(QWidget):
    def __init__(self, screens, application):
        super().__init__()
        self.application = application
        self.layout = QGridLayout()
        self.experiment_selection = QComboBox()
        self.run_experiment_button = QPushButton("Run EXPERIMENT")
        self.save_defaults_button = QPushButton("Save defaults")
        self.load_defaults_button = QPushButton("Load defaults")
        self.slm_controller = MultiSLMController(screens, [(512, 512),
                                                             (512, 512)])

        self.experiments = inspect.getmembers(experiments, inspect.isfunction)
        for ex in self.experiments:
            self.experiment_selection.addItem(ex[0])

        self.coincidence_widget = CoincidenceWidget()

        self.run_experiment_button.clicked.connect(self.run_experiment)
        self.load_defaults_button.clicked.connect(self.try_load_defaults)
        self.save_defaults_button.clicked.connect(self.try_save_defaults)

        self.layout.addWidget(self.slm_controller, 0, 0)
        self.layout.addWidget(self.coincidence_widget, 0, 1)
        self.layout.addWidget(self.experiment_selection, 1, 0, 1, 1)
        self.layout.addWidget(self.run_experiment_button, 1, 1, 1, 1)
        self.layout.addWidget(self.save_defaults_button, 2, 0, 1, 1)
        self.layout.addWidget(self.load_defaults_button, 2, 1, 1, 1)
        self.setLayout(self.layout)

        self.try_load_defaults()

    def try_load_defaults(self, defaults_filename='.defaults.slmc'):
        '''Function to try to load defaults from a given file
        '''
        if os.path.exists(defaults_filename):
            self.try_read_values_from_json_file(default_filename)

    def try_save_defaults(self, defaults_filename='.defaults.slmc'):
        '''Try to save the defaults
        '''
        try:
            self.save_values_to_json_file(defaults_filename)
        except:
            pass

    def closeEvent(self, e):
        self.slm_controller.close()

    def get_values(self):
        '''Get the values contained in the slm controller and the HH setup controller
        '''
        return {
            'coincidence_widget': self.coincidence_widget.get_values(),
            'slm_controller': self.slm_controller.get_values()
        }

    def set_values(self, values):
        self.coincidence_widget.set_values(values['coincidence_widget'])
        self.slm_controller.set_values(values['slm_controller'])

    def save_values_to_json_file(self, filename):
        '''Save the values to a given filename
        doesn't catch any errors
        '''
        values = self.get_values()
        with open(filename, 'w') as f:
            json.dump(values, f)

    def read_values_from_json_file(self, filename):
        '''Read the values from a given filename
        doesn't catch any errors
        '''
        with open(filename, 'r') as f:
            self.set_values(json.load(f))

    def try_read_values_from_json_file(self, filename):
        '''wraps reading values in a try except thing,
        so it doesn't fail when reading a naughty file
        '''
        try:
            self.read_values_from_json_file(filename)
        except:
            pass

    @pyqtSlot()
    def run_experiment(self):
        ''' Runs the experiment, using values set on the device measurement
        page
        '''
        function_index = self.experiment_selection.currentIndex()
        self.measurement_receiver = self.experiments[function_index][1](
            self.slm_controller, self.coincidence_widget, self.application)

        with open('.last_experiment_run_data', 'wb') as f:
            self.measurement_receiver.save_data(f)

        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "")
        if filename:
            with open(filename, 'wb') as f:
                self.measurement_receiver.save_data(f)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = PizzaExperimentController(app.screens(), app)
    window.show()
    app.exec()
