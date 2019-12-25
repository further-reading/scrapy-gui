import sys
import requests
from parsel import Selector
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit,
    QMainWindow, QGridLayout, QDialog, QPlainTextEdit,
    QTableWidget, QLabel, QTabWidget, QVBoxLayout,
    QTableWidgetItem, QAbstractScrollArea
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

MAIN_WIDTH = 2000
MAIN_HEIGHT = 1200

POP_OUT_WIDTH = MAIN_WIDTH/2
POP_OUT_HEIGHT = MAIN_HEIGHT/2

class Main(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Browser')
        self.setCentralWidget(QtBrowser(self))
        self.resize(MAIN_WIDTH, MAIN_HEIGHT)
        self.show()


class QtBrowser(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.html = None
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.open_css_button = QPushButton('CSS')
        self.open_css_button.clicked.connect(self.open_css)
        grid.addWidget(self.open_css_button, 0, 4)
        self.open_css_button.setDisabled(True)

        go_button = QPushButton('Go')
        go_button.clicked.connect(self.go_to_page)
        grid.addWidget(go_button, 0, 3)

        self.entry_box = QLineEdit()
        self.entry_box.returnPressed.connect(go_button.click)
        grid.addWidget(self.entry_box, 0, 2)

        self.web = QWebEngineView()
        grid.addWidget(self.web, 1, 0, 1, 5)
        self.web.urlChanged.connect(self.update_url)
        self.web.loadFinished.connect(self.loadFinished)
        self.web.load(QUrl('http://quotes.toscrape.com/'))

        back_button = QPushButton('Back')
        back_button.clicked.connect(self.web.back)
        grid.addWidget(back_button, 0, 0)

        forward_button = QPushButton('Forward')
        forward_button.clicked.connect(self.web.forward)
        grid.addWidget(forward_button, 0, 1)

    def go_to_page(self):
        self.open_css_button.setDisabled(True)
        entered_page = self.entry_box.text()
        if not entered_page.startswith('http'):
            entered_page = f'https://{entered_page}'
        elif not entered_page.startswith('https'):
            entered_page = entered_page.replace('http', 'https', 1)

        self.web.load(QUrl(entered_page))

    def update_url(self):
        url = self.get_url()
        self.entry_box.setText(url)

    def open_css(self):
        self.open_css_button.setDisabled(True)
        url = self.get_url()
        dial = AnalysisDialog(url=url)
        dial.exec()
        self.open_css_button.setDisabled(False)

    def get_url(self):
        qurl = self.web.url()
        url = qurl.url()
        return url

    def loadFinished(self):
        self.open_css_button.setDisabled(False)


class AnalysisDialog(QDialog):
    def __init__(self, *args, url, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.html = self.get_html_source()
        self.initUI()
        self.resize(
            POP_OUT_WIDTH,
            POP_OUT_HEIGHT,
        )

    def initUI(self):
        self.setWindowTitle('Tabs')
        tabs = QTabWidget()
        box = QVBoxLayout()
        self.setLayout(box)
        parser = ParserTab(html=self.html)
        tabs.addTab(parser, "Parser")

        html_source = QPlainTextEdit()
        html_source.setPlainText(self.html)
        html_source.setReadOnly(True)
        tabs.addTab(html_source, 'Source')

        box.addWidget(tabs)

    def get_html_source(self):
        # pyqt5 webengine has the final html including manipulation from javascript, etc
        # for scraping with scrapy the first one matters, so will get again
        # in future = look for way to grab initial html response from pyqt5
        response = requests.get(self.url)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        html_out = soup.prettify()
        return html_out


class ParserTab(QWidget):
    def __init__(self, *args, html, **kwargs):
        super().__init__(*args, **kwargs)
        self.html = html
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        css_label = QLabel('Enter CSS Query:')
        grid.addWidget(css_label, 0, 0)

        self.query = QPlainTextEdit()
        grid.addWidget(self.query, 0, 1)

        run_query_button = QPushButton('Run CSS Query')
        grid.addWidget(run_query_button, 1, 1)
        run_query_button.clicked.connect(self.do_query)

        self.results = QTableWidget()
        self.results.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents)
        grid.addWidget(self.results, 2, 0, 1, 2)

    def do_query(self):
        query = self.query.toPlainText()
        sel = Selector(text=self.html)
        results = sel.css(query).getall()
        if results:
            self.results.clearContents()
            self.results.setColumnCount(1)
            # self.results.setRowCount(len(results))
            for index, result in enumerate(results):
                self.results.insertRow(index)
                self.results.setItem(
                    index,
                    0,
                    QTableWidgetItem(result),
                )
            self.results.resizeColumnsToContents()
            self.results.resizeRowsToContents()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
