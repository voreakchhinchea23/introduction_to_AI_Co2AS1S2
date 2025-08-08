import sys
import sqlite3
import requests
import time 
import os
import sounddevice as sd
import wavio
from dotenv import load_dotenv
import pygame
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableView, QMessageBox, QLabel,
    QTabWidget, QDateEdit, QTimeEdit, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QDate, QDateTime, QTime, QTimer

# Load environment variaables from .env file
load_dotenv()
api_key = os.getenv('ASSEMBLYAI_API_KEY')
if not api_key:
    raise ValueError("ASSEMBLYAI_API_KEY not found in .env file")

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
    
class SmartTodoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart To-Do List")
        self.setGeometry(100, 100, 900, 700)
        
        self.speech_to_text = SpeechToText(api_key)
        
        # initialize pygame mixer for alarm sound
        pygame.mixer.init()
        
        self.active_reminder_id = None
        self.init_database()
        self.setup_ui()
        self.update_task_filter()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(1000) # check every 1 second
        
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
                    reminder_time TEXT,
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
        
        date_time_layout = QHBoxLayout()
        date_label = QLabel("Select Date:")
        date_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        date_time_layout.addWidget(date_label)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setStyleSheet("padding: 8px; font-size: 14px;")
        self.date_input.dateChanged.connect(self.update_task_filter)
        date_time_layout.addWidget(self.date_input)
        
        time_label = QLabel("Reminder Time (HH:mm:ss):")
        time_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        date_time_layout.addWidget(time_label)
        
        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm:ss")
        self.time_input.setTime(QTime(0,0,0)) # 00:00:00 as default
        self.time_input.setStyleSheet("padding: 8px; font-size: 14px;")
        date_time_layout.addWidget(self.time_input)
        
        date_time_layout.addStretch()
        main_layout.addLayout(date_time_layout)
        
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task for selected date...")
        self.task_input.setStyleSheet("padding: 8px; font-size: 14px;")
        input_layout.addWidget(self.task_input)
        
        self.add_update_button = QPushButton("Add Task")
        self.add_update_button.clicked.connect(self.add_or_update_task)
        self.add_update_button.setStyleSheet("padding: 8px; font-size: 14px; background-color: #4CAF50; color: white;")
        input_layout.addWidget(self.add_update_button)
        
        self.voice_button = QPushButton("🎤")
        self.voice_button.clicked.connect(self.record_and_transcribe)
        self.voice_button.setStyleSheet("padding: 8px; font-size: 14px; background-color: #2196F3")
        input_layout.addWidget(self.voice_button)
        
        main_layout.addLayout(input_layout)
        
        # task table 
        self.task_table = QTableView()
        self.task_model = QStandardItemModel(self)
        self.task_model.setHorizontalHeaderLabels(["ID", "Task", "Category", "Priority", "Due Date", "Reminder Time", "Created Date", "Updated Date"])
        self.task_table.setModel(self.task_model)
        self.task_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.setStyleSheet("font-size: 14px;")
        # hide due_date, created_date, and updated_date columns
        self.task_table.setColumnHidden(4, True)
        self.task_table.setColumnHidden(6, True)
        self.task_table.setColumnHidden(7, True)
        self.task_table.selectionModel().selectionChanged.connect(self.on_row_selection_changed)
        main_layout.addWidget(self.task_table)
        
        action_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel_action)
        cancel_button.setStyleSheet("padding: 8px; font-size: 14px; background-color: #FFC107; color: black;")
        action_layout.addWidget(cancel_button)
        
        remove_button = QPushButton("Remove Task")
        remove_button.clicked.connect(self.remove_task)
        remove_button.setStyleSheet("padding: 8px; font-size: 14px; background-color: #F44336; color: white;")
        action_layout.addWidget(remove_button)
        
        main_layout.addLayout(action_layout)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 14px; color: white;")
        main_layout.addWidget(self.status_label)
        
        # apply general style
        central_widget.setStyleSheet("""
            QWidget { font-family: Arial; }
            QPushButton:hover { background-color: #45a049; }
        """)
    
    # show tasks by selected date
    def update_task_filter(self):
        selected_date = self.date_input.date().toString("dd-MM-yyyy")
        try:
            conn = sqlite3.connect("todo.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE due_date = ? ORDER BY due_date DESC", (selected_date,))
            rows = cursor.fetchall()
            
            self.task_model.removeRows(0, self.task_model.rowCount())
            for row in rows:
                items = [QStandardItem(str(item)) for item in row]
                for item in items:
                    item.setEditable(False)
                self.task_model.appendRow(items)
            
            current_date = QDate.currentDate().toString("dd-MM-yyyy")
            if selected_date == current_date:
                self.status_label.setText(f"Showing tasks for today ({selected_date})")
            elif selected_date == QDate.currentDate().addDays(1).toString("dd-MM-yyyy"):
                self.status_label.setText(f"Showing tasks for tomorrow ({selected_date})")
            else:
                self.status_label.setText(f"Showing tasks for {selected_date}")
        
        except sqlite3.Error as e :
            self.status_label.setText(f"Database error: {str(e)}")
        finally:
            conn.close()
    
    def on_row_selection_changed(self):
        selected = self.task_table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            task_text = self.task_model.item(row, 1).text()
            reminder_time = self.task_model.item(row, 5).text()
            self.task_input.setText(task_text)
            
            try:
                time_obj = QTime.fromString(reminder_time, "HH:mm:ss")
                if time_obj.isValid():
                    self.time_input.setTime(time_obj)
                else:
                    self.time_input.setTime(QTime(0, 0, 0))
            except:
                self.time_input.setTime(QTime(0, 0, 0))
            self.add_update_button.setText("Update Task")
        else:
            self.task_input.clear()
            self.time_input.setTime(QTime(0, 0, 0))
            self.add_update_button.setText("Add Task")

    def add_or_update_task(self):
        task_text = self.task_input.text().strip()
        if not task_text:
            QMessageBox.warning(self, "Warning", "Task cannot be empty")
            return

        try:
            conn = sqlite3.connect("todo.db")
            cursor = conn.cursor()
            selected = self.task_table.selectionModel().selectedRows()
            reminder_time = self.time_input.time().toString("HH:mm:ss")
            if selected:
                # update existing task
                row = selected[0].row()
                task_id = self.task_model.item(row, 0).text() 
                new_category, new_priority = self.categorize_task(task_text)
                new_due_date = self.date_input.date().toString("dd-MM-yyyy")
                updated_datetime = QDateTime.currentDateTime().toString("dd-MM-yyyy HH:mm:ss")
                
                cursor.execute("""
                    UPDATE tasks
                    SET task = ?, category = ?, priority = ?, due_date = ?, reminder_time = ?, updated_date = ?
                    WHERE id = ?
                """, (task_text, new_category, new_priority, new_due_date, reminder_time, updated_datetime, task_id))
                conn.commit()
                
                self.update_task_filter()
                self.task_input.clear()
                self.time_input.setTime(QTime(0, 0, 0))
                self.add_update_button.setText("Add Task")
                self.task_table.selectionModel().clearSelection()
                self.status_label.setText("Task updated successfully")
            else:
                # add new task
                category, priority = self.categorize_task(task_text)
                due_date = self.date_input.date().toString("dd-MM-yyyy")
                current_datetime = QDateTime.currentDateTime().toString("dd-MM-yyyy HH:mm:ss")
                
                cursor.execute("""
                    INSERT INTO tasks (task, category, priority, due_date, reminder_time, created_date, updated_date)
                    VALUES (?,?,?,?,?,?,?)
                """, (task_text, category, priority, due_date, reminder_time, current_datetime, current_datetime))
                conn.commit()
                
                self.update_task_filter()
                self.task_input.clear()
                self.time_input.setTime(QTime(0, 0, 0))
                self.status_label.setText("Task added successfully")
                
        except sqlite3.Error as e:
            self.status_label.setText(f"Database error: {str(e)}")  
        finally: 
            conn.close()
            
    def cancel_action(self):
        self.task_input.clear()
        self.time_input.setTime(QTime(0, 0, 0))
        self.task_table.selectionModel().clearSelection()
        self.add_update_button.setText("Add Task") 
        self.status_label.setText("Action cancelled")
        
    def remove_task(self):
        selected = self.task_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Warning", "Select a task to remove")
            return
        
        row = selected[0].row()
        task_id = self.task_model.item(row, 0).text() 
        
        try:
            conn = sqlite3.connect("todo.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            
            self.update_task_filter()
            self.task_input.clear()
            self.time_input.setTime(QTime(0, 0, 0))
            self.add_update_button.setText("Add Task")
            self.status_label.setText("Text removed successfully")
            
        except sqlite3.Error as e:
            self.status_label.setText(f"Database error: {str(e)}")
        finally:
            conn.close()       
    
    def record_and_transcribe(self):
        self.voice_button.setText("🔴")
        self.voice_button.setStyleSheet("padding: 8px; font-size: 14px; background-color: #000000")
        self.status_label.setText("Recording... Speak now (5s)")
        QApplication.processEvents() # ensure UI updates immediately
        
        fs = 44100      #hz
        duration = 5    #s
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        
        audio_file = "temp_recording.wav"
        wavio.write(audio_file, recording, fs, sampwidth=2)
        
        try:
            audio_url = self.speech_to_text.upload_audio(audio_file)
            transcribed_text = self.speech_to_text.transcribe(audio_url)
            
            if transcribed_text:
                self.task_input.setText(transcribed_text)
                self.status_label.setText("Transcription complete")
            else:
                self.status_label.setText("No speech detected")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
        finally:
            # revert button text and color
            self.voice_button.setText("🎤")
            self.voice_button.setStyleSheet("padding: 8px; font-size: 14px; background-color: #2196F3")
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
    def check_reminders(self):
        try:
            conn = sqlite3.connect("todo.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, task, due_date, reminder_time FROM tasks")
            tasks = cursor.fetchall()
            
            current_datetime = QDateTime.currentDateTime().toString("dd-MM-yyyy HH:mm:ss")
            
            for task in tasks:
                task_id, task_text, due_date, reminder_time = task
                # combine due_date and reminder_time for comparison
                if reminder_time and reminder_time != "00:00:00" :
                    reminder_datetime = f"{due_date} {reminder_time}"
                    # check if reminder matches current time and is not already active
                    if reminder_datetime == current_datetime and (self.active_reminder_id is None or self.active_reminder_id != task_id):
                        self.active_reminder_id = task_id
                        try:
                            pygame.mixer.music.load("getup.mp3")
                            pygame.mixer.music.play(-1) # loop sound
                            
                            msg = QMessageBox.information(self, "Task Alert", f"Reminder: {task_text}", QMessageBox.StandardButton.Ok)
                            if(msg == QMessageBox.StandardButton.Ok):
                                pygame.mixer.music.stop()
                                self.status_label.setText("Reminder stopped")
                                self.active_reminder_id = None
                            
                        except pygame.error as e:
                            print(f"Sound error: {e}")
                            self.status_label.setText(f"Reminder: {task_text} (sound failed)")
                        
        except sqlite3.Error as e:
            self.status_label.setText(f"Database error: {str(e)}")
        finally:
            conn.close()
                
    def categorize_task(self, task_text):
        task_text = task_text.lower()
        if any(word in task_text for word in ["study", "assignment", "homework", "exam", "lecture", 
                                             "project", "research", "essay", "lab", "quiz", "thesis", "deadline"]):
            category = "University Work"
            priority = "High" if any(word in task_text for word in ["urgent", "deadline", "tomorrow", "tonight"]) else "Medium"
            
        elif any(word in task_text for word in ["chore", "errand", "grocery", "shopping", "clean", 
                                               "laundry", "exercise", "cook", "meal", "sleep", "routine"]):
            category = "Daily"
            priority = "Low"
        elif any(word in task_text for word in ["friend", "family", "call", "meet", "hangout", 
                                               "date", "party", "birthday", "visit", "message", "chat"]):
            category = "Relationship"
            priority = "Medium"
        elif any(word in task_text for word in ["hobby", "read", "book", "meditate", "journal", 
                                               "plan", "goal", "relax", "music", "art", "personal"]):
            category = "Personal"
            priority = "Low"
        else:
            category = "General"
            priority = "Medium"
        return category, priority
    
    def closeEvent(self, evnet):
        pygame.mixer.quit()
        evnet.accept()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SmartTodoApp()
    window.show()
    sys.exit(app.exec())     