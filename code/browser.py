import sys
import requests
from parsel import Selector
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit,
    QMainWindow, QGridLayout, QPlainTextEdit,
    QTableWidget, QLabel, QTabWidget, QSplitter,
    QTableWidgetItem, QAbstractScrollArea, QCheckBox,
    QMessageBox, QFrame, QVBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPixmap, QPainter, QCursor
from cssselect.xpath import ExpressionError
from cssselect.parser import SelectorSyntaxError
import traceback

HOME = 'http://quotes.toscrape.com/'


class QueryError(Exception):
    pass


class Main(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Browser')
        tabs = QTabWidget()
        self.browser = QtBrowser(main=self)
        self.queries = Queries(main=self)
        self.source = QPlainTextEdit()
        self.source.setReadOnly(True)
        tabs.addTab(self.browser, 'Browser')
        tabs.addTab(self.queries, 'Tools')
        tabs.addTab(self.source, 'Source')
        self.setCentralWidget(tabs)
        self.show()

    def update_url(self, url):
        self.queries.update_url(url)

    def update_source(self, text):
        self.source.setReadOnly(False)
        self.source.setPlainText(text)
        self.source.setReadOnly(True)


class QtBrowser(QWidget):
    def __init__(self, *args, main, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main
        self.html = None
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        self.setLayout(grid)

        go_button = QPushButton('Go')
        go_button.clicked.connect(self.go_to_page)
        grid.addWidget(go_button, 0, 3)

        self.entry_box = QLineEdit()
        self.entry_box.returnPressed.connect(go_button.click)
        grid.addWidget(self.entry_box, 0, 2)

        self.web = QWebEngineView()
        grid.addWidget(self.web, 1, 0, 1, 4)
        self.web.urlChanged.connect(self.update_url)
        self.web.loadFinished.connect(self.loadFinished)
        self.web.load(QUrl(HOME))

        back_button = BrowserButton(image=r'images/back.png')
        back_button.clicked.connect(self.web.back)
        grid.addWidget(back_button, 0, 0)

        forward_button = BrowserButton(image=r'images/forward.png')
        forward_button.clicked.connect(self.web.forward)
        grid.addWidget(forward_button, 0, 1)

    def go_to_page(self):
        entered_page = self.entry_box.text()
        if not entered_page.startswith('http'):
            entered_page = f'https://{entered_page}'
        elif not entered_page.startswith('https'):
            entered_page = entered_page.replace('http', 'https', 1)

        self.web.load(QUrl(entered_page))

    def update_url(self):
        url = self.get_url()
        self.entry_box.setText(url)

    def get_url(self):
        qurl = self.web.url()
        url = qurl.url()
        return url

    def loadFinished(self):
        url = self.get_url()
        self.main.update_url(url)


class BrowserButton(QPushButton):
    def __init__(self, *args, image):
        super().__init__(*args)
        self.pixmap = QPixmap(image)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)
        self.update()


class BigHandleSplitter(QSplitter):
    css_sheet = """
    QSplitter::handle {
    background-color: #000
    ;}
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.setHandleWidth(1)
        self.setStyleSheet(self.css_sheet)


class Queries(BigHandleSplitter):
    url = None
    html = None
    use_re = False

    def __init__(self, *args, main):
        super().__init__(*args)
        self.main = main
        self.initUI()

    def initUI(self):
        self.setOrientation(Qt.Vertical)
        top = BigHandleSplitter(Qt.Horizontal)
        left_frame = BigHandleSplitter(Qt.Vertical)

        self.css_section = QueryEntry(label='CSS Query:')
        self.css_section.initUI()
        left_frame.addWidget(self.css_section)

        left_bottom = QFrame()
        left_bottom_box = QVBoxLayout()
        left_bottom.setLayout(left_bottom_box)

        self.re_section = OptionalQuery(label='Regex')
        self.re_section.initUI()
        left_bottom_box.addWidget(self.re_section)

        run_button = QPushButton('Run Query')
        run_button.clicked.connect(self.do_query)
        left_bottom_box.addWidget(run_button)
        left_frame.addWidget(left_bottom)
        top.addWidget(left_frame)

        self.function_section = OptionalQuery(label='Function')
        self.function_section.initUI()
        top.addWidget(self.function_section)
        self.addWidget(top)

        self.results = QTableWidget()
        self.results.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents,
        )
        self.addWidget(self.results)

    def do_query(self):
        if self.html is None:
            return
        try:
            results = self.get_results()

            if not results:
                message = f'No results found for css query'
                QMessageBox.information(self, 'No Results', message)
                return

            use_regex = self.re_section.use
            if use_regex:
                results = self.regex_filter(results)
                if not results:
                    message = f'No results found for regex filter'
                    QMessageBox.information(self, 'No Results', message)
                    return
            else:
                results = results.getall()

            use_function = self.function_section.use
            if use_function:
                results = self.apply_function(results)
                if not results:
                    message = f'No results found for custom function'
                    QMessageBox.information(self, 'No Function Results', message)
                    return
        except QueryError:
            # error occured on a step
            # messaging handled in each method, so just end method
            return

        self.results.clearContents()
        self.results.setColumnCount(1)
        self.results.setRowCount(0)

        for index, result in enumerate(results):
            self.results.insertRow(index)
            self.results.setItem(
                index,
                0,
                QTableWidgetItem(result),
            )
        self.results.resizeColumnsToContents()
        self.results.resizeRowsToContents()

    def get_results(self):
        query = self.css_section.get_query()
        sel = Selector(text=self.html)
        try:
            results = sel.css(query)
        except (ExpressionError, SelectorSyntaxError) as e:
            message = f'Error parsing css query\n\n{e}'
            QMessageBox.critical(self, 'CSS Error', message)
            raise QueryError

        return results

    def regex_filter(self, results):
        regex = self.re_section.get_query()
        try:
            results = results.re(regex)
        except Exception as e:
            message = f'Error running regex\n\n{e}'
            QMessageBox.critical(self, 'RegEx Error', message)
            raise QueryError
        return results

    def apply_function(self, results):
        function = self.function_section.get_query()
        if not function:
            return
        if 'def user_fun(results):' not in function:
            message = f'Custom function needs to be named user_fun and have results as argument'
            QMessageBox.critical(self, 'Function Error', message)
            raise QueryError
        with open('user_fun.py', 'w') as file:
            file.write(function)
        try:
            from user_fun import user_fun
            results = user_fun(results)
        except Exception as e:
            message = f'Error running custom function\n\n{type(e).__name__}: {e.args}'
            message += f'\n\n{traceback.format_exc()}'
            print('hello')
            QMessageBox.critical(self, 'Function Error', message)
            raise QueryError

        if not isinstance(results, list) and results is not None:
            message = f'Custom function must return a list or None'
            QMessageBox.critical(self, 'Function Error', message)
            raise QueryError

        return results

    def update_url(self, url):
        self.url = url
        self.html = self.get_html_source()
        self.main.update_source(self.html)

    def get_html_source(self):
        # pyqt5 webengine has the final html including manipulation from javascript, etc
        # for scraping with scrapy the first one matters, so will get again
        # in future = look for way to grab initial html response from pyqt5
        response = requests.get(self.url)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        html_out = soup.prettify()
        return html_out


class QueryEntry(QWidget):
    def __init__(self, *args, label, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        label = QLabel(self.label)
        grid.addWidget(label, 0, 0)

        self.query = QPlainTextEdit()
        grid.addWidget(self.query, 1, 0)

    def get_query(self):
        return self.query.toPlainText()


class OptionalQuery(QueryEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use = False

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        label = QLabel(self.label)
        grid.addWidget(label, 0, 0)

        check = QCheckBox(f'Use {self.label.title()}')
        check.setChecked(False)
        check.clicked.connect(self.check_click)
        grid.addWidget(check, 0, 1)

        self.query = QPlainTextEdit()
        grid.addWidget(self.query, 2, 0, 1, 2)
        self.query.setDisabled(True)

    def check_click(self):
        self.use = not self.use
        self.query.setDisabled(not self.use)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
