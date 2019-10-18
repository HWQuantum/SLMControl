'''This file contains a widget which wraps up the slm and 
coincidence counting widgets
and controls them itself to allow taking a run of measurements
'''

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from slm_display import MultiSLMController
from coincidence_counting import CoincidenceWidget
from experiments import coincidences_3x3_with_correction
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
        self.run_experiment_button = QPushButton("Run EXPERIMENT")
        self.slm_controller = MultiPixelController(screens, [(512, 512),
                                                             (512, 512)])

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


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = PizzaExperimentController(app.screens(), app)
    window.show()
    app.exec()
