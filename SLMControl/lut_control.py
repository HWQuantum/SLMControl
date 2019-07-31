from PyQt5.QtWidgets import QWidget, QFormLayout, QGridLayout, QScrollArea, QPushButton
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from scipy.interpolate import CubicSpline
import numpy as np

from oam_pattern_controls import XYController, CloseWrapper


class LUTPoints(QWidget):
    '''Contains the list of points in the lookup table
    '''
    value_changed = pyqtSignal(list)

    def __init__(self, points=[(-np.pi, 0), (np.pi, 255)]):
        '''points is a list of tuples - (x, y)
        '''
        super().__init__()
        self.layout = QFormLayout()
        self.set_values(points)

        self.setLayout(self.layout)

    def add_point(self, point=(0, 0)):
        '''Point is a tuple - (x, y)
        '''
        controller = XYController('LUT Point')
        controller.x.setOpts(bounds=(-np.pi, np.pi))
        controller.y.setOpts(bounds=(0, 255), int=True, step=1)
        controller.set_values(point)
        wrapped_controller = CloseWrapper(controller)
        wrapped_controller.close.connect(
            lambda: self.remove_pattern(wrapped_controller))

        self.layout.addRow(wrapped_controller)
        self.value_changed.emit(self.get_values())

    def remove_all_rows(self):
        while self.layout.rowCount() > 0:
            self.layout.removeRow(0)
        self.value_changed.emit([])

    def remove_pattern(self, pattern):
        '''Remove the given pattern from the set
        '''
        self.layout.removeRow(pattern)
        self.value_changed.emit(self.get_values())

    def get_values(self):
        '''Get the points contained and return them in a list
        [(x, y)]
        '''
        return [
            self.layout.itemAt(i).widget().wrapped.get_values()
            for i in range(self.layout.count())
        ]

    def set_values(self, points):
        '''Set the values from a list of points [(x, y)]
        Each self.add_point emits a value_changed signal,
        so don't need to do one here
        '''
        self.remove_all_rows()
        for point in points:
            self.add_point(point)


class LUTWidget(QWidget):
    '''Defines a lookup table
    '''
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()

        self.points_widget = LUTPoints()
        self.add_point = QPushButton("Add LUT Point")
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.points_widget)
        scroll_area.setWidgetResizable(True)

        self.add_point.clicked.connect(self.points_widget.add_point)

        self.layout.addWidget(self.add_point, 0, 0)
        self.layout.addWidget(scroll_area, 1, 0)

        self.setLayout(self.layout)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = LUTWidget()
    window.show()
    app.exec()
