import sys
import requests
from parsel import Selector
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit,
    QMainWindow, QGridLayout, QPlainTextEdit,
    QTableWidget, QLabel, QTabWidget, QVBoxLayout,
    QTableWidgetItem, QAbstractScrollArea, QCheckBox,
    QRadioButton, QMessageBox, QAbstractButton,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from cssselect.xpath import ExpressionError
from cssselect.parser import SelectorSyntaxError

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

        back_button = QPushButton('Back')
        back_button.clicked.connect(self.web.back)
        grid.addWidget(back_button, 0, 0)

        forward_button = QPushButton('Forward')
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


class Queries(QWidget):
    url = None
    html = None
    use_re = False

    def __init__(self, *args, main, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main
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
        if self.html is None:
            return
        try:
            results = self.get_results()

            if not results:
                message = f'No results found for css query'
                QMessageBox.information(self, 'No Results', message)
                return

            use_regex = self.re_section.use_re
            if use_regex:
                results = self.regex_filter(results)
                if not results:
                    message = f'No results found for regex filter'
                    QMessageBox.information(self, 'No Results', message)
                    return
            else:
                results = results.getall()

            use_function = self.function_section.use_function
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
        iterate = self.function_section.iterate
        results_out = []
        if iterate:
            function = f'{function}\nresults_out.append(result)'
            for result in results:
                # function is a string which contains operations on result variable
                try:
                    exec(function)
                except Exception as ex:

                    message = f'Error running custom function\n\n{type(ex).__name__}: {ex.args}'
                    QMessageBox.critical(self, 'Function Error', message)
                    raise QueryError
        else:
            # function is a string which contains operations on results
            function = f'{function}\nresults_out.append(results)'
            try:
                exec(function)
            except Exception as ex:
                message = f'Error running custom function\n\n{type(ex).__name__}: {ex.args}'
                QMessageBox.critical(self, 'Function Error', message)
                raise QueryError

        return results_out

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
