"""This file contains information about the data structures
of the different classes

-------
Classes
-------

Each pattern is stored inside a pattern dictionary with a uuid4 id 
which is generated when the pattern is made.
Patterns = {uuid: pattern}

This uuid allows the widgets to refer to the data without references.

* Bronwie pattern
A brownie pattern is an ordered list of Rectangles
[Rect]

* Pizza pattern
A pizza pattern has:
inner radius
outer radius
slice spacing
circle span (how much of a circle does the pizza actually go around)

-------
Creating the widgets
-------

Each type of data pattern should also create a widget.
There should be a widget creating function for each pattern
which has registered callbacks.
"""

# from square_splitting import Rect
import numpy as np
from uuid import uuid4
import io
import csv

import PyQt5.QtWidgets as qw
import PyQt5.QtCore as qc
import PyQt5.QtGui as qg

import pyqtgraph as pg

from square_splitting import Rect

brownie_default = [Rect((1, 1), (0, 0), (0, 0))]


class SpinBoxDelegate(qw.QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = pg.SpinBox(parent)
        editor.setFrame(False)

        return editor

    def setEditorData(self, editor, index):
        editor.setValue(index.data())

    def setModelData(self, editor, model, index):
        editor.interpretText()
        value = editor.value()

        model.setData(index, value, qc.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class ChangeValueCommand(qw.QUndoCommand):
    def __init__(self, index, value):
        super().__init__()
        self.index = index
        self.row = index.row()
        self.col = index.column()
        self.old_val = index.data()
        self.new_val = value
        self.setText("Change index ({}, {}) from {} to {}".format(
            self.row, self.col, self.old_val, self.new_val))
        self.model = index.model()

    def redo(self):
        self.model._data[self.row][self.col] = self.new_val
        self.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        self.model._data[self.row][self.col] = self.old_val
        self.model.dataChanged.emit(self.index, self.index)


class ChangeValuesCommand(qw.QUndoCommand):
    def __init__(self, indices, new_values):
        super().__init__()
        self.setText("Setting multiple values")
        self.indices = indices
        self.model = indices[0].model()
        rows = [i.row() for i in indices]
        cols = [i.column() for i in indices]
        self.top_left_index = self.model.index(min(rows), min(cols))
        self.bottom_right_index = self.model.index(max(rows), max(cols))
        self.new_values = new_values
        self.old_values = [i.data() for i in indices]

    def redo(self):
        for i, index in enumerate(self.indices):
            self.model._data[index.row()][index.column()] = self.new_values[i]
        self.model.dataChanged.emit(self.top_left_index,
                                    self.bottom_right_index)

    def undo(self):
        for i, index in enumerate(self.indices):
            self.model._data[index.row()][index.column()] = self.old_values[i]
            self.model.dataChanged.emit(self.top_left_index,
                                        self.bottom_right_index)


class AddRowsCommand(qw.QUndoCommand):
    def __init__(self, row, count, parent):
        super().__init__()
        self.setText("Add {} rows after index {}".format(count, row))
        self.row = row
        self.count = count
        self.model = parent

    def redo(self):
        self.model.beginInsertRows(qc.QModelIndex(), self.row,
                                   self.row + self.count - 1)
        for _ in range(self.count):
            self.model._data.insert(self.row, Rect())
        self.model.endInsertRows()

    def undo(self):
        self.model.beginRemoveRows(qc.QModelIndex(), self.row,
                                   self.row + self.count - 1)
        del self.model._data[self.row:(self.row + self.count)]
        self.model.endRemoveRows()


class RemoveRowsCommand(qw.QUndoCommand):
    def __init__(self, row, count, parent):
        super().__init__()
        self.setText("Remove {} rows after index {}".format(count, row))
        self.row = row
        self.count = count
        self.model = parent
        self.old_data = self.model._data[row:(row + count)]

    def redo(self):
        self.model.beginRemoveRows(qc.QModelIndex(), self.row,
                                   self.row + self.count - 1)
        del self.model._data[self.row:(self.row + self.count)]
        self.model.endRemoveRows()

    def undo(self):
        self.model.beginInsertRows(qc.QModelIndex(), self.row,
                                   self.row + self.count - 1)
        self.model._data[self.row:self.row] = self.old_data
        self.model.endInsertRows()


class ConstantColumnTableModel(qc.QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers
        self._undo_stack = qw.QUndoStack()

    def headerData(self, section, orientation, role):
        if orientation == qc.Qt.Vertical and role == qc.Qt.DisplayRole:
            return section
        if orientation == qc.Qt.Horizontal and role == qc.Qt.DisplayRole:
            return self._headers[section]
        else:
            return None

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._headers)

    def data(self, index, role):
        if role == qc.Qt.DisplayRole:
            return "{}".format(self._data[index.row()][index.column()])
        else:
            return None

    def setData(self, index, value, role):
        if role == qc.Qt.EditRole:
            try:
                self._undo_stack.push(ChangeValueCommand(index, float(value)))
            except ValueError:
                return False
            return True
        else:
            return False

    def setMultiple(self, indices, values):
        """Set multiple indices at the same time without using
        multiple undo commands
        """
        self._undo_stack.push(ChangeValuesCommand(indices, values))

    def flags(self, index):
        return qc.QAbstractItemModel.flags(self, index) | qc.Qt.ItemIsEditable

    def insertRows(self, row, count, parent=qc.QModelIndex()):
        self._undo_stack.push(AddRowsCommand(row, count, self))
        return True

    def removeRows(self, row, count, parent=qc.QModelIndex()):
        self._undo_stack.push(RemoveRowsCommand(row, count, self))
        return True


class ConstantColumnTableView(qw.QTableView):
    """A table view which allows for copying and pasting data
    """
    def __init__(self):
        super().__init__()
        self.setSelectionMode(qw.QAbstractItemView.ContiguousSelection)

    def copySelection(self):
        """Copy the selected cells, separating columns
        by tabs and rows by newlines
        """
        selection = self.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data()
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            qw.qApp.clipboard().setText(stream.getvalue())

    def keyPressEvent(self, event):
        """Add in the custom copy/paste and undo/redo
        """
        if event.matches(qg.QKeySequence.Copy):
            self.copySelection()
        elif event.matches(qg.QKeySequence.Paste):
            self.pasteSelection()
        elif event.matches(qg.QKeySequence.Undo):
            self.model()._undo_stack.undo()
        elif event.matches(qg.QKeySequence.Redo):
            self.model()._undo_stack.redo()
        else:
            super().keyPressEvent(event)

    def pasteSelection(self):
        """Custom copying and pasting
        """
        selection = self.selectedIndexes()
        if selection:
            model = self.model()

            buffer = qw.qApp.clipboard().text()
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            reader = csv.reader(io.StringIO(buffer), delimiter='\t')
            indices = []
            values = []
            if len(rows) == 1 and len(columns) == 1:
                # only one cell is selected
                for i, line in enumerate(reader):
                    for j, cell in enumerate(line):
                        index = model.index(rows[0] + i, columns[0] + j)
                        if index.isValid():
                            indices.append(index)
                            values.append(cell)
            else:
                # more than one cell is selected
                arr = [[cell for cell in row] for row in reader]
                for index in selection:
                    row = index.row() - rows[0]
                    column = index.column() - columns[0]
                    if row < len(arr) and column < len(arr[0]):
                        indices.append(model.index(index.row(),
                                                   index.column()))
                        values.append(arr[row][column])
            model.setMultiple(indices, values)


class BrownieController(ConstantColumnTableView):
    def __init__(self, data):
        super().__init__()
        self._model = ConstantColumnTableModel(
            data, ["width", "height", "x", "y", "a_x", "a_y"])
        self.horizontalHeader().setSectionResizeMode(qw.QHeaderView.Stretch)
        self._delegate = SpinBoxDelegate(self)
        self.setItemDelegate(self._delegate)
        self.setModel(self._model)

    def setDimension(self, dim):
        rows = self.model().rowCount(qc.QModelIndex())
        if dim > rows:
            num_to_insert = dim - rows
            self.model().insertRows(rows, num_to_insert)


if __name__ == "__main__":
    app = qw.QApplication([])
    d = brownie_default.copy()
    r = BrownieController(d)
    r.setDimension(100)
    r.show()
    app.exec()
    print(d)
