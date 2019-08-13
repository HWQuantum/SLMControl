'''This file defines functions which take measurements
'''
import numpy as np
from time import sleep
import pickle


class MeasurementReceiver:
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


def bell_test_2x2_12345(slm_widget, coincidence_widget, application):
    '''Takes a 2x2 bell test in each of l=[1, 2, 3, 4, 5]
    With an integration time of 20s
    '''
    integration_time = 20000  # integration time in ms
    coincidence_window = 3000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with

    measurement_receiver = MeasurementReceiver()
    angle_a = np.arange(0, 2 * np.pi, np.pi / 2)
    # angle_b = np.linspace(0, 2 * np.pi, 200)
    angle_b = np.arange(0 + np.pi / 4, 2 * np.pi, np.pi / 2)

    measurement_receiver.set_key('coincidence_counter_values')
    measurement_receiver.add_data(coincidence_widget.device_setup.get_values())
    measurement_receiver.set_key('measurement_parameters')
    measurement_receiver.add_data({
        "integration_time": integration_time,
        "coincidence_window": coincidence_window,
        "histogram_bins": histogram_bins,
        "sync_channel": sync_channel,
    })

    for l in [1, 2, 3, 4, 5]:
        for i, a in enumerate(angle_a):
            for j, b in enumerate(angle_b):
                measurement_receiver.set_key(("l_a_b", l, a, b))
                slm_widget.set_values([{
                    "oam_controller": [{
                        "amplitude": 1,
                        "ang_mom": l,
                        "phase": 0,
                    }, {
                        "amplitude": 1,
                        "ang_mom": -l,
                        "phase": a,
                    }]
                }, {
                    "oam_controller": [{
                        "amplitude": 1,
                        "ang_mom": l,
                        "phase": 0,
                    }, {
                        "amplitude": 1,
                        "ang_mom": -l,
                        "phase": b,
                    }]
                }])
                application.processEvents()
                sleep(0.3)
                measurement_receiver.add_data(
                    coincidence_widget.measurement_thread.run_measurement_once(
                        integration_time, coincidence_window, histogram_bins,
                        sync_channel))

            print("Done {}/{}".format(i + 1, len(angle_a)))
    return measurement_receiver


def coincidences_5x5(slm_widget, coincidence_widget, application):
    '''Takes the coincidences for l = [-2..2]
    With an integration time of 10s
    '''
    integration_time = 10000  # integration time in ms
    coincidence_window = 3000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with

    measurement_receiver = MeasurementReceiver()

    measurement_receiver.set_key('coincidence_counter_values')
    measurement_receiver.add_data(coincidence_widget.device_setup.get_values())
    measurement_receiver.set_key('measurement_parameters')
    measurement_receiver.add_data({
        "integration_time": integration_time,
        "coincidence_window": coincidence_window,
        "histogram_bins": histogram_bins,
        "sync_channel": sync_channel,
    })

    for a in [-2, -1, 0, 1, 2]:
        for b in [-2, -1, 0, 1, 2]:
            measurement_receiver.set_key(("l1_l2", a, b))
            slm_widget.set_values([{
                "oam_controller": [{
                    "amplitude": 1,
                    "ang_mom": a,
                    "phase": 0,
                }]
            }, {
                "oam_controller": [{
                    "amplitude": 1,
                    "ang_mom": b,
                    "phase": 0,
                }]
            }])
            application.processEvents()
            sleep(0.3)
            measurement_receiver.add_data(
                coincidence_widget.measurement_thread.run_measurement_once(
                    integration_time, coincidence_window, histogram_bins,
                    sync_channel))

            print("Done a: {}, b: {}".format(a, b))
    return measurement_receiver


def coincidences_5x5_with_concentration(slm_widget, coincidence_widget,
                                        application):
    '''Takes the coincidences for l = [-2..2]
    With an integration time of 10s
    Add in a modification to the 0 mode to try to concentrate it
    '''
    integration_time = 10000  # integration time in ms
    coincidence_window = 3000  # coincidence window in ps
    histogram_bins = 300  # number of bins for the histogram
    sync_channel = 0  # the channel the values should be compared with

    # slm_vals = [(*t.position_controller.get_values(),
    #              *t.diffraction_grating.get_values())
    #             for t in slm_widget.slm_tabs]
    # x, y = np.mgrid[-1:1:500j, -1:1:500j]

    # overlays = [
    #     np.sum([
    #         a * np.exp(1j * (l * np.arctan2(y - p_y, x - p_x)))
    #         for l, a in [(-2, 1), (-1, 0.75), (0, 0.5), (1, 0.75), (2, 1)]
    #     ],
    #            axis=0) for p_x, p_y, d_x, d_y in slm_vals
    # ]
    # for i, o in enumerate(overlays):
    #     slm_widget.slm_tabs[i].overlay = o

    measurement_receiver = MeasurementReceiver()

    measurement_receiver.set_key('coincidence_counter_values')
    measurement_receiver.add_data(coincidence_widget.device_setup.get_values())
    measurement_receiver.set_key('measurement_parameters')
    measurement_receiver.add_data({
        "integration_time": integration_time,
        "coincidence_window": coincidence_window,
        "histogram_bins": histogram_bins,
        "sync_channel": sync_channel,
    })

    l_values = np.linspace(-2, 2, 5)

    for l in l_values:
        slm_widget.set_values([{
            "oam_controller": [{
                "amplitude": 1,
                "ang_mom": l,
                "phase": 0,
            }]
        }, {
            "oam_controller": [{
                "amplitude": 1,
                "ang_mom": -l,
                "phase": 0,
            }]
        }])

        application.processEvents()
        sleep(0.3)

        l_counts.append(
            coincidence_widget.measurement_thread.run_measurement_once(
                20000, coincidence_window, histogram_bins, sync_channel)[3][3])

    print("Found concentrations :^)")

    # these are the normalised values to do concentration with
    l_norms = [min(l_counts)/i for i in l_counts]
    slm_vals = [(*t.position_controller.get_values(),
                 *t.diffraction_grating.get_values())
                for t in slm_widget.slm_tabs]
    x, y = np.mgrid[-1:1:500j, -1:1:500j]

    overlays = []
    overlays.append(
        np.sum([
            a * np.exp(1j *
                       (l_values[i] *
                        np.arctan2(y - slm_vals[0][1], x - slm_vals[0][0])))
            for i, a in enumerate(l_norms)
        ],
               axis=0))
    overlays.append(
        np.sum([
            a * np.exp(1j *
                       (-l_values[i] *
                        np.arctan2(y - slm_vals[1][1], x - slm_vals[1][0])))
            for i, a in enumerate(l_norms)
        ],
               axis=0))

    for i, o in enumerate(overlays):
        slm_widget.slm_tabs[i].overlay = o

    for a in l_values:
        for b in l_values:
            measurement_receiver.set_key(("l1_l2", a, b))
            slm_widget.set_values([{
                "oam_controller": [{
                    "amplitude": 1,
                    "ang_mom": a,
                    "phase": 0,
                }]
            }, {
                "oam_controller": [{
                    "amplitude": 1,
                    "ang_mom": b,
                    "phase": 0,
                }]
            }])
            application.processEvents()
            sleep(0.3)
            measurement_receiver.add_data(
                coincidence_widget.measurement_thread.run_measurement_once(
                    integration_time, coincidence_window, histogram_bins,
                    sync_channel))

            print("Done a: {}, b: {}".format(a, b))
    return measurement_receiver
