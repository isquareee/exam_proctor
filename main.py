"""
main.py - FIXED Entry Point
Run this file to start the exam proctoring system
"""

import sys
from PyQt5.QtWidgets import QApplication
import importlib.util
from pathlib import Path

# Load `auth.py` explicitly to avoid import-time conflicts or partial modules
spec = importlib.util.spec_from_file_location('auth_local', str(Path(__file__).parent / 'auth.py'))
auth_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth_mod)
AuthManager = auth_mod.AuthManager

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.auth = AuthManager()
        self.user_data = None
        self.show_login()
    
    def show_login(self):
        from exam_app import LoginWindow
        self.login_window = LoginWindow(self.auth)
        self.login_window.login_success.connect(self.start_exam)
        self.login_window.show()
    
    def start_exam(self, user_data):
        self.user_data = user_data
        from exam_app import ExamWindow
        self.exam_window = ExamWindow(user_data, self.auth)
        self.exam_window.show()
    
    def run(self):
        return self.app.exec_()


if __name__ == '__main__':
    app = App()
    sys.exit(app.run())