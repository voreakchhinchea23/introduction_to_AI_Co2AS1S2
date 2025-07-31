import sys
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
                             QTableView, QMessageBox, QHeaderView, QFrame, 
                             QScrollArea, QSplitter, QAbstractItemView, QDialog,
                             QDialogButtonBox, QTextBrowser, QTabWidget, QGroupBox,
                             QFormLayout, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtGui import QFont, QFontDatabase, QAction 

class FontManager:
    """Manage Khmer OS Siemreap font for the application - Single font size 11"""
    
    def __init__(self):
        self.khmer_font = None
        self.font_size = 11 # single font size for entire app
        self.init_fonts()
        
    def init_fonts(self):
        """Initialize and load Khmer OS Siemreap"""
        preferred_fonts = [
            "Khmer OS Siemreap"
        ]
        
        try:
            available_families = QFontDatabase().families()
        except:
            available_families = []
        
        for font_name in preferred_fonts:
            if font_name in available_families:
                self.khmer_font = QFont(font_name, self.font_size)
                break
        
        if self.khmer_font is None:
            self.khmer_font = QFont("Khmer OS Siemreap", self.font_size)
            
        # Configure font properties for optional Khmer rendering
        self.khmer_font.setStyleHint(QFont.StyleHint.System)
        self.khmer_font.setWeight(QFont.Weight.Normal)
        self.khmer_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
        self.khmer_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        
    def get_font(self, size=None, bold=False):
        """get the standard font with sepecified size and weight"""
        if size is None:
            size = self.font_size
        font = QFont(self.khmer_font)
        font.setPointSize(size)
        if bold:
            font.setWeight(QFont.Weight.Bold)
        return font
    
    def get_font_family(self):
        """get the font family name"""
        return self.khmer_font.family()
    
    def apply_font(self, widget, size=None, bold=False):
        """apply font to any widget recursively"""
        if size is None:
            size = self.font_size
        try:
            font = self.get_font(size, bold)
            widget.setFont(font)
            # apply to all child widgets recursively
            for child in widget.findChildren(QWidget):
                if hasattr(child, 'setFont'):
                    child.setFont(font)
        except Exception as e:
            print(f"Font applicatoin error: {e}")
        
    def create_message_box(self, parent, icon, title, text, buttons=None):
        """create a message box with proper Khmer font"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        # apply font to message box and all children
        self.apply_font(msg_box, self.font_size)
        
        if buttons:
            msg_box.setStandardButtons(buttons)
            
        return msg_box
    
class DicitonaryTableModel(QAbstractTableModel):
    """table model for dicitonary entries with full CRUD support"""
    
    def __init__(self, data=None):
        super().__init__()
        self.headers = ["ID", "English", "Khmer", "Type", "Definition", "Example"]
        self._data = data or []
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            if row < len(self._data):
                # return data excluding created_at and updated_at column
                data_item = self._data[row]
                if col < 6: #only first 6 columns
                    value = data_item[col] if data_item[col] is not None else ""
                    return str(value)
                
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section < len(self.headers):
                return self.headers[section]
        return QVariant()
    
    def update_data(self, new_data):
        """update the model with new data"""
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
    
    def get_row_data(self, row):
        """get complete data for a specific row"""
        if 0 < row < len(self._data):
            return self._data[row]
        return None
    
    def add_row(self, row_data):
        """add a new row to the model"""
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(row_data)
        self.endInsertRows()
        
        def remove_row(self, row):
            """remove a row from the model"""
            if 0 <= row < len(self._data):
                self.beginRemoveRows(QModelIndex(), row, row)
                del self._data[row]
                self.endRemoveRows()
                return True
            return False
        
class DictionaryDatabase:
    """manage the SQLite database for dictionary operations"""
    
    def __init__(self, db_path="khmer_english_dictionary.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dictionary(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_word TEXT NOT NULL UNIQUE,
                khmer_word TEXT NOT NULL,
                word_type TEXT DEFAULT 'noun',
                definition TEXT,
                example_sentence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''') 
        
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        if cursor.fetchone()[0] == 0:
            sample_data = [
                ("hello", "សួស្ដី", "greeting", "A greeting used when meeting someone", "Hello, how are you?"),
                ("goodbye", "លាហើយ", "greeting", "A farewell expression", "Goodbye, see you tomorrow!"),
                ("thank you", "អរគុណ", "expression", "Expression of gratitude", "Thank you for your help"),
                ("please", "សូម", "adverb", "Used to make a polite request", "Please help me"),
                ("yes", "បាទ/ចាស", "response", "Affirmative response", "Yes, I agree"),
                ("no", "ទេ", "response", "Negative response", "No, I don't want to"),
                ("water", "ទឹក", "noun", "Clear liquid essential for life", "I want to drink a cup of water"),
                ("food", "អាហារ", "noun", "Substance consumed for nutrition","The food is delicious"),
                ("house", "ផ្ទះ", "noun", "A building for living", "This is my house"),
                ("school", "សាលា", "noun", "Institution for education", "I go to school every day"),
                ("book", "សៀវភៅ", "noun", "Written or printed work", "I am reading a book"),
                ("student", "សិស្ស", "noun", "Person who studies", "She is a good student")
            ]
        
            cursor.executemany('''
                INSERT INTO dictionary (english_word, khmer_word, word_type, definition, example_sentence)
                VALUES(?, ?, ?, ?, ?)
                ''', sample_data)
        
        conn.commit()
        conn.close()
        
    def create_word(self, english_word, khmer_word, word_type="noun", definition="", example=""):
        """Create operation - Add new word to dictionary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dictionary (english_word, khmer_word, word_type, definition, example_sentence)
                VALUES(?,?,?,?,?)         
            ''', (english_word.lower().strip(), khmer_word.strip(), word_type, definition, example))
            conn.commit()
            word_id = cursor.lastrowid
            conn.close()
            return word_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Word '{english_word}' already exsits in dictionary")
        except Exception as e:
            raise ValueError(f"Database error: {str(e)}")
        
    def read_word(self, search_term, search_type="english"):
        """READ operation - Searching for words"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if search_type == "english":
                cursor.execute('''
                    SELECT * FROM dictionary
                    WHERE english_word LIKE ? OR english_word = ?
                    ORDER BY english_word       
                ''', (f"%{search_term.lower()}%", search_term.lower()))
            else:
                cursor.execute('''
                    SELECT * FROM dictionary
                    WHERE khmer_word LIKE ?
                    ORDER BY khmer_word
                ''', (f"%{search_term}%",))
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            conn.close()
            return []
        
    def read_all_words(self):
        """READ operation - Get all words"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM dictionary ORDER BY english_word")
            results = cursor.fetchall()
            return results
        except Exception as e:
            conn.close()
            return []
        
    def update_word(self, word_id, english_word=None, khmer_word=None, word_type=None, definition=None, example=None):
        """Update operation - Modify existing word"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            updates = []
            params = []
            if english_word is not None:
                updates.append("english_word = ?")
                params.append(english_word.lower().strip())
            if khmer_word is not None:
                updates.append("khmer_word = ?")
                params.append(khmer_word.strip())
            if word_type is not None:
                updates.append("word_type = ?")
                params.append(word_type)
            if definition is not None:
                updates.append("definition = ?")
                params.append(definition)  
            if example is not None:
                updates.append("example = ?")
                params.append(example)
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(word_id)
            if updates:
                query = f"UPDATE dictionary SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
            conn.close()
        except Exception as e:
            conn.close()
            raise ValueError(f"Update error: {str(e)}")
    
    def delete_word(self, word_id):
        """DELETE operation - Remove word from dictionary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM dictionary WHERE id = ?", (word_id,))
            conn.commit()
            deleted_count = cursor.rowCount
            conn.close()
            return deleted_count > 0
        except Exception as e:
            conn.close()
            raise ValueError(f"Delete error: {str(e)}")
        
    def get_random_words(self, limit=5):
        """Get random words for display"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM dictionary ORDER BY RANDOM() LIMIT ?", (limit,))
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            conn.close()
            return []
        
class WordDetailsDialog(QDialog):
    """Dialog for viewing detailed word information"""
    
    def __init__(self, word_data, font_manager, parent=None):
        super().__init__(parent)
        self.font_manager = font_manager
        self.word_data = word_data
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Word Details")
        self.setModal(True)
        self.resize(500, 400)
        
        # apply font to dialog
        self.font_manager.apply_font(self)
        
        layout = QVBoxLayout()
        
        if self.word_data:
            word_id, english, khmer, word_type, definition, example, created, updated = self.word_data
            
            #display word information
            info_text = f"""
            <h2 style = 'color: #2E7D32;'>{english.title()} ↔ {khmer}</h2>
            <p><strong>Word ID:</strong> {word_id}</p>
            <p><strong>Type:</strong> {word_type.title()}</p>
            <p><strong>Definition:</strong> {definition or 'No definition provided'}</p>
            <p><strong>Example:</strong> {example or 'No example provided'}</p>
            <p><strong>Created:</strong> {created}</p>
            <p><strong>Updated:</strong> {updated}</p>
            """
                
            details_browser = QTextBrowser()
            details_browser.setHtml(info_text)
            self.font_manager.apply_font(details_browser)
            layout.addWidget(details_browser)
                
        # buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.font_manager.apply_font(button_box)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
            
        self.setLayout(layout)
            
class   TranslatorWidgets(QWidget):
    word_searched = pyqtSignal(str, str)
    
    def __init__(self, db, font_manager):
        super().__init__()
        self.db = db
        self.font_manager = font_manager
        self.init_ui()
        
    def init_ui(self):
        # apply font to entire widget
        self.font_manager.apply_font(self)
        
        layout = QVBoxLayout()
        
        # title section
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        title_layout = QVBoxLayout()
        
        title = QLabel("Khmer-English Dictonary")
        self.font_manager.apply_font(title, bold=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("រចនានុក្រមអង់គ្លេស-ខ្មែរ")
        self.font_manager.apply_font(subtitle)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_frame.setLayout(title_layout)
        layout.addWidget(title_frame)
        
        # search section
        search_group = QGroupBox("Search Translation")
        search_group.setFixedHeight(550)
        self.font_manager.apply_font(search_group, bold = True)
        search_layout = QVBoxLayout()
        
        # search controls
        controls_layout = QHBoxLayout()
        
        direction_label = QLabel("Direction:")
        self.font_manager.apply_font(direction_label)
        
        self.search_combo = QComboBox()
        self.search_combo.addItems(["English ➞ Khmer", "Khmer ➞ English"])
        self.font_manager.apply_font(self.search_combo)
        
        word_label = QLabel("Word:")
        self.font_manager.apply_font(word_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type word to translate...")
        self.font_manager.apply_font(self.search_input)
        self.search_input.returnPressed.connect(self.search_word)
        
        self.search_button = QPushButton("Search")
        self.font_manager.apply_font(self.search_button)
        self.search_button.clicked.connect(self.search_word)
        self.search_button.setDefault(True)
        
        controls_layout.addWidget(direction_label)
        controls_layout.addWidget(self.search_combo)
        controls_layout.addWidget(word_label)
        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(self.search_button)
        
        search_layout.addLayout(controls_layout)
        
        # Results display
        results_label = QLabel("Results:")
        self.font_manager.apply_font(results_label)
        
        self.results_display = QTextBrowser()
        self.results_display.setMaximumHeight(500)
        self.font_manager.apply_font(self.results_display)
        
        search_layout.addWidget(results_label)
        search_layout.addWidget(self.results_display)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.font_manager.apply_font(self.clear_button)
        self.clear_button.clicked.connect(self.clear_search)
        
        self.random_button = QPushButton("Random Word")
        self.font_manager.apply_font(self.random_button)
        self.random_button.clicked.connect(self.show_random_word)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.random_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def search_word(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning, 
                "Input Error",
                "Please enter a word to search!"
            )
            msg.exec()
            return
        
        search_direction = self.search_combo.currentText()
        
        search_type = "english" if search_direction.startswith("English") else "Khmer"
        
        results = self.db.read_word(search_term, search_type)
        
        if results:
            self.display_results(results)
            self.word_searched.emit(search_term, search_type)
        else:
            no_results = f"""
            <h3>No results found for '{search_term}' </h3>
            <p><strong>Search Details:</strong></p>
            <ul>
                <li>Search Direction: {search_direction}</li>
                <li>Search Type: {search_type}</li>
                <li>Search Term: {search_term}</li>
            </ul>
            <p><strong>Suggestions:</strong></p>
            <ul>
                <li>Check Spelling</li>
                <li>Try simpler words</li>
                <li>Use the dictionary Manager to add new words</li>
            </ul>
            """
            self.results_display.setHtml(no_results)
    
    def display_results(self, results):
        html_content = "<h3>Translation Results:</h3>"
        
        for result in results:
            word_id, english, khmer, word_type, definition, example, created, updated = result
            
            html_content += f"""
            <div style='border: 1px solid #ccc; margin: 10px 0; padding: 10px; background-color: #f9f9f9;'>
                <h4>{english.title()} ↔ {khmer}</h4>
                <p><strong>Type:</strong> {word_type.title()} | <strong>ID:</strong> {word_id}</p>
                {f"<p><strong>Definition:</strong> {definition}</p>" if definition else ""}
                {f"<p><strong>Example:</strong> <em>{example}</em></p>" if example else ""}
            </div> 
            """
        
        self.results_display.setHtml(html_content)
    
    def clear_search(self):
        self.search_input.clear()
        self.results_display.clear()
        self.search_input.setFocus()
        
    def show_random_word(self):
        random_words = self.db.get_random_words(1)
        if random_words:
            self.display_results(random_words)
            word = random_words[0]
            self.search_input.setText(word[1])
            
class DictionaryManagerWidget(QWidget):
    word_added = pyqtSignal(str)
    word_updated = pyqtSignal(int)
    word_deleted = pyqtSignal(int)
    
    def __init__(self, db, font_manager):
        super().__init__()
        self.db = db
        self.font_manager = font_manager
        self.current_edit_id = None
        self.table_model = DicitonaryTableModel()
        self.init_ui()
        self.refresh_dictionary()
        
    def init_ui(self):
        # apply font to entire widget
        self.font_manager.apply_font(self)
        
        layout = QVBoxLayout()
        
        # Create splitter for form and table
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # form section with QHBoxLayout
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        
        form_group = QGroupBox("Add/Edit Dictionary Entry")
        self.font_manager.apply_font(form_group, bold = True)
        form_group_layout = QVBoxLayout()
        
        # create form inputs using QHBoxLayout
        inputs_layout = QHBoxLayout()
        
        
        # English word
        english_layout = QVBoxLayout()
        english_label = QLabel("English Word:")
        self.font_manager.apply_font(english_label)
        self.english_input = QLineEdit()
        self.english_input.setPlaceholderText("e.g., computer")
        self.font_manager.apply_font(self.english_input)
        english_layout.addWidget(english_label)
        english_layout.addWidget(self.english_input)
        
        # Khmer word
        khmer_layout = QVBoxLayout()
        khmer_label = QLabel("Khmer Word:")
        self.font_manager.apply_font(khmer_label)
        self.khmer_input = QLineEdit()
        self.khmer_input.setPlaceholderText("e.g., កុំព្យូទ័រ")
        self.font_manager.apply_font(self.khmer_input)
        khmer_layout.addWidget(khmer_label)
        khmer_layout.addWidget(self.khmer_input)
        
        # Word type
        type_layout = QVBoxLayout()
        type_label = QLabel("Word Type:")
        self.font_manager.apply_font(type_label)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["noun", "verb", "adjective", "adverb", "greeting", "expression", "response"])
        self.font_manager.apply_font(self.type_combo)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        
        # definition
        definition_layout = QVBoxLayout()
        definition_label = QLabel("Definition:")
        self.font_manager.apply_font(definition_label)
        self.definition_input = QLineEdit()
        self.definition_input.setPlaceholderText("Brief definition...")
        self.font_manager.apply_font(self.definition_input)
        definition_layout.addWidget(definition_label)
        definition_layout.addWidget(self.definition_input)
        # example
        example_layout = QVBoxLayout()
        example_label = QLabel("Example:")
        self.font_manager.apply_font(example_label)
        self.example_input = QLineEdit()
        self.example_input.setPlaceholderText("Example sentence...")
        self.font_manager.apply_font(self.example_input)
        example_layout.addWidget(example_label)
        example_layout.addWidget(self.example_input)
       
        # add all input groups to horizontal layout
        inputs_layout.addLayout(english_layout)
        inputs_layout.addLayout(khmer_layout)
        inputs_layout.addLayout(type_layout)
        inputs_layout.addLayout(definition_layout)
        inputs_layout.addLayout(example_layout)
        
        form_group_layout.addLayout(inputs_layout)
        
        # CRUD operation buttons
        button_layout = QHBoxLayout()
       
        # Create button
        self.add_button = QPushButton("Create Word")
        self.font_manager.apply_font(self.add_button)
        self.add_button.clicked.connect(self.create_word)
        self.add_button.setDefault(True)
        
        # Update button
        self.update_button = QPushButton("Update Word")
        self.font_manager.apply_font(self.update_button)
        self.update_button.clicked.connect(self.update_word)
        self.update_button.setVisible(False)
       
        self.cancel_button = QPushButton("Cancel Edit")
        self.font_manager.apply_font(self.cancel_button)
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.cancel_button.setVisible(False)
        
        self.clear_button = QPushButton("Clear Form")
        self.font_manager.apply_font(self.clear_button)
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
       
        form_group_layout.addLayout(button_layout)
        form_group.setLayout(form_group_layout)
        form_layout.addWidget(form_group)
        form_widget.setLayout(form_layout)
        # Table sectionn for READ/UPDATE/DELETE operations
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        
        table_group = QGroupBox("Dictionary Entries")
        self.font_manager.apply_font(table_group, bold=True)
        table_group_layout = QVBoxLayout()
        # Filter for READ operations
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        self.font_manager.apply_font(filter_label)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter entries...")
        self.font_manager.apply_font(self.filter_input)
        self.filter_input.textChanged.connect(self.filter_dictionary)
        
        self.refresh_button = QPushButton("Refresh")
        self.font_manager.apply_font(self.refresh_button)
        self.refresh_button.clicked.connect(self.refresh_dictionary)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)
        filter_layout.addWidget(self.refresh_button)
        
        # Table view for displaying data
        self.table_view = QTableView()
        self.font_manager.apply_font(self.table_view)
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        
        # Configure headers
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True) 
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.font_manager.apply_font(header, bold=True)
        
        # CRUD action buttons
        table_button_layout = QHBoxLayout()
        
        # READ operation - View details
        self.view_button = QPushButton("View Details") 
        self.font_manager.apply_font(self.view_button)
        self.view_button.clicked.connect(self.view_selected_word)
        
        # UPDATE operation - Edit
        self.edit_button = QPushButton("Edit Selected")
        self.font_manager.apply_font(self.edit_button)
        self.edit_button.clicked.connect(self.edit_selected_word)
        
        # DELETE operation - Delete
        self.delete_button = QPushButton("Delete Selected")
        self.font_manager.apply_font(self.delete_button)
        self.delete_button.clicked.connect(self.delete_selected_word)
        
        self.stats_label = QLabel()
        self.font_manager.apply_font(self.stats_label)
        
        table_button_layout.addWidget(self.view_button)
        table_button_layout.addWidget(self.edit_button)
        table_button_layout.addWidget(self.delete_button)
        table_button_layout.addStretch()
        table_button_layout.addWidget(self.stats_label)
        
        table_group_layout.addLayout(filter_layout)
        table_group_layout.addWidget(self.table_view)
        table_button_layout.addLayout(table_button_layout)
        
        table_group.setLayout(table_group_layout)
        table_layout.addWidget(table_group)
        table_widget.setLayout(table_layout)
        
        # Add to splitter
        splitter.addWidget(form_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
    def create_word(self):
        """CREATE operation - Add new word to dictionary"""
        english = self.english_input.text().strip()
        khmer = self.khmer_input.text().strip()
        word_type = self.type_combo.currentText()
        definition = self.definition_input.text().strip()
        example = self.example_input.text().strip()
        
        if not english or not khmer:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning,
                "Input Error",
                "Please enter both English and Khmer words!"
            )
            msg.exec()
            return
        
        try:
            word_id = self.db.create_word(english, khmer, word_type, definition, example)
            self.clear_form()
            self.refresh_dictionary()
            self.word_added.emit(english)
            
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Information,
                "Success",
                f"Word '{english}' ➞ '{khmer}' created successfully!\nWord ID: {word_id}"
            )  
            msg.exec()
            
             
        except ValueError as e:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning,
                "Error",
                str(e)
            )
            msg.exec()
    
    def view_selected_word(self):
        """READ operation - View detailed information about selected word"""
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning,
                "No Selection",
                "Please select a word to view details!"
            )
            msg.exec()
            return
        
        row = selection[0].row()
        word_data = self.table_model.get_row_data(row)
        if word_data:
            dialog = WordDetailsDialog(word_data, self.font_manager, self)
            dialog.exec()
            
    def update_word(self):
        """UPDATE operation - Modify existing word"""
        if self.current_edit_id is None:
            return
        
        english = self.english_input.text().strip()
        khmer = self.khmer_input.text().strip()
        word_type = self.type_combo.currentText()
        definition = self.definition_input.text().strip()
        example = self.example_input.text().strip()
        if not english or not khmer:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning,
                "Input Error",
                "Please enter both English and Khmer words!"
            )
            msg.exec()
            return
        
        try:
            self.db.update_word(self.current_edit_id, english, khmer, word_type, definition, example)
            self.cancel_edit()
            self.refresh_dictionary()
            self.word_updated.emit(self.current_edit_id)
            
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Information,
                "Success",
                f"Word updated successfully!\nNew values: '{english}' ➞ '{khmer}'"            
                )
            msg.exec()
        except ValueError as e:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning,
                "Update Error",
                str(e)
            )
            msg.exec()
            
    def edit_selected_word(self):
        """Prepare UPDATE operation - Load selected word into form for editing"""
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning,
                "No Selection",
                "Please select a word to edit!"
            )
            msg.exec()
            return
        
        row = selection[0].row()
        word_data = se;f.table_model.get_row_data(row)
        if word_data:
            word_id, english, khmer, word_type, definition, example = word_data[:6]
            
            self.current_edit_id = word_id
            self.english_input.setText(english)
            self.khmer_input.setText(khmer)
            self.type_combo.setCurrentText(word_type)
            self.definition_input.setText(definition or "")
            self.example_input.setText(example or "")
            
            # Switch to update mode
            self.add_button.setVisible(False)
            self.update_button.setVisible(True)
            self.cancel_button.setVisible(True)
            
            # Focus on first input
            self.english_input.setFocus()
            
    def delete_selected_word(self):
        """DELETE operation - Remove selected word from dictionary"""
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Warning, "No Selection", "Please select a word to delete!"
            )
            msg.exec()
            return
        row = selection[0].row()
        word_data = self.table_model.get_row_data(row)
        if word_data:
            word_id, english, khmer = word_data[0], word_data[1], word_data[2]
            
            msg = self.font_manager.create_message_box(
                self, QMessageBox.Icon.Questions,
                "Confirm Delete",
                f"Are you sure you want to delete this word?\n\n'{english} ➞ '{khmer}'\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if msg.exec() == QMessageBox.StandardButton.Yes:
                try:
                    if self.db.delete_word(word_id):
                        self.refresh_dictionary()
                        self.word_deleted.emit(word_id)
                        success_msg = self.font_manager.create_message_box(
                            self, QMessageBox.Icon.Information,
                            information
                        )
                        success_msg.exec()
                    else:
                        error_msg = self.font_manager.create_message_box(
                            self, QMessageBox.Icon.Warning,
                            "Delete Failed", "Failed to delete the word. It may have already been removed."
                        )
                        error_msg.exec()
                except ValueError as e:
                    error_msg = self.font_manager.create_message_box(
                    self, QMessageBox.Icon.Critical, "Delete Error", str(e)
                    )
                    error_msg.exec()
    
    def refresh_dictionary(self):
        """refresh the table view with current database data"""
        words = self.db.read_all_words()
        self.table_model.update_data(words)
        self.stats_label.setText(f"Total entries: {len(words)}")
        
    def filter_dictionary(self):
        """filter dictionary entries based on search text"""
        filter_text = self.filter_input.text().strip().lower()
        
        if not filter_text:
            self.refresh_dictionary()
            return
        
        words = self.db.read_all_words()
        filtered_words = []
        
        for word in words:
            word_id, english, khmer, word_type, definition, example, created, updated = word
            if(filter_text in english.lower() or 
               filter_text in khmer or 
               filter_text in word_type.lower() or
               filter_text in (definition or "").lower()):
                filtered_words.append(word) 
                
            self.table_model.update_data(filtered_words)
            self.stats_label.setText(f"Showing {len(filtered_words)} of {len(words)} entries")
    
    def cancel_edit(self):
        """Cancel edit mode and return to create mode"""
        self.current_edit_id = None
        self.clear_form()
        
        # switch back to create mode
        self.add_button.setVisible(True)
        self.update_button.setVisible(False)
        self.cancel_button.setVisible(False)
        
    def clear_form(self):
        """Clear all form inputs"""
        self.english_input.clear()
        self.khmer_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.definition_input.clear()
        self.example_input.clear()
        self.english_input.setFocus()

class StatisticsWidget(QWidget):
    def __init__(self, db, font_manager):
        super().__init__()
        self.db = db
        self.font_manager = font_manager
        self.search_count = 0
        self.init_ui()
        self.update_stats()
        
    def init_ui(self):
        # apply font to entire widget
        self.font_manager.apply_font(self)
        
        layout = QVBoxLayout()
        
        # statistics section
        stats_group = QGroupBox("Dictionary Statistics")
        self.font_manager.apply_font(stats_group, bold=True)
        stats_layout = QVBoxLayout()
        
        self.total_words_label = QLabel()
        self.font_manager.apply_font(self.total_words_label)
        
        self.word_types_label = QLabel()
        self.font_manager.apply_font(self.word_types_label)
        self.word_types_label.setWordWrap(True)
        
        self.searches_label = QLabel()
        self.font_manager.apply_font(self.searches_label)
        
        stats_layout.addWidget(self.total_words_label)
        stats_layout.addWidget(self.word_types_label)
        stats_layout.addWidget(self.searches_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Sample words
        sample_group = QGroupBox("Sample Khmer Words")
        sample_group.setFixedHeight(490)
        self.font_manager.apply_font(sample_group, bold=True)
        
        sample_layout = QVBoxLayout()
        
        self.sample_display = QTextBrowser()
        self.sample_display.setMaximumHeight(600)
        self.font_manager.apply_font(self.sample_display)
        
        sample_layout.addWidget(self.sample_display)
        sample_group.setLayout(sample_layout)
        layout.addWidget(sample_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        update_btn = QPushButton("Update Statistics")
        self.font_manager.apply_font(update_btn)
        update_btn.clicked.connect(self.update_stats)
        
        export_btn = QPushButton("Export Word List")
        self.font_manager.apply_font(export_btn)
        export_btn.clicked.connect(self.export_word_list)
        
        button_layout.addWidget(update_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def update_stats(self):
        words = self.db.read_all_words()
        
        total_words = len(words)
        self.total_words_label.setText(f"Total Dictionary Entries: {total_words}")
        
        type_counts = {}
        for word in words:
            word_type = word[3]
            type_counts[word_type] = type_counts.get(word_type, 0) + 1
            
        type_text = "Word Types: " + ", ".join([f"{t}: {c}" for t, c in type_counts.items()])
        self.word_types_label.setText(type_text)
        
        self.searches_label.setText(f"Searches This Session: {self.search_count}")
        
        # Display sample words with Khmer font
        sample_words = self.db.get_random_words(10)
        html_content = "<h3>Sample Words:</h3>"
        for word in sample_words:
            english, khmer = word[1], word[2]
            html_content += f"<p><strong>{english}</strong> ➞ {khmer}</p>"
            
        self.sample_display.setHtml(html_content)
        
    def export_word_list(self):
        msg = self.font_manager.create_message_box(
            self, QMessageBox.Icon.Information,
            "Export",
            "Export feature coming soon!\n\nThis will allow you to save your dictionary as:\n• CSV files\n• Printable lists"
        )
        msg.exec()
    
    def increment_search_count(self):
        self.search_count += 1
        self.searches_label.setText(f"Searches This Session: {self.search_count}")
        
class KhmerEnglishDictionaryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DictionaryDatabase()
        self.font_manager = FontManager()
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        # Apply font to entire application
        self.font_manager.apply_font(self)
        
        self.setWindowTitle("Khmer-English Dictionary • វចនានុក្រមអង់គ្លេស-ខ្មែរ")
        self.setGeometry(100,100,1200,800)
        
        # use standard Qt styling with Khmer font
        self.setStyleSheet(f"""
            QMainWindow{{
                background-color: #f5f5f5;
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
            }}
            QTabWidget::pane{{
                border: 1px solid #c0c0c0;
                background-color: white;
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
            }}
            QTabBar::tab{{
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
            }}
            QTabBar::tab:selected{{
                background-color: white;
                border-bottom: 2px solid #4a90e2;
            }}
            QGroupBox{{
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
            }}
            QGroupBox::title{{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
            }}
            QLineEdit, QComboBox, QPushButton, QTextEdit, QTextBrowser{{
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
                padding: 5px;
            }}
            QTableView{{
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
                gridline-color: #d0d0d0;
            }}
            QHeaderView::section{{
                background-color: #e8e8e8;
                padding: 8px;
                border: 1px solid #c0c0c0;
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
                font-weight: bold;
            }}
            QLabel{{
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
            }}
            * {{
                font-family: '{self.font_manager.get_font_family()}';
                font-size: {self.font_manager.font_size}pt;
            }}
        """)
        
        central_widget = QWidget()
        self.font_manager.apply_font(central_widget)
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        self.tab_widget = QTabWidget()
        self.font_manager.apply_font(self.tab_widget)
        
        # create tabs with CRUD functionality
        self.translator_tab = TranslatorWidgets(self.db, self.font_manager)
        self.manager_tab = DictionaryManagerWidget(self.db, self.font_manager)
        self.stats_tab = StatisticsWidget(self.db, self.font_manager)
        
        self.tab_widget.addTab(self.translator_tab, "Translator")
        self.tab_widget.addTab(self.manager_tab, "Dictionary Manager (CRUD)")
        self.tab_widget.addTab(self.stats_tab, "Statistics")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar with Khmer font
        status_bar = self.statusBar()
        self.font_manager.apply_font(status_bar)
        status_bar.showMessage("Ready - សូមស្វាគមន៍មកកាន់វចនានុក្រម (Welcome to the Dictionary)")
        
        # focus on the first tab
        self.tab_widget.setCurrentIndex(0)
        
    def connect_signals(self):
        """Connect signals betweenn widgets"""
        self.translator_tab.word_searched.connect(
            lambda word, search_type: self.stats_tab.increment_search_count()
        )
        
        self.manager_tab.word_added.connect(
            lambda word: self.statusBar().showMessage(f"✔️ Created word: {word}")
        )
        
        self.manager_tab.word_updated.connect(
            lambda word_id: self.statusBar().showMessage(f"✔️ Updated word ID: {word_id}")
        )
        
        self.manager_tab.word_deleted.connect(
            lambda word_id: self.statusBar().showMessage(f"✔️ Deleted word ID: {word_id}")
        )
    
def main():
    app = QApplication(sys.argv)
    
    # create font manager and set applicatoin-wide font
    font_manager = FontManager()
    app.setFont(font_manager.get_font())
    
    app.setApplicationName("Khmer-English Dictionary")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Student Learning Tools")
    
    try:
        window = KhmerEnglishDictionaryApp()
        window.show()
        window.showMaximized()
        sys.exit(app.exec())
    
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
if __name__ == '__main__':
    main()