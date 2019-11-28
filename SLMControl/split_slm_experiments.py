import numpy as np
import matplotlib.pyplot as plt
from time import sleep
from square_splitting import Rect
import pickle
import time

from experiments import MeasurementReceiver

SLEEP_TIME = 1 # sleeping time in seconds

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
        sleep(SLEEP_TIME)

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
    
    def QC(rho):
        """Calculate the quantum contrast from the diagonals 
        of a coincidence matrix
        """
        off_diag_avg = (rho.sum() - rho.diagonal().sum()) / (rho.shape[0] *
                                                            (rho.shape[1] - 1))
        return np.average(rho.diagonal()) / off_diag_avg

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
            sleep(SLEEP_TIME)
            coincidences[
                a,
                b] = coincidence_widget.measurement_thread.run_measurement_once(
                    integration_time, coincidence_window, histogram_bins,
                    sync_channel)[3][3]

    measurement_receiver.set_key('coincidence_data')
    measurement_receiver.add_data(coincidences)

    np.savetxt("last_measurement_{}".format(time.strftime("%Y_%m_%d-%H_%M_%S")), coincidences, fmt="%.1f", footer="QC = {}".format(QC(coincidences)))
    fig, axs = plt.subplots(1, 1)
    axs.imshow(coincidences)
    plt.show()

    return measurement_receiver


coincidence_measurement.__menu_name__ = "Coincidence measurement"
coincidence_measurement.__tooltip__ = "Take the whole coincidence matrix in the given MUB"


def multi_pos_coincidence_measurement(s, coincidence_widget, application):
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with
    dim = s.alice_dimension
    mub = s.alice_mub

    a_x, a_y = s.alice.position.get_values()
    b_x, b_y = s.bob.position.get_values()

    num_pos = 3

    pos_range = np.linspace(-0.012, 0.012, num_pos)

    s.alice_dimension = dim
    s.bob_dimension = dim
    s.alice_mub = mub
    s.bob_mub = mub

    coincidences = np.zeros((num_pos, num_pos, dim, dim))

    for i, p_x in enumerate(pos_range):
        for j, p_y in enumerate(pos_range):
            s.alice.position.set_values((a_x + p_x, a_y + p_y))
            s.bob.position.set_values((b_x + p_x, b_y + p_y))
            for a in range(dim):
                s.alice_basis = a
                for b in range(dim):
                    s.bob_basis = b
                    application.processEvents()
                    sleep(0.2)
                    coincidences[
                        i, j, a,
                        b] = coincidence_widget.measurement_thread.run_measurement_once(
                            integration_time, coincidence_window,
                            histogram_bins, sync_channel)[3][3]

    measurement_receiver.set_key('coincidence_data')
    measurement_receiver.add_data(coincidences)

    fig, axs = plt.subplots(num_pos, num_pos)
    for i, row in enumerate(axs):
        for j, ax in enumerate(row):
            ax.imshow(coincidences[i, j])
    plt.show()

    return measurement_receiver


multi_pos_coincidence_measurement.__menu_name__ = "Multi Pos coincidence measurement"
multi_pos_coincidence_measurement.__tooltip__ = "Take the whole coincidence matrix at multiple positions in the given MUB"


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

    coincidences = np.zeros((dim, dim, dim, dim))

    for mub_a in range(1, dim + 1):
        s.alice_mub = mub_a
        for mub_b in range(1, dim + 1):
            s.bob_mub = mub_b
            for a in range(dim):
                s.alice_basis = a
                for b in range(dim):
                    s.bob_basis = b
                    application.processEvents()
                    sleep(0.15)
                    coincidences[
                        mub_a-1, mub_b-1, a,
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


def all_mub_corrected_coincidence_measurement(s, coincidence_widget,
                                              application):
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
    mub_pairs = [(0, 0), (1, 1), (2, 7), (3, 6), (4, 5), (5, 4), (6, 3),
                 (7, 2)]

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


def split_square_test(s, coincidence_widget, application):
    """Split the first square on both controllers and test the coincidences
    """
    measurement_receiver = MeasurementReceiver()
    integration_time = coincidence_widget.device_measurement.measurement_time.value(
    )  # integration time in ms
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with

    old_sq_a = s.alice.patterns[2].get_values()
    old_sq_b = s.bob.patterns[2].get_values()

    b_a = s.split_control.basis_a.value()
    b_b = s.split_control.basis_b.value()

    square_a = Rect((old_sq_a[b_a][2], old_sq_a[b_a][3]),
                    (old_sq_a[b_a][0], old_sq_a[b_a][1]), (0.5, 0.5))
    square_b = Rect((old_sq_b[b_b][2], old_sq_b[b_b][3]),
                    (old_sq_b[b_b][0], old_sq_b[b_b][1]), (0.5, 0.5))

    distance_a = s.split_control.distance_a.value()
    distance_b = s.split_control.distance_b.value()

    splits_a = s.split_control.range_n_a.value()
    splits_b = s.split_control.range_n_b.value()

    r_min_a = s.split_control.range_min_a.value()
    r_min_b = s.split_control.range_min_b.value()
    r_max_a = s.split_control.range_max_a.value()
    r_max_b = s.split_control.range_max_b.value()

    horizontal = s.split_control.horizontal.isChecked()

    s.alice_mub = 0
    s.bob_mub = 0

    s.alice_dimension = 2
    s.bob_dimension = 2

    split_data = np.zeros((splits_a, splits_b, 2, 2))

    a_squares = []
    b_squares = []

    for i, alice_split in enumerate(np.linspace(r_min_a, r_max_a, splits_a)):
        a_s_1, a_s_2 = square_a.split_in_half(not horizontal, distance_a,
                                              alice_split)
        a_squares.append((a_s_1, a_s_2))
        s.alice.patterns[2].set_values([[*p.centre, p.size[0], p.size[1]]
                                        for p in [a_s_1, a_s_2]])
        for j, bob_split in enumerate(np.linspace(r_min_b, r_max_b, splits_b)):
            b_s_1, b_s_2 = square_b.split_in_half(not horizontal, distance_b,
                                                  bob_split)
            if j == 0:
                b_squares.append((b_s_1, b_s_2))
            s.bob.patterns[2].set_values([[*p.centre, p.size[0], p.size[1]]
                                          for p in [b_s_1, b_s_2]])
            for a_i in [0, 1]:
                s.alice_basis = a_i
                for b_i in [0, 1]:
                    s.bob_basis = b_i
                    application.processEvents()
                    sleep(0.15)
                    split_data[
                        i, j, a_i,
                        b_i] = coincidence_widget.measurement_thread.run_measurement_once(
                            integration_time, coincidence_window,
                            histogram_bins, sync_channel)[3][3]

    fig, axs = plt.subplots(splits_a, splits_b)
    for i, row in enumerate(axs):
        for j, ax in enumerate(row):
            ax.imshow(split_data[i, j])
    plt.show()

    np.save("split_data", split_data)

    print("A squares")
    for i, (sq_a_1, sq_a_2) in enumerate(a_squares):
        print("{}: {}, {} --- {}, {}".format(i, sq_a_1.centre, sq_a_1.size,
                                             sq_a_2.centre, sq_a_2.size))
    print("B squares")
    for i, (sq_a_1, sq_a_2) in enumerate(b_squares):
        print("{}: {}, {} --- {}, {}".format(i, sq_a_1.centre, sq_a_1.size,
                                             sq_a_2.centre, sq_a_2.size))

    s.alice.patterns[2].set_values(old_sq_a)
    s.bob.patterns[2].set_values(old_sq_b)


split_square_test.__menu_name__ = "Split square test"
split_square_test.__tooltip__ = "Split square test"


def weekend_measurement(s, coinc_wid, app):
    """The basis should be defined in 7 dim - this function will reduce the dimension as it progresses
    """
    comp_mub_integration_time = 300000
    other_integration_time = 80000
    sleep_time = 2
    coincidence_window = 6000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with

    original_data_a = s.alice.patterns[2].get_values()
    original_data_b = s.bob.patterns[2].get_values()

    for d in np.arange(7, 1, -1):
        if (d % 2) != 0:
            mub_range = range(d + 1)
            dim_data = np.zeros((d + 1, d, d))
        else:
            mub_range = [0, 1]
            dim_data = np.zeros((2, d, d))
        # Then d is prime, and we should do all mubs
        s.alice_dimension = d
        s.bob_dimension = d
        for mub in mub_range:
            if mub < 2:
                # then it's a comp or fourier mub, we can just apply to both
                alice_mub = mub
                bob_mub = mub
            else:
                alice_mub = mub
                bob_mub = (d + 2) - mub
            s.alice_mub = alice_mub
            s.bob_mub = bob_mub
            for a_basis in range(d):
                s.alice_basis = a_basis
                for b_basis in range(d):
                    s.bob_basis = b_basis
                    app.processEvents()
                    sleep(sleep_time)
                    if mub == 0:
                        dim_data[
                            mub, a_basis,
                            b_basis] = coinc_wid.measurement_thread.run_measurement_once(
                                comp_mub_integration_time, coincidence_window,
                                histogram_bins, sync_channel)[3][3]
                    else:
                        dim_data[
                            mub, a_basis,
                            b_basis] = coinc_wid.measurement_thread.run_measurement_once(
                                other_integration_time, coincidence_window,
                                histogram_bins, sync_channel)[3][3]
        np.save("weekend_run_data_dim_{}".format(d), dim_data)

    s.alice.patterns[2].set_values(original_data_a)
    s.bob.patterns[2].set_values(original_data_b)


weekend_measurement.__menu_name__ = "Weekend Measurement"
weekend_measurement.__tooltip__ = "Weekend Measurement"
