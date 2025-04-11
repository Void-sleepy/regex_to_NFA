import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QScrollArea, QFileDialog, QMessageBox
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt
from graphviz import Digraph

from NFA_CODE import regex_to_nfa, visualize_nfa


class NFAConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Regex to NFA")
        self.setGeometry(100, 100, 900, 600)
        
      
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        
 # Input section
        input_layout = QHBoxLayout()
      
        self.regex_input = QLineEdit()
        self.regex_input.setFont(QFont('Arial', 16))
        self.regex_input.setPlaceholderText("Enter regex")
        convert_button = QPushButton("Convert to NFA")
        convert_button.clicked.connect(self.convert_regex)
        input_layout.addWidget(self.regex_input)
        input_layout.addWidget(convert_button)
        
        # Clear button 
        clear_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_all)
        clear_button.setFixedWidth(100)  
        clear_layout.addStretch()  
        clear_layout.addWidget(clear_button)
        clear_layout.addStretch()  
        
        # Output section
        output_section = QWidget()
        output_layout = QHBoxLayout(output_section)
        
        # Image display 
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_scroll.setWidget(self.image_label)
        output_layout.addWidget(self.image_scroll)
        
        #####################
        main_layout.addLayout(input_layout)
        main_layout.addLayout(clear_layout)  
        main_layout.addWidget(output_section)
        
    
        self.setCentralWidget(main_widget)
    
        # Initialize variables
        self.current_nfa_image_path = None
    
    def convert_regex(self):
        regex = self.regex_input.text().strip()
        if not regex:
            QMessageBox.warning(self, "Input Error", "Please enter a regular expression.")
            return
        
        try:
            # Convert regex to NFA
            nfa = regex_to_nfa(regex)
            if nfa is None:
                QMessageBox.warning(self, "Error", "Failed to convert regex to NFA. Check your regex syntax.")
                return
            
            # Visualize NFA
            self.current_nfa_image_path = visualize_nfa(nfa, "nfa_output")
            
            # Check if the path is None
            if self.current_nfa_image_path is None:
                QMessageBox.warning(self, "Error", "Visualization failed: No image path returned. Check if Graphviz is installed and if the output directory is writable.")
                return
                
            # Display the image
            if os.path.exists(self.current_nfa_image_path):
                pixmap = QPixmap(self.current_nfa_image_path)
                if pixmap.isNull():
                    QMessageBox.warning(self, "Error", "Failed to load the generated image. The file might be corrupted.")
                    return
                self.image_label.setPixmap(pixmap)
                self.image_label.adjustSize()
            else:
                QMessageBox.warning(self, "Error", f"Image file not found at: {self.current_nfa_image_path}")
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")
            self.image_label.clear()
    
    def save_image(self):
        if self.current_nfa_image_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save NFA Image", "", "PNG Files (*.png);;All Files (*)"
            )
            if file_path:
                pixmap = QPixmap(self.current_nfa_image_path)
                pixmap.save(file_path)
                QMessageBox.information(self, "Save Successful", f"Image saved to {file_path}")
        else:
            QMessageBox.warning(self, "No Image", "No NFA image to save. Convert a regex first.")
       
    def clear_all(self):
        self.regex_input.clear()
        self.image_label.clear()
        self.current_nfa_image_path = None

def main():
    app = QApplication(sys.argv)
    window = NFAConverterGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()