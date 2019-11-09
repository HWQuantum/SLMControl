import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import pickle

from experiments import MeasurementReceiver


def diagonal_measurement(s, coincidence_widget, application):
    '''Scan over multiple positions and take the standard deviation of the diagonal to measure the flatness of the state
    '''
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = s.alice_dimension
    mub = s.alice_mub

    s.alice_dimension = dim
    s.bob_dimension = dim
    s.alice_mub = mub
    s.bob_mub = mub

    diagonal = np.zeros((dim))

    for b in range(dim):
        s.alice_basis = b
        s.bob_basis = b
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


def coincidence_measurement(s, coincidence_widget, application):
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = s.alice_dimension
    mub = s.alice_mub

    s.alice_dimension = dim
    s.bob_dimension = dim
    s.alice_mub = mub
    s.bob_mub = mub

    coincidences = np.zeros((dim, dim))

    for a in range(dim):
        s.alice_basis = a
        for b in range(dim):
            s.bob_basis = b
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


def all_mub_coincidence_measurement(s, coincidence_widget, application):
    """Measure the coincidence matrix in all mubs
    """
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = s.alice_dimension

    s.alice_dimension = dim
    s.bob_dimension = dim

    coincidences = np.zeros((dim + 1, dim, dim))

    for mub in range(dim + 1):
        s.alice_mub = mub
        s.bob_mub = mub
        for a in range(dim):
            s.alice_basis = a
            for b in range(dim):
                s.bob_basis = b
                application.processEvents()
                sleep(0.15)
                coincidences[
                    mub, a,
                    b] = coincidence_widget.measurement_thread.run_measurement_once(
                        integration_time, coincidence_window, histogram_bins,
                        sync_channel)[3][3]

    measurement_receiver.set_key('coincidence_data')
    measurement_receiver.add_data(coincidences)
    with open("all_mubs_measurement_{}_dim".format(dim), "wb") as f:
        measurement_receiver.save_data(f)

    fig, axs = plt.subplots(1, dim + 1)
    for i, ax in enumerate(axs):
        ax.imshow(coincidences[i])
    plt.show()

    return measurement_receiver


all_mub_coincidence_measurement.__menu_name__ = "All MUB Coincidence Measurement"
all_mub_coincidence_measurement.__tooltip__ = "Measure the coincidence matrix in all MUBs"


def every_single_mub_coincidence_measurement(s, coincidence_widget,
                                             application):
    """Measure the coincidence matrix in all mubs vs all mubs
    """
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = s.alice_dimension

    s.alice_dimension = dim
    s.bob_dimension = dim

    coincidences = np.zeros((dim + 1, dim + 1, dim, dim))

    for mub_a in range(dim + 1):
        s.alice_mub = mub_a
        for mub_b in range(dim + 1):
            s.bob_mub = mub_b
            for a in range(dim):
                s.alice_basis = a
                for b in range(dim):
                    s.bob_basis = b
                    application.processEvents()
                    sleep(0.15)
                    coincidences[
                        mub_a, mub_b, a,
                        b] = coincidence_widget.measurement_thread.run_measurement_once(
                            integration_time, coincidence_window,
                            histogram_bins, sync_channel)[3][3]

    measurement_receiver.set_key('coincidence_data')
    measurement_receiver.add_data(coincidences)
    with open("every_single_mub_measurement_{}_dim".format(dim), "wb") as f:
        measurement_receiver.save_data(f)

    return measurement_receiver


every_single_mub_coincidence_measurement.__menu_name__ = "EVERY SINGLE MUB Coincidence Measurement"
every_single_mub_coincidence_measurement.__tooltip__ = "Measure the coincidence matrix in all combinations of MUBs"

def all_mub_corrected_coincidence_measurement(s, coincidence_widget, application):
    """Measure the coincidence matrix in all mubs
    """
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = s.alice_dimension

    s.alice_dimension = dim
    s.bob_dimension = dim

    coincidences = np.zeros((dim + 1, dim, dim))
    mub_pairs = [(0, 0), (1, 1), (2, 7), (3, 6), (4, 5), (5, 4), (6, 3), (7, 2)]

    for mub_a, mub_b in mub_pairs:
        s.alice_mub = mub_a
        s.bob_mub = mub_b
        for a in range(dim):
            s.alice_basis = a
            for b in range(dim):
                s.bob_basis = b
                application.processEvents()
                sleep(0.15)
                coincidences[
                    mub_a, a,
                    b] = coincidence_widget.measurement_thread.run_measurement_once(
                        integration_time, coincidence_window, histogram_bins,
                        sync_channel)[3][3]

    measurement_receiver.set_key('coincidence_data')
    measurement_receiver.add_data(coincidences)
    with open("all_mubs_corrected_measurement_{}_dim".format(dim), "wb") as f:
        measurement_receiver.save_data(f)

    fig, axs = plt.subplots(1, dim + 1)
    for i, ax in enumerate(axs):
        ax.imshow(coincidences[i])
    plt.show()

    return measurement_receiver


all_mub_corrected_coincidence_measurement.__menu_name__ = "All MUB corrected Coincidence Measurement"
all_mub_corrected_coincidence_measurement.__tooltip__ = "Measure the corrected coincidence matrix in all MUBs"
