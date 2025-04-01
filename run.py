import os
import sys
import site

# Add site-packages to path if needed
site_packages = site.getsitepackages()
for path in site_packages:
    if path not in sys.path:
        sys.path.append(path)

# Before importing Django, set up the environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

# Import Django after setting the environment
import django
django.setup()

# Import and patch face_recognition if needed
try:
    import face_recognition_models
    import face_recognition
    # Set any necessary attributes
    if not hasattr(face_recognition, 'face_recognition_models'):
        face_recognition.face_recognition_models = face_recognition_models
except ImportError as e:
    print(f"Import Error: {e}")
    pass

# Run Django
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'runserver'])
