import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QListWidget, QMessageBox)

class LexiconBuilder(QWidget):
    def __init__(self):
        super().__init__()
        self.lexicon_file = "lexicon_data.json"
        self.lexicon_data = {}
        
        self.load_lexicon()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PyQt5 Lexicon Builder')
        self.resize(600, 400)

        main_layout = QHBoxLayout()

        # Left side: List of words & Add/Delete buttons
        left_layout = QVBoxLayout()
        self.word_list_widget = QListWidget()
        self.word_list_widget.itemClicked.connect(self.display_word)
        
        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton('Delete Word')
        self.delete_btn.clicked.connect(self.delete_word)
        btn_layout.addWidget(self.delete_btn)
        
        left_layout.addWidget(QLabel("Your Words:"))
        left_layout.addWidget(self.word_list_widget)
        left_layout.addLayout(btn_layout)

        # Right side: Add new words & Editor
        right_layout = QVBoxLayout()
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Enter new word...")
        
        self.meaning_input = QTextEdit()
        self.meaning_input.setPlaceholderText("Enter definition...")
        
        self.save_btn = QPushButton('Save Word')
        self.save_btn.clicked.connect(self.save_word)

        right_layout.addWidget(QLabel("Add/Edit Word:"))
        right_layout.addWidget(self.word_input)
        right_layout.addWidget(QLabel("Definition:"))
        right_layout.addWidget(self.meaning_input)
        right_layout.addWidget(self.save_btn)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

        self.update_list_view()

    def load_lexicon(self):
        if os.path.exists(self.lexicon_file):
            with open(self.lexicon_file, 'r') as f:
                self.lexicon_data = json.load(f)

    def save_lexicon_to_disk(self):
        with open(self.lexicon_file, 'w') as f:
            json.dump(self.lexicon_data, f, indent=4)

    def update_list_view(self):
        self.word_list_widget.clear()
        self.word_list_widget.addItems(sorted(self.lexicon_data.keys()))

    def save_word(self):
        word = self.word_input.text().strip()
        meaning = self.meaning_input.toPlainText().strip()

        if not word or not meaning:
            QMessageBox.warning(self, 'Error', 'Both Word and Definition are required.')
            return

        self.lexicon_data[word] = meaning
        self.save_lexicon_to_disk()
        self.update_list_view()
        
        # Clear inputs
        self.word_input.clear()
        self.meaning_input.clear()

    def display_word(self, item):
        word = item.text()
        self.word_input.setText(word)
        self.meaning_input.setPlainText(self.lexicon_data.get(word, ""))

    def delete_word(self):
        selected_item = self.word_list_widget.currentItem()
        if not selected_item:
            return
        
        word = selected_item.text()
        del self.lexicon_data[word]
        self.save_lexicon_to_disk()
        self.update_list_view()
        
        self.word_input.clear()
        self.meaning_input.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LexiconBuilder()
    ex.show()
    sys.exit(app.exec_())
