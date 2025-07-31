import sys 
import sqlite3
import pyaudio
import wave
import requests
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTableView, QMessageBox, QLabel,
                             QTabWidget, QDateEdit, QHeaderView, QAbstractButton)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QDate, QDateTime
import sounddevice as sd
import wavio

# API key
ASSEMBLYAI_API_KEY = "018d260f3a2f42589e8d8149e6e09453"

class SpeechToText:
    def __init__(self, api_key):
        self.endpoint = "https://api.assemblyai.com/v2/"
        self.header = {"authorization": api_key}
        
    def upload_audio(self, audio_file):
        url = self.endpoint + "upload"
        with open(audio_file, "rb") as f:
            response = requests.post(url, headers=self.header, data=f)
        return response.json().get("upload_url")
    
    def transcribe(self, audio_url):
        url = self.endpoint + "transcript"
        json_data = {"audio_url": audio_url}
        response = requests.post(url, headers=self.header, json=json_data)
        transcript_id = response.json().get("id")
        
        while True:
            result = requests.get(f"{url}/{transcript_id}", headers=self.header).json()
            if result["status"] == "completed":
                return result["text"]
            elif result["status"] == "error":
                raise Exception("Transcription failed")
            time.sleep(1)
            
class SmartToDoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart To-Do List")
        self.setGeometry(100, 100, 900, 700)
        
        # Initialize APIs
        self.speech_to_text = SpeechToText(ASSEMBLYAI_API_KEY)
        
        # Initialize database
        self.init_database()
        
        # Setup UI
        self.setup_ui()
        
        # Initialize task filter for current date
        self.update_task_filter()
        
    def init_database(self):
        try:
            conn = sqlite3.connect("todo.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    category TEXT,
                    priority TEXT,
                    due_date TEXT,
                    created_date TEXT,
                    updated_date TEXT
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
            sys.exit(1)
        finally:
            conn.close()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # main UI tab
        main_tab = QWidget()
        main_layout_tab = QVBoxLayout(main_tab)
        
        # date selection section
        date_layout = QHBoxLayout()
        date_label = QLabel("Select Date:")
        date_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        date_layout.addWidget(date_label)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setStyleSheet("padding: 8px; font-size: 14px;")
        self.date_input.dateChanged.connect(self.update_task_filter)
        date_layout.addWidget(self.date_input)
        date_layout.addStretch()
        main_layout_tab.addLayout(date_layout)
        
        # input section
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task for selected date...")
        self.task_input.setStyleSheet("padding: 8px; font-size: 14px;")
        input_layout.addWidget(self.task_input)