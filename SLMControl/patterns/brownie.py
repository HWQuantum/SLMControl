from PyQt5.QtWidgets import QWidget, QUndoCommand, QUndoStack, QTableView, QStyledItemDelegate
from PyQt5.QtCore import QAbstractTableModel, pyqtSignal, pyqtSlot, Qt
import numpy as np
import pyqtgraph as pg


class SpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = pg.SpinBox(parent)
        editor.setFrame(False)

        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        editor.interpretText()
        value = editor.value()

        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect);


class BrownieModel(QAbstractTableModel):

    headers = ["Width", "Height", "x", "y", "Rect x", "Rect y"]

    def __init__(self, dimension):
        super().__init__()
        self._data = np.random.random((dimension, 6))

    def rowCount(self, parent):
        return self._data.shape[0]

    def columnCount(self, parent):
        return 6

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
                self._data[index.row(), index.column()] = value
            except ValueError as ve:
                return False
            return True

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    m = BrownieModel(7)

    w = QTableView()
    w.setModel(m)
    de = SpinBoxDelegate(w)
    w.setItemDelegate(de)
    w.show()


    app.exec()
