import sys
import sqlite3
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit,
    QPushButton, QListWidget, QWidget, QListWidgetItem,
    QHBoxLayout, QLabel, QMessageBox, QComboBox
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

# Download NLTK data
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('punkt', quiet=True)

class SmartToDoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI To-Do List")
        self.setGeometry(100, 100, 600, 600)
        
        # Initialize database
        self.conn = sqlite3.connect('smart_todo.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                            (id INTEGER PRIMARY KEY, task TEXT, 
                             category TEXT, priority TEXT, 
                             created_at TIMESTAMP)''')
        self.conn.commit()

        # GUI Components
        self.create_widgets()
        self.setup_layout()
        self.setup_connections()
        
        # Load initial tasks
        self.load_tasks()

    def create_widgets(self):
        """Create all UI widgets"""
        self.task_input = QLineEdit(placeholderText="Enter your task...")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Study", "Work", "Personal", "Shopping"])
        self.add_button = QPushButton("Add Task")
        self.suggest_button = QPushButton("Get AI Suggestion")
        self.task_list = QListWidget()
        self.status_label = QLabel("Ready")
        self.clear_button = QPushButton("Clear Completed")

    def setup_layout(self):
        """Arrange widgets in the window"""
        main_layout = QVBoxLayout()
        
        # Input row
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Task:"), 20)
        input_layout.addWidget(self.task_input, 60)
        input_layout.addWidget(QLabel("Category:"), 15)
        input_layout.addWidget(self.category_combo, 25)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.suggest_button)
        button_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(input_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.task_list)
        main_layout.addWidget(self.status_label)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def setup_connections(self):
        """Connect signals to slots"""
        self.add_button.clicked.connect(self.add_task)
        self.suggest_button.clicked.connect(self.suggest_task)
        self.clear_button.clicked.connect(self.clear_completed)
        self.task_list.itemDoubleClicked.connect(self.toggle_completion)

    # ================== AI Functions ==================
    def detect_priority(self, task_text):
        """Use WordNet to find urgent synonyms"""
        urgent_synonyms = {"urgent", "critical", "important", "emergency"}
        for syn in wordnet.synsets("urgent"):
            for lemma in syn.lemmas():
                urgent_synonyms.add(lemma.name().replace('_', ' '))
        
        tokens = word_tokenize(task_text.lower())
        return "High" if any(word in urgent_synonyms for word in tokens) else "Medium"

    def auto_categorize(self, task_text):
        """Use POS tagging to suggest categories"""
        tagged = pos_tag(word_tokenize(task_text))
        
        # Noun-heavy = Study/Work, Verb-heavy = Action
        noun_count = sum(1 for _, tag in tagged if tag.startswith('NN'))
        verb_count = sum(1 for _, tag in tagged if tag.startswith('VB'))
        
        if noun_count > verb_count:
            return "Study" if any(word in task_text.lower() for word in ["study", "read"]) else "Work"
        else:
            return "Personal" if any(word in task_text.lower() for word in ["call", "meet"]) else "Shopping"

    def generate_suggestion(self):
        """Generate smart suggestions using NLTK"""
        suggestions = [
            "Review notes for 30 minutes",
            "Schedule a break at 3 PM",
            "Drink water and stretch",
            "Prioritize high-importance tasks",
            "Check upcoming deadlines"
        ]
        return random.choice(suggestions)

    # ================== Core Functions ==================
    def add_task(self):
        task_text = self.task_input.text().strip()
        if task_text:
            # AI-powered processing
            priority = self.detect_priority(task_text)
            category = self.auto_categorize(task_text)
            
            # Store in database
            self.cursor.execute(
                "INSERT INTO tasks (task, category, priority, created_at) VALUES (?, ?, ?, ?)",
                (task_text, category, priority, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            self.conn.commit()
            
            self.task_input.clear()
            self.load_tasks()
            self.status_label.setText(f"Added: {task_text} ({priority} priority)")

    def suggest_task(self):
        suggestion = self.generate_suggestion()
        QMessageBox.information(self, "AI Suggestion", f"How about:\n\n{suggestion}")

    def load_tasks(self):
        """Load tasks from database with color coding"""
        self.task_list.clear()
        self.cursor.execute("SELECT id, task, category, priority FROM tasks WHERE completed = 0")
        
        for task_id, task, category, priority in self.cursor.fetchall():
            item = QListWidgetItem(f"[{priority}] {category}: {task}")
            item.setData(Qt.ItemDataRole.UserRole, task_id)
            
            # Color coding
            if priority == "High":
                item.setForeground(QColor(200, 0, 0))  # Red
            elif category == "Study":
                item.setForeground(QColor(0, 100, 200))  # Blue
            elif category == "Work":
                item.setForeground(QColor(150, 0, 150))  # Purple
            
            self.task_list.addItem(item)

    def toggle_completion(self, item):
        """Mark task as completed when double-clicked"""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        self.cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()

    def clear_completed(self):
        """Remove completed tasks"""
        self.cursor.execute("DELETE FROM tasks WHERE completed = 1")
        self.conn.commit()
        self.load_tasks()
        self.status_label.setText("Cleared completed tasks")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartToDoApp()
    window.show()
    sys.exit(app.exec())