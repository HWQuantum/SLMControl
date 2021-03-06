from PyQt5.QtWidgets import QWidget, QFormLayout, QGridLayout, QScrollArea, QPushButton, QHBoxLayout, QGroupBox
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import pyqtgraph as pg
import numpy as np

from pattern import XYController

LUT_plot_xs = np.linspace(-np.pi, np.pi, 100)


class CloseWrapper(QGroupBox):
    """Wrap a widget with a close button
    """
    close = pyqtSignal()

    def __init__(self, other_widget):
        super().__init__()
        self.wrapped = other_widget

        layout = QHBoxLayout()
        close = QPushButton("Close")

        close.clicked.connect(self.close.emit)

        layout.addWidget(self.wrapped, 6)
        layout.addWidget(close, 1)

        self.setLayout(layout)


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
        controller.value_changed.connect(
            lambda: self.value_changed.emit(self.get_values()))
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
        vals = [
            self.layout.itemAt(i).widget().wrapped.get_values()
            for i in range(self.layout.count())
        ]
        vals.sort(key=lambda p: p[0])
        # Remove any points duplicate in x (For CubicSpline function)
        index = 0
        while index < len(vals):
            if index != 0:
                if vals[index][0] == vals[index - 1][0]:
                    vals.pop(index)
                else:
                    index += 1
            else:
                index += 1
        return vals

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
    value_changed = pyqtSignal(list)
    closed = pyqtSignal()

    def __init__(self, points=[(-np.pi, 0), (np.pi, 255)]):
        super().__init__()
        self.layout = QGridLayout()

        self.points_widget = LUTPoints(points)
        self.add_point = QPushButton("Add LUT Point")
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.points_widget)
        scroll_area.setWidgetResizable(True)

        self.plot = pg.PlotWidget()
        self.plot.setLimits(xMin=-np.pi - 0.1,
                            xMax=np.pi + 0.1,
                            yMin=0 - 3,
                            yMax=255 + 3,
                            minXRange=2 * np.pi + 0.2,
                            maxXRange=2 * np.pi + 0.2,
                            minYRange=255 + 6,
                            maxYRange=255 + 6)
        self.plot_line = self.plot.plot()
        self.plot_points = pg.ScatterPlotItem(size=10,
                                              pen=pg.mkPen(None),
                                              brush=pg.mkBrush(
                                                  255, 255, 255, 120))
        self.plot.addItem(self.plot_points)

        self.add_point.clicked.connect(self.points_widget.add_point)

        self.layout.addWidget(self.add_point, 0, 0)
        self.layout.addWidget(scroll_area, 1, 0)
        self.layout.addWidget(self.plot, 0, 1, 2, 1)
        self.points_widget.value_changed.connect(lambda i: self.set_plot(i))
        self.points_widget.value_changed.connect(
            lambda i: self.value_changed.emit(i))

        self.setLayout(self.layout)

        self.set_plot(self.points_widget.get_values())

    def set_plot(self, points):
        if len(points) >= 2:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            self.plot_line.setData(LUT_plot_xs, np.interp(LUT_plot_xs, xs, ys))
            self.plot_points.setData(xs, ys)

    def closeEvent(self, event):
        self.closed.emit()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    window = LUTWidget()
    window.show()
    app.exec()
