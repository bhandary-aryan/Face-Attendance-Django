import sys
import site
import os

# Print paths to debug
print("Python Path:", sys.path)
print("Site Packages:", site.getsitepackages())

# Add site-packages to path if needed
site_packages = site.getsitepackages()
for path in site_packages:
    if path not in sys.path:
        sys.path.append(path)

# Try to import and verify
try:
    import face_recognition_models
    print("face_recognition_models is available at:", face_recognition_models.__file__)
except ImportError as e:
    print("Import Error:", e)
