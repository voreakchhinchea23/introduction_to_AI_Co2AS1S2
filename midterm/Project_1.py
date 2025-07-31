from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QWidget

class ToDoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart To-Do List")
        
        # Widgets
        self.task_input = QLineEdit()
        self.add_button = QPushButton("Add Task")
        self.task_list = QListWidget()
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.task_input)
        layout.addWidget(self.add_button)
        layout.addWidget(self.task_list)
        
        # Connect button to function
        self.add_button.clicked.connect(self.add_task)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def add_task(self):
        task_text = self.task_input.text()
        if task_text:
            priority = self.detect_priority(task_text)  # AI step!
            self.task_list.addItem(f"{priority}: {task_text}")
            self.task_input.clear()

    def detect_priority(self, task_text):
        task_text = task_text.lower()
        if "exam" in task_text or "urgent" in task_text:
            return "High"
        elif "homework" in task_text or "soon" in task_text:
            return "Medium"
        else:
            return "Low"

app = QApplication([])
window = ToDoApp()
window.show()
app.exec()