from PyQt5.QtWidgets import *
from bs4 import BeautifulSoup

from .utils_ui.text_processor import EnhancedTextViewer
from .utils_ui.scrapy_tools import Queries

import sys


class MiniUI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Shell UI')
        tabs = QTabWidget()
        self.queries = Queries(main=self)
        self.source = EnhancedTextViewer()
        self.notes = QPlainTextEdit()
        tabs.addTab(self.queries, 'Tools')
        tabs.addTab(self.source, 'Source')
        tabs.addTab(self.notes, 'Notes')
        self.setCentralWidget(tabs)

    def add_selector(self, response):
        self.queries.update_source(response)
        soup = BeautifulSoup(response.text, 'html.parser')
        html_out = soup.prettify()
        self.source.setPlainText(html_out)


def load_selector(selector):
    print('Shell UI window opened - Close window to regain use of shell')
    app = QApplication(sys.argv)
    main = MiniUI()
    main.add_selector(selector)
    main.show()
    app.exec_()
