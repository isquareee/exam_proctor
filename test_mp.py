try:
    import mediapipe as mp
    print(f"Mediapipe version: {mp.__version__}")
    print(f"Has solutions: {hasattr(mp, 'solutions')}")
    if hasattr(mp, 'solutions'):
        print(f"Solutions: {dir(mp.solutions)}")
    else:
        print(f"Dir mp: {dir(mp)}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
