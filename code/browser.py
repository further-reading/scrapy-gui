import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit,
    QMainWindow, QGridLayout,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView


class Main(QMainWindow):
    initial_width = 1080
    initial_height = 720

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Browser')
        self.setCentralWidget(QtBrowser(self))
        self.resize(self.initial_width, self.initial_height)
        self.show()


class QtBrowser(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history = []
        self.forward = []
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        self.setLayout(grid)

        back_button = QPushButton('Back')
        back_button.clicked.connect(self.go_back)
        grid.addWidget(back_button, 0, 0)

        forward_button = QPushButton('Forward')
        forward_button.clicked.connect(self.go_forward)
        forward_button.setDisabled(True)
        grid.addWidget(forward_button, 0, 1)

        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.refresh_page)
        grid.addWidget(refresh_button, 0, 2)

        go_button = QPushButton('Go')
        go_button.clicked.connect(self.go_to_page)
        grid.addWidget(go_button, 0, 3)

        self.entry_box = QLineEdit()
        self.entry_box.returnPressed.connect(go_button.click)
        grid.addWidget(self.entry_box, 0, 2)

        self.web = QWebEngineView()
        grid.addWidget(self.web, 1, 0, 1, 4)

    def go_back(self):
        pass

    def go_forward(self):
        pass

    def refresh_page(self):
        pass

    def go_to_page(self):
        print('foo')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
