from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class EnhancedTextViewer(QWidget):
    current_index = 0
    total_hits = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indexes = None
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        search_button = QPushButton('Search')
        grid.addWidget(search_button, 0, 1)
        search_button.clicked.connect(self.find_pressed)

        self.search_bar = QLineEdit()
        grid.addWidget(self.search_bar, 0, 0)
        self.search_bar.returnPressed.connect(self.find_pressed)

        self.results = QLabel('0 of 0 Results')
        grid.addWidget(self.results, 0, 2)

        next_button = QPushButton('Next')
        next_button.clicked.connect(self.next_pressed)
        grid.addWidget(next_button, 0, 3)

        previous_button = QPushButton('Previous')
        previous_button.clicked.connect(self.previous_pressed)
        grid.addWidget(previous_button, 0, 4)

        self.source_text = QTextEdit()
        grid.addWidget(self.source_text, 1, 0, 1, 5)
        self.source_text.setReadOnly(True)

        self.keywordFormat = QTextCharFormat()
        self.keywordFormat.setBackground(Qt.yellow)
        self.keywordFormat.setFontWeight(QFont.Bold)

    def setPlainText(self, text):
        self.source_text.setReadOnly(False)
        self.source_text.setPlainText(text)
        self.source_text.setReadOnly(True)

    def find_pressed(self):
        self.source_text.setReadOnly(False)
        self.find_indexes()
        self.current_index = 1
        self.total_hits = len(self.indexes)
        self.set_format()
        self.update_position()
        self.source_text.setReadOnly(True)

    def make_cursor(self, index):
        cursor = self.source_text.textCursor()
        size = len(self.search_bar.text())
        cursor.setPosition(index)
        cursor.setPosition(index + size, QTextCursor.KeepAnchor)
        return cursor

    def set_format(self):
        for index in self.indexes:
            cursor = self.make_cursor(index)
            cursor.setCharFormat(self.keywordFormat)

    def find_indexes(self):
        search_term = self.search_bar.text().lower()
        all_text = self.source_text.toPlainText().lower()
        if not search_term or not all_text:
            return
        del self.indexes
        self.indexes = [i for i in range(len(all_text)) if all_text.startswith(search_term, i)]

    def next_pressed(self):
        if not self.indexes:
            return
        self.current_index += 1
        if self.current_index > self.total_hits:
            self.current_index = 1

        self.update_position()

    def previous_pressed(self):
        if not self.indexes:
            return
        self.current_index -= 1
        if self.current_index < 1:
            self.current_index = self.total_hits

        self.update_position()

    def update_position(self):
        if not self.indexes:
            return
        index = self.indexes[self.current_index - 1]
        cursor = self.make_cursor(index)
        self.source_text.setTextCursor(cursor)
        self.results.setText(f'{self.current_index} of {self.total_hits} Results')