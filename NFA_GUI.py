import sys
import os
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QScrollArea, QFileDialog
)
from PySide6.QtGui import QPixmap, QFont, QMovie
from PySide6.QtCore import Qt, QTimer
from graphviz import Digraph

from NFA_CODE import regex_to_nfa, visualize_nfa

class NFAConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Regex to NFA")
        self.setGeometry(100, 100, 900, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Group for input and buttons (to be centered)
        input_button_group = QHBoxLayout()
        
        # Input field
        self.regex_input = QLineEdit()
        self.regex_input.setFont(QFont('Arial', 16))  
        placeholder_font = QFont('Arial', 12)
        self.regex_input.setPlaceholderText("Enter regex")
        self.regex_input.setFont(placeholder_font)
        self.regex_input.setStyleSheet("QLineEdit { font: 16pt 'Arial'; }")  
        self.regex_input.setFixedSize(300, 70) 
        input_button_group.addWidget(self.regex_input)
        
        # Button section (stacked vertically, to the right of the input field)
        button_layout = QVBoxLayout()
        convert_button = QPushButton("Convert to NFA")
        convert_button.clicked.connect(self.convert_regex)
        convert_button.setFixedWidth(150)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_all)
        clear_button.setFixedWidth(150)
        button_layout.addWidget(convert_button)
        button_layout.addWidget(clear_button)
        button_layout.setSpacing(10)  
        input_button_group.addLayout(button_layout)
        
        # Center the entire group (input + buttons)
        group_wrapper = QHBoxLayout()
        group_wrapper.addStretch()
        group_wrapper.addLayout(input_button_group)
        group_wrapper.addStretch()
        
        # Output section
        output_section = QWidget()
        output_layout = QHBoxLayout(output_section)
        
        # Image display area with scroll
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_scroll.setWidget(self.image_label)
        output_layout.addWidget(self.image_scroll)
        
        # Add a label for the "NFA" text
        self.waiting_label = QLabel("NFA", self.image_label)
        self.waiting_label.setFont(QFont('Arial', 16))
        self.waiting_label.setStyleSheet("color: white; background: transparent;")
        self.waiting_label.hide()  
        
        # Add a label for error messages
        self.error_label = QLabel("", self.image_label)
        self.error_label.setFont(QFont('Arial', 14))
        self.error_label.setStyleSheet("color: red; background: transparent;")
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()  
        # Position the error label in the center of the image area
        self.error_label.setGeometry(0, 0, self.image_label.width(), self.image_label.height())
        
        # Timer for moving the "NFA" text
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_waiting_text)
        self.timer.start(16) #60 Frames  
        
        # Timer for the 5-second loading delay
        self.loading_timer = QTimer(self)
        self.loading_timer.setSingleShot(True)  # Run only once
        self.loading_timer.timeout.connect(self.show_nfa_result)
        
        # Variables for text movement
        self.text_x = 0
        self.text_y = 0
        self.dx = 2
        self.dy = 2 
        
        # Add sections to main layout
        main_layout.addLayout(group_wrapper)  # Centered input and buttons
        main_layout.addWidget(output_section)  # Image scroll area at the bottom
        
        self.setCentralWidget(main_widget)
    
        # Initialize variables
        self.current_nfa_image_path = None
        self.movie = None 
        self.nfa_result = None 
    
    def move_waiting_text(self):
        # Show the waiting label if no image, GIF, or error message is displayed
        if not self.image_label.pixmap() and (self.movie is None or not self.movie.isValid()) and not self.error_label.isVisible():
            self.waiting_label.show()
        else:
            self.waiting_label.hide()
            return
        
        # Update the label size to match the current text
        self.waiting_label.adjustSize()

        # Ensure font size remains 16px
        font = self.waiting_label.font()
        font.setPointSize(16)
        self.waiting_label.setFont(font)

        # Get the size of the image label (the area where the text will move)
        label_size = self.image_label.size()
        text_size = self.waiting_label.size()
        
        # Update position
        self.text_x += self.dx
        self.text_y += self.dy
        
        # Bounce off the edges
        if self.text_x <= 0 or self.text_x + text_size.width() >= label_size.width():
            self.dx = -self.dx  
            self.text_x = max(0, min(self.text_x, label_size.width() - text_size.width()))
        if self.text_y <= 0 or self.text_y + text_size.height() >= label_size.height():
            self.dy = -self.dy  
            self.text_y = max(0, min(self.text_y, label_size.height() - text_size.height()))
        
        # Move the text
        self.waiting_label.move(int(self.text_x), int(self.text_y))
    
    def show_error_message(self, message):
        # Clear any existing image or GIF
        self.image_label.clear()
        if self.movie:
            self.movie.stop()
            self.movie = None
        
        # Show the error message
        self.error_label.setText(message)
        self.error_label.show()
        # Update the geometry to center the error message
        label_size = self.image_label.size()
        self.error_label.setGeometry(0, 0, label_size.width(), label_size.height())
    
    def show_gif(self, gif_path):
        # Stop any existing GIF
        if self.movie:
            self.movie.stop()
        # Clear any existing error message or image
        self.error_label.hide()
        self.image_label.clear()
        # Display the GIF
        absolute_path = os.path.abspath(gif_path)
        print(f"Attempting to load GIF from: {absolute_path}")  
        if not os.path.exists(absolute_path):
            print(f"GIF file not found at: {absolute_path}")
            self.show_error_message(f"GIF file not found: {gif_path}")
            return False
        self.movie = QMovie(gif_path)
        if self.movie.isValid():
            print("GIF loaded successfully, starting playback.") 
            self.image_label.setMovie(self.movie)
            self.movie.start()
            return True
        else:
            print("Failed to load GIF.") 
            self.show_error_message(f"Failed to load GIF: {gif_path}")
            return False
    
    def show_nfa_result(self):
        # Stop the loading GIF
        if self.movie:
            self.movie.stop()
            self.movie = None
        self.image_label.clear()
        # Ensure the error label is hidden before showing the NFA result
        self.error_label.hide()
        
        # Display the NFA result (or error) that was computed during the loading period
        if self.nfa_result is None:
            self.show_error_message("Failed to convert regex to NFA. Check your regex syntax.")
        elif self.current_nfa_image_path is None:
            self.show_error_message("Visualization failed: No image path returned. Check if Graphviz is installed and if the output directory is writable.")
        elif os.path.exists(self.current_nfa_image_path):
            pixmap = QPixmap(self.current_nfa_image_path)
            if pixmap.isNull():
                self.show_error_message("Failed to load the generated image. The file might be corrupted.")
            else:
                self.image_label.setPixmap(pixmap)
                self.image_label.adjustSize()
        else:
            self.show_error_message(f"Image file not found at: {self.current_nfa_image_path}")
    
    def convert_regex(self):
        regex = self.regex_input.text().strip()
        if not regex:
            self.waiting_label.setText("String is empty")
            self.waiting_label.setStyleSheet("color: red; background: transparent;")
            self.waiting_label.show()
            QTimer.singleShot(2000, self.reset_waiting_label)  # Reset after 2 seconds
            return 

        # Clear any GIF or error message if present
        if self.movie:
            self.movie.stop()
            self.movie = None
        self.error_label.hide()
        self.image_label.clear()
        
        # Show the loading GIF and start the timer
        if self.show_gif("loading.gif"):
            self.loading_timer.start(1500)  # 1500ms = 1.5 seconds
        else:
            self.loading_timer.start(1500)  
        
        # Compute the NFA result in the background
        try:
            # Convert regex to NFA
            self.nfa_result = regex_to_nfa(regex)
            if self.nfa_result is None:
                return  
            
            # Visualize NFA
            self.current_nfa_image_path = visualize_nfa(self.nfa_result, "nfa_output")
            
        except Exception as e:
            self.nfa_result = None  # Indicate an error
            self.current_nfa_image_path = None
            print(f"Error during NFA conversion: {str(e)}") 
    
    def reset_waiting_label(self):
        self.waiting_label.setText("NFA")
        self.waiting_label.setStyleSheet("color: white; background: transparent;")  	
        font = QFont('Arial', 16)
        self.waiting_label.setFont(font)

    def save_image(self):
        if self.current_nfa_image_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save NFA Image", "", "PNG Files (*.png);;All Files (*)"
            )
            if file_path:
                pixmap = QPixmap(self.current_nfa_image_path)
                pixmap.save(file_path)
                # Show success message in the image area
                self.image_label.clear()
                self.show_error_message(f"Image saved to {file_path}")
        else:
            self.show_error_message("No NFA image to save. Convert a regex first.")
       
    def clear_all(self):
        self.regex_input.clear()
        self.image_label.clear()
        self.current_nfa_image_path = None
        self.nfa_result = None
        self.error_label.hide()
        # Stop any GIF if present
        if self.movie:
            self.movie.stop()
            self.movie = None
        # Stop the loading timer if it's running
        if self.loading_timer.isActive():
            self.loading_timer.stop()
        # Reset waiting label
        self.waiting_label.setText("NFA")
        self.waiting_label.setStyleSheet("color: white; background: transparent;") 	
        font = QFont('Arial', 16)
        self.waiting_label.setFont(font)
    
def main():
    app = QApplication(sys.argv)
    window = NFAConverterGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
