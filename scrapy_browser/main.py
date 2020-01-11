from PyQt5.QtWidgets import *

from bs4 import BeautifulSoup
from parsel import Selector
import requests

from .utils_ui.text_processor import EnhancedTextViewer
from .browser_window.browser import QtBrowser
from .utils_ui.scrapy_tools import Queries
import sys


class Main(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Browser')
        tabs = QTabWidget()
        self.browser = QtBrowser(main=self)
        self.queries = Queries(main=self)
        self.source = EnhancedTextViewer()
        self.notes = QPlainTextEdit()
        tabs.addTab(self.browser, 'Browser')
        tabs.addTab(self.queries, 'Tools')
        tabs.addTab(self.source, 'Source')
        tabs.addTab(self.notes, 'Notes')
        self.setCentralWidget(tabs)
        self.show()

    def update_source(self, url):
        # pyqt5 webengine has the final html including manipulation from javascript, etc
        # for scraping with scrapy the first one matters, so will get again
        # in future = look for way to grab initial html response from pyqt5
        response = requests.get(url)
        html = response.text
        selector = Selector(text=html)
        self.queries.update_source(selector)
        soup = BeautifulSoup(html, 'html.parser')
        html_out = soup.prettify()
        self.source.setPlainText(html_out)


def open_browser():
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
