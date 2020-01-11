from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from .parser import Parser
from . import errors


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

# must have 'user_fun' function with\n'results' and 'selector' as arguments\nand return a list

def user_fun(results, selector):
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
        parser = Parser(self.html)
        css = self.css_section.get_query()

        if self.re_section.use:
            regex = self.re_section.get_query()
        else:
            regex = None
        if self.function_section.use:
            function = self.function_section.get_query()
        else:
            function = None

        try:
            results = parser.do_query(css, parser.selector, regex, function)
        except errors.QueryError as e:
            errors.show_error_dialog(
                self,
                e.title,
                e.message,
                e.error_type,
            )
            return

        self.results.add_results(results)

    def update_source(self, text):
        self.html = text


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
        self.query.setLineWrapMode(QPlainTextEdit.NoWrap)

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
        self.query.setLineWrapMode(QPlainTextEdit.NoWrap)
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
