from PyQt5.QtWidgets import *

from .utils_ui.text_viewer import TextViewer
from .utils_ui.tools_tab_ui import Queries
from .utils_ui.headers_tab_ui import HeadersViewer

import sys


class MiniUI(QMainWindow):
    def __init__(self, *args, response=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.response = response
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Scrapy GUI')
        tabs = QTabWidget()
        self.queries = Queries(main=self)
        self.source_viewer = TextViewer()
        if self.response:
            self.headers = HeadersViewer()
        self.notes = QPlainTextEdit()
        tabs.addTab(self.queries, 'Tools')
        tabs.addTab(self.source_viewer, 'Source')
        tabs.addTab(self.notes, 'Notes')
        self.setCentralWidget(tabs)

    def add_selector(self, selector, response=False):
        self.queries.update_source(selector)
        self.source_viewer.setPrettyHtml(selector.text)
        if response:
            self.headers.update_source(selector)


def load_selector(selector):
    print('Shell UI window opened - Close window to regain use of shell')
    app = QApplication(sys.argv)
    main = MiniUI()
    main.add_selector(selector)
    main.show()
    app.exec_()


def load_response(response):
    print('Shell UI window opened - Close window to regain use of shell')
    app = QApplication(sys.argv)
    main = MiniUI(response=True)
    main.add_selector(response, response=True)
    main.show()
    app.exec_()
