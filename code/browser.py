import sys
import requests
from parsel import Selector
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit,
    QMainWindow, QGridLayout, QDialog, QPlainTextEdit,
    QTableWidget, QLabel, QTabWidget, QVBoxLayout,
    QTableWidgetItem, QAbstractScrollArea, QCheckBox,
    QRadioButton,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

MAIN_WIDTH = 2000
MAIN_HEIGHT = 1200

POP_OUT_WIDTH = MAIN_WIDTH * 0.75
POP_OUT_HEIGHT = MAIN_HEIGHT * 0.75

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
        self.use_re = False
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.css_section = QueryEntry(label='CSS Query:')
        self.css_section.initUI()
        grid.addWidget(self.css_section, 0, 0)

        self.re_section = RegExEntry(label='Regex:')
        self.re_section.initUI()
        grid.addWidget(self.re_section, 1, 0)

        self.function_section = FunctionEntry(label='Function:')
        self.function_section.initUI()
        grid.addWidget(self.function_section, 0, 1, 2, 1)

        run_button = QPushButton('Run Query')
        run_button.clicked.connect(self.do_query)
        grid.addWidget(run_button, 2, 0)

        self.results = QTableWidget()
        self.results.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents,
        )
        grid.addWidget(self.results, 3, 0, 1, 2)

    def do_query(self):
        results = self.get_results()

        if not results:
            # add code to say no results
            return

        use_function = self.function_section.use_function
        if use_function:
            # add code here to catch errors in function
            results = self.apply_function(results)

        self.results.clearContents()
        self.results.setColumnCount(1)
        self.results.setRowCount(len(results))

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
        if self.re_section.use_re:
            regex = self.re_section.get_query()
        else:
            regex = None

        sel = Selector(text=self.html)
        # add try/except here to handle bad query
        results = sel.css(query)

        if not results:
            return

        if regex:
            # add try/except here to handle bad regex
            results = results.re(regex)
        else:
            results = results.getall()

        return results

    def apply_function(self, results):
        function = self.function_section.get_query()
        iterate = self.function_section.iterate
        results_out = []
        if iterate:
            function = f'{function}\nresults_out.append(result)'
            for result in results:
                # function is a string which contains operations on result
                exec(function)
        else:
            # function is a string which contains operations on results
            function = f'{function}\nresults_out.append(results)'
            exec(function)
            print(results_out)

        return results_out


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


class RegExEntry(QueryEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_re = False

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        label = QLabel(self.label)
        grid.addWidget(label, 0, 0)

        re_check = QCheckBox('Use RegEx')
        re_check.setChecked(False)
        re_check.clicked.connect(self.re_check_click)
        grid.addWidget(re_check, 0, 1)

        self.query = QPlainTextEdit()
        grid.addWidget(self.query, 2, 0, 1, 2)
        self.query.setDisabled(True)

    def re_check_click(self):
        self.use_re = not self.use_re
        self.query.setDisabled(not self.use_re)


class FunctionEntry(QueryEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_function = False
        self.iterate = False

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.query = QPlainTextEdit()
        self.query.setDisabled(True)
        grid.addWidget(self.query, 4, 0)

        label = QLabel(self.label)
        grid.addWidget(label, 0, 0)

        none_button = QRadioButton('None')
        none_button.clicked.connect(lambda: self.clicked(none_button))
        grid.addWidget(none_button, 1, 0)
        none_button.setChecked(True)

        iterate_button = QRadioButton('Iterate')
        iterate_button.clicked.connect(lambda: self.clicked(iterate_button))
        grid.addWidget(iterate_button, 2, 0)

        no_iterate_button = QRadioButton("Don't Iterate")
        no_iterate_button.clicked.connect(lambda: self.clicked(no_iterate_button))
        grid.addWidget(no_iterate_button, 3, 0)

    def clicked(self, button):
        text = button.text()
        print(text)
        if text == 'None':
            self.use_function = False
            self.query.setDisabled(True)
        elif text == 'Iterate':
            self.iterate = True
            self.use_function = True
            self.query.setDisabled(False)
        elif text == 'Don\'t Iterate':
            self.iterate = False
            self.use_function = True
            self.query.setDisabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
