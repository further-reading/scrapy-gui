from PyQt5.QtWidgets import *

from .utils_ui.text_viewer import TextViewer
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
        self.source_viewer = TextViewer()
        self.notes = QPlainTextEdit()
        tabs.addTab(self.queries, 'Tools')
        tabs.addTab(self.source_viewer, 'Source')
        tabs.addTab(self.notes, 'Notes')
        self.setCentralWidget(tabs)

    def add_selector(self, selector):
        self.queries.update_source(selector)
        self.source_viewer.setPrettyHtml(selector.text)


def load_selector(selector):
    print('Shell UI window opened - Close window to regain use of shell')
    app = QApplication(sys.argv)
    main = MiniUI()
    main.add_selector(selector)
    main.show()
    app.exec_()
