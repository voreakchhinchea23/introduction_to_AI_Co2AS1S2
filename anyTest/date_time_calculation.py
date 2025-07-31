import sys
from PyQt6.QtCore import QDateTime
from datetime import timedelta, datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)

class TimeCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Date Time Calculator")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.input_label = QLabel("Enter time to add (dd/hh/mm/ss):")
        layout.addWidget(self.input_label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("e.g. 01/02/30/15")
        layout.addWidget(self.input_field)

        self.calc_button = QPushButton("Calculate")
        self.calc_button.clicked.connect(self.calculate_time)
        layout.addWidget(self.calc_button)

        self.result_label = QLabel("Result will appear here.")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def calculate_time(self):
        input_text = self.input_field.text().strip()
        try:
            parts = input_text.split('/')
            if len(parts) != 4:
                raise ValueError("Input must be in dd/hh/mm/ss format.")
            days, hours, minutes, seconds = map(int, parts)
            delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            now = datetime.now()
            future_time = now + delta
            self.result_label.setText(
                f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Future time:  {future_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeCalculator()
    window.show()
    sys.exit(app.exec())