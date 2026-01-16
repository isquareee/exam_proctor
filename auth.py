"""
Complete Authentication System
Login, database, session management
"""

import sqlite3
import hashlib
from datetime import datetime
"""
Complete Authentication System
Login, database, session management
"""

import sqlite3
import hashlib
from datetime import datetime
import os


class AuthManager:
    """Handle authentication and database operations"""
    
    def __init__(self):
        self.db_path = 'data/users.db'
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Exam sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                exam_code TEXT,
                start_time TEXT,
                end_time TEXT,
                total_violations INTEGER DEFAULT 0,
                score REAL DEFAULT 0,
                status TEXT DEFAULT 'in_progress',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Check if score column exists (migration for existing db)
        cursor.execute("PRAGMA table_info(exam_sessions)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'score' not in columns:
            try:
                cursor.execute("ALTER TABLE exam_sessions ADD COLUMN score REAL DEFAULT 0")
                print("✅ specific score column added to existing database")
            except Exception as e:
                print(f"⚠️ Could not add score column: {e}")
        
        # Violations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                violation_type TEXT,
                message TEXT,
                confidence REAL,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES exam_sessions(session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Database initialized")
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, student_id, full_name, email, password):
        """Register new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (student_id, full_name, email, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (student_id, full_name, email, password_hash))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            print(f"✅ User registered: {full_name}")
            return True, user_id
            
        except sqlite3.IntegrityError:
            print(f"❌ Student ID {student_id} already exists")
            return False, "Student ID already registered"
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False, str(e)
    
    def login_user(self, student_id, password):
        """Login user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                SELECT id, student_id, full_name, email
                FROM users
                WHERE student_id = ? AND password_hash = ?
            ''', (student_id, password_hash))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                user_data = {
                    'user_id': result[0],
                    'student_id': result[1],
                    'name': result[2],
                    'email': result[3]
                }
                print(f"✅ Login successful: {user_data['name']}")
                return True, user_data
            else:
                print("❌ Invalid credentials")
                return False, "Invalid student ID or password"
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False, str(e)
    
    def start_exam_session(self, user_id, exam_code):
        """Start new exam session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exam_sessions (user_id, exam_code, start_time, status, score)
                VALUES (?, ?, ?, 'in_progress', 0)
            ''', (user_id, exam_code, datetime.now().isoformat()))
            
            conn.commit()
            session_id = cursor.lastrowid
            conn.close()
            
            print(f"✅ Exam session started: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ Session start error: {e}")
            return None
    
    def end_exam_session(self, session_id, total_violations, score=0):
        """End exam session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE exam_sessions
                SET end_time = ?, total_violations = ?, score = ?, status = 'completed'
                WHERE session_id = ?
            ''', (datetime.now().isoformat(), total_violations, score, session_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Exam session ended: {session_id} with score {score}")
            return True
            
        except Exception as e:
            print(f"❌ Session end error: {e}")
            return False
    
    def log_violation(self, session_id, violation_type, message, confidence):
        """Log violation to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO violations (session_id, violation_type, message, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, violation_type, message, confidence, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Violation log error: {e}")
            return False
    
    def get_session_violations(self, session_id):
        """Get all violations for a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT violation_type, message, confidence, timestamp
                FROM violations
                WHERE session_id = ?
                ORDER BY timestamp
            ''', (session_id,))
            
            violations = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'type': v[0],
                    'message': v[1],
                    'confidence': v[2],
                    'timestamp': v[3]
                }
                for v in violations
            ]
            
        except Exception as e:
            print(f"❌ Get violations error: {e}")
            return []

    def get_user_history(self, user_id):
        """Get exam history for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, exam_code, start_time, end_time, total_violations, score, status
                FROM exam_sessions
                WHERE user_id = ? AND status = 'completed'
                ORDER BY start_time DESC
            ''', (user_id,))
            
            sessions = cursor.fetchall()
            conn.close()
            history = []
            
            for s in sessions:
                history.append({
                    'session_id': s[0],
                    'exam_code': s[1],
                    'start_time': s[2],
                    'end_time': s[3],
                    'violations': s[4],
                    'score': s[5],
                    'status': s[6]
                })
            
            return history
            
        except Exception as e:
            print(f"❌ Get history error: {e}")
            return []