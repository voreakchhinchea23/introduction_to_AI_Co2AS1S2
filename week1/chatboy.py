import sys
import json
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QTextEdit, QLineEdit, QPushButton, QScrollArea,
                            QLabel, QFrame, QMessageBox, QSplitter, QDialog, 
                            QDialogButtonBox, QFormLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QTextCursor

class ApiKeyDialog(QDialog):
    """Dialog for setting/changing API key and provider"""
    def __init__(self, current_api_key="", current_provider="deepseek"):
        super().__init__()
        self.setWindowTitle("API Configuration")
        self.setModal(True)
        self.resize(500, 350)
        
        layout = QVBoxLayout()
        
        # Provider selection
        provider_label = QLabel("Choose AI Provider:")
        provider_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(provider_label)
        
        from PyQt6.QtWidgets import QComboBox
        self.provider_combo = QComboBox()
        providers = [
            ("OpenAI GPT (Paid)", "openai"),
            ("DeepSeek (Paid)", "deepseek"),
            ("Groq - Llama 3.1 (FREE)", "groq"),
            ("HuggingFace Inference (FREE)", "huggingface"),
            ("Cohere (FREE Tier)", "cohere")
        ]
        
        for display_name, value in providers:
            self.provider_combo.addItem(display_name, value)
        
        # Set current provider
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == current_provider:
                self.provider_combo.setCurrentIndex(i)
                break
        
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        layout.addWidget(self.provider_combo)
        
        # Info about selected provider
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #007ACC; font-size: 12px; margin: 10px 0;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # API key input
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(api_key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(current_api_key)
        self.api_key_input.setPlaceholderText("Enter your API key here...")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.api_key_input)
        
        # Help text
        self.help_label = QLabel()
        self.help_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        self.help_label.setWordWrap(True)
        layout.addWidget(self.help_label)
        
        # Update info for current selection
        self.on_provider_changed()
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def on_provider_changed(self):
        provider = self.provider_combo.currentData()
        
        info_texts = {
            "groq": "🆓 FREE! Fast inference with Llama 3.1. Rate limited but no cost.",
            "huggingface": "🆓 FREE! Use any model on HuggingFace. Some rate limits apply.",
            "cohere": "🆓 FREE tier available. 100 requests/month free.",
            "openai": "💰 Paid service. High quality but requires credits.",
            "deepseek": "💰 Paid service. Good quality, lower cost than OpenAI."
        }
        
        help_texts = {
            "groq": "Get free API key from: https://console.groq.com/keys",
            "huggingface": "Get free API key from: https://huggingface.co/settings/tokens",
            "cohere": "Get API key from: https://dashboard.cohere.ai/api-keys",
            "openai": "Get API key from: https://platform.openai.com/api-keys",
            "deepseek": "Get API key from: https://platform.deepseek.com"
        }
        
        self.info_label.setText(info_texts.get(provider, ""))
        self.help_label.setText(help_texts.get(provider, ""))
        
        # Update placeholder
        if provider in ["groq", "huggingface", "cohere"]:
            self.api_key_input.setPlaceholderText("Free API key - get from the link below")
        else:
            self.api_key_input.setPlaceholderText("API key required")
    
    def get_api_key(self):
        return self.api_key_input.text().strip()
    
    def get_provider(self):
        return self.provider_combo.currentData()

class ChatThread(QThread):
    """Thread for handling API calls to prevent UI freezing"""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_key, message, conversation_history, provider="deepseek"):
        super().__init__()
        self.api_key = api_key
        self.message = message
        self.conversation_history = conversation_history
        self.provider = provider
        
    def run(self):
        try:
            if self.provider == "groq":
                self.call_groq_api()
            elif self.provider == "huggingface":
                self.call_huggingface_api()
            elif self.provider == "cohere":
                self.call_cohere_api()
            elif self.provider == "openai":
                self.call_openai_api()
            elif self.provider == "deepseek":
                self.call_deepseek_api()
            else:
                self.error_occurred.emit("Unsupported provider selected")
                
        except requests.exceptions.Timeout:
            self.error_occurred.emit("Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Connection error. Please check your internet connection.")
        except Exception as e:
            self.error_occurred.emit(f"An error occurred: {str(e)}")
    
    def call_groq_api(self):
        """Call Groq API (FREE!)"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        messages = []
        for msg in self.conversation_history:
            messages.append(msg)
        messages.append({"role": "user", "content": self.message})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.1-8b-instant",  # Free model
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]
            self.response_received.emit(assistant_message)
        else:
            self.error_occurred.emit(f"Groq API Error {response.status_code}: {response.text}")
    
    def call_huggingface_api(self):
        """Call HuggingFace Inference API (FREE!)"""
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Simple prompt for DialoGPT
        prompt = self.message
        if self.conversation_history:
            # Add last few exchanges for context
            recent = self.conversation_history[-4:]  # Last 2 exchanges
            context = ""
            for msg in recent:
                if msg["role"] == "user":
                    context += f"Human: {msg['content']}\n"
                else:
                    context += f"Bot: {msg['content']}\n"
            prompt = context + f"Human: {self.message}\nBot:"
        
        data = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                assistant_message = result[0].get("generated_text", "").replace(prompt, "").strip()
                if assistant_message:
                    self.response_received.emit(assistant_message)
                else:
                    self.response_received.emit("I'm thinking... try asking something else!")
            else:
                self.response_received.emit("I'm processing your request...")
        else:
            self.error_occurred.emit(f"HuggingFace API Error {response.status_code}: {response.text}")
    
    def call_cohere_api(self):
        """Call Cohere API (FREE tier available)"""
        url = "https://api.cohere.ai/v1/generate"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build prompt with context
        prompt = f"Human: {self.message}\nAssistant:"
        if self.conversation_history:
            context = ""
            for msg in self.conversation_history[-6:]:  # Last 3 exchanges
                if msg["role"] == "user":
                    context += f"Human: {msg['content']}\n"
                else:
                    context += f"Assistant: {msg['content']}\n"
            prompt = context + prompt
        
        data = {
            "model": "command-light",  # Free tier model
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.7,
            "stop_sequences": ["Human:"]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            assistant_message = result["generations"][0]["text"].strip()
            self.response_received.emit(assistant_message)
        else:
            self.error_occurred.emit(f"Cohere API Error {response.status_code}: {response.text}")
    
    def call_openai_api(self):
        """Call OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        
        messages = []
        for msg in self.conversation_history:
            messages.append(msg)
        messages.append({"role": "user", "content": self.message})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]
            self.response_received.emit(assistant_message)
        else:
            self.error_occurred.emit(f"OpenAI API Error {response.status_code}: {response.text}")
    
    def call_deepseek_api(self):
        """Call DeepSeek API"""
        url = "https://api.deepseek.com/chat/completions"
        
        messages = []
        for msg in self.conversation_history:
            messages.append(msg)
        messages.append({"role": "user", "content": self.message})
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.7,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]
            self.response_received.emit(assistant_message)
        else:
            error_msg = f"DeepSeek API Error {response.status_code}: {response.text}"
            self.error_occurred.emit(error_msg)

class MessageBubble(QFrame):
    """Custom widget for chat message bubbles"""
    def __init__(self, text, is_user=True):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(self.get_bubble_style(is_user))
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Message text
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet("background: transparent; border: none;")
        
        # Set font
        font = QFont("Arial", 10)
        label.setFont(font)
        
        layout.addWidget(label)
        self.setLayout(layout)
        
        # Set alignment
        if is_user:
            self.setMaximumWidth(400)
        else:
            self.setMaximumWidth(500)
    
    def get_bubble_style(self, is_user):
        if is_user:
            return """
                QFrame {
                    background-color: #007ACC;
                    border: none;
                    border-radius: 18px;
                    color: white;
                }
            """
        else:
            return """
                QFrame {
                    background-color: #F0F0F0;
                    border: none;
                    border-radius: 18px;
                    color: black;
                }
            """

class ChatBoyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = ""
        self.provider = "groq"  # Default to free provider
        self.conversation_history = []
        self.chat_thread = None
        
        # Show API key dialog first
        self.configure_api_key()
        
        self.init_ui()
        self.setup_styling()
        
    def init_ui(self):
        self.setWindowTitle("ChatBoy - DeepSeek AI Assistant")
        self.setGeometry(100, 100, 900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header
        header = QLabel("ChatBoy - Multi-AI Assistant")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #007ACC;
                padding: 15px;
                background-color: #F8F9FA;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(header)
        
        # Chat area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                background-color: white;
            }
        """)
        
        # Chat widget
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()
        self.chat_widget.setLayout(self.chat_layout)
        self.scroll_area.setWidget(self.chat_widget)
        
        main_layout.addWidget(self.scroll_area)
        
        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        input_layout = QHBoxLayout()
        input_frame.setLayout(input_layout)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 25px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007ACC;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        main_layout.addWidget(input_frame)
        
        # Menu bar
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('Settings')
        
        api_key_action = settings_menu.addAction('Configure API Key')
        api_key_action.triggered.connect(lambda: self.configure_api_key(True))
        
        clear_chat_action = settings_menu.addAction('Clear Chat History')
        clear_chat_action.triggered.connect(self.clear_chat)
        
        # Status bar
        self.statusBar().showMessage("Ready to chat!")
        
        # Add welcome message
        if self.api_key:
            provider_names = {
                "groq": "Groq (FREE & Fast!)",
                "huggingface": "HuggingFace (FREE)",
                "cohere": "Cohere",
                "openai": "OpenAI GPT",
                "deepseek": "DeepSeek"
            }
            provider_name = provider_names.get(self.provider, self.provider)
            self.add_message(f"Hello! I'm ChatBoy powered by {provider_name}. How can I help you today?", False)
        else:
            self.add_message("Please configure your API key using the Settings menu. Try the FREE options like Groq or HuggingFace!", False)
    
    def configure_api_key(self, show_current=False):
        """Show API key configuration dialog"""
        current_key = self.api_key if show_current else ""
        current_provider = getattr(self, 'provider', 'groq')
        dialog = ApiKeyDialog(current_key, current_provider)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = dialog.get_api_key()
            new_provider = dialog.get_provider()
            if new_key:
                self.api_key = new_key
                self.provider = new_provider
                provider_names = {
                    "groq": "Groq (FREE)",
                    "huggingface": "HuggingFace (FREE)",
                    "cohere": "Cohere",
                    "openai": "OpenAI",
                    "deepseek": "DeepSeek"
                }
                self.statusBar().showMessage(f"Using {provider_names.get(new_provider, new_provider)} - API key updated!")
                return True
            else:
                QMessageBox.warning(self, "Warning", "Please enter a valid API key.")
                return False
        return False
        
    def setup_styling(self):
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QStatusBar {
                background-color: #F8F9FA;
                color: #666666;
            }
        """)
        
    def add_message(self, text, is_user=True):
        # Create message container
        message_container = QWidget()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(10, 5, 10, 5)
        
        # Create message bubble
        bubble = MessageBubble(text, is_user)
        
        if is_user:
            message_layout.addStretch()
            message_layout.addWidget(bubble)
        else:
            message_layout.addWidget(bubble)
            message_layout.addStretch()
        
        message_container.setLayout(message_layout)
        
        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_container)
        
        # Auto-scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
        
        # Check if API key is set
        if not self.api_key:
            QMessageBox.warning(self, "API Key Missing", 
                              "Please configure your API key in Settings menu first.")
            return
        
        # Store the current message for history tracking
        self.current_user_message = message
            
        # Add user message to chat
        self.add_message(message, True)
        
        # Clear input field
        self.input_field.clear()
        
        # Disable send button
        self.send_button.setEnabled(False)
        self.send_button.setText("Sending...")
        
        # Update status
        self.statusBar().showMessage("Sending message...")
        
        # Start chat thread
        self.chat_thread = ChatThread(self.api_key, message, self.conversation_history, self.provider)
        self.chat_thread.response_received.connect(self.on_response_received)
        self.chat_thread.error_occurred.connect(self.on_error_occurred)
        self.chat_thread.start()
        
    def on_response_received(self, response):
        # Add assistant message to chat
        self.add_message(response, False)
        
        # Update conversation history with the stored user message
        if hasattr(self, 'current_user_message'):
            self.conversation_history.append({"role": "user", "content": self.current_user_message})
            self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep conversation history manageable (last 10 exchanges)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Re-enable send button
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        
        # Update status
        self.statusBar().showMessage("Ready to chat!")
        
        # Focus input field
        self.input_field.setFocus()
        
    def on_error_occurred(self, error):
        # Show error message
        if "402" in error or "Insufficient Balance" in error:
            error_msg = ("❌ Insufficient API Credits\n\n"
                        "Your DeepSeek account doesn't have enough credits. "
                        "Please add credits to your account at https://platform.deepseek.com")
            self.add_message(error_msg, False)
        else:
            self.add_message(f"Sorry, there was an error: {error}", False)
        
        # Re-enable send button
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        
        # Update status
        self.statusBar().showMessage("Error occurred - Ready to retry")
        
        # Focus input field
        self.input_field.setFocus()
    
    def clear_chat(self):
        """Clear chat history"""
        # Remove all messages except welcome message
        for i in reversed(range(self.chat_layout.count())):
            item = self.chat_layout.itemAt(i)
            if item and item.widget() and item != self.chat_layout.itemAt(self.chat_layout.count() - 1):
                item.widget().setParent(None)
        
        # Clear conversation history
        self.conversation_history.clear()
        
        # Add new welcome message
        if self.api_key:
            provider_names = {
                "groq": "Groq (FREE & Fast!)",
                "huggingface": "HuggingFace (FREE)",
                "cohere": "Cohere",
                "openai": "OpenAI GPT",
                "deepseek": "DeepSeek"
            }
            provider_name = provider_names.get(self.provider, self.provider)
            self.add_message(f"Chat cleared! Using {provider_name}. How can I help you today?", False)
        else:
            self.add_message("Please configure your API key using the Settings menu. Try the FREE options!", False)

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ChatBoy")
    app.setApplicationVersion("1.0")
    
    window = ChatBoyMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()