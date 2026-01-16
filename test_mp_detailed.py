import sys
try:
    import mediapipe
    print(f"Path: {mediapipe.__path__}")
    try:
        from mediapipe import solutions
        print("Imported solutions directly")
    except ImportError:
        print("Could not import solutions directly")
    
    try:
        import mediapipe.python.solutions as solutions
        print("Imported mediapipe.python.solutions")
    except ImportError:
        print("Could not import mediapipe.python.solutions")

    import mediapipe as mp
    if hasattr(mp, 'solutions'):
         print("mp.solutions exists")
    else:
         print("mp.solutions does NOT exist")

except Exception as e:
    print(e)
