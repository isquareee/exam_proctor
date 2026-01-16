import mediapipe
print(f"File: {mediapipe.__file__}")
try:
    import mediapipe.python
    print(f"Mediapipe Python: {mediapipe.python}")
    from mediapipe.python import solutions
    print("Solutions found in mediapipe.python")
except ImportError as e:
    print(f"ImportError: {e}")
