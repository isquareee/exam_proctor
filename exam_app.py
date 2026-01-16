"""
Professional CBT Exam Proctoring System - COMPLETE
Tech Guru Level - MCQ with Timer, History, and Live Monitoring
"""

import sys
import cv2
import os
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np

# Assuming auth and detector are in the same directory and have been implemented/verified
from auth import AuthManager
from detector import ProctorMonitor


class VideoThread(QThread):
    """Thread for camera processing"""
    frame_ready = pyqtSignal(np.ndarray, dict) # Changed signal signature
    
    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self.running = False
    
    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if ret:
                processed_frame, info = self.detector.process_frame(frame)
                self.frame_ready.emit(processed_frame, info)
            self.msleep(33)
        cap.release()
    
    def stop(self):
        self.running = False
        self.wait()

class LoginWindow(QWidget):
    """Modern Login Screen"""
    login_success = pyqtSignal(dict)
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("CBT Exam Proctoring System")
        self.setMinimumSize(550, 650)
        
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        header = QLabel("🎓 CBT EXAM SYSTEM")
        header.setFont(QFont("Arial", 28, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            color: #1976D2;
            padding: 20px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #E3F2FD, stop:1 #BBDEFB);
            border-radius: 15px;
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Secure AI-Powered Proctoring")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 14px; font-style: italic;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Student ID
        id_label = QLabel("📋 Student ID")
        id_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        layout.addWidget(id_label)
        
        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Enter your Student ID")
        self.student_id_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus { border: 2px solid #2196F3; }
        """)
        layout.addWidget(self.student_id_input)
        
        # Password
        pwd_label = QLabel("🔒 Password")
        pwd_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        layout.addWidget(pwd_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(self.student_id_input.styleSheet())
        self.password_input.returnPressed.connect(self.login)
        layout.addWidget(self.password_input)
        
        layout.addSpacing(10)
        
        # Login button
        login_btn = QPushButton("🚀 LOGIN")
        login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                padding: 18px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976D2, stop:1 #1565C0);
            }
        """)
        login_btn.clicked.connect(self.login)
        login_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(login_btn)
        
        # Register link
        register_layout = QHBoxLayout()
        register_layout.addStretch()
        
        reg_label = QLabel("New student?")
        reg_label.setStyleSheet("color: #666;")
        register_layout.addWidget(reg_label)
        
        reg_btn = QPushButton("Register here")
        reg_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2196F3;
                border: none;
                font-weight: bold;
                text-decoration: underline;
            }
        """)
        reg_btn.clicked.connect(self.show_register)
        reg_btn.setCursor(Qt.PointingHandCursor)
        register_layout.addWidget(reg_btn)
        
        register_layout.addStretch()
        layout.addLayout(register_layout)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #FAFAFA;")
    
    def login(self):
        student_id = self.student_id_input.text().strip()
        password = self.password_input.text().strip()
        
        if not student_id or not password:
            QMessageBox.warning(self, "Error", "⚠️ Please enter both Student ID and Password")
            return
        
        success, result = self.auth.login_user(student_id, password)
        
        if success:
            self.login_success.emit(result)
            self.close()
        else:
            QMessageBox.critical(self, "Login Failed", f"❌ {result}")
    
    def show_register(self):
        dialog = RegisterDialog(self.auth, self)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "✅ Registration successful! Please login.")


class RegisterDialog(QDialog):
    """Registration Dialog"""
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth = auth_manager
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Student Registration")
        self.setFixedSize(500, 550)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)
        
        title = QLabel("📝 New Student Registration")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #2196F3;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Form fields
        self.student_id = QLineEdit()
        self.student_id.setPlaceholderText("Student ID")
        
        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Full Name")
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email (optional)")
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setPlaceholderText("Confirm Password")
        self.confirm_pwd.setEchoMode(QLineEdit.Password)
        
        for field in [self.student_id, self.full_name, self.email, self.password, self.confirm_pwd]:
            field.setStyleSheet("""
                QLineEdit {
                    padding: 12px;
                    border: 2px solid #E0E0E0;
                    border-radius: 6px;
                    font-size: 14px;
                }
                QLineEdit:focus { border: 2px solid #2196F3; }
            """)
            layout.addWidget(field)
        
        layout.addSpacing(20)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        register_btn = QPushButton("✅ Register")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        register_btn.clicked.connect(self.register)
        btn_layout.addWidget(register_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: white;")
    
    def register(self):
        if not all([self.student_id.text(), self.full_name.text(), self.password.text()]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields")
            return
        
        if self.password.text() != self.confirm_pwd.text():
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        
        success, result = self.auth.register_user(
            self.student_id.text().strip(),
            self.full_name.text().strip(),
            self.email.text().strip(),
            self.password.text().strip()
        )
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Registration Failed", str(result))


class HistoryWindow(QDialog):
    """Exam History Window"""
    
    def __init__(self, user_data, auth_manager, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.auth = auth_manager
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Exam History - {self.user_data['name']}")
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📊 Exam History")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Exam Code", "Score", "Violations", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)
        layout.addWidget(self.table)
        
        self.load_history()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: white;")
        
    def load_history(self):
        history = self.auth.get_user_history(self.user_data['user_id'])
        self.table.setRowCount(len(history))
        
        for i, sess in enumerate(history):
            # Parse date
            try:
                date_str = datetime.fromisoformat(sess['start_time']).strftime("%Y-%m-%d %H:%M")
            except:
                date_str = sess['start_time']
                
            self.table.setItem(i, 0, QTableWidgetItem(date_str))
            self.table.setItem(i, 1, QTableWidgetItem(sess['exam_code']))
            
            # Score processing
            score_item = QTableWidgetItem(f"{sess['score']}%")
            if sess['score'] >= 75:
                score_item.setForeground(QColor("#4CAF50")) # Green
            elif sess['score'] >= 50:
                score_item.setForeground(QColor("#FF9800")) # Orange
            else:
                score_item.setForeground(QColor("#F44336")) # Red
            score_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.table.setItem(i, 2, score_item)
            
            viol_item = QTableWidgetItem(str(sess['violations']))
            if sess['violations'] > 0:
                viol_item.setForeground(QColor("#F44336"))
            self.table.setItem(i, 3, viol_item)
            
            self.table.setItem(i, 4, QTableWidgetItem(sess['status']))


class DashboardWindow(QWidget):
    """Main Dashboard after login"""
    start_exam_signal = pyqtSignal()
    logout_signal = pyqtSignal()
    
    def __init__(self, user_data, auth_manager):
        super().__init__()
        self.user_data = user_data
        self.auth = auth_manager
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"Dashboard - {self.user_data['name']}")
        self.setMinimumSize(1000, 700)
        
        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Welcome header
        welcome = QLabel(f"👋 Welcome, {self.user_data['name']}!")
        welcome.setFont(QFont("Arial", 32, QFont.Bold))
        welcome.setStyleSheet("color: #1976D2;")
        layout.addWidget(welcome)
        
        subtitle = QLabel(f"Student ID: {self.user_data['student_id']}")
        subtitle.setStyleSheet("color: #666; font-size: 16px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        # Action buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(20)
        
        # Start Exam button
        start_btn = QPushButton("🎓 START EXAM")
        start_btn.setMinimumHeight(100)
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 15px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #45a049, stop:1 #388E3C);
            }
        """)
        start_btn.clicked.connect(self.start_exam_signal.emit)
        start_btn.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(start_btn)
        
        # Secondary buttons
        sec_layout = QHBoxLayout()
        sec_layout.setSpacing(20)
        
        history_btn = QPushButton("📊 VIEW HISTORY")
        history_btn.setMinimumHeight(80)
        history_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        history_btn.clicked.connect(self.view_history)
        history_btn.setCursor(Qt.PointingHandCursor)
        sec_layout.addWidget(history_btn)
        
        logout_btn = QPushButton("🚪 LOGOUT")
        logout_btn.setMinimumHeight(80)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        logout_btn.clicked.connect(self.logout_signal.emit)
        logout_btn.setCursor(Qt.PointingHandCursor)
        sec_layout.addWidget(logout_btn)
        
        btn_layout.addLayout(sec_layout)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #FAFAFA;")
        
    def view_history(self):
        history_win = HistoryWindow(self.user_data, self.auth, self)
        history_win.exec_()


class ExamWindow(QWidget):
    """Professional CBT Exam Window"""
    
    def __init__(self, user_data, auth_manager):
        super().__init__()
        self.user_data = user_data
        self.auth = auth_manager
        self.detector = ProctorMonitor()
        
        # Exam data
        self.questions = self.load_questions()
        self.current_q = 0
        self.answers = {}
        self.score = 0
        
        # Session state
        self.session_id = None
        self.violations = []
        
        # Timer
        self.exam_duration = 30 * 60  # 30 minutes in seconds
        self.time_left = self.exam_duration
        
        self.init_ui()
        self.start_exam()


    
    def init_ui(self):
        self.setWindowTitle(f"CBT Exam - {self.user_data['name']}")
        self.setWindowState(Qt.WindowMaximized)
        self.setMinimumSize(1200, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Split view
        split = QHBoxLayout()
        split.setSpacing(0)
        
        # LEFT: Questions (65%)
        questions_panel = self.create_questions_panel()
        split.addWidget(questions_panel, 65)
        
        # RIGHT: Camera (35%)
        camera_panel = self.create_camera_panel()
        split.addWidget(camera_panel, 35)
        
        main_layout.addLayout(split)
        
        self.setLayout(main_layout)
        
        # Setup Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        # Video thread
        self.video_thread = VideoThread(self.detector)
        self.video_thread.frame_ready.connect(self.update_frame)
    
    def create_top_bar(self):
        bar = QWidget()
        bar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1976D2, stop:1 #2196F3);
            padding: 15px;
        """)
        bar.setFixedHeight(80)
        
        layout = QHBoxLayout()
        
        # Exam title
        title = QLabel(f"📝 NETWORKING BASICS EXAM")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Student name
        name = QLabel(f"👤 {self.user_data['name']}")
        name.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(name)
        
        layout.addSpacing(30)
        
        # Timer
        timer_container = QWidget()
        timer_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 10px 20px;
        """)
        timer_layout = QHBoxLayout()
        timer_layout.setContentsMargins(10, 5, 10, 5)
        
        timer_icon = QLabel("⏱️")
        timer_icon.setStyleSheet("font-size: 24px;")
        timer_layout.addWidget(timer_icon)
        
        self.timer_label = QLabel("30:00")
        self.timer_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        timer_layout.addWidget(self.timer_label)
        
        timer_container.setLayout(timer_layout)
        layout.addWidget(timer_container)
        
        layout.addSpacing(20)
        
        # Violations
        self.violation_label = QLabel("⚠️ 0")
        self.violation_label.setStyleSheet("""
            color: #ffeb3b;
            font-size: 22px;
            font-weight: bold;
            background-color: rgba(255, 255, 255, 0.2);
            padding: 10px 20px;
            border-radius: 8px;
        """)
        layout.addWidget(self.violation_label)
        
        bar.setLayout(layout)
        return bar
    
    def create_questions_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: #FAFAFA;")
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Progress bar
        progress_widget = QWidget()
        progress_widget.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 15px;
        """)
        progress_layout = QVBoxLayout()
        
        self.progress_text = QLabel("Question 1 of 20")
        self.progress_text.setStyleSheet("font-size: 14px; font-weight: bold; color: #666;")
        progress_layout.addWidget(self.progress_text)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(20)
        self.progress_bar.setValue(1)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #E0E0E0;
                height: 10px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        progress_widget.setLayout(progress_layout)
        layout.addWidget(progress_widget)
        
        # Question display
        q_widget = QWidget()
        q_widget.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            padding: 25px;
        """)
        q_layout = QVBoxLayout()
        
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #333;
            padding: 15px;
            background-color: #E3F2FD;
            border-radius: 8px;
        """)
        q_layout.addWidget(self.question_label)
        
        q_widget.setLayout(q_layout)
        layout.addWidget(q_widget)
        
        # Options
        options_widget = QWidget()
        options_widget.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            padding: 20px;
        """)
        options_layout = QVBoxLayout()
        options_layout.setSpacing(15)
        
        self.option_group = QButtonGroup()
        self.option_buttons = []
        
        for i in range(4):
            radio = QRadioButton()
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 16px;
                    padding: 15px;
                    background-color: #F5F5F5;
                    border-radius: 8px;
                    spacing: 10px;
                }
                QRadioButton:hover {
                    background-color: #E3F2FD;
                }
                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                }
                QRadioButton::indicator:checked {
                    background-color: #2196F3;
                    border: 2px solid #1976D2;
                    border-radius: 10px;
                }
            """)
            self.option_group.addButton(radio, i)
            self.option_buttons.append(radio)
            options_layout.addWidget(radio)
            
        # Connect button clicked signal instead of toggled for cleaner handling
        self.option_group.buttonClicked.connect(self.option_selected)
        
        options_widget.setLayout(options_layout)
        layout.addWidget(options_widget)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(15)
        
        self.prev_btn = QPushButton("⬅️ PREVIOUS")
        self.prev_btn.setMinimumHeight(50)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #616161; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        self.prev_btn.clicked.connect(self.prev_question)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("NEXT ➡️")
        self.next_btn.setMinimumHeight(50)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        nav_layout.addWidget(self.next_btn)
        
        self.submit_btn = QPushButton("✅ SUBMIT EXAM")
        self.submit_btn.setMinimumHeight(50)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.submit_btn.clicked.connect(self.submit_exam)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setVisible(True) # Always visible now
        nav_layout.addWidget(self.submit_btn)
        
        layout.addLayout(nav_layout)
        
        panel.setLayout(layout)
        return panel
    
    def create_camera_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: #263238;")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 30, 20, 30)
        
        # Title
        title = QLabel("📹 LIVE MONITORING")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            background-color: #37474F;
            padding: 10px;
            border-radius: 8px;
        """)
        layout.addWidget(title)
        
        # Camera feed
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(400, 300)
        self.camera_label.setStyleSheet("""
            border: 3px solid #00BCD4;
            background-color: black;
            border-radius: 10px;
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setScaledContents(True)
        layout.addWidget(self.camera_label)
        
        # Status
        self.status_label = QLabel("✅ System Active")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #4CAF50;
            background-color: #1B5E20;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
        """)
        layout.addWidget(self.status_label)
        
        # Violations
        viol_header = QLabel("⚠️ Recent Violations")
        viol_header.setStyleSheet("color: #ffeb3b; font-weight: bold; font-size: 14px;")
        layout.addWidget(viol_header)
        
        self.violations_list = QListWidget()
        self.violations_list.setStyleSheet("""
            QListWidget {
                background-color: #37474F;
                color: #ffeb3b;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #455A64;
            }
        """)
        self.violations_list.setMaximumHeight(180)
        layout.addWidget(self.violations_list)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def load_questions(self):
        """Load 20 networking questions"""
        return [
            {"q": "What does LAN stand for?", "options": ["Large Area Network", "Local Area Network", "Long Area Network", "Limited Area Network"], "answer": 1},
            {"q": "Which device is used to connect multiple computers within a LAN?", "options": ["Modem", "Router", "Switch", "Firewall"], "answer": 2},
            {"q": "What is the main function of a router?", "options": ["To store data", "To connect different networks", "To amplify signals", "To protect against viruses"], "answer": 1},
            {"q": "Which network topology connects all devices to a central hub or switch?", "options": ["Bus", "Ring", "Star", "Mesh"], "answer": 2},
            {"q": "What does IP stand for in networking?", "options": ["Internet Process", "Internal Protocol", "Internet Protocol", "Information Path"], "answer": 2},
            {"q": "Which of the following is a valid IPv4 address?", "options": ["256.168.1.1", "192.168.1", "192.168.1.1", "192.168.1.999"], "answer": 2},
            {"q": "Which device connects a local network to the Internet?", "options": ["Switch", "Hub", "Router", "Repeater"], "answer": 2},
            {"q": "What type of cable is commonly used in Ethernet networks?", "options": ["Coaxial", "Fiber optic", "Twisted pair", "HDMI"], "answer": 2},
            {"q": "What does WAN stand for?", "options": ["Web Area Network", "Wide Area Network", "Wireless Access Network", "World Area Network"], "answer": 1},
            {"q": "Which protocol is used to send emails?", "options": ["FTP", "HTTP", "SMTP", "SNMP"], "answer": 2},
            {"q": "What is the purpose of a firewall?", "options": ["To speed up network traffic", "To block unauthorized access", "To connect networks", "To store data"], "answer": 1},
            {"q": "Which layer of the OSI model is responsible for data encryption?", "options": ["Physical", "Data Link", "Network", "Presentation"], "answer": 3},
            {"q": "What does DNS stand for?", "options": ["Domain Name System", "Data Network Service", "Digital Network Standard", "Domain Network Server"], "answer": 0},
            {"q": "Which protocol is used for secure web browsing?", "options": ["HTTP", "FTP", "SSH", "HTTPS"], "answer": 3},
            {"q": "What is the function of a MAC address?", "options": ["To identify a device on a network", "To route data packets", "To encrypt data", "To assign IP addresses"], "answer": 0},
            {"q": "Which of the following is a NOT a type of network?", "options": ["LAN", "WAN", "PAN", "CAN"], "answer": 3},
            {"q": "What does VPN stand for?", "options": ["Virtual Private Network", "Variable Public Network", "Verified Private Node", "Virtual Public Node"], "answer": 0},
            {"q": "Which protocol is used to transfer files over the Internet?", "options": ["HTTP", "FTP", "SMTP", "TCP"], "answer": 1},
            {"q": "What is the main purpose of the TCP protocol?", "options": ["To provide error-free data transmission", "To route data packets", "To encrypt data", "To assign IP addresses"], "answer": 0},
            {"q": "Which device regenerates and amplifies signals in a network?", "options": ["Router", "Switch", "Hub", "Repeater"], "answer": 3},
        ]

    def start_exam(self):
        # Create session in DB
        self.session_id = self.auth.start_exam_session(
            self.user_data['user_id'], 
            "NET-101"
        )
        
        # Start timer and video
        self.timer.start(1000)
        self.video_thread.start()
        
        self.update_question_display()

    def update_timer(self):
        self.time_left -= 1
        
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # Color coding
        if self.time_left <= 300: # 5 mins
            self.timer_label.setStyleSheet("color: #FF5252; font-size: 28px; font-weight: bold;")
        elif self.time_left <= 600: # 10 mins
            self.timer_label.setStyleSheet("color: #FFC107; font-size: 28px; font-weight: bold;")
            
        if self.time_left <= 0:
            self.timer.stop()
            self.submit_exam()

    def update_frame(self, frame, info):
        # Capture reference face if not set
        if not self.detector.identity_confirmed:
            if self.detector.set_reference_face(frame):
                self.status_label.setText("✅ Identity Locked")

        # Using info dict from ProctorMonitor
        # info keys: 'face_count', 'away_now', 'phone_present', 'book_present', 'counters', 'triggers'
        
        triggers = info.get('triggers', {})
        new_violations = []

        if triggers.get('away'):
             new_violations.append({'type': 'looking_away', 'message': '😒 Looking Away', 'confidence': 1.0})
        if triggers.get('phone'):
             new_violations.append({'type': 'phone_detected', 'message': '📱 Phone Detected', 'confidence': 1.0})
        if triggers.get('book'):
             new_violations.append({'type': 'book_detected', 'message': '📖 Book Detected', 'confidence': 1.0})
        if triggers.get('multi'):
             new_violations.append({'type': 'multiple_faces', 'message': '👥 Multiple Faces Detected', 'confidence': 1.0})
        if triggers.get('identity'):
             new_violations.append({'type': 'identity_mismatch', 'message': '🕵️ Identity Mismatch', 'confidence': 1.0})
        
        # Convert frame to QPixmap
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_img))
        
        # Log new violations
        for v in new_violations:
            self.auth.log_violation(
                self.session_id,
                v['type'],
                v['message'],
                v['confidence']
            )
            
            # Update UI
            item = QListWidgetItem(f"{v['message']} ({datetime.now().strftime('%H:%M:%S')})")
            if 'phone' in v['type'] or 'book' in v['type'] or 'identity' in v['type']:
                 item.setForeground(QColor("#FF5252")) # Red for severe
            else:
                 item.setForeground(QColor("#FFEB3B")) # Yellow for warning
            self.violations_list.insertItem(0, item)
            self.violations.append(v)
            
        # Update counts
        self.violation_label.setText(f"⚠️ {len(self.violations_list)}")

    def update_question_display(self):
        question = self.questions[self.current_q]
        
        self.progress_text.setText(f"Question {self.current_q + 1} of {len(self.questions)}")
        self.progress_bar.setValue(self.current_q + 1)
        
        self.question_label.setText(question['q'])
        
        # Temporarily disconnect to avoid triggering events while setting up
        self.option_group.setExclusive(False)
        for i, btn in enumerate(self.option_buttons):
            btn.setText(question['options'][i])
            if self.current_q in self.answers and self.answers[self.current_q] == i:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        self.option_group.setExclusive(True)
        
        # Enable/Disable buttons
        self.prev_btn.setEnabled(self.current_q > 0)
        
        if self.current_q == len(self.questions) - 1:
            self.next_btn.setVisible(False)
            self.submit_btn.setVisible(True)
        else:
            self.next_btn.setVisible(True)
            self.submit_btn.setVisible(False)

    def prev_question(self):
        if self.current_q > 0:
            self.current_q -= 1
            self.update_question_display()
            
    def next_question(self):
        if self.current_q < len(self.questions) - 1:
            self.current_q += 1
            self.update_question_display()
            
    def option_selected(self, btn):
        id = self.option_group.id(btn)
        self.answers[self.current_q] = id

    def submit_exam(self):
        # Confirmation
        if self.time_left > 0:
            confirm = QMessageBox.question(self, "Submit Exam", 
                                         "Are you sure you want to submit? This cannot be undone.",
                                         QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.No:
                return

        self.timer.stop()
        self.video_thread.stop()
        
        # Calculate score
        correct_count = 0
        for i, q in enumerate(self.questions):
            if i in self.answers and self.answers[i] == q['answer']:
                correct_count += 1
        
        pct_score = (correct_count / len(self.questions)) * 100
        
        # Save results
        self.auth.end_exam_session(self.session_id, len(self.violations_list), pct_score)
        
        # Show result
        msg = QMessageBox()
        msg.setWindowTitle("Exam Completed")
        msg.setText(f"Exam Submitted Automatically!" if self.time_left <= 0 else "Exam Submitted successfully!")
        msg.setInformativeText(f"Your Score: {pct_score:.1f}%\nViolations Detected: {len(self.violations_list)}")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        
        self.close()