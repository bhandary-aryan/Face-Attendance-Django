import face_recognition
import cv2
import numpy as np
import json
from authentication.models import User, Student
from core.models import ClassSchedule, Attendance
from django.utils import timezone
import datetime

def load_known_faces():
    """Load all known face encodings from the database"""
    known_face_encodings = []
    known_face_names = []
    known_face_ids = []
    
    students = Student.objects.select_related('user').all()
    
    for student in students:
        user = student.user
        if user.face_encodings:
            try:
                face_encoding = np.array(json.loads(user.face_encodings))
                known_face_encodings.append(face_encoding)
                known_face_names.append(f"{user.first_name} {user.last_name}")
                known_face_ids.append(student.id)
                print(f"Loaded face data for: {user.first_name} {user.last_name}")
            except Exception as e:
                print(f"Error loading face encoding for {user.username}: {str(e)}")
    
    print(f"Successfully loaded {len(known_face_encodings)} face encodings")
    return known_face_encodings, known_face_names, known_face_ids

# In face_recognition_module/utils.py
def process_attendance(class_schedule_id, staff_user):
    """Process attendance for a specific class schedule with enhanced recognition"""
    print("Starting face recognition process...")
    
    try:
        class_schedule = ClassSchedule.objects.get(id=class_schedule_id)
    except ClassSchedule.DoesNotExist:
        return False, "Class schedule not found."
    
    # Load all known faces
    known_face_encodings, known_face_names, known_face_ids = load_known_faces()
    
    if not known_face_encodings:
        return False, "No student face data found. Please make sure students have uploaded profile pictures."
    
    print(f"Loaded {len(known_face_encodings)} known faces")
    
    # Initialize webcam
    video_capture = cv2.VideoCapture(0)
    
    # Improve camera settings if supported
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    video_capture.set(cv2.CAP_PROP_FPS, 30)
    
    if not video_capture.isOpened():
        return False, "Could not open webcam."
    
    # Set current date
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    
    # Track recognized students to avoid duplicates
    recognized_students = set()
    recognition_counts = {}  # Track multiple recognitions for confidence
    
    # Process frames from webcam
    process_this_frame = True
    
    # Initialize face_locations and face_names to avoid UnboundLocalError
    face_locations = []
    face_names = []
    
    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        
        if not ret:
            continue
        
        # Always process frames in test mode or alternate frames in normal mode
        if process_this_frame:
            # Resize frame for faster face recognition
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)  # Increased size for better detection
            
            # Convert BGR to RGB
            rgb_small_frame = small_frame[:, :, ::-1]
            
            # Apply light normalization to improve recognition in different lighting
            lab = cv2.cvtColor(rgb_small_frame, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            rgb_small_frame = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
            
            try:
                # Find all faces in the current frame
                face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
                print(f"Found {len(face_locations)} faces in frame")
                
                # Reset face_names for each frame
                face_names = []
                
                # Process face encodings
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    for face_encoding in face_encodings:
                        # Compare with known faces
                        name = "Unknown"
                        student_id = None
                        
                        # Use higher tolerance for challenging conditions
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.65)
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        
                        if len(face_distances) > 0:
                            best_match_index = np.argmin(face_distances)
                            confidence = 1 - face_distances[best_match_index]
                            print(f"Best match: {known_face_names[best_match_index]}, confidence: {confidence:.2f}")
                            
                            if matches[best_match_index] and confidence > 0.45:  # Lower threshold
                                name = known_face_names[best_match_index]
                                student_id = known_face_ids[best_match_index]
                                
                                # Increase recognition count
                                if student_id not in recognition_counts:
                                    recognition_counts[student_id] = 0
                                recognition_counts[student_id] += 1
                                
                                # Only mark attendance after multiple recognitions (reduces false positives)
                                if recognition_counts[student_id] >= 5 and student_id not in recognized_students:
                                    student = Student.objects.get(id=student_id)
                                    
                                    # Check if student is enrolled in this course
                                    if class_schedule.course in student.courses.all():
                                        # Determine status (present or late)
                                        status = 'present'
                                        if current_time > class_schedule.start_time:
                                            class_time = datetime.datetime.combine(
                                                datetime.date.today(), 
                                                class_schedule.start_time
                                            )
                                            current_datetime = datetime.datetime.combine(
                                                datetime.date.today(), 
                                                current_time
                                            )
                                            
                                            # If more than 15 minutes late
                                            if (current_datetime - class_time).total_seconds() > 15 * 60:
                                                status = 'late'
                                        
                                        # Create or update attendance record
                                        Attendance.objects.update_or_create(
                                            student=student,
                                            class_schedule=class_schedule,
                                            date=current_date,
                                            defaults={
                                                'time_in': current_time,
                                                'status': status,
                                                'face_confidence': float(confidence),
                                                'marked_by': staff_user
                                            }
                                        )
                                        
                                        recognized_students.add(student_id)
                                        print(f"Marked attendance for {name}")
                        
                        face_names.append(name)
            except Exception as e:
                print(f"Error during face detection: {str(e)}")
        
        process_this_frame = not process_this_frame
        
        # Display results
        display_frame = frame.copy()
        
        # Draw face boxes and names
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2
            
            # Draw a box around the face
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 0, 255), 2)
            
            # Draw a label with a name below the face
            cv2.rectangle(display_frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(display_frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        
        # Show info overlay
        cv2.putText(display_frame, f"Recognized: {len(recognized_students)} students", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Add list of recognized students
        y_pos = 70
        for i, student_id in enumerate(recognized_students):
            if i >= 10:  # Limit to showing 10 names
                cv2.putText(display_frame, f"... and {len(recognized_students) - 10} more", 
                            (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                break
                
            # Get student name
            for idx, sid in enumerate(known_face_ids):
                if sid == student_id:
                    name = known_face_names[idx]
                    cv2.putText(display_frame, f"✓ {name}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                    y_pos += 25
                    break
        
        cv2.putText(display_frame, "Press 'q' to finish", (10, display_frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Display the resulting image
        cv2.imshow('Face Recognition Attendance System', display_frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release webcam and close windows
    video_capture.release()
    cv2.destroyAllWindows()
    
    return True, f"Attendance processed successfully. Recognized {len(recognized_students)} students."

def train_face_model(user_id):
    """Train face recognition model for a user"""
    print(f"Starting face training for user ID: {user_id}")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False, "User not found."
    
    if not user.profile_pic:
        return False, "No profile picture found."
    
    try:
        # Load image and detect faces
        print(f"Loading image from: {user.profile_pic.path}")
        image = face_recognition.load_image_file(user.profile_pic.path)
        print(f"Image shape: {image.shape}")
        
        # Try multiple face detection methods
        face_locations = []
        
        # Try HOG method first (faster)
        face_locations = face_recognition.face_locations(image, model="hog")
        print(f"HOG model found {len(face_locations)} faces")
        
        # If HOG fails, try CNN (more accurate)
        if not face_locations:
            try:
                print("Trying CNN face detection model...")
                face_locations = face_recognition.face_locations(image, model="cnn")
                print(f"CNN model found {len(face_locations)} faces")
            except Exception as e:
                print(f"CNN detection error: {str(e)}")
        
        # If both fail, try with enhanced image
        if not face_locations:
            print("Trying image enhancement...")
            # Convert to grayscale and apply CLAHE
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            
            # Try detection on enhanced image
            face_locations = face_recognition.face_locations(enhanced_rgb)
            print(f"Enhanced image detection found {len(face_locations)} faces")
            
            if face_locations:
                image = enhanced_rgb
        
        if not face_locations:
            return False, "No face detected in the profile picture. Please upload a clearer photo with your face clearly visible."
        
        # If multiple faces found, use the largest one
        if len(face_locations) > 1:
            print(f"Multiple faces ({len(face_locations)}) found, using the largest one")
            largest_area = 0
            largest_idx = 0
            
            for i, (top, right, bottom, left) in enumerate(face_locations):
                area = (bottom - top) * (right - left)
                if area > largest_area:
                    largest_area = area
                    largest_idx = i
            
            face_locations = [face_locations[largest_idx]]
        
        try:
            # Get face encodings
            print("Generating face encoding...")
            face_encoding = face_recognition.face_encodings(image, face_locations)[0]
            
            # Save face encoding to user
            print("Saving face encoding...")
            user.face_encodings = json.dumps(face_encoding.tolist())
            user.save()
            
            return True, "Face model trained successfully."
        except IndexError:
            return False, "Could not generate encoding from the detected face. Please try a different photo."
        except Exception as e:
            print(f"Error during encoding: {str(e)}")
            
            # Try one more approach - extract the face and process it directly
            try:
                print("Trying direct face extraction...")
                top, right, bottom, left = face_locations[0]
                face_image = image[top:bottom, left:right]
                
                if face_image.size > 0:  # Make sure we extracted a valid face
                    # Try to encode this isolated face
                    face_encoding = face_recognition.face_encodings(face_image)[0]
                    
                    # Save face encoding to user
                    user.face_encodings = json.dumps(face_encoding.tolist())
                    user.save()
                    
                    return True, "Face model trained successfully using direct approach."
            except Exception as nested_e:
                print(f"Direct extraction failed: {str(nested_e)}")
            
            return False, f"Error generating face encoding: {str(e)}. Please upload a clearer photo with good lighting and a direct view of your face."
            
    except Exception as e:
        print(f"Fatal error in face training: {str(e)}")
        return False, f"Error training face model: {str(e)}"