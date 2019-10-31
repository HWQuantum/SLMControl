from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QAction
from PyQt5.QtCore import QSettings

from slm_controller import MultiSLMController


class ExperimentController(QMainWindow):
    def __init__(self, screens, display_sizes):
        super().__init__()

        layout = QHBoxLayout()
        self.settings = QSettings("HWQuantum", "SLMControl")

        self.slm_controller = MultiSLMController(screens, display_sizes)

        layout.addWidget(self.slm_controller)

        self.internal_widget = QWidget()
        self.internal_widget.setLayout(layout)
        self.setCentralWidget(self.internal_widget)

        
    def create_actions(self):
        pass

    def create_menus(self):
        pass

    def closeEvent(self, event):
        self.slm_controller.close()

        event.accept()

    def set_values(self, slm_values, coincidence_values):
        self.slm_controller.set_values(slm_values)

    def load_values_from_default(self):
        settings = QSettings("HWQuantum", "SLMControl")
        self.set_values(settings.value("slm_settings", {}),
                        settings.value("coincidence_settings", {}))

    def save_values_to_default(self):
        settings = QSettings("HWQuantum", "SLMControl")
        settings.setValue("slm_settings", self.slm_controller.get_values())


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    w = ExperimentController(app.screens(), [(512, 512), (512, 512)])

    w.show()

    app.exec()
