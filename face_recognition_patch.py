import os

# Path to the face_recognition api.py file
api_path = os.path.join(os.path.expanduser('~'), 'Documents/FaceAttendance/venv/lib/python3.12/site-packages/face_recognition/api.py')

# Read the current content
with open(api_path, 'r') as f:
    content = f.read()

# Replace the problematic code block
original_block = """try:
    import face_recognition_models
except Exception:
    print("Please install `face_recognition_models` with this command before using `face_recognition`:\\n")
    print("pip install git+https://github.com/ageitgey/face_recognition_models")
    quit()"""

fixed_block = """try:
    import face_recognition_models
except Exception:
    print("Warning: Could not import face_recognition_models")
    # Instead of quitting, we'll define fallback paths for the models
    import os
    models_dir = os.path.join(os.path.expanduser('~'), 'Documents/FaceAttendance/venv/lib/python3.12/site-packages/face_recognition_models/models')
    
    class FaceRecognitionModelsFallback:
        @staticmethod
        def pose_predictor_model_location():
            return os.path.join(models_dir, 'shape_predictor_68_face_landmarks.dat')
            
        @staticmethod
        def pose_predictor_five_point_model_location():
            return os.path.join(models_dir, 'shape_predictor_5_face_landmarks.dat')
            
        @staticmethod
        def cnn_face_detector_model_location():
            return os.path.join(models_dir, 'mmod_human_face_detector.dat')
            
        @staticmethod
        def face_recognition_model_location():
            return os.path.join(models_dir, 'dlib_face_recognition_resnet_model_v1.dat')
    
    face_recognition_models = FaceRecognitionModelsFallback()"""

patched_content = content.replace(original_block, fixed_block)

# Save the patched file
with open(api_path, 'w') as f:
    f.write(patched_content)

print("Successfully patched face_recognition module!")
