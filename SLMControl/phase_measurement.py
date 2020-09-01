from slm_controller import SLMDisplay
import numpy as np
import PyQt5.QtWidgets as qw
import PyQt5.QtCore as qc
import pyqtgraph as pg
from time import sleep
from lut_calibration_interface import Camera

N_PHASE_MEASUREMENTS = 4
N_FRAMES_PER_MEASUREMENT = 10


class MatView(pg.PlotWidget):
    def __init__(self, image_size):
        super().__init__()
        self.image_size = (image_size[1], image_size[0])
        self.image_display = pg.ImageItem(np.zeros(self.image_size))

        self.hideAxis('left')
        self.hideAxis('bottom')

        self.addItem(self.image_display)

    @qc.pyqtSlot()
    def update_image(self, frame):
        self.image_display.setImage(frame)


class CameraView(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.cam = Camera()
        self.camera_size = (self.cam.width.value, self.cam.height.value)
        self.image_display = pg.ImageItem(np.zeros(self.camera_size))

        self.hideAxis('left')
        self.hideAxis('bottom')

        self.addItem(self.image_display)

        self.timer = qc.QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(0.1)

    @qc.pyqtSlot()
    def update_image(self):
        self.frame = self.cam.get_frame()
        self.image_display.setImage(self.frame)


class PhaseMeasurement(qw.QWidget):
    def __init__(self, slm_window, app, resolution=(1920, 1152), parent=None):
        super().__init__(parent)
        self.slm_window = slm_window
        self.res = resolution
        self.camera_view = CameraView()
        self.measurement_index = 0
        self.mat_view = MatView(self.camera_view.camera_size)
        run_button = qw.QPushButton("Run experiment")
        run_button.clicked.connect(self.run_measurement)
        prev_meas_button = qw.QPushButton("Previous Measurement")
        prev_meas_button.clicked.connect(
            lambda: self.change_shown_measurement(-1))
        next_meas_button = qw.QPushButton("Next Measurement")
        next_meas_button.clicked.connect(
            lambda: self.change_shown_measurement(1))
        newest_meas_button = qw.QPushButton("Newest Measurement")
        newest_meas_button.clicked.connect(
            lambda: self.view_newest_measurement())
        self.use_inverse_of_current_phase = qw.QPushButton(
            "Use inverse of current phase measurement")
        self.use_inverse_of_current_phase.setCheckable(True)
        self.grating = pg.SpinBox()
        self.num_measurement_per_phase = pg.SpinBox(value=N_PHASE_MEASUREMENTS,
                                                    int=True,
                                                    bounds=(1, None))
        self.num_phases = pg.SpinBox(value=N_FRAMES_PER_MEASUREMENT,
                                     int=True,
                                     bounds=(1, None))
        layout = qw.QGridLayout()
        layout.addWidget(self.camera_view, 0, 0, 1, 2)
        layout.addWidget(self.mat_view, 0, 2, 1, 2)
        layout.addWidget(qw.QLabel("Number of phases"), 1, 0)
        layout.addWidget(self.num_phases, 1, 1)
        layout.addWidget(qw.QLabel("Number of measurements per phase"), 1, 2)
        layout.addWidget(self.num_measurement_per_phase, 1, 3)
        layout.addWidget(run_button, 2, 0, 1, 4)
        layout.addWidget(prev_meas_button, 3, 0, 1, 2)
        layout.addWidget(next_meas_button, 3, 2, 1, 2)
        layout.addWidget(self.use_inverse_of_current_phase, 4, 0, 1, 4)
        self.measurements = []
        self.setLayout(layout)

    def closeEvent(self, event):
        self.slm_window.window.close()

    @qc.pyqtSlot()
    def run_measurement(self):
        measurement_mat = np.zeros(
            (self.num_phases.value(), *self.camera_view.camera_size))
        x, y = np.linspace(1, self.res[0],
                           self.res[0]), np.linspace(1, self.res[1],
                                                     self.res[1])
        x, y = np.meshgrid(x, y)
        # if self.use_inverse_of_current_phase.isChecked() and len(
        #         self.measurements) > 0:
        #     grating = np.exp(1j * (x.T * self.grating.value())) * np.exp(
        #         -1j * self.measurements[self.measurement_index][1])
        # else:
        grating = np.exp(1j * (x.T * self.grating.value()))

        for i, phase in enumerate(
                np.linspace(0, 2 * np.pi,
                            self.num_phases.value() + 1)[:-1]):

            self.slm_window.set_image(np.angle(np.exp(1j * phase) * grating),
                                      autoLevels=False,
                                      levels=(-np.pi, np.pi))
            app.processEvents()
            sleep(0.1)
            for _ in range(self.num_measurement_per_phase.value()):
                self.camera_view.update_image()
                measurement_mat[i] += self.camera_view.frame[:, :, 0].T
                sleep(0.1)
            measurement_mat[i] /= self.num_measurement_per_phase.value()
        self.measurements.append(
            (measurement_mat, np.angle(np.fft.fft(measurement_mat,
                                                  axis=0))[1, :, :]))
        self.view_newest_measurement()
        # np.save("phase_measurement", measurement_mat)

    @qc.pyqtSlot()
    def view_newest_measurement(self):
        if len(self.measurements) > 0:
            self.measurement_index = len(self.measurements) - 1
            self.set_mat_view_from_index()

    @qc.pyqtSlot(int)
    def change_shown_measurement(self, offset):
        if len(self.measurements) > 0:
            self.measurement_index = (self.measurement_index + offset) % len(
                self.measurements)
            self.set_mat_view_from_index()

    def set_mat_view_from_index(self):
        self.mat_view.update_image(
            self.measurements[self.measurement_index][1].T)


if __name__ == '__main__':
    app = qw.QApplication([])

    slm_window = SLMDisplay("SLM Display", app.screens()[0], (1920, 1152))

    w = PhaseMeasurement(slm_window, app)

    w.show()
    app.exec()
