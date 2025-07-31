import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt
from openai import OpenAI

class ChatbotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek Chatbot")
        self.setGeometry(100, 100, 600, 400)

        # Initialize DeepSeek API client
        self.client = OpenAI(
            api_key="sk-752cacf5583a486da52dcac7c8cdb2e2",  # Replace with your DeepSeek API key
            base_url="https://api.deepseek.com"
        )

        # Set up the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Chat history display (read-only text area)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        # Input area and send button
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)

        # Store conversation history
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    def send_message(self):
        user_message = self.input_field.text().strip()
        if not user_message:
            return

        # Append user message to chat history
        self.chat_history.append(f"<b>You:</b> {user_message}")
        self.messages.append({"role": "user", "content": user_message})
        self.input_field.clear()

        # Get response from DeepSeek API
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                stream=False
            )
            bot_response = response.choices[0].message.content
            self.chat_history.append(f"<b>Bot:</b> {bot_response}")
            self.messages.append({"role": "assistant", "content": bot_response})
        except Exception as e:
            self.chat_history.append(f"<b>Error:</b> Failed to get response: {str(e)}")
        

def main():
    app = QApplication(sys.argv)
    window = ChatbotWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()