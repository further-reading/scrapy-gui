from PyQt5.QtWidgets import QMessageBox

ERROR_TYPES = {
    'info': QMessageBox.information,
    'critical': QMessageBox.critical,
}


class QueryError(Exception):
    def __init__(self, *args, title, message, error_type):
        super().__init__(*args)
        self.title = title
        self.message = message
        self.error_type = error_type


def show_error_dialog(parent, title, message, error_type):
    message_box = ERROR_TYPES[error_type]
    message_box(parent, title, message)
