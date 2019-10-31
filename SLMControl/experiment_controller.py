from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QAction, QFileDialog
from PyQt5.QtCore import QSettings

from slm_controller import MultiSLMController
# from coincidence_counting import CoincidenceWidget


class ExperimentController(QMainWindow):
    def __init__(self, screens, display_sizes):
        super().__init__()

        layout = QHBoxLayout()

        self.slm_controller = MultiSLMController(screens, display_sizes)
        # self.coincidence_counter =

        layout.addWidget(self.slm_controller)

        self.internal_widget = QWidget()
        self.internal_widget.setLayout(layout)
        self.setCentralWidget(self.internal_widget)

        self.create_menus()
        self.load_values_from_default()

    def create_menus(self):
        save_defaults_action = QAction("Save new defaults", self)
        save_defaults_action.triggered.connect(self.save_values_to_default)
        load_defaults_action = QAction("Load defaults", self)
        load_defaults_action.triggered.connect(self.load_values_from_default)
        save_action = QAction("Save values", self)
        save_action.triggered.connect(self.save_values)
        load_action = QAction("Load values", self)
        load_action.triggered.connect(self.load_values)
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")
        file_menu.addAction(save_defaults_action)
        file_menu.addAction(load_defaults_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)

        experiment_menu = main_menu.addMenu("Experiments")
        for name in [
                "Hello", "There", "testing", "this", "Very", "long", "test"
        ]:
            act = QAction(name, self)
            act.triggered.connect(self.run_experiment)
            experiment_menu.addAction(act)

    def closeEvent(self, event):
        self.slm_controller.close()

        event.accept()

    def set_values(self, slm_values, coincidence_values):
        self.slm_controller.set_values(slm_values)
        # self.coincidence_counter.set_values(coincidence_values)

    def load_values_from_default(self):
        settings = QSettings("HWQuantum", "SLMControl")
        self.set_values(settings.value("slm_settings", {}),
                        settings.value("coincidence_settings", {}))

    def save_values_to_default(self):
        settings = QSettings("HWQuantum", "SLMControl")
        settings.setValue("slm_settings", self.slm_controller.get_values())
        # settings.setValue("coincidence_settings",
        #                   self.coincidence_counter.get_values())

    def load_values(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "")
        if filename:
            settings = QSettings(filename, QSettings.IniFormat)
            self.set_values(settings.value("slm_settings", {}),
                            settings.value("coincidence_settings", {}))

    def save_values(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "")
        if filename:
            settings = QSettings(filename, QSettings.IniFormat)
            settings.setValue("slm_settings", self.slm_controller.get_values())
            # settings.setValue("coincidence_settings",
            #                   self.coincidence_counter.get_values())

    def run_experiment(self):
        from time import sleep
        print("Hi")
        self.setEnabled(False)
        sleep(1)
        self.setEnabled(True)
        print("Ho")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    w = ExperimentController(app.screens(), [(512, 512), (512, 512)])

    w.show()

    app.exec()
