import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon


CONFIG_FILE = 'config.json'

class ConfigDialog(QDialog):
    def __init__(self, work_time, break_time, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Configuración')
        self.setGeometry(150, 150, 300, 150)

        self.layout = QFormLayout(self)

        self.work_time_input = QLineEdit(self)
        self.work_time_input.setPlaceholderText(str(work_time // 60))
        self.layout.addRow("Tiempo de trabajo (min):", self.work_time_input)

        self.break_time_input = QLineEdit(self)
        self.break_time_input.setPlaceholderText(str(break_time // 60))
        self.layout.addRow("Tiempo de descanso (min):", self.break_time_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_values(self, current_work_time, current_break_time):
        work_time = self.work_time_input.text()
        break_time = self.break_time_input.text()

        if work_time and not work_time.isdigit():
            QMessageBox.warning(self, "Entrada inválida", "Por favor, introduce un valor numérico válido para el tiempo de trabajo.")
            return None, None

        if break_time and not break_time.isdigit():
            QMessageBox.warning(self, "Entrada inválida", "Por favor, introduce un valor numérico válido para el tiempo de descanso.")
            return None, None

        work_time = int(work_time) if work_time else current_work_time // 60
        break_time = int(break_time) if break_time else current_break_time // 60

        return work_time, break_time

class PomodoroApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_config()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QLabel {
                background-color: #000000;
                color: #f7ffff;
                font-size: 48px;
                qproperty-alignment: 'AlignCenter';
            }
            QPushButton {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
        """)
        self.setWindowTitle('Pomodoro Timer')
        self.setGeometry(100, 100, 300, 250)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.session_label = QLabel("Trabajo", self)
        self.session_label.setAlignment(Qt.AlignCenter)
        self.session_label.setStyleSheet("font-size: 16px;")

        self.label = QLabel("25:00", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_timer)

        self.pause_button = QPushButton('Pause', self)
        self.pause_button.clicked.connect(self.pause_timer)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_timer)

        self.next_button = QPushButton('Next', self)
        self.next_button.clicked.connect(self.next_phase)

        self.config_button = QPushButton('Config', self)
        self.config_button.clicked.connect(self.open_config)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.stop_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.session_label)
        main_layout.addWidget(self.label)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.config_button)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.work_time = 25 * 60  # 25 minutes
        self.break_time = 5 * 60  # 5 minutes
        self.time_left = self.work_time
        self.is_working = True

    def start_timer(self):
        self.timer.start(1000)

    def pause_timer(self):
        self.timer.stop()

    def stop_timer(self):
        self.timer.stop()
        self.time_left = self.work_time if self.is_working else self.break_time
        self.update_display()

    def next_phase(self):
        try:
            self.timer.stop()  # Asegúrate de detener el temporizador antes de cambiar de fase
            self.is_working = not self.is_working
            self.time_left = self.work_time if self.is_working else self.break_time
            self.session_label.setText("Trabajo" if self.is_working else "Descanso")
            self.update_display()
            self.start_timer()  # Inicia el temporizador automáticamente cuando cambia la fase
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ha ocurrido un error: {e}")


    def update_timer(self):
        self.time_left -= 1
        self.update_display()

        if self.time_left <= 0:
            self.next_phase()  # Automatically switch to the next phase

    def update_display(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.label.setText(f"{minutes:02}:{seconds:02}")

    def open_config(self):
        dialog = ConfigDialog(self.work_time, self.break_time, self)
        if dialog.exec_():
            work_time, break_time = dialog.get_values(self.work_time, self.break_time)
            if work_time is not None and break_time is not None:
                self.work_time = work_time * 60  # Convert to seconds
                self.break_time = break_time * 60  # Convert to seconds
                self.time_left = self.work_time if self.is_working else self.break_time
                self.update_display()
                self.save_config()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as file:
                config = json.load(file)
                self.work_time = config.get('work_time', 25 * 60)
                self.break_time = config.get('break_time', 5 * 60)
                self.time_left = self.work_time if self.is_working else self.break_time
                self.update_display()
        except FileNotFoundError:
            pass

    def save_config(self):
        config = {
            'work_time': self.work_time,
            'break_time': self.break_time
        }
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PomodoroApp()
    ex.show()
    sys.exit(app.exec_())
