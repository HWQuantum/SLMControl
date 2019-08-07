from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGridLayout, QTabWidget, QGroupBox, QLabel, QScrollArea, QHBoxLayout
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
    measurement_done = pyqtSignal(list, list, list)

    def __init__(self, device):
        super().__init__()
        self.dev = device

    @pyqtSlot(int)
    def run_measurement(self, time):
        values = hhlib_sys.measure_and_get_counts(self.dev, time, 50000, 100, 0)
        self.measurement_done.emit(*values)


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
        self.layout = QVBoxLayout()
        self.sync_channel = ChannelSetting("Sync Channel")
        self.layout.addWidget(self.sync_channel)
        self.input_channels = []
        for i in range(8):

            c = ChannelSetting("Input Channel {}".format(i))
            self.layout.addWidget(c)
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
                        getattr(self, key).setValue(value)
                    except AttributeError:
                        pass
        for key, value in kwargs.items():
            if key == "input_channels":
                for i, v in enumerate(value):
                    self.input_channels[i].set_values(v)
            else:
                try:
                    getattr(self, key).setValue(value)
                except AttributeError:
                    pass


class DeviceSetup(QWidget):
    '''Widget which controls the initialisation of a counting device
    '''
    device_initialised = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.initialise = QPushButton("Initialise Device")

        self.channel_settings = ChannelSettingContainer()

        channel_scroll_area = QScrollArea()
        channel_scroll_area.setWidget(self.channel_settings)

        channel_scroll_area.setWidgetResizable(False)

        self.initialise.clicked.connect(self.init_device)
        self.device_initialised.connect(lambda: self.setEnabled(True))

        self.layout.addWidget(channel_scroll_area, 0, 0)
        self.layout.addWidget(self.initialise, 1, 0)
        self.setLayout(self.layout)

    @pyqtSlot()
    def init_device(self):
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

        values = self.channel_settings.get_values()

        hhlib_sys.set_sync_CFD(dev, values["sync_channel"]["discriminator"],
                               values["sync_channel"]["zero_cross"])
        hhlib_sys.set_sync_channel_offset(dev,
                                          values["sync_channel"]["offset"])

        for i in range(hhlib_sys.get_number_of_input_channels(dev)):
            hhlib_sys.set_input_CFD(
                dev, i, values["input_channels"][i]["discriminator"],
                values["input_channels"][i]["zero_cross"])
            hhlib_sys.set_input_channel_offset(
                dev, i, values["input_channels"][i]["offset"])

        sleep(0.2)

        if dev is not None:
            self.device_initialised.emit(dev)
        else:
            print("Couldn't initialise device!")
            self.device_initialised.emit(dev)

    @pyqtSlot(bool)
    def enable_device_interaction(self, enable):
        self.initialise.setEnabled(enable)


class CoincidencePlot(pg.PlotWidget):
    '''A coincidences plot, which stores
    number_of_values values, and pushes values in to the
    right
    '''
    def __init__(self, number_of_values):
        super().__init__()
        self.data = np.zeros((number_of_values))
        self.coincidence_plot = self.plot(self.data)

    @pyqtSlot(float)
    def add_new_value(self, x):
        '''Adds a new value to the data
        '''
        self.data = np.roll(self.data, -1)
        self.data[-1] = x
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
        pens = [pg.mkPen('b'), pg.mkPen('r')]
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


class DeviceMeasurement(QWidget):
    '''Widget which displays and orders measurements from
    a counting device


    The measurement_button_first_push keeps track of whether
    it's the first time the toggle has been pushed, to stop
    queueing up measurements in the measurement thread
    '''
    # run a measurement for a given number of ms
    run_measurement = pyqtSignal(int)

    enable_device_settings_interaction = pyqtSignal(bool)

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
        self.histogram = self.histogram_plot.plot([0, 1], [1],
                                                  stepMode=True,
                                                  fillLevel=0,
                                                  brush=(0, 0, 255, 150))

        self.coincidence_plot = CoincidencePlot(100)
        self.singles_plot = SinglesPlot(100)

        self.run_measurement_button = QPushButton("Run measurement")

        self.run_measurement_button.setCheckable(True)
        self.run_measurement_button.clicked.connect(self.try_run_measurement)
        self.measurement_button_first_push = True


        self.layout.addWidget(self.histogram_plot, 0, 0, 3, 1)
        self.layout.addWidget(self.run_measurement_button, 0, 1)
        self.layout.addWidget(self.measurement_time, 1, 1)
        self.layout.addWidget(self.coincidence_plot, 3, 0, 2, 1)
        self.layout.addWidget(self.singles_plot, 3, 1, 2, 1)

        self.setLayout(self.layout)
        self.setEnabled(False)

    @pyqtSlot(list, list, list)
    def update_data(self, singles, coincs, hists):
        '''Update the plots based on the counts data'''
        self.histogram.setData(np.linspace(0, 1, len(hists[3])+1), hists[3])
        self.coincidence_plot.add_new_value(coincs[3])
        self.singles_plot.add_new_values([singles[0], singles[3]])
        if self.run_measurement_button.isChecked():
            # we want to take another measurement
            self.run_measurement.emit(self.measurement_time.value())
        else:
            # reset the toggle, so that another measurement can be queued
            self.measurement_button_first_push = True
            self.enable_device_settings_interaction.emit(True)

    @pyqtSlot(bool)
    def try_run_measurement(self, checked):
        if checked:
            # the measurement button has been toggled on
            if self.measurement_button_first_push:
                self.run_measurement.emit(self.measurement_time.value())
                self.measurement_button_first_push = False
                self.enable_device_settings_interaction.emit(False)

    @pyqtSlot(object)
    def get_device(self, dev):
        '''Assign the initialised device
        '''
        self.setEnabled(True)

        self.measurement_thread = QThread()
        self.test = MeasurementThread(dev)
        self.test.moveToThread(self.measurement_thread)
        self.test.measurement_done.connect(self.update_data)
        self.run_measurement.connect(self.test.run_measurement)
        self.measurement_thread.start()


class CoincidenceWidget(QWidget):
    run_measurement = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.device_measurement = DeviceMeasurement()
        self.device_setup = DeviceSetup()

        self.device_measurement.enable_device_settings_interaction.connect(
            self.device_setup.enable_device_interaction)

        self.device_setup.device_initialised.connect(self.device_measurement.get_device)

        self.tab_widget.addTab(self.device_setup, "Device Setup")
        self.tab_widget.addTab(self.device_measurement, "Plot")

        self.layout.addWidget(self.tab_widget)

        self.setLayout(self.layout)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = CoincidenceWidget()
    window.show()
    app.exec()
