import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import pickle


class MeasurementReceiver:
    """Class used to receive measurement data
    Stores the received data in a dictionary, with a given key
    The dictionary is of the form {key: [data]}
    Where each key has a list of data associated with it
    """
    def __init__(self):
        self.data = {}

    def set_key(self, new_key):
        """Sets the key to store in, converting any lists or dicts to tuples
        with the tuplise function
        """
        self.key = MeasurementReceiver.tuplise(new_key)
        if self.key not in self.data:
            self.data[self.key] = []

    def add_data(self, new_data):
        """Adds data to the associated key
        """
        self.data[self.key].append(new_data)

    def save_data(self, file):
        pickle.dump(self.data, file)

    def tuplise(data):
        """Recursively converts any lists/dicts in data into tuples
        """
        if type(data) == list:
            return tuple(MeasurementReceiver.tuplise(i) for i in data)
        elif type(data) == dict:
            return tuple((":key:", k, MeasurementReceiver.tuplise(v))
                         for k, v in data.items())
        else:
            return data


def diagonal_measurement(slm_widget, coincidence_widget, application):
    '''Scan over multiple positions and take the standard deviation of the diagonal to measure the flatness of the state
    '''
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = slm_widget.slms[0].dimension
    mub = slm_widget.slms[0].mub

    slm_widget.slms[0].dimension = dim
    slm_widget.slms[1].dimension = dim
    slm_widget.slms[0].mub = mub
    slm_widget.slms[1].mub = mub

    diagonal = np.zeros((dim))

    for b in range(dim):
        slm_widget.slms[0].basis = b
        slm_widget.slms[1].basis = b
        application.processEvents()
        sleep(0.2)

        diagonal[
            b] = coincidence_widget.measurement_thread.run_measurement_once(
                integration_time, coincidence_window, histogram_bins,
                sync_channel)[3][3]

    measurement_receiver.set_key('coincidence_data')
    measurement_receiver.add_data(diagonal)

    fig, axs = plt.subplots(1, 1)
    axs.imshow(np.diag(diagonal))
    plt.show()

    return measurement_receiver


diagonal_measurement.__menu_name__ = "Diagonal measurement"
diagonal_measurement.__tooltip__ = "Take a diagonal measurement in the given MUB"


def coincidence_measurement(slm_widget, coincidence_widget, application):
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = slm_widget.slms[0].dimension
    mub = slm_widget.slms[0].mub

    slm_widget.slms[0].dimension = dim
    slm_widget.slms[1].dimension = dim
    slm_widget.slms[0].mub = mub
    slm_widget.slms[1].mub = mub

    coincidences = np.zeros((dim, dim))

    for a in range(dim):
        slm_widget.slms[0].basis = a
        for b in range(dim):
            slm_widget.slms[1].basis = b
            application.processEvents()
            sleep(0.2)
            coincidences[
                a,
                b] = coincidence_widget.measurement_thread.run_measurement_once(
                    integration_time, coincidence_window, histogram_bins,
                    sync_channel)[3][3]

    measurement_receiver.set_key('coincidence_data')
    measurement_receiver.add_data(coincidences)

    fig, axs = plt.subplots(1, 1)
    axs.imshow(coincidences)
    plt.show()

    return measurement_receiver


coincidence_measurement.__menu_name__ = "Coincidence measurement"
coincidence_measurement.__tooltip__ = "Take the whole coincidence matrix in the given MUB"
