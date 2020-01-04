import sys
import requests
from parsel import Selector
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from cssselect.xpath import ExpressionError
from cssselect.parser import SelectorSyntaxError
import traceback
import errors

from text_processor import EnhancedTextViewer

HOME = 'http://quotes.toscrape.com/'


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

    def update_url(self, url):
        self.queries.update_url(url)

    def update_source(self, text):
        self.source.setPlainText(text)


class QtBrowser(QWidget):
    def __init__(self, *args, main, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main
        self.html = None
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.go_button = QPushButton('Go')
        self.go_button.clicked.connect(self.go_to_page)
        grid.addWidget(self.go_button, 0, 3)

        self.entry_box = QLineEdit()
        self.entry_box.returnPressed.connect(self.go_button.click)
        grid.addWidget(self.entry_box, 0, 2)

        self.web = QWebEngineView()
        grid.addWidget(self.web, 1, 0, 1, 5)
        self.web.urlChanged.connect(self.update_url)
        self.web.loadStarted.connect(self.load_started)
        self.web.loadFinished.connect(self.load_finished)
        self.web.load(QUrl(HOME))

        back_button = BrowserButton(image=r'images/back.png')
        back_button.clicked.connect(self.web.back)
        grid.addWidget(back_button, 0, 0)

        forward_button = BrowserButton(image=r'images/forward.png')
        forward_button.clicked.connect(self.web.forward)
        grid.addWidget(forward_button, 0, 1)

        self.movie = MovieScreen(
            movie_file=r'images/loader.gif',
            end_file=r'images/empty.png',
        )
        self.movie.setMaximumHeight(20)
        self.movie.setMaximumWidth(20)
        grid.addWidget(self.movie, 0, 4)

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

    def load_started(self):
        self.go_button.setDisabled(True)
        self.movie.start()

    def load_finished(self):
        url = self.get_url()
        self.movie.stop()
        self.main.update_url(url)
        self.go_button.setEnabled(True)


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
        self.function_section.query.setPlainText(
            """# import packages

# must have 'user_fun' function with 'results' as argument and return a list

def user_fun(results):
  # your code
  return results"""
        )
        top.addWidget(self.function_section)
        self.addWidget(top)

        self.results = ResultsWidget()
        self.addWidget(self.results)

    def do_query(self):
        if self.html is None:
            return
        try:
            results = self.get_results()

            if not results:
                message = f'No results found for css query'
                errors.show_error_dialog(self, 'No Results', message, 'info')
                return

            use_regex = self.re_section.use
            if use_regex:
                results = self.regex_filter(results)
                if not results:
                    message = f'No results found for regex filter'
                    errors.show_error_dialog(self, 'No Results', message, 'info')
                    return
            else:
                results = results.getall()

            use_function = self.function_section.use
            if use_function:
                results = self.apply_function(results)
                if not results:
                    message = f'No results found for custom function'
                    errors.show_error_dialog(self, 'No Results', message, 'info')
                    return
        except errors.QueryError as e:
            errors.show_error_dialog(self, e.title, e.message, e.error_type)
            return

        self.results.add_results(results)

    def get_results(self):
        query = self.css_section.get_query()
        sel = Selector(text=self.html)
        try:
            results = sel.css(query)
        except (ExpressionError, SelectorSyntaxError) as e:
            message = f'Error parsing css query\n\n{e}'
            raise errors.QueryError(
                title='CSS Error',
                message=message,
                error_type='critical',
            )

        return results

    def regex_filter(self, results):
        regex = self.re_section.get_query()
        try:
            results = results.re(regex)
        except Exception as e:
            message = f'Error running regex\n\n{e}'
            raise errors.QueryError(
                title='RegEx Error',
                message=message,
                error_type='critical',
            )
        return results

    def apply_function(self, results):
        function = self.function_section.get_query()
        if not function:
            return
        if 'def user_fun(results):' not in function:
            message = f'Custom function needs to be named "user_fun" and have "results" as argument'
            raise errors.QueryError(
                title='Function Error',
                message=message,
                error_type='critical',
            )

        try:
            exec(function, globals())
            results = user_fun(results)
        except Exception as e:
            message = f'Error running custom function\n\n{type(e).__name__}: {e.args}'
            message += f'\n\n{traceback.format_exc()}'
            raise errors.QueryError(
                title='Function Error',
                message=message,
                error_type='critical',
            )

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


class ResultsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        label = QLabel("Results:")
        grid.addWidget(label, 0, 0)

        self.table = QTableWidget()
        self.table.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents,
        )

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        grid.addWidget(self.table, 1, 0)

    def add_results(self, results):
        self.table.clearContents()
        self.table.setColumnCount(1)
        self.table.setRowCount(0)

        for index, result in enumerate(results):
            if result is not None:
                self.table.insertRow(index)
                self.table.setItem(
                    index,
                    0,
                    QTableWidgetItem(str(result)),
                )
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        del results


class MovieScreen(QLabel):
    def __init__(self, *args, movie_file, end_file):
        super().__init__(*args)
        self.movie = QMovie(movie_file, QByteArray(), self)
        self.end = QMovie(end_file, QByteArray(), self)
        self.movie.setScaledSize(QSize(20, 20))
        self.end.setScaledSize(QSize(20, 20))
        self.setMovie(self.movie)

    def start(self):
        self.setMovie(self.movie)
        self.movie.start()

    def stop(self):
        self.movie.stop()
        self.setMovie(self.end)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
