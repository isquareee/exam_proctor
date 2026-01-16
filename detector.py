
import time
import math
import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from ultralytics import YOLO

# ==========================================
# Helpers / Utils
# ==========================================

class RollingFlag:
    """
    smooths out flickering detections.
    If 'is_active' is True for 'hold_seconds', the flag triggers.
    """
    def __init__(self, hold_seconds: float):
        self.hold = hold_seconds
        self.active_since = None

    def update(self, is_active: bool) -> bool:
        now = time.time()
        if is_active:
            if self.active_since is None:
                self.active_since = now
            return (now - self.active_since) >= self.hold
        else:
            self.active_since = None
            return False

def put_label(img, text, org=(10, 30), color=(0, 255, 0)):
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX,
                0.7, color, 2, cv2.LINE_AA)

def draw_box(img, box, color=(0, 255, 0), label=None):
    x1, y1, x2, y2 = [int(v) for v in box]
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    if label:
        cv2.rectangle(img, (x1, y1 - 22), (x1 + 8*len(label), y1), color, -1)
        cv2.putText(img, label, (x1 + 4, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

def compute_head_pose_flags(kps, box):
    """
    Return True if head pose suggests looking away based on simple yaw/pitch heuristics.
    kps: np.array shape (5,2) -> [left_eye, right_eye, nose, mouth_left, mouth_right]
    """
    left_eye, right_eye, nose, mouth_l, mouth_r = kps
    eyes_center = (left_eye + right_eye) / 2.0
    mouth_center = (mouth_l + mouth_r) / 2.0
    eye_dist = np.linalg.norm(right_eye - left_eye) + 1e-6
    
    # Yaw: horizontal offset of nose from eyes midpoint normalized by eye distance
    yaw_ratio = (nose[0] - eyes_center[0]) / eye_dist
    
    # Pitch: relative vertical position of nose between eyes and mouth
    eyes_to_mouth = (mouth_center[1] - eyes_center[1]) + 1e-6
    pitch_pos = (nose[1] - eyes_center[1]) / eyes_to_mouth  # ~0 near eyes, ~1 near mouth
    
    # Heuristics
    # You may need to tune these thresholds for your specific camera setup
    yaw_away = abs(yaw_ratio) > 0.45
    pitch_away = (pitch_pos < 0.15) or (pitch_pos > 0.85)
    
    return yaw_away or pitch_away

def preprocess_bgr_to_rgb(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


# ==========================================
# Main Detection Logic
# ==========================================

COCO_PHONE_NAME = "cell phone"
COCO_BOOK_NAME = "book"

class ProctorMonitor:
    """
    Per-frame monitoring: 
    1. Multi-face detection (using MTCNN)
    2. Head pose / Looking away (using Facial Keypoints)
    3. Object detection (Phone, Book using YOLOv8)
    4. Identity Verification (InceptionResnetV1)
    """

    def __init__(self, device: str | None = None):
        # Automatically detect device
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[ProctorMonitor] Using device: {self.device}")

        # Initialize MTCNN for face detection
        self.mtcnn = MTCNN(keep_all=True, device=self.device)
        
        # Initialize Face Recognition (vggface2)
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        self.reference_embedding = None
        self.identity_confirmed = False
        
        # Initialize YOLO for object detection
        # Ensure 'yolov8n.pt' is available or allowed to download
        self.yolo = YOLO("yolov8n.pt") 
        self.yolo.to(self.device)

        # Event timers (seconds) - to prevent instant triggering
        self.away_flag = RollingFlag(hold_seconds=2.5)
        self.multi_flag = RollingFlag(hold_seconds=1.0)
        self.phone_flag = RollingFlag(hold_seconds=1.0)
        self.book_flag = RollingFlag(hold_seconds=1.0)
        self.identity_flag = RollingFlag(hold_seconds=1.0)

        # Counters for stats
        self.counters = {
            "away_events": 0, 
            "multi_face_events": 0,
            "phone_events": 0, 
            "book_events": 0,
            "identity_events": 0
        }

        # Optimization: run YOLO less frequently than face detection
        self.last_yolo_time = 0.0
        self.yolo_interval = 0.6  # seconds
        self.last_objects = []

    def set_reference_face(self, frame_bgr):
        """Capture embedding for the first face found"""
        if frame_bgr is None: return False
        rgb = preprocess_bgr_to_rgb(frame_bgr)
        try:
            # Get cropped face tensor directly
            img_cropped = self.mtcnn(rgb)
            if img_cropped is not None:
                # mtcnn returns list of tensors if keep_all=True
                # But here we want the main face. 
                # If keep_all=True, it returns a LIST of tensors.
                # Use detect to find largest face first?
                # Simpler: just use detect to get box, then crop/resize manually or use mtcnn on crop
                
                # Let's rely on detect first to pick the best face (largest)
                boxes, probs = self.mtcnn.detect(rgb)
                if boxes is not None and len(boxes) > 0:
                    # Pick largest
                    areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
                    idx = int(np.argmax(areas))
                    box = boxes[idx]
                    
                    # Crop and resize to 160x160
                    x1, y1, x2, y2 = [int(n) for n in box]
                    padding = 10
                    h, w, _ = rgb.shape
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(w, x2 + padding)
                    y2 = min(h, y2 + padding)
                    
                    face_img = rgb[y1:y2, x1:x2]
                    if face_img.size == 0: return False
                    
                    face_resized = cv2.resize(face_img, (160, 160))
                    # Normalize (0-1) and standardized for Inception
                    face_tensor = torch.from_numpy(face_resized).permute(2, 0, 1).float() / 255.0
                    info_mean = 127.5/255.0 # standard
                    face_tensor = (face_tensor - 0.5) / 0.5 # Approximate standardization
                    
                    # Get embedding
                    with torch.no_grad():
                         self.reference_embedding = self.resnet(face_tensor.unsqueeze(0).to(self.device))
                    
                    self.identity_confirmed = True
                    print("✅ Identity Locked with Deep Learning")
                    return True
        except Exception as e:
            print(f"Set Reference Error: {e}")
        return False

    def process_frame(self, frame_bgr):
        """
        Takes a BGR frame (standard OpenCV format), performs detection,
        and returns:
          1. Annotated Frame (numpy array)
          2. Info Dictionary (status flags, counts)
        """
        if frame_bgr is None:
            return frame_bgr, {"face_count": 0, "away_now": False, "phone_present": False, "book_present": False, "identity_mismatch": False, "counters": self.counters}

        h, w = frame_bgr.shape[:2]
        rgb = preprocess_bgr_to_rgb(frame_bgr)
        annotated = frame_bgr.copy()

        # ---------------------------
        # 1. Face & Head Pose (MTCNN)
        # ---------------------------
        # Using try-except to handle MTCNN errors gracefully if any
        try:
             boxes, probs, landmarks = self.mtcnn.detect(rgb, landmarks=True)
        except Exception as e:
             # Fallback if detection fails
             print(f"MTCNN Error: {e}")
             boxes, probs, landmarks = None, None, None
             
        face_count = 0 if boxes is None else len(boxes)

        # Multi-face detection
        multi_trigger = self.multi_flag.update(face_count > 1)
        if multi_trigger:
            self.counters["multi_face_events"] += 1

        # Looking Away detection
        away_now = False  # Changed: Assume NOT away if no face (to avoid spam if camera blips)
        identity_mismatch = False
        
        if boxes is not None and landmarks is not None and face_count > 0:
            # Pick primary face (largest area)
            areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
            idx = int(np.argmax(areas))
            box = boxes[idx]
            kps = landmarks[idx]  # (5,2) points

            # Check head pose
            away_now = compute_head_pose_flags(kps, box)
            
            # Check Identity (if verified)
            if self.identity_confirmed and self.reference_embedding is not None:
                try:
                    # Crop face for recognition
                    x1, y1, x2, y2 = [int(n) for n in box]
                    padding = 10
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(w, x2 + padding)
                    y2 = min(h, y2 + padding)
                    face_img = rgb[y1:y2, x1:x2]
                    
                    if face_img.size > 0:
                        face_resized = cv2.resize(face_img, (160, 160))
                        face_tensor = torch.from_numpy(face_resized).permute(2, 0, 1).float() / 255.0
                        face_tensor = (face_tensor - 0.5) / 0.5
                        
                        with torch.no_grad():
                            curr_emb = self.resnet(face_tensor.unsqueeze(0).to(self.device))
                            # Euclidean distance
                            dist = (curr_emb - self.reference_embedding).norm().item()
                            
                            # Threshold (approx 1.0 for VGGface2, tune as needed)
                            if dist > 0.9: 
                                identity_mismatch = True
                                cv2.putText(annotated, f"ID: MISMATCH ({dist:.2f})", (x1, y1-20), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                            else:
                                cv2.putText(annotated, f"ID: Verified ({dist:.2f})", (x1, y1-20), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                except Exception as e:
                    print(f"Identity Check Error: {e}")

            # Draw primary face
            color = (0, 0, 255) if (away_now or identity_mismatch) else (0, 255, 0)
            draw_box(annotated, box, color=color, label="Primary")
            
            # Draw landmarks
            for (lx, ly) in kps:
                cv2.circle(annotated, (int(lx), int(ly)), 2, (0, 255, 255), -1)

        away_trigger = self.away_flag.update(away_now)
        if away_trigger:
            self.counters["away_events"] += 1
            
        identity_trigger = self.identity_flag.update(identity_mismatch)
        if identity_trigger:
            self.counters["identity_events"] += 1

        # ---------------------------
        # 2. Object Detection (YOLO)
        # ---------------------------
        now = time.time()
        detect_now = (now - self.last_yolo_time) >= self.yolo_interval
        phone_present = False
        book_present = False

        if detect_now:
            self.last_yolo_time = now
            # Resize for speed optimization
            short_side = 320 # Reduced from 640 for speed
            scale = short_side / max(h, w)
            new_w, new_h = int(w*scale), int(h*scale)
            resized = cv2.resize(rgb, (new_w, new_h))
            
            # Run YOLO
            # stream=True is faster
            results = self.yolo.predict(
                resized,
                imgsz=short_side, 
                conf=0.4,
                verbose=False,
                device=self.device
            )
            
            found = []
            for r in results:
                names = r.names
                for b in r.boxes:
                    cls_id = int(b.cls.item())
                    name = names.get(cls_id, str(cls_id))
                    conf = float(b.conf.item())
                    
                    if name in (COCO_PHONE_NAME, COCO_BOOK_NAME):
                        # Scale bbox back to original frame size
                        x1, y1, x2, y2 = b.xyxy[0].cpu().numpy().tolist()
                        x1, y1, x2, y2 = [v/scale for v in (x1, y1, x2, y2)]
                        found.append((name, conf, (x1, y1, x2, y2)))
            
            self.last_objects = found
        else:
             # Check consistency with previous frames for flags
             pass
        
        # Check objects from last detection
        for name, conf, box in self.last_objects:
             if name == COCO_PHONE_NAME: phone_present = True
             if name == COCO_BOOK_NAME: book_present = True

        # Draw tracked objects
        for name, conf, box in self.last_objects:
            color = (0, 0, 255) if name == COCO_PHONE_NAME else (255, 0, 0)
            draw_box(annotated, box, color=color, label=f"{name} {conf:.2f}")

        # Update persistent flags
        phone_trigger = self.phone_flag.update(phone_present)
        book_trigger = self.book_flag.update(book_present)
        
        if phone_trigger:
            self.counters["phone_events"] += 1
        if book_trigger:
            self.counters["book_events"] += 1

        # ---------------------------
        # 3. Annotations / HUD
        # ---------------------------
        put_label(annotated, f"Faces: {face_count}", (10, 28))
        put_label(annotated, f"Away: {'YES' if away_now else 'NO'}", (10, 56), 
                 color=(0, 0, 255) if away_now else (0, 255, 0))
        put_label(annotated, f"Phone: {'YES' if phone_present else 'NO'}", (10, 84), 
                 color=(0, 0, 255) if phone_present else (0, 255, 0))
        put_label(annotated, f"Book: {'YES' if book_present else 'NO'}", (10, 112), 
                 color=(0, 0, 255) if book_present else (0, 255, 0))
        
        stats_str = f"Events A/M/P/B/I: {self.counters['away_events']}/{self.counters['multi_face_events']}/{self.counters['phone_events']}/{self.counters['book_events']}/{self.counters['identity_events']}"
        put_label(annotated, stats_str, (10, 140))

        info = {
            "face_count": face_count,
            "away_now": away_now,
            "phone_present": phone_present,
            "book_present": book_present,
            "counters": self.counters,
            "triggers": {
                "away": away_trigger,
                "multi": multi_trigger,
                "phone": phone_trigger,
                "book": book_trigger,
                "identity": identity_trigger
            }
        }
        return annotated, info

    def cleanup(self):
        pass