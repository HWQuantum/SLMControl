import numpy as np
import matplotlib.pyplot as plt
from time import sleep


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
        self.key = tuplise(new_key)
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
            return tuple(tuplise(i) for i in data)
        elif type(data) == dict:
            return tuple((":key:", k, tuplise(v)) for k, v in data.items())
        else:
            return data


def diagonal_measurement(slm_widget, coincidence_widget, application):
    '''Scan over multiple positions and take the standard deviation of the diagonal to measure the flatness of the state
    '''
    measurement_receiver = MeasurementReceiver()
    return measurement_receiver


diagonal_measurement.__menu_name__ = "Diagonal measurement"
diagonal_measurement.__tooltip__ = "Take a diagonal measurement in the given MUB"
