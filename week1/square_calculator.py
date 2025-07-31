 
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit
import sys

def compute_square():
    try:
        num = float(num_input.text())
        result_label.setText(f"Square = {num ** 2}")
    except ValueError:  
        result_label.setText("Please enter a valid number")
        
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Compute Square App")

# widgets
num_input = QLineEdit()
num_input.setPlaceholderText("Enter a number")

compute_button = QPushButton("Compute Square")
compute_button.clicked.connect(compute_square)

result_label = QLabel("")

# Layout    
layout = QVBoxLayout()
layout.addWidget(num_input)
layout.addWidget(compute_button)
layout.addWidget(result_label)

window.setLayout(layout)
window.show()
sys.exit(app.exec())
      