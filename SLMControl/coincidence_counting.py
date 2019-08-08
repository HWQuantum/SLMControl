from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGridLayout, QTabWidget, QGroupBox, QLabel, QScrollArea, QHBoxLayout, QComboBox
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import pyqtgraph as pg
from time import sleep
import numpy as np
import hhlib_sys


class TestThread(QObject):
    measurement_done = pyqtSignal(np.ndarray, np.ndarray, list)

    def __init__(self):
        super().__init__()

    @pyqtSlot(int)
    def run_measurement(self, time):
        sleep(time / 1000)
        self.measurement_done.emit(*(np.random.randint(0, high=100, size=(9)),
                                     np.random.randint(0, high=100, size=(9)),
                                     [np.random.rand(9) for _ in range(9)]))


class MeasurementThread(QObject):
    measurement_done = pyqtSignal(int, int, list, list, list)
    measurement_error = pyqtSignal()

    def __init__(self, device):
        super().__init__()
        self.dev = device

    @pyqtSlot(int, int, int, int)
    def run_measurement(self, time, coincidence_window, bins, sync_channel):
        try:
            values = hhlib_sys.measure_and_get_counts(self.dev, time,
                                                      coincidence_window, bins,
                                                      sync_channel)
            self.measurement_done.emit(time, coincidence_window, *values)
        except Exception as e:
            print("Couldn't read values!")
            self.measurement_error.emit()

    @pyqtSlot()
    def close_device(self):
        hhlib_sys.close_device(self.dev)


class ChannelSetting(QGroupBox):
    def __init__(self, name):
        super().__init__()
        self.setTitle(name)

        self.discriminator = pg.SpinBox(value=0.0, int=True, step=1)
        self.zero_cross = pg.SpinBox(value=0.0, int=True, step=1)
        self.offset = pg.SpinBox(value=0.0, int=True, step=1)

        self.layout = QGridLayout()

        self.layout.addWidget(QLabel("Discriminator (mV)"), 0, 0)
        self.layout.addWidget(self.discriminator, 0, 1)
        self.layout.addWidget(QLabel("Zero crossing (mV)"), 1, 0)
        self.layout.addWidget(self.zero_cross, 1, 1)
        self.layout.addWidget(QLabel("Timing offset (ps)"), 2, 0)
        self.layout.addWidget(self.offset, 2, 1)

        self.setLayout(self.layout)

    def get_values(self):
        return {
            "discriminator": self.discriminator.value(),
            "zero_cross": self.zero_cross.value(),
            "offset": self.offset.value(),
        }

    def set_values(self, *args, **kwargs):
        '''Set the values of this channel controller
        '''
        for dictionary in args:
            for key, value in dictionary.items():
                try:
                    getattr(self, key).setValue(value)
                except AttributeError:
                    pass
        for key, value in kwargs.items():
            try:
                getattr(self, key).setValue(value)
            except AttributeError:
                pass


class ChannelSettingContainer(QWidget):
    '''Contains the channel settings
    '''
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.sync_channel = ChannelSetting("Sync Channel")
        self.layout.addWidget(self.sync_channel, 0, 0)
        self.input_channels = []
        for i, pos in enumerate([(0, 1), (1, 0), (1, 1), (2, 0), (2, 1),
                                 (3, 0), (3, 1), (4, 0)]):
            c = ChannelSetting("Input Channel {}".format(i))
            self.layout.addWidget(c, pos[0], pos[1])
            self.input_channels.append(c)

        self.setLayout(self.layout)

    def get_values(self):
        return {
            "sync_channel": self.sync_channel.get_values(),
            "input_channels": [c.get_values() for c in self.input_channels],
        }

    def set_values(self, *args, **kwargs):
        '''Set the values of this set of channel controllers
        '''
        for dictionary in args:
            for key, value in dictionary.items():
                if key == "input_channels":
                    for i, v in enumerate(value):
                        self.input_channels[i].set_values(v)
                else:
                    try:
                        getattr(self, key).set_values(value)
                    except AttributeError:
                        pass
        for key, value in kwargs.items():
            if key == "input_channels":
                for i, v in enumerate(value):
                    self.input_channels[i].set_values(v)
            else:
                try:
                    getattr(self, key).set_values(value)
                except AttributeError:
                    pass


class DeviceSetup(QWidget):
    '''Widget which controls the initialisation of a counting device
    '''
    try_initialisation = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.initialise = QPushButton("Initialise Device")

        self.channel_settings = ChannelSettingContainer()

        channel_scroll_area = QScrollArea()
        channel_scroll_area.setWidget(self.channel_settings)

        channel_scroll_area.setWidgetResizable(False)

        self.initialise.clicked.connect(self.init_device)

        self.layout.addWidget(channel_scroll_area, 0, 0)
        self.layout.addWidget(self.initialise, 1, 0)
        self.setLayout(self.layout)

    @pyqtSlot()
    def init_device(self):
        '''Send the signal to initialise the device
        '''
        self.try_initialisation.emit(
            {"channel_settings": self.channel_settings.get_values()})

    @pyqtSlot(bool)
    def enable_device_interaction(self, enable):
        self.initialise.setEnabled(enable)

    def get_values(self):
        '''get the values
        '''
        return {
            "channel_settings": self.channel_settings.get_values(),
        }

    def set_values(self, *args, **kwargs):
        '''Set the values
        '''
        for dictionary in args:
            for key, value in dictionary.items():
                try:
                    getattr(self, key).set_values(value)
                except AttributeError:
                    pass
        for key, value in kwargs.items():
            try:
                getattr(self, key).set_values(value)
            except AttributeError:
                pass


class CoincidencePlot(pg.PlotWidget):
    '''A coincidences plot, which stores
    number_of_values values, and pushes values in to the
    right
    '''
    def __init__(self, number_of_values):
        super().__init__()
        self.data = np.zeros((1))
        self.coincidence_plot = self.plot(self.data)
        self.max_values = number_of_values

    @pyqtSlot(float)
    def add_new_value(self, x):
        '''Adds a new value to the data
        '''
        if len(self.data) >= self.max_values:
            self.data = np.roll(self.data, -1)
            self.data[-1] = x
        else:
            self.data = np.append(self.data, x)
        self.update_plot()

    @pyqtSlot()
    def update_plot(self):
        self.coincidence_plot.setData(self.data)

    @pyqtSlot()
    def clear_plot(self):
        self.coincidence_plot.setData(np.zeros((len(self.data))))


class SinglesPlot(pg.PlotWidget):
    '''A singles plot, which stores
    number_of_values values, and pushes values in to the
    right
    '''
    def __init__(self, number_of_values):
        super().__init__()
        self.max_values = number_of_values
        self.data = [np.zeros((1)), np.zeros((1))]
        pens = [pg.mkPen('w'), pg.mkPen('r')]
        self.plots = [
            self.plot(d, pen=pens[i]) for i, d in enumerate(self.data)
        ]

    @pyqtSlot(float)
    def add_new_values(self, data):
        '''Adds new values to the data
        '''
        for i, p in enumerate(self.data):
            if len(p) >= self.max_values:
                self.data[i] = np.roll(p, -1)
                self.data[i][-1] = data[i]
            else:
                self.data[i] = np.append(p, data[i])
        self.update_plot()

    @pyqtSlot()
    def update_plot(self):
        for i, p in enumerate(self.plots):
            p.setData(self.data[i])

    @pyqtSlot()
    def clear_plot(self):
        for i, d in enumerate(self.data):
            self.data[i] = np.zeros((1))
        self.update_plot()


class MeasurementCountDisplay(QWidget):
    '''Display the counts from the measurements
    '''
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()

        self.coincidences_value = pg.ValueLabel()
        self.sync_singles = pg.ValueLabel()
        self.other_singles = pg.ValueLabel()
        self.sync_efficiency = pg.ValueLabel()
        self.other_efficiency = pg.ValueLabel()
        self.accidentals = pg.ValueLabel()
        self.quantum_contrast = pg.ValueLabel()

        self.layout.addWidget(QLabel("Sync singles (1/s)"), 0, 0)
        self.layout.addWidget(self.sync_singles, 0, 1)
        self.layout.addWidget(QLabel("Other singles (1/s)"), 1, 0)
        self.layout.addWidget(self.other_singles, 1, 1)
        self.layout.addWidget(QLabel("Sync efficiency (%)"), 2, 0)
        self.layout.addWidget(self.sync_efficiency, 2, 1)
        self.layout.addWidget(QLabel("Other efficiency (%)"), 3, 0)
        self.layout.addWidget(self.other_efficiency, 3, 1)
        self.layout.addWidget(QLabel("Coincidences (1/s)"), 4, 0)
        self.layout.addWidget(self.coincidences_value, 4, 1)
        self.layout.addWidget(QLabel("Accidentals (1/s)"), 5, 0)
        self.layout.addWidget(self.accidentals, 5, 1)
        self.layout.addWidget(QLabel("Quantum contrast"), 6, 0)
        self.layout.addWidget(self.quantum_contrast, 6, 1)

        self.setLayout(self.layout)

    @pyqtSlot(list)
    def update_values(self, values):
        '''Update the labels with a set of values
        values is a list with values in this order:
        [singles_sync, singles_other, efficiency_sync, efficiency_other,
        coincidences, accidentals, quantum_contrast]
        '''
        self.sync_singles.setValue(values[0])
        self.other_singles.setValue(values[1])
        self.sync_efficiency.setValue(values[2])
        self.other_efficiency.setValue(values[3])
        self.coincidences_value.setValue(values[4])
        self.accidentals.setValue(values[5])
        self.quantum_contrast.setValue(values[6])


class DeviceMeasurement(QWidget):
    '''Widget which displays and orders measurements from
    a counting device


    The measurement_button_first_push keeps track of whether
    it's the first time the toggle has been pushed, to stop
    queueing up measurements in the measurement thread
    '''
    # run a measurement for a given number of ms
    run_measurement = pyqtSignal(int, int, int, int)
    measurement_run_status = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # for queueing of measurements
        self.measurement_queued = False

        self.layout = QGridLayout()

        self.measurement_time = pg.SpinBox(value=1000,
                                           bounds=(20, None),
                                           decimals=10,
                                           int=True,
                                           step=1)

        self.histogram_plot = pg.PlotWidget()
        self.histogram = self.histogram_plot.plot([0, 1], [0],
                                                  stepMode=True,
                                                  fillLevel=0,
                                                  brush=(0, 0, 255, 150))

        self.coincidence_plot = CoincidencePlot(1000)
        self.singles_plot = SinglesPlot(1000)
        self.measurement_labels = MeasurementCountDisplay()

        self.coincidences_window = pg.SpinBox(value=50000,
                                              int=True,
                                              bounds=(0, None),
                                              step=1)
        self.histogram_bins = pg.SpinBox(value=100,
                                         int=True,
                                         bounds=(0, 1000),
                                         step=1)

        self.sync_channel = QComboBox()
        self.sync_channel.addItems(["Sync"] +
                                   ["Input {}".format(i) for i in range(8)])
        self.other_channel = QComboBox()
        self.other_channel.addItems(["Sync"] +
                                    ["Input {}".format(i) for i in range(8)])

        self.run_measurement_button = QPushButton("Run measurement")

        self.run_measurement_button.setCheckable(True)
        self.run_measurement_button.clicked.connect(self.try_run_measurement)
        self.measurement_button_first_push = True

        self.layout.addWidget(QLabel("Sync on channel:"), 0, 0)
        self.layout.addWidget(self.sync_channel, 0, 1)
        self.layout.addWidget(QLabel("Plot on channel:"), 1, 0)
        self.layout.addWidget(self.other_channel, 1, 1)
        self.layout.addWidget(QLabel("Coincidence window (ps):"), 2, 0)
        self.layout.addWidget(self.coincidences_window, 2, 1)
        self.layout.addWidget(QLabel("Histogram Bins:"), 3, 0)
        self.layout.addWidget(self.histogram_bins, 3, 1)
        self.layout.addWidget(QLabel("Measurement time (ms):"), 4, 0)
        self.layout.addWidget(self.measurement_time, 4, 1)
        self.layout.addWidget(self.run_measurement_button, 5, 0, 1, 2)
        self.layout.addWidget(self.measurement_labels, 6, 0, 2, 2)

        self.layout.addWidget(self.histogram_plot, 0, 3, 6, 2)
        self.layout.addWidget(self.coincidence_plot, 6, 3, 1, 2)
        self.layout.addWidget(self.singles_plot, 7, 3, 1, 2)

        self.setLayout(self.layout)

    @pyqtSlot(int, int, list, list, list)
    def update_data(self, time, coincidence_window, singles, coincs, hists):
        '''Update the plots based on the counts data'''
        channel_1 = self.sync_channel.currentIndex()
        channel_2 = self.other_channel.currentIndex()

        singles_per_second_1 = singles[channel_1] / time * 1000
        singles_per_second_2 = singles[channel_2] / time * 1000

        coincidences_per_second = coincs[channel_2] / time * 1000

        if singles_per_second_1 != 0:
            efficiency_1 = coincidences_per_second / singles_per_second_1 * 100
        else:
            efficiency_1 = float('inf')

        if singles_per_second_2 != 0:
            efficiency_2 = coincidences_per_second / singles_per_second_2 * 100
        else:
            efficiency_2 = float('inf')

        accidentals = singles_per_second_1 * singles_per_second_1 * (
            coincidence_window / 1_000_000_000_000)

        if accidentals != 0:
            quantum_contrast = coincidences_per_second / accidentals
        else:
            quantum_contrast = float('inf')

        self.measurement_labels.update_values([
            singles_per_second_1, singles_per_second_2, efficiency_1,
            efficiency_2, coincidences_per_second, accidentals,
            quantum_contrast
        ])

        self.histogram.setData(
            np.linspace(0, self.coincidences_window.value(),
                        len(hists[channel_2]) + 1), hists[channel_2])
        self.coincidence_plot.add_new_value(coincidences_per_second)
        self.singles_plot.add_new_values(
            [singles_per_second_1, singles_per_second_2])

        if self.run_measurement_button.isChecked():
            # we want to take another measurement
            self.run_measurement.emit(self.measurement_time.value(),
                                      self.coincidences_window.value(),
                                      self.histogram_bins.value(),
                                      self.sync_channel.currentIndex())
        else:
            # reset the toggle, so that another measurement can be queued
            self.measurement_button_first_push = True
            self.measurement_run_status.emit(True)

    @pyqtSlot(bool)
    def try_run_measurement(self, checked):
        if checked:
            # the measurement button has been toggled on
            if self.measurement_button_first_push:
                self.run_measurement.emit(self.measurement_time.value(),
                                          self.coincidences_window.value(),
                                          self.histogram_bins.value(),
                                          self.sync_channel.currentIndex())
                self.measurement_button_first_push = False
                self.measurement_run_status.emit(False)

    @pyqtSlot()
    def reset_measurement_button(self):
        '''reset the state of the measurement button
        for use when a measurement fails
        '''
        self.measurement_button_first_push = True
        self.run_measurement_button.setChecked(False)


class CoincidenceWidget(QWidget):
    run_measurement = pyqtSignal()
    close_device = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.measurement_thread_container = None

        self.layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.device_measurement = DeviceMeasurement()
        self.device_setup = DeviceSetup()

        ######### SET DEFAULTS ########
        self.device_setup.set_values(
            channel_settings={
                "sync_channel": {
                    "discriminator": 100,
                    "zero_cross": 10,
                    "offset": 11000
                },
                "input_channels": [
                    {
                        "discriminator": 100,
                        "zero_cross": 10,
                        "offset": 10700
                    },
                    {
                        "discriminator": 100,
                        "zero_cross": 10,
                        "offset": -6100
                    },
                    {
                        "discriminator": 100,
                        "zero_cross": 10,
                        "offset": 0
                    },
                ],
            })
        ######### SET DEFAULTS ########

        self.tab_widget.addTab(self.device_setup, "Device Setup")
        self.tab_widget.addTab(self.device_measurement, "Plot")

        self.device_setup.try_initialisation.connect(
            self.initialise_and_thread_device)

        self.layout.addWidget(self.tab_widget)

        self.setLayout(self.layout)

    @pyqtSlot(dict)
    def initialise_and_thread_device(self, values):
        '''Initialise a hydraharp and send it to a thread
        '''
        if self.measurement_thread_container is not None:
            self.close_device.emit()
            sleep(1)
            self.measurement_thread_container.quit()
            self.measurement_thread_container.wait()
            self.measurement_thread_container = None
        self.dev = initialise_device(values)

        self.measurement_thread_container = QThread()
        self.measurement_thread = MeasurementThread(self.dev)
        self.measurement_thread.moveToThread(self.measurement_thread_container)
        self.measurement_thread.measurement_done.connect(
            self.device_measurement.update_data)
        self.measurement_thread.measurement_error.connect(
            self.reset_after_failed_measurement)
        self.close_device.connect(self.measurement_thread.close_device)
        self.device_measurement.run_measurement.connect(
            self.measurement_thread.run_measurement)

        self.measurement_thread_container.start()

    @pyqtSlot()
    def reset_after_failed_measurement(self):
        '''If a measurement failed, we want to reset the measurement button
        '''
        self.device_measurement.reset_measurement_button()


def initialise_device(values):
    '''Initialise the first hydraharp device that is found
    with the values given in values
    '''
    dev = None

    for i in range(8):
        try:
            dev = hhlib_sys.open_device(i)
            break
        except Exception as e:
            if e.__class__.__name__ != 'DeviceFailedToOpen':
                raise e

    hhlib_sys.initialise(dev, 2, 0)
    hhlib_sys.calibrate(dev)

    hhlib_sys.set_sync_CFD(
        dev, values["channel_settings"]["sync_channel"]["discriminator"],
        values["channel_settings"]["sync_channel"]["zero_cross"])
    hhlib_sys.set_sync_channel_offset(
        dev, values["channel_settings"]["sync_channel"]["offset"])

    for i in range(hhlib_sys.get_number_of_input_channels(dev)):
        hhlib_sys.set_input_CFD(
            dev, i,
            values["channel_settings"]["input_channels"][i]["discriminator"],
            values["channel_settings"]["input_channels"][i]["zero_cross"])
        hhlib_sys.set_input_channel_offset(
            dev, i, values["channel_settings"]["input_channels"][i]["offset"])

    sleep(0.2)

    return dev


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = CoincidenceWidget()
    window.show()
    app.exec()
