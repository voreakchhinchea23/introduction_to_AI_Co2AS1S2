# Import necessary PyQt6 widgets and core modules
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QHBoxLayout, QSlider, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt
import sys

# Define a simple rule-based AI agent
class SimpleAgent:
    """
    A very basic rule-based AI agent that decides to Buy, Sell, or Wait based on price.
    """
    def decide(self, environment):
        price = environment["price"]
        if price < 30:
            return "Buy"
        elif price > 70:
            return "Sell"
        else:
            return "Wait"

# Main GUI class for the AI Agent Simulator
class AIAgentSimulator(QWidget):
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("AI Agent Simulator")
        self.setGeometry(100, 100, 400, 300)

        # Initialize environment and agent
        self.environment = {"price": 50}      # Simulated environment with a price value
        self.agent = SimpleAgent()            # Create a simple agent instance

        # Create and arrange UI components
        self.create_widgets()
        self.layout_widgets()
    
    def create_widgets(self):
        # Display the current price
        self.price_label = QLabel(f"Price: {self.environment['price']}")

        # Create a horizontal slider to adjust price (0 to 100)
        self.price_slider = QSlider(Qt.Orientation.Horizontal)
        self.price_slider.setRange(0, 100)
        self.price_slider.setValue(self.environment['price'])
        self.price_slider.valueChanged.connect(self.update_price)  # Connect slider movement to update function

        # Group box for manual agent actions
        self.action_group = QGroupBox("Trigger Agent Action")

        # Manual action buttons
        self.buy_button = QPushButton("Buy")
        self.sell_button = QPushButton("Sell")
        self.wait_button = QPushButton("Wait")

        # Connect each button to a function that logs the manual action
        self.buy_button.clicked.connect(lambda: self.manual_action("Buy"))
        self.sell_button.clicked.connect(lambda: self.manual_action("Sell"))
        self.wait_button.clicked.connect(lambda: self.manual_action("Wait"))

        # Text box to show output (read-only)
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)

        # Button to trigger AI agent decision automatically
        self.auto_decide_button = QPushButton("Auto Decide")
        self.auto_decide_button.clicked.connect(self.agent_decision)
    
    def layout_widgets(self):
        # Set up the overall layout
        layout = QVBoxLayout()

        # Add environment controls
        layout.addWidget(QLabel("Environment Controls"))
        layout.addWidget(self.price_label)
        layout.addWidget(self.price_slider)

        # Horizontal layout for action buttons inside the group box
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.buy_button)
        h_layout.addWidget(self.sell_button)
        h_layout.addWidget(self.wait_button)
        self.action_group.setLayout(h_layout)

        # Add components to the main layout
        layout.addWidget(self.action_group)
        layout.addWidget(self.auto_decide_button)
        layout.addWidget(QLabel("Agent Output"))
        layout.addWidget(self.result_box)

        # Apply layout to the window
        self.setLayout(layout)

    # Called when the slider value changes — updates the price in environment
    def update_price(self, value):
        self.environment["price"] = value
        self.price_label.setText(f"Price: {value}")

    # Called when a manual action button is pressed
    def manual_action(self, action):
        self.result_box.append(f"👤Manual Action: {action}")  # Log the manual action
        self.result_box.append(f"🤖Agent Decision: {self.agent.decide(self.environment)}")  # Show agent's suggestion

    # Called when the Auto Decide button is pressed
    def agent_decision(self):
        decision = self.agent.decide(self.environment)
        self.result_box.append(f"🤖Agent decision based on price {self.environment['price']}: {decision}")

# Entry point of the application
if __name__ == "__main__":
    app = QApplication(sys.argv)          # Create application
    simulator = AIAgentSimulator()        # Create the main window
    simulator.show()                      # Show the window
    sys.exit(app.exec())                  # Start the application loop
