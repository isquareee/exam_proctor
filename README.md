# Intelligent Exam Proctoring System

An AI-powered desktop application built with Python and PyQt5 designed to monitor online exams and detect potential academic dishonesty in real-time.

## 🚀 Features

- **Identity Verification**: Uses facial recognition (MTCNN + InceptionResnetV1) to ensure the correct candidate is taking the exam.
- **Head Pose Estimation**: Detects if the candidate is looking away from the screen for extended periods.
- **Object Detection**: Leverages YOLOv8 to detect prohibited items like cell phones and books.
- **Multi-Face Detection**: Ensures only one person is visible in the camera frame.
- **Modern UI**: A sleek, user-friendly interface built with PyQt5.
- **Local Database**: Securely stores user credentials and exam session data.

## 🛠️ Tech Stack

- **GUI**: PyQt5
- **AI/ML**: 
  - [PyTorch](https://pytorch.org/)
  - [YOLOv8 (Ultralytics)](https://github.com/ultralytics/ultralytics)
  - [FaceNet (facenet-pytorch)](https://github.com/timesler/facenet-pytorch)
  - [MTCNN](https://github.com/ipazc/mtcnn)
- **Computer Vision**: OpenCV
- **Database**: SQLite

## 📋 Prerequisites

Before running the application, ensure you have:
- Python 3.10 or higher
- A working webcam
- (Optional) NVIDIA GPU with CUDA for faster AI inference

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/exam_proctor.git
   cd exam_proctor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🖥️ Usage

1. **Start the application**:
   ```bash
   python main.py
   ```

2. **Login/Register**: Use the authentication screen to create an account or log in.
3. **Face Capture**: The system will first capture your reference face for identity verification.
4. **Take Exam**: Proceed to the exam screen. The AI monitor will run in the sidebar, providing real-time feedback on violations.

## 📁 Project Structure

- `main.py`: Entry point for the application.
- `exam_app.py`: PyQt5 GUI implementation (Login, Exam screens).
- `detector.py`: Core AI logic for face detection, pose estimation, and object detection.
- `auth.py`: Authentication and database management.
- `requirements.txt`: List of Python dependencies.

---
Built with ❤️ by AI and Human collaboration.
