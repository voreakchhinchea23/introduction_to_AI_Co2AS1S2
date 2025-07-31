import sys
import time
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QLineEdit, QTableWidget,
    QDialog, QFormLayout, QGraphicsScene, QGraphicsView, QMenu, QComboBox, QGraphicsItem
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QFontMetrics, QIcon 
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ColorCell(QGraphicsItem):
    def __init__(self, color_name, colors_list, parent_window, i, j, cell_size, parent=None):
        super().__init__(parent)
        self.original_color_name = color_name
        self.display_color = QColor(self.get_color_rgb(color_name))
        self.default_color = self.display_color
        self.selected_color_name = None
        self.colors_list = colors_list
        self.parent_window = parent_window
        self.i = i
        self.j = j
        self.cell_size = cell_size
        self.toggle_state = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.toggle_flash_color) 
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)
        
    def boundingRect(self):
        return QRectF(-self.cell_size / 2, -self.cell_size / 2, self.cell_size, self.cell_size)
        
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(Qt.GlobalColor.black, 1.5)
        painter.setPen(pen)
        painter.setBrush(self.display_color)
        rect = self.boundingRect()
        painter.drawRoundedRect(rect, 10, 10)
            
        display_text = self.selected_color_name or ""
        painter.setPen(Qt.GlobalColor.black)
        font = QFont("Segoe UI", int(self.cell_size * 0.2), QFont.Weight.Medium)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(display_text)
        painter.drawText(QPointF(-text_width / 2, 5), display_text)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = event.scenePos()
            item = self.scene().itemAt(scene_pos, self.parent_window.view.transform())
            if item == self:
                logging.debug(f"Cell clicked at ({self.i}, {self.j}), scene coordinates: ({scene_pos.x()}, {scene_pos.y()})")
                menu = QMenu()
                for color in self.colors_list:
                    action = menu.addAction(color)
                    action.triggered.connect(lambda checked, c=color: self.setSelectedColor(c))
                menu.exec(event.screenPos())
                event.accept()
                    
    def setSelectedColor(self, color_name):
        logging.debug(f"Setting selected color: {color_name} for cell ({self.i}, {self.j})")
        self.selected_color_name = color_name
        self.update()
        self.parent_window.update_cell(self.i, self.j, color_name)
            
    def evaluate_match(self, correct_color):
        if self.selected_color_name == correct_color:
            self.display_color = QColor(self.get_color_rgb(self.original_color_name))    
            self.update()
            self.stop_flash()
        else:
            self.start_flash()
                
    def start_flash(self):
        if not self.timer.isActive():
            self.toggle_state = False
            self.timer.start(500)

    def stop_flash(self):
        if self.timer.isActive():
            self.timer.stop()
            self.display_color = QColor(self.get_color_rgb(self.original_color_name))
            self.update()
                
    def toggle_flash_color(self):
        if self.toggle_state:
            self.display_color = QColor("red")
        else:
            self.display_color = QColor("green")
        self.toggle_state = not self.toggle_state
        self.update()
            
    def get_color_rgb(self, color_name):
        color_map = {
            "red": "#FF0000", "orange": "#FFA500", "yellow": "#FFFF00",
            "green": "#008000", "blue": "#0000FF", "purple": "#800080",
            "black": "#000000", "white": "#FFFFFF", "brown": "#8B4513",
        }
        return color_map.get(color_name.lower(), "#ADD8E6")  # Default to light blue if color not found
    
class TimeUpdater:
    def __init__(self, label):
        self.label = label
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        self.update_time()

    def update_time(self):
        current_time = time.strftime("%H:%M:%S %p +07, %B %d, %Y", time.localtime())
        self.label.setText(f"CSP Color Matching Game - {current_time}")

class ColorMatchingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSP Color Matching Game")
        self.setGeometry(100, 100, 600, 600)
        self.setWindowIcon(QIcon("icon.png"))
        
        self.size = 3
        self.colors = []
        self.init_colors = []
        self.user_grid = []
        self.cells = []
    
        self.setStyleSheet("""
            QLabel#HeaderLabel {
                font-size: 20px;
                font-weight: bold;
                padding: 6px;
                color: #333333;
            }
            QLabel#StatusLabel {
                font-size: 14px;
                padding: 6px;
                color: #444444;
            }     
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 14px;
                font-size: 14px;
                border: none;
                border-radius: 6px;
            }                  
            QPushButton:hover {
                background-color: #45a049;
            }
            QGraphicsView {
                border: 2px solid #999999;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
        """)
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        current_time = time.strftime("%I:%M %p +07, %B %d, %Y", time.localtime())
        self.header_label = QLabel(f"CSP Color Matching Game - {current_time}")
        self.header_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 6px; color: #008000;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setObjectName("HeaderLabel")
        layout.addWidget(self.header_label)
        
        self.admin_btn = QPushButton("Admin Settings")
        self.admin_btn.clicked.connect(self.show_admin_dialog)
        layout.addWidget(self.admin_btn)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.view)
        
        button_layout = QHBoxLayout()
        self.check_btn = QPushButton("Check Matching")
        self.check_btn.clicked.connect(self.check_csp)
        self.check_btn.setEnabled(False)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_grid)
        self.clear_btn.setEnabled(False)
        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.clicked.connect(self.new_game)
        self.new_game_btn.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(self.check_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.new_game_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.status_label = QLabel("Welcome! Use Admin Settings to configure.")
        self.status_label.setStyleSheet("font-size: 14px; padding: 6px; color: green;")
        self.status_label.setObjectName("StatusLabel")
        layout.addWidget(self.status_label)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.generate_game()
        
    def show_admin_dialog(self):
        dialog = AdminDialog(self.colors or ["red", "orange", "yellow", "green",
                                            "blue", "purple", "black", "white", "brown"], self)
        if dialog.exec():
            self.status_label.setText("Grid generated. Click cells to select.")
            self.check_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            self.new_game_btn.setEnabled(True)
        
    def generate_game(self):
        if not self.init_colors:
            return
        self.scene.clear()
        view_width = self.view.viewport().width()
        view_height = self.view.viewport().height()
        available_size = min(view_width, view_height)
        spacing = 10
        total_spacing = spacing * (self.size + 1)
        cell_size = (available_size - total_spacing) / self.size
        
        total_grid_width = self.size * (cell_size + spacing)
        total_grid_height = self.size * (cell_size + spacing)
        x_offset = (view_width - total_grid_width) / 2 + cell_size / 2
        y_offset = (view_height - total_grid_height) / 2 + cell_size / 2 
        
        self.cells = [[None for _ in range(self.size)] for _ in range(self.size)]
        for i in range(self.size):
            for j in range(self.size):
                cell = ColorCell(self.init_colors[i][j], self.colors, self, i, j, cell_size)
                x = j * (cell_size + spacing) + x_offset
                y = i * (cell_size + spacing) + y_offset
                cell.setPos(x, y)
                self.scene.addItem(cell)
                self.cells[i][j] = cell
                self.user_grid[i][j] = None
        self.scene.setSceneRect(0, 0, view_width, view_height)
    
    def update_cell(self, i, j, selected_color_name):
        self.user_grid[i][j] = selected_color_name
        
    def clear_grid(self):
        for i in range(self.size):
            for j in range(self.size):
                cell = self.cells[i][j]
                cell.selected_color_name = None
                cell.display_color = QColor(cell.get_color_rgb(cell.original_color_name))
                cell.stop_flash()
                cell.update()
                self.user_grid[i][j] = None
        self.status_label.setText("Grid cleared. Click cells to select colors.")
        
    def new_game(self):
        self.show_admin_dialog()
    
    def check_csp(self):
        consistent = True
        for i in range(self.size):
            for j in range(self.size):
                cell = self.cells[i][j]
                correct_color = self.init_colors[i][j]
                if cell.selected_color_name != correct_color:
                    consistent = False
                cell.evaluate_match(correct_color)
        score = sum(1 for i in range(self.size) for j in range(self.size) if self.user_grid[i][j] == self.init_colors[i][j]) 
        
        result_dialog = QDialog(self)
        result_dialog.setWindowTitle("CSP Matching Result")
        result_layout = QVBoxLayout(result_dialog)
        
        result_label = QLabel(f"CSP Evaluation Result: {'✔️ Consistent' if consistent else '❌ Inconsistent'}")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold;") 
        result_layout.addWidget(result_label)
        
        score_label = QLabel(f"Matching Score: {score} / {self.size * self.size}")
        score_label.setStyleSheet("font-size: 14px;")
        result_layout.addWidget(score_label)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(result_dialog.accept)
        result_layout.addWidget(close_button)
        result_dialog.exec()
        
class AdminDialog(QDialog):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Color Entry")
        self.parent = parent

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.colors_input = QLineEdit(",".join(colors))
        form.addRow("Colors (comma-separated):", self.colors_input)
        layout.addLayout(form)
        
        self.init_grid = QTableWidget(3, 3)
        self.init_grid.setHorizontalHeaderLabels(["0", "1", "2"])
        self.init_grid.setVerticalHeaderLabels(["0", "1", "2"])
        for i in range(3):
            for j in range(3):
                combo = QComboBox()
                combo.addItems(colors)
                self.init_grid.setCellWidget(i, j, combo)
        layout.addWidget(self.init_grid)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_and_generate)
        layout.addWidget(self.save_button)
        
    def save_and_generate(self):
        self.parent.size, self.parent.colors, self.parent.init_colors = self.get_data()
        self.parent.user_grid = [[None for _ in range(self.parent.size)] for _ in range(self.parent.size)]
        self.parent.generate_game()
        self.accept()
        
    def get_data(self):
        size = 3
        colors = [c.strip() for c in self.colors_input.text().split(",") if c.strip()]
        init_colors = []
        for i in range(size):
            row = []
            for j in range(size):
                combo = self.init_grid.cellWidget(i, j)
                color = combo.currentText()
                row.append(color if color in colors else "white")
            init_colors.append(row)
        return size, colors, init_colors

def main():
    app = QApplication(sys.argv)
    window = ColorMatchingWindow()
    window.show()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()