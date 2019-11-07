from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QSizePolicy, QHeaderView
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg

import numpy as np
from numba import njit

@njit()
def point_in_square(px, py, sx, sy, w, h):
    """Check if the point (px, py) is inside the square defined by
    the centre (sx, sy) and width and height (w, h)
    """
    lx = sx-w/2
    rx = sx+w/2
    ty = sy+h/2
    by = sy-h/2
    return (lx <= px < rx) and (by <= py < ty)


class ShapeController(QTableWidget):
    """ShapeController gives the controls for a set of shapes
    """

    value_changed = pyqtSignal()

    def __init__(self, dim):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["x", "y", "width", "height"])
        self.set_values([[2, 3, 4, 5], [4, 3, 5, 4], [4, 5, 6, 7]])

    @pyqtSlot()
    def add_row(self, row_data=[0, 0, 0, 0]):
        """Add a row, optionally giving the data to be added
        """
        new_row_index = self.rowCount()
        self.insertRow(new_row_index)
        x = pg.SpinBox(value=row_data[0])
        y = pg.SpinBox(value=row_data[1])
        w = pg.SpinBox(value=row_data[2])
        h = pg.SpinBox(value=row_data[3])
        self.setCellWidget(new_row_index, 0, x)
        self.setCellWidget(new_row_index, 1, y)
        self.setCellWidget(new_row_index, 2, w)
        self.setCellWidget(new_row_index, 3, h)

    @pyqtSlot()
    def remove_row(self, index=None):
        """Remove a row. If index is None, remove the last row
        otherwise remove at the index
        """
        if index is None:
            self.removeRow(self.rowCount() - 1)

        else:
            self.removeRow(index)

    def get_values(self):
        """Return the contained values in a list of lists [[x, y, w, h]]
        """
        return [[
            self.cellWidget(row, col).value()
            for col in range(self.columnCount())
        ] for row in range(self.rowCount())]

    def set_dimension(self, d):
        """Set the dimension of the table.
        Removes widgets from the end if too large
        Adds widgets to the end if too small.
        """
        row_count = self.rowCount()
        if d == row_count:
            return
        elif d > row_count:
            for _ in range(d - row_count):
                self.add_row()
        else:
            for _ in range(row_count - d):
                self.remove_row()

    def set_values(self, values):
        """Set the values from a list of lists [[x, y, w, h]]
        """
        row_count = self.rowCount()
        d = len(values)

        if d < row_count:
            for _ in range(row_count-d):
                self.remove_row()
            row_count = d

        elif d > row_count:
            for row in values[row_count:]:
                self.add_row(row)
        for i, row in enumerate(values[:row_count]):
            for j, col in enumerate(row):
                self.cellWidget(i, j).setValue(col)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = ShapeController(2)
    w.show()

    # app.exec()
    print(point_in_square(0, 0, 1, 1, 1, 1))
