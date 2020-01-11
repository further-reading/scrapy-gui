from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView

import os

HOME = 'http://quotes.toscrape.com/'


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

        back_button = BrowserButton(image=get_path('images/back.png'))
        back_button.clicked.connect(self.web.back)
        grid.addWidget(back_button, 0, 0)

        forward_button = BrowserButton(image=get_path('images/forward.png'))
        forward_button.clicked.connect(self.web.forward)
        grid.addWidget(forward_button, 0, 1)

        self.movie = MovieScreen(
            movie_file=get_path('images/loader.gif'),
            end_file=get_path('images/empty.png'),
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
        self.main.update_source(url)
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


def get_path(relative_path):
    dirname = os.path.dirname(__file__)
    print(dirname)
    full_path = os.path.join(dirname, relative_path)
    return full_path
