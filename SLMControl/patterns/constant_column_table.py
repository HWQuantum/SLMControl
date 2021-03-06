from PyQt5.QtWidgets import QWidget, QUndoCommand, QUndoStack, QTableView, QStyledItemDelegate, QUndoView, QHeaderView, QAbstractItemView, QTableWidget, QLabel, QTableWidgetItem, qApp
from PyQt5 import QtGui
from PyQt5.QtCore import QAbstractTableModel, pyqtSignal, pyqtSlot, Qt, QModelIndex, QItemSelectionModel, QItemSelection, QAbstractItemModel
import numpy as np
import pyqtgraph as pg
import io
import csv


class SpinBoxDelegate(QStyledItemDelegate):
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

        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class ChangeValueCommand(QUndoCommand):
    def __init__(self, index, value, parent):
        super().__init__()
        self.row = index.row()
        self.col = index.column()
        self.old_val = index.data()
        self.new_val = value
        self.setText("Change index ({}, {}) from {} to {}".format(
            self.row, self.col, self.old_val, self.new_val))
        self.model = parent

    def redo(self):
        self.model._data[self.row, self.col] = self.new_val
        self.model.dataChanged.emit(self.model.index(self.row, self.col),
                                    self.model.index(self.row, self.col))

    def undo(self):
        self.model._data[self.row, self.col] = self.old_val
        self.model.dataChanged.emit(self.model.index(self.row, self.col),
                                    self.model.index(self.row, self.col))


class AddRowsCommand(QUndoCommand):
    def __init__(self, row, count, parent):
        super().__init__()
        self.setText("Add {} rows after index {}".format(count, row))
        self.row = row
        self.count = count
        self.model = parent

    def redo(self):
        self.model.beginInsertRows(QModelIndex(), self.row,
                                   self.row + self.count - 1)
        self.model._data = np.insert(self.model._data,
                                     self.row,
                                     np.zeros((self.count,
                                               self.model.columnCount(QModelIndex()))),
                                     axis=0)
        self.model.endInsertRows()

    def undo(self):
        self.model.beginRemoveRows(QModelIndex(), self.row,
                                   self.row + self.count - 1)
        self.model._data = np.delete(self.model._data,
                                     range(self.row, self.row + self.count),
                                     axis=0)
        self.model.endRemoveRows()


class RemoveRowsCommand(QUndoCommand):
    def __init__(self, row, count, parent):
        super().__init__()
        self.setText("Remove {} rows after index {}".format(count, row))
        self.row = row
        self.count = count
        self.model = parent
        self.old_data = self.model._data[row:row + count]

    def redo(self):
        self.model.beginRemoveRows(QModelIndex(), self.row,
                                   self.row + self.count - 1)
        self.model._data = np.delete(self.model._data,
                                     range(self.row, self.row + self.count),
                                     axis=0)
        self.model.endRemoveRows()

    def undo(self):
        self.model.beginInsertRows(QModelIndex(), self.row,
                                   self.row + self.count - 1)
        self.model._data = np.insert(self.model._data,
                                     self.row,
                                     self.old_data,
                                     axis=0)
        self.model.endInsertRows()


class ConstantColumnTableModel(QAbstractTableModel):
    """A class which provides changeable row numbers, but constant column width
    Data is stored in a numpy array
    """
    def __init__(self, initial_rows, headers):
        super().__init__()
        self._data = np.zeros((initial_rows, len(headers)))
        self.undo_stack = QUndoStack()
        self.headers = headers

    def rowCount(self, parent):
        return self._data.shape[0]

    def columnCount(self, parent):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section
        elif orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        else:
            return None

    def data(self, index, role):
        if role != Qt.DisplayRole:
            return None
        else:
            return "{}".format(self._data[index.row(), index.column()])

    def setData(self, index, value, role):
        if role != Qt.EditRole:
            return False
        else:
            try:
                self.undo_stack.push(ChangeValueCommand(index, float(value), self))
            except ValueError as e:
                return False
            return True

    def flags(self, index):
        return QAbstractItemModel.flags(self, index) | Qt.ItemIsEditable

    def insertRows(self, row, count, parent=QModelIndex()):
        self.undo_stack.push(AddRowsCommand(row, count, self))
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        self.undo_stack.push(RemoveRowsCommand(row, count, self))
        return True


class ConstantColumnTableView(QTableView):
    """A table view which allows for copying and pasting data
    """
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.ContiguousSelection)

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
            qApp.clipboard().setText(stream.getvalue())

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copySelection()
        elif event.matches(QtGui.QKeySequence.Paste):
            self.pasteSelection()
        elif event.matches(QtGui.QKeySequence.Undo):
            self.model().undo_stack.undo()
        elif event.matches(QtGui.QKeySequence.Redo):
            self.model().undo_stack.redo()
        else:
            super().keyPressEvent(event)

    def pasteSelection(self):
        selection = self.selectedIndexes()
        if selection:
            model = self.model()

            buffer = qApp.clipboard().text()
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            reader = csv.reader(io.StringIO(buffer), delimiter='\t')
            if len(rows) == 1 and len(columns) == 1:
                # only one cell is selected
                for i, line in enumerate(reader):
                    for j, cell in enumerate(line):
                        index = model.index(rows[0] + i, columns[0] + j)
                        if index.isValid():
                            model.setData(
                                model.index(rows[0] + i, columns[0] + j), cell,
                                Qt.EditRole)
            else:
                # more than one cell is selected
                arr = [[cell for cell in row] for row in reader]
                for index in selection:
                    row = index.row() - rows[0]
                    column = index.column() - columns[0]
                    if row < len(arr) and column < len(arr[0]):
                        model.setData(model.index(index.row(), index.column()),
                                      arr[row][column], Qt.EditRole)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    m = ConstantColumnTableModel(100, ["hi", "there", "wow"])

    w = ConstantColumnTableView()
    w.setModel(m)
    de = SpinBoxDelegate(w)
    w.setItemDelegate(de)
    w.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    w.show()
    from PyQt5.QtWidgets import QPushButton
    v = QUndoView()
    v.setStack(m.undo_stack)
    v.show()

    app.exec()
